FROM alpine

RUN apk --update add certbot netcat-openbsd

EXPOSE 80 443

COPY *.sh /

RUN chmod +x /*.sh

CMD ["/run.sh"]