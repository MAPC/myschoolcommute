apt-get install -y python-software-properties
add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
add-apt-repository -y ppa:mapnik/nightly-trunk
apt-add-repository -y ppa:georepublic/pgrouting
apt-get update
#GeoDjango
apt-get -y install postgis binutils libproj-dev gdal-bin
#Mapnik
apt-get -y install libmapnik mapnik-utils python-mapnik
#Routing
apt-get -y install postgresql-9.1-pgrouting 

#Python requirements
easy_install pip
pip install -r requirements.txt
