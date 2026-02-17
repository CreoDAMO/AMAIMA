.PHONY: help dev test test-agents test-all lint format clean build docker-build docker-up docker-down

help:
	@echo "AMAIMA Backend - Available Commands"
	@echo "===================================="
	@echo "  dev            Start development server"
	@echo "  test           Run all tests"
	@echo "  test-agents    Run agent tests only"
	@echo "  test-all       Run all tests with coverage"
	@echo "  lint           Run linter checks"
	@echo "  format         Format code"
	@echo "  clean          Clean build artifacts"
	@echo "  build          Build for production"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-up      Start all services"
	@echo "  docker-down    Stop all services"

dev:
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

test:
	python -m pytest tests/ -v --tb=short

test-agents:
	python -m pytest tests/agents/ -v --tb=short

test-all:
	python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

lint:
	python -m ruff check app/ tests/

format:
	python -m ruff format app/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

build:
	pip install -r requirements.txt

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
