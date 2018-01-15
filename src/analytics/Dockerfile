FROM python:2.7-alpine

RUN apk --update add build-base postgresql-dev linux-headers

ENV PYTHONUNBUFFERED 1
RUN mkdir /analytics
WORKDIR /analytics
COPY requirements.txt /analytics/
RUN pip install -r requirements.txt

CMD python manage.py runserver 0.0.0.0:8000