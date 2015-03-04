import os, sys

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, GEOSGeometry, MultiPolygon, Polygon, LinearRing
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
import random
from shapely import ops, geometry

from survey.models import School, Survey, MODE_DICT

from myschoolcommute.local_settings import DATABASES

BLUE = "#0088CC"
GRAY = "#DDDDDD"

LAVENDER = "#E6E6FA"
PURPLE = "#9370DB"
VIOLET = "#9400D3"
PEACHPUFF = "#FFDAB9"
LIGHTCYAN = "#E0FFFF"


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

    school = """
        ST_SetSRID(
            (SELECT geometry FROM survey_school WHERE id = {}), 26986
        )
    """.format(int(school_id))

    closest_street = """
        (SELECT source from {0} ORDER BY
            {1} <-> geometry
            asc limit 1
        )
    """.format(network, school)

    query = """
        SELECT ogc_fid, geometry, route.cost from {0} as w
        JOIN
        (SELECT * FROM
           pgr_drivingdistance(
                'SELECT ogc_fid as id, source, target, miles AS cost
                 FROM {0}
                 WHERE geometry && ST_Buffer(ST_Envelope({1}), 8000)'
                , {2}, {3}, false, false
            )) AS route
        ON
        w.target = route.id1
    """.format(network, school, closest_street, miles)

    return query


def get_sheds(school_id):
    query = paths_sql(school_id, miles=1.5)
    bike_query = paths_sql(school_id, 'survey_network_bike', miles=2.0)

    cursor = connection.cursor()
    hull_query = """
        WITH paths as (%s)
        SELECT ST_AsEWKT(
            ST_MakeValid(
                ST_Transform(
                    ST_Union(
                        array(
                            select ST_BUFFER(geometry, 100) from (%s) as BIKE
                        )
                    ),
                    26986
                )
            )
        ) as _20,
        ST_AsEWKT(
            ST_MakeValid(
                ST_Transform(
                    ST_Union(
                        array(
                            select ST_BUFFER(geometry, 100) from paths where cost < 1.5
                        )
                    ),
                    26986
                )
            )
        ) as _15,
        ST_AsEWKT(
            ST_MakeValid(
                ST_Transform(
                    ST_Union(
                        array(
                            select ST_BUFFER(geometry, 100) from paths where cost < 1.0
                        )
                    ),
                    26986
                )
            )
        ) as _10,
        ST_AsEWKT(
            ST_MakeValid(
                ST_Transform(
                    ST_Union(
                        array(
                            select ST_BUFFER(geometry, 100) from paths where cost < 0.5
                        )
                    ),
                    26986
                )
            )
        ) as _05
    """ % (query, bike_query)

    cursor.execute(hull_query)
    row = cursor.fetchone()
    data = {2.0: row[0], 1.5: row[1], 1.0: row[2], 0.5: row[3]}

    return data


def school_sheds(request=None, school_id=None, bbox=None, width=816, height=1056, srid=3857, format='png'):
    '''
    Default height and width are 'Letter' ratio
    '''

    format = format.encode('ascii')
    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(3400.0)

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
        r.filter = mapnik.Expression("[name] = "+name)
        c = mapnik.Color(color)
        c.a = 80
        line_symbolizer = mapnik.LineSymbolizer(mapnik.Color("gray"), 1)
        poly_symbolizer = mapnik.PolygonSymbolizer(c)
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'legend_box'")
    poly_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("white"))
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color("black"), 0.5)
    poly_symbolizer.fill_opacity = 0.8
    r.symbols.append(line_symbolizer)
    r.symbols.append(poly_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] != 'map_title' and [name] != 'map_subtitle' and [name] != 'legend_title' and [name] != 'school'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 9, mapnik.Color('black'))
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.halo_radius = 1
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    #text_symbolizer.label_placement = mapnik.label_placement.VERTEX_PLACEMENT
    text_symbolizer.allow_overlap = True
    text_symbolizer.displacement = (12, 0)
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'map_title'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 15, mapnik.Color('black'))
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.allow_overlap = True
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'map_subtitle'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 12, mapnik.Color('black'))
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.allow_overlap = True
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'school'")
    ps = mapnik.PointSymbolizer(mapnik.PathExpression(os.path.dirname(__file__)+'/static/img/School.svg'))
    ps.transform = 'scale(0.06)'
    ps.allow_overlap = True
    #shield.label_placement = mapnik.label_placement.POINT_PLACEMENT
    r.symbols.append(ps)
    s.rules.append(r)

    m.append_style("surveys", s)

    def p2l(pct_x, pct_y):
        loc_x = bbox.minx + (bbox.maxx - bbox.minx) * pct_x / 100.0
        loc_y = bbox.miny + (bbox.maxy - bbox.miny) * pct_y / 100.0
        return (loc_x, loc_y)

    sheds = {
        0.5: school.shed_05,
        1.0: school.shed_10,
        1.5: school.shed_15,
        2.0: school.shed_20
    }

    csv_string = 'wkt,name,label\n'
    for key, g in reversed(sorted(sheds.items(), key=lambda a: a[0])):
        if g is None:
            continue
        g.srid = 26986
        g.transform(srid)
        csv_string += '"%s","%s",""\n' % (g.wkt, str(key))

    #Add School geometry
    school.geometry.transform(srid)
    csv_string += '"%s","school","%s"\n' % (school.geometry.wkt, school.name)

    def box(minx, miny, maxx, maxy):
        lmin = Point(p2l(minx, miny))
        lmax = Point(p2l(maxx, maxy))
        lr = LinearRing((lmin.x, lmin.y), (lmax.x, lmin.y), (lmax.x, lmax.y), (lmin.x, lmax.y), (lmin.x, lmin.y))
        poly = Polygon(lr)
        return poly

    legend = box(2, 108, 50, 113.5)
    csv_string += '"%s","%s","%s"\n' % (legend.wkt, "legend_box", "")

    xy = p2l(3.5, 112)
    point = Point(*xy)
    csv_string += '"%s","%s","School Commute Walksheds"\n' % (point.wkt, "map_title")

    xy = p2l(3.5, 109.5)
    point = Point(*xy)
    csv_string += '"%s","%s","%s, %s"\n' % (point.wkt, "map_subtitle", school, school.districtid)

    legend_x = 80

    #legend = box(legend_x, 97, 97.5, 113.5)
    #csv_string += '"%s","%s","%s"\n' % (legend.wkt, "legend_box", "")

    xy = p2l(legend_x + 1.5, 112)
    point = Point(*xy)
    csv_string += '"%s","legend_title","Approx. home locations and travel to school mode"\n' % (point.wkt, )

    walksheds_x = 88
    xy = p2l(walksheds_x, 112)
    point = Point(*xy)
    csv_string += '"%s","legend_title","Walksheds"\n' % (point.wkt, )

    y = 110
    for name in ('0.5', '1.0', '1.5', '2.0',):
        y -= 2.4
        ws = box(walksheds_x, y, walksheds_x+2, y+1.5)
        csv_string += '"%s","%s","%s  Mile"\n' % (ws.wkt, name, name)

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
    else:
        im = mapnik.Image(m.width, m.height)
        mapnik.render(m, im)
        im = im.tostring(format)

    response = HttpResponse()
    response['Content-length'] = str(len(im))
    response['Content-Type'] = mimetypes.types_map['.'+format]
    response.write(im)

    return response


SCHOOL_COLORS = (
    ('w', "blue"),
    ('fv', "red"),
    ('cp', "violet"),
    ('sb', "yellow"),
    ('b', "lightgreen"),
    ('t', "purple"),
    ('o', 'lightgrey'),
)


def school_sheds_results(request=None, school_id=None, bbox=None, width=816, height=1056, srid=3857, format='png'):
    '''
    Default height and width are 'Letter' ratio
    '''

    format = format.encode('ascii')
    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(3400.0)

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
        r.filter = mapnik.Expression("[name] = "+name)
        c = mapnik.Color(color)
        c.a = 80
        line_symbolizer = mapnik.LineSymbolizer(mapnik.Color("gray"), 1)
        poly_symbolizer = mapnik.PolygonSymbolizer(c)
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)

    # styles for schools
    school_colors = SCHOOL_COLORS

    for name, color in school_colors:
        r = mapnik.Rule()
        r.filter = mapnik.Expression("[name] = '"+name+"'")
        line_symbolizer = mapnik.LineSymbolizer()
        poly_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(color))
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)
    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] != 'map_title' and [name] != 'map_subtitle' and [name] != 'legend_title' and [name] != 'school'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 9, mapnik.Color('black'))
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.halo_radius = 1
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    #text_symbolizer.label_placement = mapnik.label_placement.VERTEX_PLACEMENT
    text_symbolizer.allow_overlap = True
    text_symbolizer.displacement = (12, 0)
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'map_title'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 15, mapnik.Color('black'))
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.allow_overlap = True
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'map_subtitle'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Book', 12, mapnik.Color('black'))
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.allow_overlap = True
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'legend_title'")
    text_symbolizer = mapnik.TextSymbolizer(mapnik.Expression('[label]'), 'DejaVu Sans Condensed Bold', 11, mapnik.Color('black'))
    text_symbolizer.horizontal_alignment = mapnik.horizontal_alignment.RIGHT
    text_symbolizer.halo_fill = mapnik.Color('white')
    text_symbolizer.halo_radius = 1
    text_symbolizer.allow_overlap = True
    r.symbols.append(text_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'legend_box'")
    poly_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("white"))
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color("black"), 0.5)
    poly_symbolizer.fill_opacity = 0.8
    r.symbols.append(line_symbolizer)
    r.symbols.append(poly_symbolizer)
    s.rules.append(r)

    r = mapnik.Rule()
    r.filter = mapnik.Expression("[name] = 'school'")
    ps = mapnik.PointSymbolizer(mapnik.PathExpression(os.path.dirname(__file__)+'/static/img/School.svg'))
    ps.transform = 'scale(0.06)'
    ps.allow_overlap = True
    #shield.label_placement = mapnik.label_placement.POINT_PLACEMENT
    r.symbols.append(ps)
    s.rules.append(r)

    m.append_style("surveys", s)

    def p2l(pct_x, pct_y):
        loc_x = bbox.minx + (bbox.maxx - bbox.minx) * pct_x / 100.0
        loc_y = bbox.miny + (bbox.maxy - bbox.miny) * pct_y / 100.0
        return (loc_x, loc_y)

    sheds = {
        0.5: school.shed_05,
        1.0: school.shed_10,
        1.5: school.shed_15,
        2.0: school.shed_20
    }

    csv_string = 'wkt,name,label\n'
    for key, g in reversed(sorted(sheds.items(), key=lambda a: a[0])):
        if g is None:
            continue
        g.srid = 26986
        g.transform(srid)
        csv_string += '"%s","%s",""\n' % (g.wkt, str(key))

    surveys = Survey.objects.filter(school=school)
    for survey in surveys:
        survey.location.transform(srid)

        children = list(survey.child_set.all())
        if len(children) > 0:
            for c in children:
                name = str(c.to_school)
                point = survey.location
                point.x += random.randint(-50, 50)
                point.y += random.randint(-50, 50)
                school_circle = point.buffer(50)
                csv_string += '"%s","%s",""\n' % (school_circle.wkt, name)

        else:
            name = "o"
            point = survey.location
            point.x += random.randint(-50, 50)
            point.y += random.randint(-50, 50)
            school_circle = point.buffer(50)
            csv_string += '"%s","%s",""\n' % (school_circle.wkt, name)

    #Add School geometry
    school.geometry.transform(srid)
    csv_string += '"%s","school","%s"\n' % (school.geometry.wkt, school.name)

    def box(minx, miny, maxx, maxy):
        lmin = Point(p2l(minx, miny))
        lmax = Point(p2l(maxx, maxy))
        lr = LinearRing((lmin.x, lmin.y), (lmax.x, lmin.y), (lmax.x, lmax.y), (lmin.x, lmax.y), (lmin.x, lmin.y))
        poly = Polygon(lr)
        return poly

    legend = box(2, 108, 50, 113.5)
    csv_string += '"%s","%s","%s"\n' % (legend.wkt, "legend_box", "")

    xy = p2l(3.5, 112)
    point = Point(*xy)
    csv_string += '"%s","%s","School Commute Survey Results"\n' % (point.wkt, "map_title")

    xy = p2l(3.5, 109.5)
    point = Point(*xy)
    csv_string += '"%s","%s","%s, %s"\n' % (point.wkt, "map_subtitle", school, school.districtid)

    legend_x = 53

    legend = box(legend_x, 97, 97.5, 113.5)
    csv_string += '"%s","%s","%s"\n' % (legend.wkt, "legend_box", "")

    xy = p2l(legend_x + 1.5, 112)
    point = Point(*xy)
    csv_string += '"%s","legend_title","Approx. home locations and travel to school mode"\n' % (point.wkt, )

    walksheds_x = 88
    xy = p2l(walksheds_x, 112)
    point = Point(*xy)
    csv_string += '"%s","legend_title","Walksheds"\n' % (point.wkt, )

    y = 111.5
    for name, label in school_colors:
        y -= 1.8
        xy = p2l(legend_x+2, y)
        point = Point(*xy)
        circle = point.buffer(50)
        csv_string += '"%s","%s","%s"\n' % (circle.wkt, name, MODE_DICT[name])

    y = 110
    for name in ('0.5', '1.0', '1.5', '2.0',):
        y -= 2.4
        ws = box(walksheds_x, y, walksheds_x+2, y+1.5)
        csv_string += '"%s","%s","%s  Mile"\n' % (ws.wkt, name, name)

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
    response = school_sheds_results(school_id=school_id, format='pdf')

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


def school_surveys_json(request, school_id):
    surveys = Survey.objects.filter(school__pk=school_id)
    surveys = surveys.exclude(location__intersects='POINT(0 0)')

    features = []
    colors = {row[0]: row[1] for row in SCHOOL_COLORS}

    for s in surveys:
        children = list(s.child_set.all())

        if children:
            for c in children:
                point = s.location
                point.transform(26986)
                point.x += random.randint(-50, 50)
                point.y += random.randint(-50, 50)
                circle = point.buffer(20)
                circle.transform(4326)
                features.append(""" {
                    "type": "Feature",
                    "geometry": %s,
                    "properties": {"color": ["%s"]}
                }""" % (circle.geojson, colors[str(c.to_school)]))
        else:
            point = s.location
            point.transform(26986)
            circle = point.buffer(20)
            circle.transform(4326)
            features.append(""" {
                "type": "Feature",
                "geometry": %s,
                "properties": {"color": ["%s"]}
            }""" % (circle.geojson, colors['o']))

    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)


def ForkRunR(school_id, date1, date2):
    import rpy2.robjects as r
    #import subprocess
    school = School.objects.get(id=school_id)
    org_code = school.schid
    rdir = os.path.abspath(os.path.join(settings.CURRENT_PATH, '../R'))
    workdir = 'figure'
    wdir = os.path.join(rdir, workdir)
    os.chdir(rdir)
    if not os.path.exists(wdir):
        os.makedirs(wdir)
    save_sheds(os.path.join(wdir, 'map.pdf'), school_id)
    print 'endmap'
    print date1, date2, school_id, org_code

    try:
        r.r("load('.RData')")
        r.r("dbname <- '%s'" % settings.DATABASES['default']['NAME'])
        r.r("dbuser <- '%s'" % settings.DATABASES['default']['USER'])
        r.r("dbpasswd <- '%s'" % settings.DATABASES['default']['PASSWORD'])
        r.r("ORG_CODE <- '%s'" % org_code)
        r.r("DATE1 <- '%s'" % str(date1))
        r.r("DATE2 <- '%s'" % str(date2))
        r.r("WORKDIR <- '%s'" % wdir)
        #r.r("print(ORG_CODE)")
        r.r("source('generate_report.R')")
    except:
        pass

    #cur_dir = os.path.dirname(os.path.realpath(__file__))
    #os.chdir(cur_dir)
    #print " ".join(['./runr.py', wdir, rdir, org_code, str(date1), str(date2)])
    #subprocess.call(['./runr.py', wdir, rdir, org_code, str(date1), str(date2)])

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

