# Wiki — Local Setup

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
