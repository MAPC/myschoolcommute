from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.cache import cache, get_cache

import ModestMaps
import pickle
import mapnik
import mimetypes
import math
import time

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
    nw_p.transform(900913)
    se_p.transform(900913)
    bbox = mapnik.Envelope(se_p.x, se_p.y, nw_p.x, nw_p.y)
    return bbox

def school_tms(request, school_id, zoom, column, row):
    bbox = rms(zoom, column, row)
    return school_sheds(request, school_id, bbox, 256, 256, 900913)

def school_sheds(request, school_id, bbox=None, width=800, height=600, srid=4326):
    format = 'png'

    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(1000.0)

    m = mapnik.Map(int(width), int(height), "+init=epsg:"+str(srid))
    if bbox is None:
        circle.transform(srid)
        bbox = mapnik.Box2d(*circle.extent)
    m.zoom_to_box(bbox)

    #m.background = mapnik.Color('steelblue')

    # styles got circle
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color(BLUE), 1)
    line_symbolizer.fill_opacity = float(1.0)
    r.symbols.append(line_symbolizer)
    s.rules.append(r)
    m.append_style('top',s)

    # styles for main
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('black'), 0.8)
    point_symbolizer = mapnik.PointSymbolizer()

    r.symbols.append(line_symbolizer)
    r.symbols.append(point_symbolizer)

    #t = mapnik.TextSymbolizer(mapnik.Expression('[ogc_fid]'), 'DejaVu Sans Book', 10, mapnik.Color('black'))
    #t.halo_fill = mapnik.Color('white')
    #t.halo_radius = 1
    #t.label_placement = mapnik.label_placement.LINE_PLACEMENT
    #r.symbols.append(t)
    #s.rules.append(r)
    m.append_style("main",s)

    wkt = circle.wkt.encode('ascii')

    csv_string = 'wkt,Name\n"%s","test"\n' % wkt
    ds = mapnik.Datasource(type="csv",inline=csv_string)

    layer = mapnik.Layer('circle', '+init=epsg:'+str(srid))
    layer.datasource = ds
    layer.styles.append('top')
    m.layers.append(layer)

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

    closest_street =  """ (SELECT ogc_fid from survey_network_bike ORDER BY 
        st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914) 
        <-> geometry  
        asc limit 1) """ % int(school_id)

    query = """select ogc_fid, geometry from survey_network_walk
                JOIN
                (SELECT * FROM 
                   driving_distance(
                        'SELECT ogc_fid as id,source,target,miles AS cost FROM survey_network_walk'
                        , %s, 0.5, false, false
                    )) AS route
                ON
                survey_network_walk.ogc_fid = route.vertex_id""" % closest_street

    #streets = NetworkWalk.objects.raw(query)

    layer = mapnik.Layer('main', "+init=epsg:"+str(srid))
    
    csv_string = "wkt,Name\n"
    for line in streets:
        line.geometry.transform(srid)
        csv_string += '"%s","test"\n' % line.geometry.wkt
    return HttpResponse(csv_string)
    print csv_string
    print bbox
    ds = mapnik.Datasource(type="csv",inline=csv_string.encode('ascii'))
    layer.datasource = ds

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

def walks(request, zoom, column, row):
    format = 'png'
    bbox = tms(zoom, column, row)

    m = mapnik.Map(256, 256, "+init=epsg:900913")
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

    t = mapnik.TextSymbolizer(mapnik.Expression('[source]'), 'DejaVu Sans Book', 12, mapnik.Color('green'))
    t.halo_fill = mapnik.Color('white')
    t.halo_radius = 3
    t.label_placement = mapnik.label_placement.LINE_PLACEMENT
    r.symbols.append(t)
    s.rules.append(r)

    t = mapnik.TextSymbolizer(mapnik.Expression('[target]'), 'DejaVu Sans Book', 12, mapnik.Color('red'))
    t.halo_fill = mapnik.Color('white')
    t.halo_radius = 3
    t.label_placement = mapnik.label_placement.LINE_PLACEMENT
    r.symbols.append(t)
    s.rules.append(r)

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
    closest_street =  """(
            with index_query as (
                SELECT st_distance(
                        geometry, 
                        st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914)
                    ) as distance, ogc_fid
                FROM survey_network_walk as w
                ORDER BY w.geometry <#> st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914)
                LIMIT 100
            )
            select ogc_fid from index_query order by distance limit 1
        ) """ % (int(school_id), int(school_id))

    closest_street =  """ (SELECT source from survey_network_walk ORDER BY 
        st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914) 
        <-> geometry  
        asc limit 1) """ % int(school_id)

    query = """SELECT ogc_fid, geometry from survey_network_walk
                JOIN
                (SELECT * FROM 
                   driving_distance(
                        'SELECT ogc_fid as id, source, target, miles AS cost FROM survey_network_walk'
                        , %s, 1, false, false
                    )) AS route
                ON
                survey_network_walk.source_fid = route.edge_id""" % closest_street

    nearby = """
            WITH index_query AS (
                SELECT st_distance(
                        geometry, 
                        st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914)
                    ) AS distance, ogc_fid
                FROM survey_network_walk as w
                ORDER BY w.geometry <#> st_transform((SELECT geometry FROM survey_school WHERE id = %d), 900914)
                LIMIT 1000
            )
            SELECT ogc_fid FROM index_query ORDER BY distance LIMIT 100
         """ % (int(school_id), int(school_id))

    query_slow = """
        SELECT 
            ogc_fid, 
            geometry, 
            (SELECT sum(cost) FROM (
                    SELECT * FROM shortest_path(
                        'SELECT ogc_fid AS id, source, target, miles AS cost
                         FROM survey_network_walk',
                        %s,
                        target,
                        false, false
                    )
                ) AS foo
            ) AS walk_distance 
        FROM survey_network_walk 
        WHERE ogc_fid IN (%s)
        ORDER BY walk_distance LIMIT 100
    """ % (closest_street, nearby)

    #query = " SELECT fid, geom FROM survey_walk WHERE ogc_fid IN (%s)" % nearby
    print query

    streets = NetworkWalk.objects.raw(query)

    features = []
    for f in list(streets):
        f.geometry.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"id": %d}
        }""" % (f.geometry.geojson, f.pk))
    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)