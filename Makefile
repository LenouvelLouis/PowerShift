# Local shortcuts — mirror Azure Pipelines (see azure-pipelines.yml).
# Requires: GNU Make, Python 3.11+, PostgreSQL at DATABASE_URL (for DB tests).
#
#   make ci      → same pytest command + env vars as the pipeline
#   make check   → ruff + make ci (stricter; add Ruff to CI if you want this in Azure too)
#
# Typical workflow:
#   make install && make ci

.PHONY: help install lint lint-fix test test-quick ci check clean

PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
PYTEST      ?= $(PYTHON) -m pytest

# Same env as Azure Pipelines job "test" (override in shell or: make test DATABASE_URL=...)
export DATABASE_URL ?= postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb
export APP_NAME     ?= Energy Grid API
export APP_VERSION  ?= 0.1.0
export ENVIRONMENT  ?= testing
export DEBUG        ?= false

# UI tests (if present): point Selenium at a running server
export TEST_BASE_URL ?= http://localhost:8000

help:
	@echo "Targets:"
	@echo "  make install     pip install -e \".[dev]\""
	@echo "  make lint        ruff check app"
	@echo "  make lint-fix    ruff check app --fix"
	@echo "  make test        same as make ci (pytest + cov + junit)"
	@echo "  make test-quick  pytest tests/ -v (no cov/junit)"
	@echo "  make ci          pytest exactly like azure-pipelines.yml"
	@echo "  make check       lint + ci (recommended before push)"
	@echo "  make clean       remove coverage / junit / htmlcov artifacts"
	@echo ""
	@echo "Env: DATABASE_URL=$(DATABASE_URL)"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check app

lint-fix:
	$(PYTHON) -m ruff check app --fix

test:
	$(PYTEST) tests/ \
		--cov=app \
		--cov-report=xml \
		--junitxml=test-results.xml \
		-v

test-quick:
	$(PYTEST) tests/ -v

# Mirrors Azure Pipelines "Run tests" step only
ci: test

check: lint ci

clean:
	rm -rf .pytest_cache htmlcov
	rm -f coverage.xml test-results.xml .coverage
