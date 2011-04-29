import os
from django.contrib.gis.utils import LayerMapping
from models import School

school_mapping = {
    'school_id': 'schid',
    'name': 'name',
    'address': 'address',
    'slug': 'slug',
    'municipality': 'town',
    'state': 'state',
    'zip': 'zip',
    'principal': 'principal',
    'phone': 'phone',
    'fax': 'fax',
    'grades': 'grades',
    'type': 'schl_type',
    'survey_active_char': 'active',
    'location' : 'POINT',
}

schools_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), 'C:/gis/shp/schools.shp'))

def run(verbose=True):
    lm = LayerMapping(School, schools_shp, school_mapping,
                      transform=False, encoding='iso-8859-1')

    lm.save(strict=True, verbose=verbose)