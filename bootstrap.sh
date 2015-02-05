#!/usr/bin/env bash
apt-get update -qq
apt-get install -y python-software-properties
apt-add-repository -y ppa:ubuntugis/ppa
add-apt-repository ppa:chris-lea/node.js
apt-get update -qq
apt-get install -y \
        python-pip \
        postgresql-9.1-postgis-2.0 \
        python-psycopg2 \
        libpq-dev \
        libjpeg-dev \
        postgresql-client \
        python-dev \
        python-virtualenv \
        build-essential \
        ruby \
        rubygems \
        gem \
        curl \
        vim \
        nodejs \
        libgdal1-dev

if [ ! -d virtualenv ]; then
    virtualenv virtualenv
fi

cd virtualenv
source ./bin/activate
pip install -r ../myschoolcommute/requirements.txt
cd ..

# cd myschoolcommute
# . ../virtualenv/bin/activate
# pip install -r requirements.txt