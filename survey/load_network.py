import os, sys
sys.path.append(os.path.realpath(".."))

from myschoolcommute.local_settings import DATABASES
db = DATABASES['default']['NAME']
usr = DATABASES['default']['USER']
pwd = DATABASES['default']['PASSWORD']

import commands

cmd = 'ogr2ogr -f PostgreSQL PG:"dbname=%s user=%s password=%s" %s -nln %s -lco GEOMETRY_NAME=geometry' 

print commands.getoutput(cmd % (db,usr,pwd, 'data/SRTS_BIKE_NETWORK.shp', 'survey_network_bike'))
print commands.getoutput(cmd % (db,usr,pwd, 'data/SRTS_WALK_NETWORK.shp', 'survey_network_walk'))
