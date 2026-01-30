.PHONY: up migrate seed test llm

up:
	docker compose up --build

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python scripts/seed_demo.py

test:
	docker compose run --rm backend pytest

llm:
	docker compose -f docker-compose.llm.yml up --build
