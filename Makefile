# RazorRecon — Developer & Hackathon Evaluation Makefile

.PHONY: help dev docker-up seed test lint clean quickstart

help:
	@echo "RazorRecon Developer Commands:"
	@echo "  make dev         - Start PostgreSQL, Redis, backend (port 8000), and frontend (port 5173)"
	@echo "  make docker-up   - Start PostgreSQL and Redis containers in background"
	@echo "  make seed        - Reset database and seed 100 benchmark reconciliation records"
	@echo "  make test        - Run all 21 Pytest unit & integration tests"
	@echo "  make quickstart  - One-command setup: docker up, migrate DB, seed data, and run tests"
	@echo "  make docker-prod - Launch production stack (FastAPI + Gunicorn + Nginx TLS + DB + Redis)"

docker-up:
	docker compose up -d

seed:
	cd backend && python -m app.seed

test:
	$env:PYTHONPATH="backend"; pytest tests/ -v

quickstart: docker-up seed test
	@echo "RazorRecon setup complete! Run 'make dev' or launch backend/frontend to evaluate."

docker-prod:
	docker-compose -f docker-compose.prod.yml up --build -d
