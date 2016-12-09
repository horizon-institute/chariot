#!/usr/bin/env bash

envFile="./.env"
if ! [ -r "$envFile" ]
then
    read -p "Secure Domains (space separated, leave empty for none): " DOMAINS
    if [[ ! ${DOMAINS} = "" ]]
    then
		read -p "Email address: " EMAIL
        if ! [ -r "cert/live/$DOMAINS/fullchain.pem" ]
        then
	        DARRAYS=(${DOMAINS})
	        LE_DOMAINS=("${DARRAYS[*]/#/-d }")
			docker run -v "$(pwd)/cert:/etc/letsencrypt" -v "$(pwd)/src/www:/www" quay.io/letsencrypt/letsencrypt \
			    certonly --standalone --agree-tos --renew-by-default --text --email ${EMAIL} ${LE_DOMAINS}

			if [ -r "cert/live/$DOMAINS/fullchain.pem" ]
	        then
	            echo "DOMAINS=$DOMAINS"$'\n'"EMAIL=$EMAIL"$'\n'"CONF_TAG=-ssl"$'\n'"CERT_RESTART=always" >> ".env"
	            docker-compose up -d
	        fi
        else
      	    echo "DOMAINS=$DOMAINS"$'\n'"EMAIL=$EMAIL"$'\n'"CONF_TAG=-ssl"$'\n'"CERT_RESTART=always" >> ".env"
      	    docker-compose up -d
	    fi
	else
	    echo "DOMAINS="$'\n'"CONF_TAG="$'\n'"CERT_RESTART=no" >> ".env"
	    docker-compose up -d
	fi
else
	docker-compose up -d
fi