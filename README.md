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

# 5. Start the server
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
| POST | `/api/v1/supplies` | Create a supply source |
| PUT | `/api/v1/supplies/{id}` | Update a supply source (partial) |
| DELETE | `/api/v1/supplies/{id}` | Delete a supply source |
| GET | `/api/v1/demands` | List all demand nodes |
| GET | `/api/v1/demands/{id}` | Get a single demand node |
| POST | `/api/v1/demands` | Create a demand node |
| PUT | `/api/v1/demands/{id}` | Update a demand node (partial) |
| DELETE | `/api/v1/demands/{id}` | Delete a demand node |
| GET | `/api/v1/network` | List all network components |
| GET | `/api/v1/network/{id}` | Get a single network component |
| POST | `/api/v1/network` | Create a network component |
| PUT | `/api/v1/network/{id}` | Update a network component (partial) |
| DELETE | `/api/v1/network/{id}` | Delete a network component |
| POST | `/api/v1/simulation/run` | Run a PyPSA grid simulation |
| GET | `/api/v1/simulation` | List past simulations |
| GET | `/api/v1/simulation/{id}` | Get a simulation result |
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
│   │   ├── demand/              # House, ElectricVehicle
│   │   └── network/             # Cable, Transformer
│   ├── interfaces/              # ABCs: ISupplyRepository, IDemandRepository,
│   │                            #   INetworkRepository, ISimulationRepository,
│   │                            #   ISimulationPersistenceRepository,
│   │                            #   IPvProfileRepository, ILoadProfileProvider
│   └── use_cases/               # GetReferentialUseCase, RunSimulationUseCase
│
├── application/                 # Application layer
│   ├── dtos/                    # SupplyDTO, DemandDTO, ReferentialDTO
│   └── services/                # ReferentialService, SimulationService
│
├── infrastructure/              # Infrastructure layer
│   ├── secrets/
│   │   └── settings.py          # get_settings() — cached settings from .env
│   ├── db/
│   │   ├── connection.py        # Async engine + get_db() FastAPI dependency
│   │   ├── models/              # SupplyModel, DemandModel, NetworkModel,
│   │   │                        #   SimulationRequestModel, SimulationResultModel,
│   │   │                        #   AssetParametersModel, PvHourlyModel
│   │   └── repositories/        # SupplyRepositoryImpl, DemandRepositoryImpl,
│   │                            #   NetworkRepositoryImpl, SimulationRepositoryImpl,
│   │                            #   PvHourlyRepositoryImpl
│   ├── external/
│   │   └── open_meteo_provider.py  # ILoadProfileProvider via Open-Meteo API
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
pyproject.toml                   # Project metadata and dependencies
.env.example                     # Environment variable template — copy to .env
```

---

## Dependency injection chains

```
GET /api/v1/referential
  └─ ReferentialService
      └─ GetReferentialUseCase
          ├─ SupplyRepositoryImpl   ─┐
          ├─ DemandRepositoryImpl   ─┤
          └─ NetworkRepositoryImpl  ─┴─ AsyncSession shared via get_db()

POST /api/v1/simulation/run
  └─ SimulationService
      └─ RunSimulationUseCase
          ├─ PyPSANetworkBuilder
          ├─ PvHourlyRepositoryImpl  ───┐
          ├─ SimulationRepositoryImpl ──┤
          └─ OpenMeteoProvider          └─ AsyncSession shared via get_db()
```
