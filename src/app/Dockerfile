FROM python

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

RUN mkdir -p /media/

CMD /app/uwsgi.sh
