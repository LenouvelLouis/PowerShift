# Energy Grid API

REST API for grid simulation and energy component management — Clean Architecture with PyPSA, SQLAlchemy async, and NeonDB.

---

## Stack

| Technology | Role |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| SQLAlchemy (asyncio) | Async ORM |
| asyncpg | Async PostgreSQL driver |
| NeonDB | Serverless PostgreSQL database |
| PyPSA | Power grid simulation |
| Azure Key Vault | Secret management (optional) |
| pydantic-settings | Environment variable loading |
| Pytest + httpx | Testing |

---

## Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd <repo-name>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies (registers the app package in editable mode)
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL to your NeonDB connection string

# 5. Create tables and seed sample data
python scripts/seed.py

# 6. Start the server
uvicorn main:app --reload
```

The API is available at [http://localhost:8000](http://localhost:8000).
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Environment variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | **Yes** | NeonDB connection string — `postgresql+asyncpg://user:pass@host/db?sslmode=require` |
| `DEBUG` | No | Set to `true` to enable SQLAlchemy query logging |
| `AZURE_KEY_VAULT_URL` | No | AKV vault URL — leave blank to skip and use `.env` only |
| `AZURE_CLIENT_ID` | No | Service-principal client ID (only when running outside Azure) |
| `AZURE_CLIENT_SECRET` | No | Service-principal secret |
| `AZURE_TENANT_ID` | No | Azure tenant ID |

> **Azure Key Vault is fully optional.** When `AZURE_KEY_VAULT_URL` is blank (the default),
> the app reads all settings from `.env`. AKV overrides take effect only when the URL is set.

---

## Tests

```bash
pytest
pytest -v   # verbose
```

---

## Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/referential` | All components (supplies + demands) |
| GET | `/api/v1/supplies` | List all supply sources |
| GET | `/api/v1/supplies/{id}` | Get a single supply source |
| GET | `/api/v1/demands` | List all demand nodes |
| GET | `/api/v1/demands/{id}` | Get a single demand node |
| POST | `/api/v1/simulation/run` | Run a PyPSA grid simulation |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## Architecture

```
app/                             # Main Python package
├── config.py                    # Settings (pydantic-settings) — single source of truth
├── main.py                      # FastAPI app + /health + v1 router registration
│
├── domain/                      # Domain layer — zero external dependencies
│   ├── entities/
│   │   ├── base_component.py    # ComponentStatus enum + BaseComponent ABC
│   │   ├── supply/              # WindTurbine, SolarPanel, NuclearPlant
│   │   └── demand/              # House, ElectricVehicle
│   ├── interfaces/              # ABCs: ISupplyRepository, IDemandRepository, ISimulationRepository
│   └── use_cases/               # GetReferentialUseCase, RunSimulationUseCase
│
├── application/                 # Application layer
│   ├── dtos/                    # SupplyDTO, DemandDTO, ReferentialDTO
│   └── services/                # ReferentialService, SimulationService
│
├── infrastructure/              # Infrastructure layer
│   ├── secrets/
│   │   ├── azure_key_vault.py   # Thin AKV SDK wrapper
│   │   └── settings.py          # get_settings() — resolves AKV overrides on top of .env
│   ├── db/
│   │   ├── connection.py        # Async engine + get_db() FastAPI dependency
│   │   ├── models/              # SupplyModel, DemandModel (SQLAlchemy ORM)
│   │   └── repositories/        # SupplyRepositoryImpl, DemandRepositoryImpl
│   └── simulation/
│       ├── pypsa_adapter.py     # AbstractGridSimulation + SimulationConfig/Result
│       └── network_builder.py   # PyPSANetworkBuilder (runs PyPSA in ThreadPoolExecutor)
│
└── api/v1/
    ├── dependencies.py          # DI wiring — the only place where api imports infra
    ├── schemas/                 # Pydantic v2 response schemas
    ├── endpoints/               # referential, supply, demand, simulation
    └── router.py                # Aggregates all endpoint routers

main.py                          # Root entry point — re-exports app for uvicorn
scripts/seed.py                  # Idempotent DB seed (2 supplies + 2 demands)
pyproject.toml                   # Project metadata and dependencies
.env.example                     # Environment variable template — copy to .env
```

---

## Dependency injection chain (GET /api/v1/referential)

```
GET /api/v1/referential
  └─ ReferentialService
      └─ GetReferentialUseCase
          ├─ SupplyRepositoryImpl  ─┐
          └─ DemandRepositoryImpl  ─┴─ AsyncSession shared via get_db()
```
