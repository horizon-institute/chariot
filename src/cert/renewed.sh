#!/bin/sh

echo "Certificates Updated"

echo "Copying certificates to /etc/letsencrypt/certs"
eval cp /etc/letsencrypt/live/$DOMAINS/* /etc/letsencrypt/certs/

if [ "$SERVER_CONTAINER" ]; then
	echo "Restarting nginx Configuration on $SERVER_CONTAINER"

	echo -e "POST /containers/$SERVER_CONTAINER/kill?signal=SIGHUP HTTP/1.0\r\n" |nc -U /tmp/docker.sock
fi