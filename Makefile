# Tongji Course Scheduler — docker compose shortcuts.
#
# Windows users: install GNU make from
#   https://gnuwin32.sourceforge.net/packages/make.htm
# Linux / macOS ship make by default.
#
# Note: this file is intentionally ASCII-only to avoid encoding issues
# across terminals (see README for Chinese docs).

COMPOSE       := docker compose
COMPOSE_ALL   := docker compose -f docker-compose.yml -f docker-compose.monitoring.yml
TEST_COMPOSE  := docker compose -f docker-compose.test.yml

# Optional crawler arguments, e.g.:
#   make crawl CALENDARS="122 121" MESSAGE="manual sync"
CALENDARS ?=
MESSAGE   ?=

.PHONY: help init up up-monitoring down down-monitoring logs ps crawl deploy test test-backend test-crawler

help:
	@echo "make init                  first-time setup: copy .env.example to .env"
	@echo "make up                    start services (mysql/redis/backend/frontend)"
	@echo "make up-monitoring         start services + monitoring stack"
	@echo "make down                  stop services"
	@echo "make down-monitoring       stop services incl. monitoring stack"
	@echo "make logs                  tail service logs"
	@echo "make ps                    show container status"
	@echo "make crawl CALENDARS=\"122 121\" [MESSAGE=note]   fetch course data"
	@echo "make deploy                production deploy (pull images, no build)"
	@echo "make test                  run backend + crawler tests"
	@echo "make test-backend          run backend tests only"
	@echo "make test-crawler          run crawler tests only"

init:
	python -c "import os, shutil; os.path.exists('.env') or shutil.copy('.env.example', '.env')"

up:
	$(COMPOSE) up -d --build

up-monitoring:
	$(COMPOSE_ALL) up -d --build

down:
	$(COMPOSE) down

down-monitoring:
	$(COMPOSE_ALL) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

crawl:
	$(COMPOSE) run --rm crawler -c $(CALENDARS) $(if $(MESSAGE),-m "$(MESSAGE)",)

deploy:
	$(COMPOSE_ALL) pull
	$(COMPOSE_ALL) up -d

test: test-backend test-crawler

test-backend:
	$(TEST_COMPOSE) up --build backend --exit-code-from backend && $(TEST_COMPOSE) down

test-crawler:
	$(TEST_COMPOSE) up --build crawler --exit-code-from crawler && $(TEST_COMPOSE) down
