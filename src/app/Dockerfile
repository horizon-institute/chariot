FROM python:alpine

RUN apk --update add build-base jpeg-dev zlib-dev postgresql-dev linux-headers

COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

RUN mkdir -p /media/

CMD /app/uwsgi.sh
