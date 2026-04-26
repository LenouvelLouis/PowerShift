# Azure-to-GitHub Migration + Docker PostgreSQL Local Dev

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all Azure DevOps dependencies, create GitHub Actions CI, add a local Docker PostgreSQL service to docker-compose for zero-config dev setup, and clean up old project references.

**Architecture:** Replace `azure-pipelines.yml` with GitHub Actions workflows. Add a `db` service (PostgreSQL 15) to `docker-compose.yml` so developers never need NeonDB credentials to run locally. Update `connection.py` to handle both local Docker PG and cloud NeonDB seamlessly. Clean all `isep-app`, Azure, and stale references from the codebase.

**Tech Stack:** GitHub Actions, Docker Compose, PostgreSQL 15, FastAPI, asyncpg, SQLAlchemy async, Nuxt 3, pnpm

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `.github/workflows/ci.yml` | Backend CI: lint + tests with PostgreSQL service |
| Create | `.github/workflows/frontend-ci.yml` | Frontend CI: lint + typecheck + build |
| Modify | `docker-compose.yml` | Add `db` PostgreSQL service, update backend to depend on it |
| Modify | `.env.example` | Rewrite: remove Azure, add Docker PG defaults, keep NeonDB as option |
| Modify | `app/config.py` | Remove hardcoded NeonDB URL, use safe Docker default |
| Modify | `app/infrastructure/db/connection.py` | Handle both asyncpg (PG) and aiosqlite (tests) cleanly |
| Modify | `Makefile` | Update comments: Azure -> GitHub, add `make docker-up` target |
| Modify | `README.md` | Update install instructions for Docker PG, remove NeonDB requirement |
| Modify | `docs/wiki-local-setup.md` | Rewrite for Docker PG local dev, remove Azure references |
| Delete | `azure-pipelines.yml` | No longer needed |
| Delete | `scripts/install-agent.sh` | Azure Pipelines agent installer, no longer needed |
| Modify | `docs/wiki-azure-deploy.md` | Rename to `docs/wiki-legacy-azure-deploy.md` (archive) |
| Modify | `app/domain/entities/demand/electric_vehicle.py` | Remove "ISEP 2026" from docstring |
| Modify | `app/infrastructure/external/open_meteo_provider.py` | Remove "ISEP 2026 QA" from comment |

---

### Task 1: Add PostgreSQL to docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Read current docker-compose.yml and verify understanding**

Current file has `backend` and `frontend` services. No database service.

- [ ] **Step 2: Add `db` service and update `backend` to depend on it**

Replace the entire `docker-compose.yml` with:

```yaml
services:

  # --- PostgreSQL database ------------------------------------------------
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: powershift
      POSTGRES_PASSWORD: powershift
      POSTGRES_DB: powershift
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U powershift"]
      interval: 5s
      timeout: 3s
      retries: 5

  # --- FastAPI backend ----------------------------------------------------
  backend:
    build:
      context: .
      dockerfile: app/Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://powershift:powershift@db:5432/powershift
      ENVIRONMENT: development
    depends_on:
      db:
        condition: service_healthy
    develop:
      watch:
        - action: sync
          path: ./app
          target: /workspace/app

  # --- Nuxt frontend ------------------------------------------------------
  frontend:
    build:
      context: ./energy-dashboard
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "80:3000"
    environment:
      NUXT_API_BASE_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  pgdata:
```

- [ ] **Step 3: Verify with `docker compose config`**

Run: `docker compose config`
Expected: valid YAML, no errors, 3 services listed (db, backend, frontend)

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add PostgreSQL service to docker-compose for local dev"
```

---

### Task 2: Update .env.example and app/config.py

**Files:**
- Modify: `.env.example`
- Modify: `app/config.py`

- [ ] **Step 1: Rewrite .env.example**

Replace the entire file with:

```env
# ── App ──────────────────────────────────────────────────
APP_NAME="Energy Grid API"
APP_VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development   # development | staging | production

# ── Database ─────────────────────────────────────────────
# Docker Compose (default — works out of the box with `docker compose up`):
DATABASE_URL=postgresql+asyncpg://powershift:powershift@localhost:5432/powershift

# NeonDB cloud (uncomment and replace for cloud DB):
# DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require

# ── Frontend ──────────────────────────────────────────────
# Docker Compose (backend reachable via service name):
NUXT_API_BASE_URL=http://backend:8000
# Local dev (outside Docker):
# NUXT_API_BASE_URL=http://localhost:8000

# ── KNMI Open Data API ────────────────────────────────────
# Register at https://developer.dataplatform.knmi.nl/ (free)
# Used by scripts/ingest_weather_profile.py
KNMI_API_KEY=your-knmi-api-key-here
```

- [ ] **Step 2: Remove hardcoded NeonDB URL from app/config.py**

Replace the `DATABASE_URL` default in `app/config.py`:

Old:
```python
    DATABASE_URL: str = "postgresql://neondb_owner:npg_OUMdt0gS5vkD@ep-silent-dream-albpp1df-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

New:
```python
    DATABASE_URL: str = "postgresql+asyncpg://powershift:powershift@localhost:5432/powershift"
```

- [ ] **Step 3: Commit**

```bash
git add .env.example app/config.py
git commit -m "fix: remove hardcoded NeonDB credentials, use local Docker PG as default"
```

---

### Task 3: Create GitHub Actions CI for backend

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/` directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create ci.yml**

```yaml
name: Backend CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: ["*"]

jobs:
  test:
    name: Lint & Test
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb
      APP_NAME: Energy Grid API
      APP_VERSION: "0.1.0"
      ENVIRONMENT: testing
      DEBUG: "false"

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint (ruff)
        run: ruff check app/

      - name: Run tests
        run: |
          pytest tests/unit/ tests/api/ tests/bdd/ tests/simulation/ tests/integration/ \
            --ignore=tests/ui \
            --cov=app \
            --cov-report=xml \
            --junitxml=test-results.xml \
            -v

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results.xml

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage
          path: coverage.xml
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: add GitHub Actions CI workflow for backend (lint + tests)"
```

---

### Task 4: Create GitHub Actions CI for frontend

**Files:**
- Create: `.github/workflows/frontend-ci.yml`

- [ ] **Step 1: Create frontend-ci.yml**

```yaml
name: Frontend CI

on:
  push:
    branches: ["*"]
    paths:
      - "energy-dashboard/**"
  pull_request:
    branches: ["*"]
    paths:
      - "energy-dashboard/**"

jobs:
  lint-and-build:
    name: Lint, Typecheck & Build
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: energy-dashboard

    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 10

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: energy-dashboard/pnpm-lock.yaml

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Typecheck
        run: pnpm typecheck

      - name: Build
        run: pnpm build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/frontend-ci.yml
git commit -m "feat: add GitHub Actions CI workflow for frontend (lint + typecheck + build)"
```

---

### Task 5: Delete Azure Pipelines files

**Files:**
- Delete: `azure-pipelines.yml`
- Delete: `scripts/install-agent.sh`

- [ ] **Step 1: Delete the files**

```bash
rm azure-pipelines.yml
rm scripts/install-agent.sh
```

- [ ] **Step 2: Commit**

```bash
git add -A azure-pipelines.yml scripts/install-agent.sh
git commit -m "chore: remove Azure Pipelines config and agent installer"
```

---

### Task 6: Update Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Rewrite Makefile**

Replace the entire file with:

```makefile
# Local shortcuts — mirrors GitHub Actions CI.
# Requires: GNU Make, Python 3.11+.
#
#   make ci        → same pytest command + env vars as the CI pipeline
#   make check     → ruff + make ci
#   make docker-up → start full stack (DB + backend + frontend) via Docker Compose
#
# Typical workflow:
#   make install && make ci

.PHONY: help install lint lint-fix test test-quick ci check clean docker-up docker-down

PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
PYTEST      ?= $(PYTHON) -m pytest

# Default env for CI-like local runs (override in shell or .env)
export DATABASE_URL ?= postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb
export APP_NAME     ?= Energy Grid API
export APP_VERSION  ?= 0.1.0
export ENVIRONMENT  ?= testing
export DEBUG        ?= false

# UI tests: point Selenium at a running server
export TEST_BASE_URL ?= http://localhost:8000

help:
	@echo "Targets:"
	@echo "  make install     pip install -e \".[dev]\""
	@echo "  make lint        ruff check app"
	@echo "  make lint-fix    ruff check app --fix"
	@echo "  make test        same as make ci (pytest + cov + junit)"
	@echo "  make test-quick  pytest tests/ -v (no cov/junit)"
	@echo "  make ci          pytest exactly like GitHub Actions CI"
	@echo "  make check       lint + ci (recommended before push)"
	@echo "  make docker-up   start DB + backend + frontend via Docker Compose"
	@echo "  make docker-down stop all Docker Compose services"
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

ci: test

check: lint ci

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache htmlcov
	rm -f coverage.xml test-results.xml .coverage
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "chore: update Makefile for GitHub Actions, add docker-up/docker-down targets"
```

---

### Task 7: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the Installation section**

Find the `## Installation` section and replace everything from `## Installation` up to (but not including) `## Endpoints` with:

```markdown
## Installation

### Docker (recommended)

Requirements: [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

```bash
# 1. Clone the repo
git clone https://github.com/LenouvelLouis/PowerShift.git
cd PowerShift

# 2. Configure environment variables
cp .env.example .env
# .env works out of the box for local dev — no cloud DB needed

# 3. Build and start all services (PostgreSQL + backend + frontend)
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (Nuxt) | http://localhost:80 |
| Backend (FastAPI) | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

To stop all services:

```bash
docker compose down
```

In development, the backend supports hot-reload via `docker compose watch`:

```bash
docker compose watch
```

Changes in `app/` are synced into the container automatically without a rebuild.

### Database

The Docker Compose stack includes a PostgreSQL 15 container. Data is persisted in a Docker volume (`pgdata`), so it survives `docker compose down`.

To fully reset the database:

```bash
docker compose down -v   # removes volumes
docker compose up --build
```

To use a cloud database (NeonDB or other) instead, set `DATABASE_URL` in your `.env` file.

---

### Manual installation

#### Backend

```bash
# 1. Clone the repo
git clone https://github.com/LenouvelLouis/PowerShift.git
cd PowerShift

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# Edit .env — point DATABASE_URL to a running PostgreSQL instance

# 5. Start the server
uvicorn app.main:app --reload
```

The API is available at [http://localhost:8000](http://localhost:8000).
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs).

#### Frontend

```bash
cd energy-dashboard
pnpm install
pnpm dev
```

The dashboard is available at [http://localhost:3000](http://localhost:3000).
```

- [ ] **Step 2: Replace the Makefile section in README.md**

Find the duplicated Makefile section and replace with a single one:

```markdown
### Makefile (run CI checks locally)

If you have **GNU Make**:

```bash
make help          # list targets
make install       # pip install -e ".[dev]"
make ci            # pytest with same flags and env as GitHub Actions CI
make check         # lint + ci (recommended before push)
make test-quick    # fast pytest without coverage / junit
make docker-up     # start full stack via Docker Compose
make docker-down   # stop all services
```
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for Docker PostgreSQL local dev, remove NeonDB requirement"
```

---

### Task 8: Update docs/wiki-local-setup.md

**Files:**
- Modify: `docs/wiki-local-setup.md`

- [ ] **Step 1: Rewrite wiki-local-setup.md**

Replace the entire file with:

```markdown
# Wiki -- Local Setup

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker | 24+ | [docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | v2+ | Included with Docker Desktop |
| Python | 3.11+ | [python.org](https://python.org) (manual install only) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) (manual install only) |
| pnpm | 10+ | `npm install -g pnpm` (manual install only) |

---

## 1. Quick start (Docker Compose)

```bash
git clone https://github.com/LenouvelLouis/PowerShift.git
cd PowerShift
cp .env.example .env
docker compose up --build
```

This starts **3 services**:
- **db** — PostgreSQL 15 on port 5432 (user: `powershift`, password: `powershift`, database: `powershift`)
- **backend** — FastAPI on port 8000
- **frontend** — Nuxt on port 80

No cloud database needed. Data persists in a Docker volume.

---

## 2. Manual backend setup (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure .env
cp .env.example .env
# Edit DATABASE_URL to point to your PostgreSQL instance

# Start the API
uvicorn app.main:app --reload
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

---

## 3. Manual frontend setup (without Docker)

```bash
cd energy-dashboard
pnpm install
pnpm dev
```

Dashboard: http://localhost:3000

---

## 4. Running tests

Tests use an in-memory SQLite database — no real DB needed.

```bash
pytest tests/ --ignore=tests/ui -v          # all tests except UI
pytest tests/bdd/ -v                         # BDD only
pytest tests/api/ -v                         # API only
pytest tests/ --cov=app --cov-report=html -v # with coverage
```

### Lint

```bash
ruff check app/        # lint
ruff check app/ --fix  # auto-fix
```

### Makefile shortcuts

```bash
make install     # pip install -e ".[dev]"
make ci          # pytest like GitHub Actions CI
make check       # lint + ci
make docker-up   # start all services
make docker-down # stop all services
```

---

## 5. Database

### Local (Docker Compose)

The `db` service runs PostgreSQL 15 with these defaults:

| Parameter | Value |
|---|---|
| Host | `localhost` (or `db` from within Docker) |
| Port | `5432` |
| User | `powershift` |
| Password | `powershift` |
| Database | `powershift` |
| Connection string | `postgresql+asyncpg://powershift:powershift@localhost:5432/powershift` |

To reset the database:
```bash
docker compose down -v && docker compose up --build
```

### Cloud (NeonDB)

To use NeonDB instead, set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

### Weather profile ingestion (KNMI data)

```bash
python scripts/ingest_weather_profile.py
```

Requires `KNMI_API_KEY` in `.env`. Register for free at [developer.dataplatform.knmi.nl](https://developer.dataplatform.knmi.nl/).

---

## 6. Key Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string (asyncpg driver) |
| `ENVIRONMENT` | yes | `development` / `staging` / `production` |
| `NUXT_API_BASE_URL` | frontend | Backend URL reachable from the frontend |
| `KNMI_API_KEY` | ingestion only | KNMI Open Data API key |
```

- [ ] **Step 2: Commit**

```bash
git add docs/wiki-local-setup.md
git commit -m "docs: rewrite local setup guide for Docker PostgreSQL, remove Azure references"
```

---

### Task 9: Archive Azure deploy doc, clean ISEP references

**Files:**
- Rename: `docs/wiki-azure-deploy.md` -> `docs/wiki-legacy-azure-deploy.md`
- Modify: `app/domain/entities/demand/electric_vehicle.py` (line 3)
- Modify: `app/infrastructure/external/open_meteo_provider.py` (line ~29)

- [ ] **Step 1: Rename azure deploy doc**

```bash
git mv docs/wiki-azure-deploy.md docs/wiki-legacy-azure-deploy.md
```

- [ ] **Step 2: Add archive notice at the top of wiki-legacy-azure-deploy.md**

Prepend to the file:

```markdown
> **ARCHIVED** — This document describes the legacy Azure DevOps deployment that is no longer in use. The project now uses GitHub Actions for CI/CD. Kept for historical reference.

---

```

- [ ] **Step 3: Clean ISEP reference in electric_vehicle.py**

In `app/domain/entities/demand/electric_vehicle.py`, find the docstring line:
```
Profile source: ISEP 2026
```
Replace with:
```
Profile source: PowerShift — EV Charging Power Profile
```

- [ ] **Step 4: Clean ISEP reference in open_meteo_provider.py**

In `app/infrastructure/external/open_meteo_provider.py`, find:
```
Source: ISEP 2026 QA
```
Replace with:
```
Source: PowerShift — Open-Meteo integration
```

- [ ] **Step 5: Commit**

```bash
git add docs/ app/domain/entities/demand/electric_vehicle.py app/infrastructure/external/open_meteo_provider.py
git commit -m "chore: archive Azure deploy doc, clean ISEP references"
```

---

### Task 10: Verify everything works

- [ ] **Step 1: Run `docker compose config` to validate compose file**

```bash
docker compose config
```
Expected: valid output with 3 services, no errors.

- [ ] **Step 2: Run `docker compose up --build -d` to start the stack**

```bash
docker compose up --build -d
```
Expected: all 3 services start (db, backend, frontend).

- [ ] **Step 3: Health check**

```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","app":"Energy Grid API",...}`

- [ ] **Step 4: Check frontend**

Open http://localhost:80 in browser.
Expected: Nuxt dashboard loads.

- [ ] **Step 5: Stop and run tests**

```bash
docker compose down
pytest tests/ --ignore=tests/ui -v
```
Expected: tests pass (they use SQLite, not the Docker PG).

- [ ] **Step 6: Verify no Azure/ISEP references remain in active code**

```bash
grep -r "azure-pipelines\|isep-app\|isep_admin\|isep_db" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.toml" --include="*.json" .
```
Expected: zero matches (except possibly in `docs/wiki-legacy-azure-deploy.md` and `pnpm-lock.yaml`).
