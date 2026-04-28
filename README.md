# PowerShift — Energy Grid Simulation Platform

Full-stack energy grid simulation platform built with Clean Architecture. Simulate, optimize and visualize local electricity grids using PyPSA Linear Optimal Power Flow.

---

## Features

- **Multi-bus network topology** with automatic voltage cascade bridging
- **3 optimization objectives**: minimize cost, minimize emissions, maximize renewables
- **Real weather data** from KNMI station Groningen-Eelde (wind + solar profiles, Jan–Dec 2025)
- **Battery storage** modeling with charge/discharge optimization
- **Live preview** with 400ms debounce (HTTP) + WebSocket endpoint
- **Export** simulation results as JSON, CSV or PDF
- **Scenario comparison** side-by-side (KPI delta + capacity factor charts)
- **i18n** French / English with runtime language switcher
- **Dark / Light mode** toggle with Tailwind semantic classes
- **API key authentication** (optional, disabled in dev)
- **Pagination** on all list endpoints
- **Structured JSON logging** with request-id correlation
- **Alembic migrations** for versioned database schema
- **Custom demand profiles** via CSV upload
- **Weather data caching** (in-memory, 1h TTL)
- **Accessibility** (ARIA labels, keyboard navigation, skip nav, contrast)

---

## Stack

### Backend
| Technology | Role |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI (async) | Web framework |
| SQLAlchemy (asyncio) + asyncpg | Async ORM + PostgreSQL driver |
| PostgreSQL 17 | Database (Docker local) |
| PyPSA + HiGHS | Power grid simulation (LOPF) |
| Alembic | Database migrations |
| slowapi | Rate limiting (60 req/min) |
| reportlab | PDF report generation |
| Pytest + httpx + pytest-bdd | Testing (216+ tests) |

### Frontend
| Technology | Role |
|---|---|
| Nuxt 4 | Vue meta-framework |
| Vue 3 + TypeScript | UI components |
| @nuxt/ui | Component library |
| Pinia | Global state management |
| ECharts (vue-echarts) | Charts and data visualization |
| @nuxtjs/i18n | Internationalization (FR/EN) |
| Vitest + @vue/test-utils | Frontend testing (30+ tests) |
| Tailwind CSS | Styling (semantic dark/light mode) |

---

## Quick Start

Requirements: [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

```bash
git clone https://github.com/LenouvelLouis/PowerShift.git
cd PowerShift

cp .env.example .env        # works out of the box for local dev
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

```bash
docker compose down          # stop
docker compose down -v       # stop + reset database
docker compose watch         # hot-reload backend in dev
```

### Manual Installation

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload    # http://localhost:8000

# Frontend
cd energy-dashboard
pnpm install && pnpm dev         # http://localhost:3000
```

---

## API Endpoints

### Referential
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/referential` | All components (supplies + demands + network) |

### Supplies
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/supplies?page=1&size=20` | List supplies (paginated) |
| GET | `/api/v1/supplies/{id}` | Get a supply |
| POST | `/api/v1/supplies` | Create a supply |
| PUT | `/api/v1/supplies/{id}` | Update a supply |
| DELETE | `/api/v1/supplies/{id}` | Delete a supply |

### Demands
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/demands?page=1&size=20` | List demands (paginated) |
| GET | `/api/v1/demands/{id}` | Get a demand |
| POST | `/api/v1/demands` | Create a demand |
| PUT | `/api/v1/demands/{id}` | Update a demand |
| DELETE | `/api/v1/demands/{id}` | Delete a demand |
| POST | `/api/v1/demands/{id}/profile` | Upload custom load profile (CSV) |
| GET | `/api/v1/demands/{id}/profile` | Get custom load profile |
| DELETE | `/api/v1/demands/{id}/profile` | Remove custom load profile |

### Network
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/network?page=1&size=20` | List network components (paginated) |
| GET | `/api/v1/network/{id}` | Get a network component |
| POST | `/api/v1/network` | Create a network component |
| DELETE | `/api/v1/network/{id}` | Delete a network component |

### Simulation
| Method | Route | Description |
|---|---|---|
| POST | `/api/v1/simulation/save` | Run and save a simulation |
| POST | `/api/v1/simulation/preview` | Run without saving (live preview) |
| POST | `/api/v1/simulation/import` | Import and run a scenario |
| GET | `/api/v1/simulation?page=1&size=20` | List past simulations (paginated) |
| GET | `/api/v1/simulation/solvers` | List available solvers |
| GET | `/api/v1/simulation/{id}` | Get a simulation result |
| DELETE | `/api/v1/simulation/{id}` | Delete a simulation |
| PATCH | `/api/v1/simulation/{id}/rename` | Rename a scenario |
| GET | `/api/v1/simulation/{id}/export` | Export scenario config (JSON) |
| GET | `/api/v1/simulation/{id}/export/csv` | Export results (CSV) |
| GET | `/api/v1/simulation/{id}/export/pdf` | Export report (PDF) |
| WS | `/api/v1/simulation/ws` | WebSocket live preview |

### Cache & System
| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check (verifies DB connection) |
| GET | `/api/v1/cache/stats` | Weather cache stats (size, hits, misses) |
| DELETE | `/api/v1/cache` | Clear weather cache |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | (docker default) | PostgreSQL connection string |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `FRONTEND_URL` | — | Frontend URL for CORS |
| `API_KEY` | (empty = no auth) | API key for authentication |
| `WEATHER_CACHE_TTL_SECONDS` | `3600` | Weather profile cache TTL |
| `NUXT_API_BASE_URL` | `http://localhost:8000` | Backend URL for Nuxt proxy |
| `NUXT_API_KEY` | — | API key forwarded by Nuxt proxy |

---

## Architecture

```
app/                             # Python backend (Clean Architecture)
├── config.py                    # Settings (pydantic-settings)
├── main.py                      # FastAPI app + middleware (CORS, rate limit, request-id)
│
├── domain/                      # Domain layer — zero external dependencies
│   ├── entities/                # Supply (Wind, Solar, Nuclear, Battery), Demand, Network
│   ├── interfaces/              # Repository ABCs
│   ├── use_cases/               # GetReferential, RunSimulation, PreviewSimulation
│   ├── wind/                    # Wind power calculation domain
│   ├── nuclear/                 # Nuclear constraints domain
│   └── simulation/              # Simulation exceptions (WeatherDataEmptyError)
│
├── application/                 # Application layer
│   └── services/                # ReferentialService, SimulationService, ExportService
│
├── infrastructure/              # Infrastructure layer
│   ├── db/                      # Async engine, models, repositories
│   ├── cache/                   # In-memory weather cache with TTL
│   ├── logging.py               # JSON formatter + request-id context
│   └── simulation/
│       ├── network_builder.py   # PyPSA LOPF (multi-bus, auto-bridge)
│       └── objectives/          # MinCost, MinEmissions, MaxRenewable strategies
│
└── api/v1/
    ├── auth.py                  # API key authentication dependency
    ├── endpoints/               # REST + WebSocket endpoints
    └── router.py                # V1 router with auth dependency

alembic/                         # Database migrations
├── env.py                       # Async migration runner
└── versions/                    # Migration scripts

energy-dashboard/                # Nuxt 4 frontend
├── app/
│   ├── components/              # Vue components (charts, features, ui, network-canvas)
│   ├── composables/             # API client, ECharts theme, live runner, scenario IO
│   ├── stores/                  # Pinia: simulation, history, referential
│   ├── pages/                   # index.vue (main dashboard)
│   └── i18n/                    # EN/FR translation files
├── i18n/                        # Translation JSON files (en.json, fr.json)
└── server/routes/               # Nitro proxy (API + WebSocket)
```

---

## Optimization Objectives

| Value | Strategy |
|---|---|
| `min_cost` | Minimize total generation cost (merit order: renewables → battery → nuclear → grid) |
| `min_emissions` | Minimize CO2 emissions (penalizes fossil, favors zero-carbon sources) |
| `max_renewable` | Maximize renewable generation share in the energy mix |

---

## Weather Data

Solar irradiance and wind speed profiles come from KNMI station Groningen-Eelde (06280), covering January–December 2025. Profiles are cached in memory (1h TTL) to avoid repeated API calls during iterative preview sessions.

When weather data is unavailable for the requested date range, the simulation returns a structured error (`ERR_WEATHER_DATA_EMPTY`) instead of silently producing zero-output results. This can be disabled via `fail_on_empty_weather: false` in the request.

---

## Testing

```bash
# Backend (216+ tests)
python -m pytest tests/unit/     # Unit tests
python -m pytest tests/api/      # API integration tests
python -m pytest tests/bdd/      # BDD scenarios

# Frontend (30+ tests)
cd energy-dashboard && pnpm test

# Linting
python -m ruff check app/        # Backend
cd energy-dashboard && pnpm lint  # Frontend
cd energy-dashboard && pnpm typecheck
```

---

## License

ISEP Project 2026 — Louis Lenouvel
