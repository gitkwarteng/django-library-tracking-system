build:
	docker build -t library-web-image .

run:
	docker run -d --name library-web-app -p 8000:8000 library-web-image

stop:
	docker stop library-web-app

start:
	docker start library-web-app

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

pull:
	git pull

logs:
	docker logs library-web-app

celery-logs:
	docker logs library-celery-app

prune:
	docker system prune -a --volumes -f

shell:
	docker exec -it library-web-app /bin/sh

celery:
	celery -A libray_system worker -l INFO