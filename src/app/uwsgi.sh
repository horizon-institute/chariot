#!/bin/sh

echo "Starting"

while ! timeout 1 bash -c 'cat < /dev/null > /dev/tcp/db/3306' >/dev/null 2>/dev/null; do sleep 0.1; done
echo "mySQL Started"
while ! timeout 1 bash -c 'cat < /dev/null > /dev/tcp/influx/8086' >/dev/null 2>/dev/null; do sleep 0.1; done
echo "InfluxDB Started"

echo "Creating mySQL Database"
/app/manage.py collectstatic --noinput
/app/manage.py syncdb --noinput
/app/manage.py migrate --noinput

uwsgi --socket :5000 --wsgi-file /app/chariot/wsgi.py --master --processes 4 --threads 2 --chdir /app