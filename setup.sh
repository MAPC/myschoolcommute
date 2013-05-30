sudo apt-get install -y python-software-properties
add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
add-apt-repository -y ppa:mapnik/nightly-trunk
apt-get update
sudo apt-get -y install libmapnik mapnik-utils python-mapnik
#GeoDjango
sudo apt-get -y install postgis binutils libproj-dev gdal-bin
