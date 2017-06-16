#!/bin/sh

trap "exit" SIGHUP SIGINT SIGTERM

if [ -z "$DOMAINS" ] ; then
	echo "No certificates required."
	echo "Exiting"
	exit 1
fi
CHECK_FREQ="${CHECK_FREQ:-10}"

CERTBOT_DOMAINS="-d ${DOMAINS/ / -d }"

check() {
	echo "Checking certificates"

    certbot certonly --webroot --text -w /www --preferred-challenges=http --agree-tos --email ${EMAIL} ${CERTBOT_DOMAINS} --post-hook "/renewed.sh"

	echo "Checking again in $CHECK_FREQ days"
	sleep ${CHECK_FREQ}d
	check
}

check
