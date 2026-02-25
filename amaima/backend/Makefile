.PHONY: help dev dev-fhe test test-agents test-fhe test-integration test-all lint format clean install docker-build docker-build-fhe docker-up docker-down

help:
	@echo "AMAIMA Backend — Available Commands"
	@echo "====================================="
	@echo "Development:"
	@echo "  dev              Start dev server (FHE disabled)"
	@echo "  dev-fhe          Start dev server (FHE enabled, requires TenSEAL)"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-agents      Run agent tests only"
	@echo "  test-fhe         Run FHE subsystem tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-all         Run all tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run ruff linter"
	@echo "  format           Format code with ruff"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  install          Install Python dependencies"
	@echo "  clean            Remove build artifacts and caches"
	@echo "  docker-build     Build standard Docker image"
	@echo "  docker-build-fhe Build 3-stage Docker image with HEXL+SEAL (slow)"
	@echo "  docker-up        Start all services via docker compose"
	@echo "  docker-down      Stop all services"

# ── Development ───────────────────────────────────────────────────────────────

dev:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=false \
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-fhe:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=true \
	SEAL_THREADS=4 \
	OMP_NUM_THREADS=4 \
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=false \
	python -m pytest tests/ -v --tb=short

test-agents:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=false \
	python -m pytest tests/agents/ -v --tb=short

test-fhe:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=true \
	python -m pytest tests/fhe/ -v --tb=short

test-integration:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=false \
	python -m pytest tests/integration/ -v --tb=short

test-all:
	AMAIMA_EXECUTION_MODE=execution-enabled \
	FHE_ENABLED=false \
	python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

# ── Code Quality ──────────────────────────────────────────────────────────────

lint:
	python -m ruff check app/ tests/

format:
	python -m ruff format app/ tests/

# ── Build & Deploy ────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

docker-build:
	docker compose build

# 3-stage build with Intel HEXL + Microsoft SEAL compiled from source.
# Adds ~10-15 min to build time; produces AVX-512-accelerated TenSEAL.
# Target ~300ms per FHE operation vs ~1,100ms from the generic wheel.
docker-build-fhe:
	docker build \
		--file amaima/backend/Dockerfile \
		--tag amaima-backend-fhe:latest \
		--no-cache \
		.

docker-up:
	docker compose up -d

docker-down:
	docker compose down
