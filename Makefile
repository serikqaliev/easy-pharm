rsgunicorn:
	systemctl restart gunicorn

daemon:
	systemctl daemon-reload

restart:
	systemctl restart nginx

build:
	sudo docker-compose -f docker-compose.deploy.yml run --rm certbot /opt/certify-init.sh

up:
	sudo docker-compose -f docker-compose.deploy.yml up -d

down:
	sudo docker-compose -f docker-compose.deploy.yml down

activate:
	source venv/bin/activate

daphne:
	daphne -b 0.0.0.0 -p 8000 project.asgi:application

migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

.PHONY: rsgunicorn daemon restart build up down activate daphne migrations migrate