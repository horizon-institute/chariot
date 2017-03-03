FROM alpine

RUN apk --update add certbot docker

EXPOSE 80 443

COPY *.sh /

RUN chmod +x /*.sh

CMD ["/run.sh"]