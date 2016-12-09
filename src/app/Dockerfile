FROM python:2.7

COPY sources.list /etc/apt/sources.list
RUN ln -s /usr/include/freetype2 /usr/local/include/freetype
COPY requirements.txt /app/
RUN pip install --no-binary django django==1.4.21
RUN pip install -r /app/requirements.txt

RUN mkdir -p /media/

CMD /app/uwsgi.sh
