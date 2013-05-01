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

BLUE = "#0088CC"
GRAY = "#DDDDDD"

class NetworkWalk(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    geometry = models.LineStringField(srid=900914)
    objects = models.GeoManager()

    class Meta:
        db_table = 'survey_network_walk'

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

def school_tms(request, school_id, zoom, column, row):
    nw = num2deg(int(row), int(column), int(zoom))
    se = num2deg(int(row)+1, int(column)+1, int(zoom))
    nw_p = Point(nw[0], nw[1], srid=4326)
    se_p = Point(se[0], se[1], srid=4326)
    nw_p.transform(900913)
    se_p.transform(900913)
    bbox = mapnik.Envelope(se_p.x, se_p.y, nw_p.x, nw_p.y)
    return school_sheds(request, school_id, bbox, 256, 256, 900913)

def school_sheds(request, school_id, bbox=None, width=800, height=600, srid=4326):
    format = 'png'
    alpha = 1.0

    background = False

    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(500.0)

    m = mapnik.Map(int(width), int(height), "+init=epsg:"+str(srid))
    #m.background = mapnik.Color('steelblue')
    '''
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color(BLUE), 1)
    line_symbolizer.fill_opacity = float(alpha)
    r.symbols.append(line_symbolizer)
    s.rules.append(r)
    m.append_style('top',s)

    wkt = circle.wkt.encode('ascii')

    csv_string = 'wkt,Name\n"%s","test"\n' % wkt
    ds = mapnik.Datasource(type="csv",inline=csv_string)

    layer = mapnik.Layer('main', '+init=epsg:'+srid)
    layer.datasource = ds
    layer.styles.append('top')
    m.layers.append(layer)
    '''
    if bbox is None:
        circle.transform(srid)
        bbox = mapnik.Box2d(*circle.extent)
    m.zoom_to_box(bbox)

    '''
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

    # Apply styles
    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('black'),0.8)
    #polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color('rgb(70%,70%,70%)'))
    #r.symbols.append(polygon_symbolizer)
    r.symbols.append(line_symbolizer)
    s.rules.append(r)
    m.append_style("bot",s)

    #ds = mapnik.Datasource(type="csv",inline=csv_string.encode('ascii'))
    layer = mapnik.Layer('bg', '+init=epsg:900914')
    #layer.datasource = ds

    #query = "select * from survey_network_walk' JOIN (select * from driving_distance("
    #    + "'select id, miles from survey_network_walk', %s"

    layer.datasource = mapnik.PostGIS(host='localhost',user='mysc',password='SuperHappyFunSlide',dbname='mysc',
        table='survey_network_walk', extent=bbox)

    layer.styles.append('bot')
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
