# add and update ppas
apt-get update -qq
apt-get install -y python-software-properties
apt-add-repository -y ppa:ubuntugis/ppa
add-apt-repository -y ppa:mapnik/v2.2.0
apt-add-repository -y ppa:georepublic/pgrouting
apt-get update -qq
#Routing
apt-get -y install postgresql-9.1-postgis-2.0
apt-get -y install postgresql-9.1-pgrouting


#GeoDjango
apt-get -y install postgis binutils libproj-dev gdal-bin libgdal-dev
#Mapnik
apt-get -y install libmapnik libmapnik-dev mapnik-utils python-mapnik

#R
apt-get -y r-base-core r-cran-dbi

#Latex - this can take significant time. Attempting https://github.com/BPA-CSIRO-Workshops/handout-template/blob/master/developers/texlive_install.sh
# sudo apt-get -y install texinfo
# sudo apt-get -y install texlive-full

wget \
  --continue \
  --directory-prefix /tmp \
  ${CTAN_MIRROR_URL:-'http://mirror.ctan.org'}/systems/texlive/tlnet/install-tl-unx.tar.gz
tar \
  --extract \
  --gunzip \
  --directory /tmp \
  --file /tmp/install-tl-unx.tar.gz

# Install texlive using the supplied texlive.profile (this just installs a
# basic LaTeX environment
/tmp/install-tl-*/install-tl \
  -repository ${CTAN_MIRROR_URL:-'http://mirror.ctan.org'}/systems/texlive/tlnet \
  -no-gui \
  -profile myschoolcommute/texlive.profile

apt-get install texlive-binaries
# Install packages required by this style
# packages=(
#   mdframed
#   preprint
#   enumitem
#   etoolbox
#   titlesec
#   xmpincl
#   comment
#   latexmk
#   lm
#   memoir
#   listings
#   xcolor
#   url
#   l3packages
#   l3kernel
#   placeins
#   microtype
#   float
#   latex-bin
#   fancyhdr
#   graphics
#   psnfss
#   pdftex-def
#   oberdiek
#   colortbl
#   hyperref
# )
# /usr/local/texlive/bin/x86_64-linux/tlmgr \
#   -repository ${CTAN_MIRROR_URL:-'http://mirror.ctan.org'}/systems/texlive/tlnet \
#   install \
#     ${packages[@]}

apt-get install -y \
        python-pip \
        python-psycopg2 \
        libpq-dev \
        libjpeg-dev \
        postgresql-client \
        python-dev \
        python-virtualenv \
        build-essential \
        curl \
        libgdal1-dev

cd myschoolcommute
#install django requirements
pip install -r requirements.txt

#setup local_settings for vagrant
if [ ! -f myschoolcommute/local_settings.py ]; then
    cat > myschoolcommute/local_settings.py <<EOF
from settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mysc',
        'USER': 'vagrant',
        'PASSWORD': 'vagrant',
        'HOST': '',
        'PORT': '',
    }
}

POSTGIS_VERSION = (2,0,3)
EOF
fi

./db_setup.sh