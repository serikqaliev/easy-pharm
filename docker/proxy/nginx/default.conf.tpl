upstream ${UPSTREAM} {
    server ${APP_HOST}:${APP_PORT};
}

server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /vol/www/;
    }

    location / {
        return 301 https://$host$request_uri; # Redirect all http requests to https
    }
}