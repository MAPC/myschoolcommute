sudo su postgres <<EOF
createdb postgis_template
psql -d postgis_template -c "create extension postgis;"
psql -d postgis_template -c "create extension pgrouting;"
createuser vagrant --no-password --createdb --no-createrole --no-superuser
psql <<EOF2
 ALTER ROLE vagrant WITH PASSWORD 'vagrant'
EOF2
createdb -O vagrant -T postgis_template mysc
EOF