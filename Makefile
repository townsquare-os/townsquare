# townsquare — common operations.
# Use `make <target>`. Run `make help` to list targets.

.PHONY: help up down restart logs build pull rebuild ps init-db gen-secrets \
        admin-list-users backup restore test lint format

help:
	@echo "townsquare — operations"
	@echo ""
	@echo "Self-host:"
	@echo "  make build               build the api image"
	@echo "  make up                  start db + api in the background"
	@echo "  make down                stop"
	@echo "  make restart             restart api only"
	@echo "  make logs                tail api logs"
	@echo "  make ps                  show running containers"
	@echo "  make rebuild             stop, rebuild, restart"
	@echo ""
	@echo "Admin:"
	@echo "  make gen-secrets         print FERNET_KEY + SECRET_KEY (paste into .env)"
	@echo "  make init-db             run init-db inside the api container"
	@echo "  make admin-list-users    list registered users"
	@echo ""
	@echo "Data:"
	@echo "  make backup              dump postgres to ./backups/<timestamp>.sql.gz"
	@echo "  make restore FILE=...    restore a postgres dump"
	@echo ""
	@echo "Dev:"
	@echo "  make test                run pytest"
	@echo "  make lint                ruff check + format"

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart api

logs:
	docker compose logs -f api

build:
	docker compose build

pull:
	docker compose pull

rebuild:
	docker compose down
	docker compose up -d --build --force-recreate

ps:
	docker compose ps

gen-secrets:
	docker compose run --rm api townsquare gen-secrets

init-db:
	docker compose exec api townsquare init-db

admin-list-users:
	docker compose exec api townsquare admin list-users

backup:
	@mkdir -p backups
	@stamp=$$(date -u +%Y%m%dT%H%M%SZ); \
	  docker compose exec -T db pg_dump -U $${DB_USER:-townsquare} $${DB_NAME:-townsquare} | gzip > backups/$$stamp.sql.gz; \
	  echo "wrote backups/$$stamp.sql.gz"

restore:
	@test -n "$(FILE)" || (echo "usage: make restore FILE=backups/20260429T....sql.gz"; exit 1)
	@gunzip -c $(FILE) | docker compose exec -T db psql -U $${DB_USER:-townsquare} $${DB_NAME:-townsquare}
	@echo "restored from $(FILE)"

test:
	.venv/bin/pytest tests/ -v

lint:
	.venv/bin/ruff check src/
	.venv/bin/ruff format --check src/

format:
	.venv/bin/ruff format src/ tests/
