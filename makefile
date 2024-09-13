test:
	docker compose -f compose.test.yml run --rm server pytest -qx --ff -v

reload: migrate
	docker compose run \
		-v /Users/roderic/Developer/rs/src/:/data/src/ \
		-v /Users/roderic/Developer/rs/dst/:/data/dst/ \
		-v /Users/roderic/Developer/rs/src/_media/:/data/media/ \
		--rm server ./manage.py loaddata

static:
	mkdir -p redsails/assets/
	docker compose run \
		-v `pwd`/redsails/assets/:/pngs/ \
		--rm server sh pngs.sh
	docker compose run --rm server ./manage.py collectstatic --noinput

migrations:
	docker compose run --rm server ./manage.py makemigrations

migrate:
	docker compose run --rm server ./manage.py migrate

clean: build

main: build
	docker compose down
	docker compose up

build:
	docker compose build

deploy:
	scp compose.prod.yml rs:redsails/compose.yml
	rsync -atuc --exclude=.git . root@rs:redsails
	ssh rs "cd redsails \
		&& docker compose build -q \
		&& docker compose down \
		&& docker compose up -d"
