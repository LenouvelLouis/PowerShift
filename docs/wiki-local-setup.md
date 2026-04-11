# Wiki — Local Setup

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| pnpm | 10+ | `npm install -g pnpm` |
| PostgreSQL | 15+ | Local install or Docker |

---

## 1. Clone and configure environment

```bash
git clone <repo-url>
cd <repo>
cp .env.example .env
```

Edit `.env` with your values:

```env
# App
APP_NAME="Energy Grid API"
APP_VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Database — pick one:
# Local PostgreSQL:
DATABASE_URL=postgresql+asyncpg://tes_user:tes_password@localhost:5432/tes_db
# DB cloud:
# DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.eu-central-1.aws.com

# Frontend (reachable from the frontend container, set to backend's internal Docker Compose hostname):
NUXT_API_BASE_URL=http://localhost:8000

# KNMI (only needed for weather data ingestion scripts)
KNMI_API_KEY=your-knmi-api-key-here
```

> `AZURE_KEY_VAULT_URL` and related Azure vars can be left blank for local dev — the app falls back to `.env`.

---

## 2. Backend

### Install dependencies

```bash
pip install -e ".[dev]"
```

### Run the API

```bash
uvicorn main:app --reload
```

API available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

### Run tests

```bash
pytest              # run all tests
pytest -v           # verbose
pytest --cov=app    # with coverage
```

Tests use an in-memory SQLite database (via `aiosqlite`) — no real DB needed.

### Lint and format

```bash
ruff check app/     # lint
ruff format app/    # format
```

---

## 3. Frontend

```bash
cd energy-dashboard
pnpm install
pnpm dev
```

Frontend available at `http://localhost:3000`.

### Type check and lint

```bash
pnpm typecheck      # must pass before any commit
pnpm lint
```

### Production build

```bash
pnpm build
```

---

## 4. Run with Docker Compose

Runs backend + frontend together. Requires Docker with Compose plugin.

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL to Cloud DB or a local PostgreSQL accessible from Docker
docker compose up --build
```

| Service | URL |
|---|---|
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:80` |

The frontend container talks to the backend via the Docker Compose internal DNS (`http://backend:8000`), set by `NUXT_API_BASE_URL` in `docker-compose.yml`.

---

## 5. Database

The project uses a **self-hosted PostgreSQL container on the Azure VM** (`74.178.89.28:5432`) in production. For local dev, you can either connect to the production DB or run a local PostgreSQL instance.

### Get the production DATABASE_URL

The credentials are stored in Azure DevOps Variable Group `energy-grid-prod` (secret `DATABASE_URL`). Ask a project member with Azure DevOps access to share it with you securely.

Connection string format:
```
postgresql+asyncpg://isep_admin:<password>@74.178.89.28:5432/isep_db
```

### Schema migrations

Migrations are run via raw SQL or Alembic. Never use `Base.metadata.create_all()` in production.

Check `alembic/` or `scripts/` for migration files.

### Weather profile ingestion (KNMI data)

The `weather_profile` table stores hourly meteorological data from KNMI station `06280` (Groningen Eelde). It is the source of truth for solar irradiance and wind speed profiles used in simulations.

To ingest data:

```bash
python scripts/ingest_weather_profile.py
```

Requires `KNMI_API_KEY` in `.env`. Register for free at [developer.dataplatform.knmi.nl](https://developer.dataplatform.knmi.nl/).

Without ingested data, simulations will run but solar/wind profiles will be all-zero and a warning will appear in `result_json["warnings"]`.

---

## 6. Key Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string (asyncpg driver) |
| `ENVIRONMENT` | yes | `development` / `staging` / `production` |
| `NUXT_API_BASE_URL` | frontend | Backend URL reachable from the frontend |
| `KNMI_API_KEY` | ingestion only | KNMI Open Data API key |
| `AZURE_KEY_VAULT_URL` | optional | Leave blank to use `.env` only |

---

## 7. Project Structure

```
.
├── app/                        # Backend (Python, FastAPI)
│   ├── api/v1/                 # HTTP layer (endpoints, schemas)
│   │   ├── dependencies.py     # DI wiring — only file that imports infrastructure
│   │   ├── endpoints/          # FastAPI routers
│   │   └── schemas/            # Pydantic v2 request/response schemas
│   ├── application/            # Use cases and services
│   │   ├── dtos/               # Data Transfer Objects
│   │   └── services/           # Business logic orchestration
│   ├── domain/                 # Pure domain — no framework imports
│   │   ├── entities/           # Domain entities (supply, demand, network…)
│   │   └── interfaces/         # Abstract base classes (repository interfaces)
│   └── infrastructure/         # Framework-specific implementations
│       ├── db/
│       │   ├── models/         # SQLAlchemy ORM models
│       │   └── repositories/   # Repository implementations
│       ├── external/           # External API clients (Open-Meteo)
│       └── simulation/         # PyPSA network builder and adapter
├── energy-dashboard/           # Frontend (Nuxt 4, Vue 4, TypeScript)
├── tests/                      # pytest test suite
├── scripts/                    # Utility scripts (KNMI ingestion, etc.)
├── docker-compose.yml
├── azure-pipelines.yml
└── .env.example
```
