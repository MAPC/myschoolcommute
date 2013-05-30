from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, GEOSGeometry
from django.core.cache import cache, get_cache
from django.db import connection

import ModestMaps
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

def school_sheds(request, school_id, bbox=None, width=800, height=600, srid=4326):
    format = 'png'

    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(2500.0)

    m = mapnik.Map(int(width), int(height), "+init=epsg:"+str(srid))
    if bbox is None:
        circle.transform(srid)
        bbox = mapnik.Box2d(*circle.extent)
    m.zoom_to_box(bbox)

    #m.background = mapnik.Color('steelblue')

    # cirlcle style
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color(BLUE), 0.5)
    line_symbolizer.fill_opacity = float(1.0)
    r.symbols.append(line_symbolizer)
    s.rules.append(r)
    m.append_style('circle',s)

    # styles for main
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer()
    poly_symbolizer = mapnik.PolygonSymbolizer()

    r.symbols.append(line_symbolizer)
    r.symbols.append(poly_symbolizer)

    t = mapnik.TextSymbolizer(mapnik.Expression('[cost]'), 'DejaVu Sans Book', 10, mapnik.Color('black'))
    t.halo_fill = mapnik.Color('white')
    t.halo_radius = 1
    t.label_placement = mapnik.label_placement.LINE_PLACEMENT
    r.symbols.append(t)
    s.rules.append(r)
    m.append_style("paths",s)

    #styles end
    '''
    wkt = circle.wkt.encode('ascii')

    csv_string = 'wkt,Name\n"%s","test"\n' % wkt
    ds = mapnik.Datasource(type="csv",inline=csv_string)

    layer = mapnik.Layer('circle', '+init=epsg:'+str(srid))
    layer.datasource = ds
    layer.styles.append('circle')
    m.layers.append(layer)
    '''
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

    query = paths_sql(school_id, 'survey_network_walk', 1.5)

    print query

    time1 = time.time()
    streets = list(NetworkWalk.objects.raw(query))
    time2 = time.time()
    print 'Query function took %0.3f ms' % ((time2-time1)*1000.0)

    csv_string = "wkt,Name,cost\n"

    polys_05 = []
    polys_1 = []
    polys_15 = []
    for line in streets:
        line.geometry.transform(srid)
        ls = geometry.LineString(line.geometry)
        polys_05.append(ls)
        
        #csv_string += '"%s","%d","%f"\n' % (ls.wkt, line.pk, line.cost)

    time1 = time.time()
    poly = None
    for ls in polys_05:
        buffered = ls.buffer(0.0007)
        try:
            poly =  poly.union(buffered)
        except Exception, e:
            print str(e)
            poly = buffered

    time2 = time.time()
    print 'Union function took %0.3f ms' % ((time2-time1)*1000.0)

    csv_string += '"%s","%s","%f"\n' % (poly.wkt, "0.5", 0)

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
    time3 = time.time()
    print 'Rendering function took %0.3f ms' % ((time3-time2)*1000.0)
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
    query = paths_sql(school_id, miles=1.5)
    cursor = connection.cursor()

    hull_query = """ 
    WITH paths as (%s)
    SELECT ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 1.5))
    ),
    ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 1))
    ),
    ST_AsText(
        ST_Union(array(select ST_BUFFER(geometry, 100) from paths where cost < 0.5))
    )""" % (query,)
    
    cursor.execute(hull_query)
    row = cursor.fetchone()
    features = []
    for col in row:
        geometry = GEOSGeometry(col)
        geometry.srid = 900914
        geometry.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"id": %d, "cost": %f}
        }""" % (geometry.geojson, 0, 0))

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

if __name__ == '__main__':
    sys.path.append(os.path.realpath(".."))
    from django.core.management import setup_environ
    from myschoolcommute import settings

    setup_environ(settings)