apt-get install -y python-software-properties
add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
add-apt-repository -y ppa:mapnik/nightly-trunk
apt-add-repository -y ppa:georepublic/pgrouting
apt-get update
#GeoDjango
apt-get -y install postgis binutils libproj-dev gdal-bin libgdal-dev
#Mapnik
apt-get -y install libmapnik mapnik-utils python-mapnik
#Routing
apt-get -y install gaul-devel postgresql-9.1-pgrouting postgresql-9.1-pgrouting-dd postgresql-9.1-pgrouting-tsp

#R
apt-get -y r-base-core r-cran-dbi

