#!/bin/bash

set -e

echo "Checking for dhparams.pem"
if [ ! -f "/vol/proxy/ssl-dhparams.pem" ]; then
  echo "dhparams.pem not found, creating..."
  openssl dhparam -out /vol/proxy/ssl-dhparams.pem 2048
fi

# Avoid replacing these with envsubst
echo "Setting up proxy config"
export host=\$host
export request_url=\$request_uri
export UPSTREAM=api_calendaria
export APP_HOST=app
export APP_PORT=8000
export DOMAIN=api.calendaria.kz

echo "Checking for fullchain.pem"
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "fullchain.pem not found, creating..."
  envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
else
  echo "SSL certificate found, enabling HTTPS"
  # shellcheck disable=SC2016
  envsubst '${UPSTREAM} ${APP_HOST} ${APP_PORT} ${DOMAIN}' < /etc/nginx/default-ssl.conf.tpl > /etc/nginx/conf.d/default.conf

  echo "Check default config"
  cat /etc/nginx/conf.d/default.conf
fi

export UPSTREAM=dev_calendaria
export APP_HOST=dev_app
export APP_PORT=8000
export DOMAIN=dev.calendaria.kz

echo "Checking for fullchain.pem"
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "fullchain.pem not found, creating..."
  envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/dev.conf
else
  echo "SSL certificate found, enabling HTTPS"
  # shellcheck disable=SC2016
  envsubst '${UPSTREAM} ${APP_HOST} ${APP_PORT} ${DOMAIN}' < /etc/nginx/default-ssl.conf.tpl > /etc/nginx/conf.d/dev.conf

  echo "Check dev config"
  cat /etc/nginx/conf.d/dev.conf
fi

echo "Starting nginx"
nginx -g "daemon off;"
