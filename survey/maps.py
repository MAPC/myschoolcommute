import os, sys

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, GEOSGeometry, MultiPolygon
from django.core.cache import cache, get_cache
from django.utils import simplejson
from django.db import connection
from django.conf import settings

import pickle
import mapnik
import cairo
import tempfile
import mimetypes
import math
import time
import urllib
from shapely import ops, geometry

from survey.models import School, Survey

from myschoolcommute.local_settings import DATABASES

BLUE = "#0088CC"
GRAY = "#DDDDDD"

LAVENDER = "#E6E6FA"
PURPLE = "#9370DB"
VIOLET = "#9400D3"
PEACHPUFF = "#FFDAB9"
LIGHTCYAN = "#E0FFFF"


class Lock:
    def __init__(self, filename):
        self.filename = filename
        # This will create it if it does not exist already
        self.handle = open(filename, 'w')

    # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock
    def acquire(self):
        fcntl.flock(self.handle, fcntl.LOCK_EX)

    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)

    def __del__(self):
        self.handle.close()


class NetworkWalk(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    geometry = models.LineStringField(srid=26986)
    objects = models.GeoManager()

    class Meta:
        db_table = 'walks'


class NetworkBike(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    geometry = models.LineStringField(srid=26986)
    objects = models.GeoManager()

    class Meta:
        db_table = 'survey_network_bike'


def mapnik_extent(geometry):
    extent = list(geometry.extent)
    bbox_ratio = (extent[2] - extent[0]) / (extent[3] - extent[1])

    if bbox_ratio < 1:
        offset = (extent[0] - extent[2]) * (1 - bbox_ratio) / 2
        extent[2] = extent[2] - offset
        extent[0] = extent[0] + offset

    elif bbox_ratio > 1:
        offset = (extent[3] - extent[1]) * (bbox_ratio - 1) / 2
        extent[1] = extent[1] - offset
        extent[3] = extent[3] + offset
    return extent


def paths_sql(school_id, network='survey_network_walk', miles=1.5):

    school = """st_transform(
        (SELECT geometry FROM survey_school WHERE id = %d), 26986
    )""" % int(school_id)

    closest_street = """(
        SELECT source from {0} ORDER BY
        {1} <-> geometry
        asc limit 1
    )""".format(network, school)

    query = """SELECT ogc_fid, geometry, route.cost from {0} as w
                JOIN
                (SELECT * FROM
                   driving_distance(
                        'SELECT ogc_fid as id, source, target, miles AS cost
                         FROM {0}
                         WHERE geometry && ST_Buffer(ST_Envelope({1}), 8000)'
                        , {2}, {3}, false, false
                    )) AS route
                ON
                w.target = route.vertex_id
    """.format(network, school, closest_street, miles)

    return query


def get_sheds(school_id):
    query = paths_sql(school_id, miles=1.5)
    bike_query = paths_sql(school_id, 'survey_network_bike', miles=2.0)

    cursor = connection.cursor()
    hull_query = """
    WITH paths as (%s)
    SELECT ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from (%s) as BIKE))
    ),
    ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 1.5))
    ),
    ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 1.0))
    ),
    ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 0.5))
    )""" % (query, bike_query)

    cursor.execute(hull_query)
    row = cursor.fetchone()
    data = {2.0: row[0], 1.5: row[1], 1.0: row[2], 0.5: row[3]}

    return data

def school_sheds(request=None, school_id=None, bbox=None, width=500, height=700, srid=3857, format='png'):
    format = format.encode('ascii')
    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(3000.0)

    m = mapnik.Map(int(width), int(height), "+init=epsg:"+str(srid))

    mapnik.load_map(m, os.path.dirname(__file__)+"/basemap/basemap.xml")

    if bbox is None:
        circle.transform(srid)
        bbox = mapnik.Box2d(*circle.extent)
    m.zoom_to_box(bbox)

    #m.background = mapnik.Color('steelblue')

    # styles for sheds
    s = mapnik.Style()
    for name, color in (('0.5', VIOLET), ('1.0', PURPLE), ('1.5', LAVENDER), ('2.0', LIGHTCYAN)):
        r = mapnik.Rule()
        r.filter = mapnik.Filter("[name] = "+name)
        c = mapnik.Color(color)
        c.a = 80
        line_symbolizer = mapnik.LineSymbolizer(mapnik.Color("gray"), 1)
        poly_symbolizer = mapnik.PolygonSymbolizer(c)
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)
    m.append_style("sheds", s)

    #styles end

    sheds = {
        0.5: school.shed_05,
        1.0: school.shed_10,
        1.5: school.shed_15,
        2.0: school.shed_20
    }

    csv_string = 'wkt,name\n'
    for key, g in reversed(sorted(sheds.items(), key=lambda a: a[0])):
        if g is None:
            continue
        g.srid = 26986
        g.transform(srid)
        csv_string += '"%s","%s"\n' % (g.wkt, str(key))

    layer = mapnik.Layer('sheds', "+init=epsg:"+str(srid))
    ds = mapnik.Datasource(type="csv", inline=csv_string.encode('ascii'))
    layer.datasource = ds
    layer.styles.append('sheds')
    m.layers.append(layer)


    # styles for schools
    school_colors = (
        ('w', "blue"),
        ('cp', "purple"),
        ('sb', "yellow"),
        ('fv', "red"),
        ('t', 'violet'),
        ('none', 'lightgrey'),
    )

    s = mapnik.Style()
    for name, color in school_colors:
        r = mapnik.Rule()
        r.filter = mapnik.Filter("[name] = '"+name+"'")
        line_symbolizer = mapnik.LineSymbolizer()
        poly_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(color))
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)
    m.append_style("surveys", s)

    csv_string = "wkt,name\n"
    surveys = Survey.objects.filter(school=school)
    for survey in surveys:
        survey.location.transform(srid)
        name = "none"
        for c in survey.child_set.all():
            name = str(c.to_school)
        school_circle = survey.location.buffer(50)
        csv_string += '"%s","%s"\n' % (school_circle.wkt, name)

    layer = mapnik.Layer('surveys', "+init=epsg:"+str(srid))
    ds = mapnik.Datasource(type="csv", inline=csv_string.encode('ascii'))
    layer.datasource = ds
    layer.styles.append('surveys')
    m.layers.append(layer)

    # Render to image
    if format == 'pdf':
        tmp_file = tempfile.NamedTemporaryFile()
        surface = cairo.PDFSurface(tmp_file.name, m.width, m.height)
        mapnik.render(m, surface)
        surface.finish()
        tmp_file.seek(0)
        im = tmp_file.read()
    elif format == 'PDF':
        from mapnik.printing import PDFPrinter
        printer = PDFPrinter()
        tmp_file = tempfile.NamedTemporaryFile()
        printer.render_map(m, tmp_file.name)
        printer.finish()
        tmp_file.seek(0)
        im = tmp_file.read()
    else:
        im = mapnik.Image(m.width, m.height)
        mapnik.render(m, im)
        im = im.tostring(format)

    response = HttpResponse()
    response['Content-length'] = str(len(im))
    response['Content-Type'] = mimetypes.types_map['.'+format]
    response.write(im)

    return response


def save_sheds(filename, school_id):
    response = school_sheds(school_id=school_id, format='pdf')

    output = open(filename, "wb")
    output.write(response.content)
    output.close()


def school_sheds_json(request, school_id):
    school = School.objects.get(pk=school_id)
    sheds = {
        0.5: school.shed_05,
        1.0: school.shed_10,
        1.5: school.shed_15,
        2.0: school.shed_20
    }

    features = []
    for dist, geom in sheds.items():
        if geom is None:
            continue

        geom.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"distance": "%0.1f"}
        }""" % (geom.geojson, dist))

    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)


def ForkRunR(school_id, date1, date2):
    import subprocess
    school = School.objects.get(id=school_id)
    org_code = school.schid
    rdir = os.path.abspath(os.path.join(settings.CURRENT_PATH, '../R'))
    workdir = 'figure'
    wdir = os.path.join(rdir, workdir)
    os.chdir(rdir)
    if not os.path.exists(wdir):
        os.makedirs(wdir)
    save_sheds(os.path.join(wdir, 'map.pdf'), school_id)

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(cur_dir)
    #print " ".join(['./runr.py', wdir, rdir, org_code, str(date1), str(date2)])
    subprocess.call(['./runr.py', wdir, rdir, org_code, str(date1), str(date2)])

    pdfpath = os.path.join(rdir, 'minimal.pdf')
    return pdfpath


def get_driving_distance(src, dst):
    '''
    Returns driving distance between geometries in miles
    '''
    url = 'http://maps.googleapis.com/maps/api/directions/json'
    src.transform(4326)
    dst.transform(4326)
    params = urllib.urlencode({
        'sensor': 'false',
        'origin': "%f,%f" % (src.y, src.x),
        'destination': "%f,%f" % (dst.y, dst.x)
    })

    response = urllib.urlopen(url+'?'+params).read()
    data = simplejson.loads(response)
    meters = data['routes'][0]['legs'][0]['distance']['value']
    miles = meters * 0.000621371
    return miles


def test_driving_distance():
    from survey.models import Survey
    s = Survey.objects.all().order_by("id")[308]
    return get_driving_distance(s.location, s.school.geometry)


def update_schools_sheds():
    schools = School.objects.filter(id__gt=30).order_by('id')
    for s in schools:
        sheds = get_sheds(s.id)
        print s.id
        s.shed_05 = MultiPolygon(GEOSGeometry(sheds[0.5]))
        s.shed_10 = MultiPolygon(GEOSGeometry(sheds[1.0]))
        s.shed_15 = MultiPolygon(GEOSGeometry(sheds[1.5]))
        s.shed_20 = MultiPolygon(GEOSGeometry(sheds[2.0]))

        g = s.shed_20.difference(s.shed_15)
        try:
            s.shed_20 = g
        except TypeError:
            if g.area == 0:
                s.shed_20 = None

        g = s.shed_15.difference(s.shed_10)
        try:
            s.shed_15 = g
        except TypeError:
            if g.area == 0:
                s.shed_15 = None

        g = s.shed_15.difference(s.shed_10)
        try:
            s.shed_15 = g
        except TypeError:
            if g.area == 0:
                s.shed_15 = None

        s.save()

