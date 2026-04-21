.PHONY: help up down build logs shell-app shell-db migrate seed test lint format

help:
	@echo "Headend Ops Platform — команды управления"
	@echo ""
	@echo "  make up          — запустить все контейнеры"
	@echo "  make down        — остановить все контейнеры"
	@echo "  make build       — пересобрать образы"
	@echo "  make logs        — показать логи"
	@echo "  make shell-app   — shell в контейнере приложения"
	@echo "  make shell-db    — psql в контейнере PostgreSQL"
	@echo "  make migrate     — применить миграции Alembic"
	@echo "  make seed        — загрузить справочные данные"
	@echo "  make test        — запустить тесты"
	@echo "  make lint        — проверить код"
	@echo "  make format      — форматировать код"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app

logs-bot:
	docker compose logs -f bot

shell-app:
	docker compose exec app bash

shell-db:
	docker compose exec postgres psql -U headend -d headend_ops

migrate:
	docker compose exec app alembic upgrade head

migrate-local:
	alembic upgrade head

seed:
	docker compose exec app python scripts/seed_data.py

seed-local:
	python scripts/seed_data.py

test:
	docker compose exec app pytest tests/ -v --cov=app --cov-report=term-missing

test-local:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	docker compose exec app python -m flake8 app/ --max-line-length=100

format:
	docker compose exec app python -m black app/ tests/

revision:
	docker compose exec app alembic revision --autogenerate -m "$(MSG)"

revision-local:
	alembic revision --autogenerate -m "$(MSG)"

report-day:
	docker compose exec app python -c "from app.reports.generator import generate_report_sync; generate_report_sync('daily')"

report-month:
	docker compose exec app python -c "from app.reports.generator import generate_report_sync; generate_report_sync('monthly')"
