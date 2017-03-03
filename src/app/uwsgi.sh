#!/bin/sh

echo "Starting"

while ! nc -z db 5432; do sleep 3; done
echo "Database Started"
while ! nc -z influx 8086; do sleep 3; done
echo "InfluxDB Started"

echo "Creating Database"
/app/manage.py collectstatic --noinput
/app/manage.py migrate --noinput

uwsgi --socket :5000 --wsgi-file /app/chariot/wsgi.py --master --processes 4 --threads 2 --chdir /app