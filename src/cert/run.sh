#!/bin/sh

trap "exit" SIGHUP SIGINT SIGTERM

if [ -z "$DOMAINS" ] ; then
	echo "No certificates required."
	echo "Exiting"
	exit 1
fi
CHECK_FREQ="${CHECK_FREQ:-10}"

check() {
	echo "Checking certificates"

	certbot renew -n --dry-run --agree-tos --email ${EMAIL} --post-hook "/renewed.sh"

	echo "Checking again in $CHECK_FREQ days"
	sleep ${CHECK_FREQ}d
	check
}

if [ "${EMAIL}" ] ; then
	echo "Requesting certificates for $DOMAINS"

	CERTBOT_DOMAINS="-d ${DOMAINS/ / -d }"

	certbot certonly --standalone --agree-tos --keep-until-expiring --dry-run --text --email ${EMAIL} ${CERTBOT_DOMAINS} --post-hook "/renewed.sh"
	sh ./renewed.sh
else
	check
fi
