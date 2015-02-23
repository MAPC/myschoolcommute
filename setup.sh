# add and update ppas
apt-get update -qq
apt-get install -y python-software-properties
add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
add-apt-repository -y ppa:mapnik/v2.2.0
apt-add-repository -y ppa:georepublic/pgrouting
apt-get update -qq
#GeoDjango
sudo apt-get -y install postgis binutils libproj-dev gdal-bin libgdal-dev
#Mapnik
sudo apt-get -y install libmapnik libmapnik-dev mapnik-utils python-mapnik
#Routing
sudo apt-get -y install gaul-devel postgresql-9.1-pgrouting postgresql-9.1-pgrouting-dd postgresql-9.1-pgrouting-tsp

#R
sudo apt-get -y r-base-core r-cran-dbi

#Latex
sudo apt-get -y install texinfo
sudo apt-get -y install texlive-full