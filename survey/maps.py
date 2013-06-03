from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, GEOSGeometry
from django.core.cache import cache, get_cache
from django.db import connection

import pickle
import mapnik
import mimetypes
import math
import time
from shapely import ops, geometry

from models import School

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
    geometry = models.LineStringField(srid=900914)
    objects = models.GeoManager()

    class Meta:
        db_table = 'walks'

class NetworkBike(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    geometry = models.LineStringField(srid=900914)
    objects = models.GeoManager()

    class Meta:
        db_table = 'survey_network_bike'

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return [lon_deg,lat_deg]

def tms(zoom, column, row):
    nw = num2deg(int(row), int(column), int(zoom))
    se = num2deg(int(row)+1, int(column)+1, int(zoom))
    nw_p = Point(nw[0], nw[1], srid=4326)
    se_p = Point(se[0], se[1], srid=4326)
    nw_p.transform(3857)
    se_p.transform(3857)
    bbox = mapnik.Envelope(se_p.x, se_p.y, nw_p.x, nw_p.y)
    return bbox

def school_tms(request, school_id, zoom, column, row):
    bbox = rms(zoom, column, row)
    return school_sheds(request, school_id, bbox, 256, 256, 3857)

def paths_sql(school_id, network='survey_network_walk', miles=1.5):

    school = """st_transform(
        (SELECT geometry FROM survey_school WHERE id = %d), 900914
    )""" % int(school_id)

    closest_street =  """(
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
    data = {2.0: row[0], 1.5:row[1], 1.0:row[2], 0.5:row[3]}

    return data

def school_sheds(request, school_id, bbox=None, width=800, height=600, srid=900914):
    format = 'png'

    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(3000.0)

    m = mapnik.Map(int(width), int(height), "+init=epsg:"+str(srid))
    if bbox is None:
        circle.transform(srid)
        bbox = mapnik.Box2d(*circle.extent)
    m.zoom_to_box(bbox)

    #m.background = mapnik.Color('steelblue')

    # styles for main
    s = mapnik.Style()
    for name, color in (('0.5',VIOLET), ('1.0',PURPLE), ('1.5', LAVENDER), ('2.0', LIGHTCYAN)):
        r = mapnik.Rule()
        r.filter = mapnik.Filter("[name] = "+name)
        line_symbolizer = mapnik.LineSymbolizer()
        poly_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(color))
        r.symbols.append(line_symbolizer)
        r.symbols.append(poly_symbolizer)
        s.rules.append(r)
    m.append_style("paths",s)
    #styles end

    '''
    # caching
    key = "school"+str(school_id)
    working = cache.get(key+"working")
    while working:
        time.sleep(0.5)
        working = cache.get(key+"working")

    csv_string = cache.get(key)
    if csv_string is None:
        cache.set(key+"working", True)
        paths = NetworkWalk.objects.filter(geometry__bboverlaps=circle)

        csv_string = "wkt,Name\n"
        for line in paths:
            csv_string += '"%s","test"\n' % line.geometry.wkt

        cache.set(key, csv_string)
        cache.delete(key+"working")
    '''

    sheds = get_sheds(school_id)

    csv_string = 'wkt,name\n'
    for key, wkt in reversed(sorted(sheds.items(), key=lambda a: a[0])):
        g = GEOSGeometry(wkt)
        g.srid = 900914
        g.transform(srid)
        csv_string += '"%s","%s"\n' % (g.wkt, str(key))
        print key

    layer = mapnik.Layer('paths', "+init=epsg:"+str(srid))
    ds = mapnik.Datasource(type="csv",inline=csv_string.encode('ascii'))
    layer.datasource = ds
    layer.styles.append('paths')
    m.layers.append(layer)

    # Render to image
    im = mapnik.Image(m.width,m.height)
    mapnik.render(m, im)
    im = im.tostring(str(format))
    response = HttpResponse()
    response['Content-length'] = str(len(im))
    response['Content-Type'] = mimetypes.types_map['.'+format]
    response.write(im)

    return response

def walks(request, zoom, column, row):
    format = 'png'
    bbox = tms(zoom, column, row)

    m = mapnik.Map(256, 256, "+init=epsg:3857")
    m.zoom_to_box(bbox)

    # styles for main
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('black'), 0.8)
    point_symbolizer = mapnik.PointSymbolizer()

    r.symbols.append(line_symbolizer)
    #r.symbols.append(point_symbolizer)

    t = mapnik.TextSymbolizer(mapnik.Expression('[fid]'), 'DejaVu Sans Book', 12, mapnik.Color('black'))
    t.halo_fill = mapnik.Color('white')
    t.halo_radius = 3
    t.label_placement = mapnik.label_placement.LINE_PLACEMENT
    r.symbols.append(t)

    m.append_style("main",s)

    query = 'survey_walk'
    db = DATABASES['default']['NAME']
    usr = DATABASES['default']['USER']
    pwd = DATABASES['default']['PASSWORD']

    layer = mapnik.Layer('bg', '+init=epsg:3857')
    layer.datasource = mapnik.PostGIS(host='localhost',user=usr,password=pwd,dbname=db, table=query, extent=bbox)

    layer.styles.append('main')
    m.layers.append(layer)

    # Render to image
    im = mapnik.Image(m.width,m.height)
    mapnik.render(m, im)
    im = im.tostring(str(format))
    response = HttpResponse()
    response['Content-length'] = str(len(im))
    response['Content-Type'] = mimetypes.types_map['.'+format]
    response.write(im)
    return response

def school_sheds_json(request, school_id):
    sheds = get_sheds(school_id)

    features = []
    for dist, wkt in sheds.items():
        geometry = GEOSGeometry(wkt)
        geometry.srid = 900914
        geometry.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"distance": "%0.1f"}
        }""" % (geometry.geojson, dist))

    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)


def school_paths_json(request, school_id):
    query = paths_sql(school_id, miles=1.5)

    streets = NetworkWalk.objects.raw(query)

    features = []
    for f in list(streets):
        f.geometry.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"id": %d, "cost": %f}
        }""" % (f.geometry.geojson, f.pk, f.cost))

    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)

def RunR():
    import rpy2.robjects as r
    from myschoolcommute import settings
    r.r("dbname <- '%s'" % settings.DATABASES['default']['NAME'])
    r.r("dbuser <- '%s'" % settings.DATABASES['default']['USER'])
    r.r("dbpasswd <- '%s'" % settings.DATABASES['default']['PASSWORD'])
    r.r("source('R_files/compile.R')")

if __name__ == '__main__':
    sys.path.append(os.path.realpath(".."))
    from django.core.management import setup_environ
    from myschoolcommute import settings

    setup_environ(settings)
