#!/bin/sh

echo "Certificates Renewed"

if [ "$CERTS_PATH" ] ; then
	echo "Copying certificates to $CERTS_PATH"
	eval cp /etc/letsencrypt/live/$DOMAINS/* $CERTS_PATH/
fi

if [ "$SERVER_CONTAINER" ]; then
	echo "Reloading Nginx configuration on $SERVER_CONTAINER"
	eval docker kill -s HUP $SERVER_CONTAINER
fi