from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.gis.db import models

import ModestMaps
import pickle
import mapnik
import mimetypes

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

def school_sheds(request, school_id, alpha=1.0):
    width = 800
    height = 800
    format = 'png'

    background = False

    school = School.objects.get(pk=school_id)
    point = school.geometry
    circle = point.buffer(2000.0)
    circle.transform(4326)

    m = mapnik.Map(int(width), int(height), "+init=epsg:4326")
    #m.background = mapnik.Color('steelblue')
    
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

    layer = mapnik.Layer('main')
    layer.datasource = ds
    layer.styles.append('top')
    m.layers.append(layer)
    
    bbox = mapnik.Envelope(*circle.extent)
    m.zoom_to_box(bbox)

    paths = NetworkWalk.objects.filter(geometry__bboverlaps=circle)

    s = mapnik.Style()
    r = mapnik.Rule()
    line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('black'),0.8)
    #polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color('rgb(70%,70%,70%)'))
    #r.symbols.append(polygon_symbolizer)
    r.symbols.append(line_symbolizer)
    s.rules.append(r)
    m.append_style("bot",s)
    
    csv_string = 'wkt,Name\n'
    for line in paths:
        csv_string += '"%s","test"\n' % line.geometry.wkt

    ds = mapnik.Datasource(type="csv",inline=csv_string.encode('ascii'))
    layer = mapnik.Layer('bg', '+init=epsg:900914')
    layer.datasource = ds
    layer.styles.append('bot')
    m.layers.append(layer)

    im = mapnik.Image(m.width,m.height)
    mapnik.render(m, im)
    im = im.tostring(str(format))
    response = HttpResponse()
    response['Content-length'] = str(len(im))
    response['Content-Type'] = mimetypes.types_map['.'+format]
    response.write(im)
    return response