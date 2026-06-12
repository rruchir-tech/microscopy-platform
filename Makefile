.PHONY: help backend frontend test test-backend test-frontend up down lint

help:
	@echo "Targets:"
	@echo "  up             docker-compose up --build"
	@echo "  down           docker-compose down"
	@echo "  backend        run FastAPI dev server (SQLite, eager Celery)"
	@echo "  frontend       run Vite dev server"
	@echo "  test           run backend + frontend tests"

up:
	docker-compose up --build

down:
	docker-compose down

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest -q

test-frontend:
	cd frontend && npm run test

test: test-backend test-frontend

lint:
	cd backend && ruff check app tests
	cd frontend && npm run build
