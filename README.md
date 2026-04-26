# Energy Grid Simulation Platform

Full-stack energy grid simulation platform — Clean Architecture backend with PyPSA, SQLAlchemy async, NeonDB, and a Nuxt 3 dashboard frontend.

---

## Stack

### Backend
| Technology | Role |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| SQLAlchemy (asyncio) | Async ORM |
| asyncpg | Async PostgreSQL driver |
| PostgreSQL 15 | Relational database (Docker local / NeonDB cloud) |
| PyPSA | Power grid simulation (OPF) |
| pydantic-settings | Environment variable loading |
| Pytest + httpx | Testing |
| pytest-bdd | BDD / Gherkin test automation |
| Selenium | UI testing (headless Chrome) |

### Frontend
| Technology | Role |
|---|---|
| Nuxt 3 | Vue meta-framework |
| Vue 3 + TypeScript | UI components |
| @nuxt/ui | Component library |
| Pinia | Global state management |
| TanStack Query | Server-state / API calls |

---

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

---

## Endpoints

### Referential
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/referential` | All components (supplies + demands + network) |

### Supplies
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/supplies` | List all supply sources |
| GET | `/api/v1/supplies/{id}` | Get a single supply source |
| POST | `/api/v1/supplies` | Create a supply source |
| PUT | `/api/v1/supplies/{id}` | Update a supply source (partial) |
| DELETE | `/api/v1/supplies/{id}` | Delete a supply source |

### Demands
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/demands` | List all demand nodes |
| GET | `/api/v1/demands/{id}` | Get a single demand node |
| POST | `/api/v1/demands` | Create a demand node |
| PUT | `/api/v1/demands/{id}` | Update a demand node (partial) |
| DELETE | `/api/v1/demands/{id}` | Delete a demand node |

### Network
| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/network` | List all network components |
| GET | `/api/v1/network/{id}` | Get a single network component |
| POST | `/api/v1/network` | Create a network component |
| PUT | `/api/v1/network/{id}` | Update a network component (partial) |
| DELETE | `/api/v1/network/{id}` | Delete a network component |

### Simulation
| Method | Route | Description |
|---|---|---|
| POST | `/api/v1/simulation/run` | Run a PyPSA grid simulation and persist result |
| POST | `/api/v1/simulation/preview` | Run a simulation without saving (live preview) |
| POST | `/api/v1/simulation/import` | Load an exported scenario and run it |
| GET | `/api/v1/simulation` | List past simulations |
| GET | `/api/v1/simulation/solvers` | List supported solvers and availability |
| GET | `/api/v1/simulation/{id}` | Get a simulation result |
| DELETE | `/api/v1/simulation/{id}` | Delete a simulation |
| PATCH | `/api/v1/simulation/{id}/rename` | Rename a simulation scenario |
| GET | `/api/v1/simulation/{id}/export` | Export a simulation scenario as JSON |

### Other
| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
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
│   │                            #   IPVProfileRepository, ILoadProfileProvider
│   ├── use_cases/               # GetReferentialUseCase, RunSimulationUseCase,
│   │                            #   PreviewSimulationUseCase
│   ├── wind/                    # Wind domain — entities, ports, services, exceptions
│   └── nuclear/                 # Nuclear domain — entities, ports, services, exceptions
│
├── application/                 # Application layer
│   ├── dtos/                    # SupplyDTO, DemandDTO, ReferentialDTO
│   ├── services/                # ReferentialService, SimulationService
│   ├── wind/                    # CalculateWindPowerUseCase, schemas
│   └── nuclear/                 # Nuclear use cases, schemas
│
├── infrastructure/              # Infrastructure layer
│   ├── secrets/
│   │   └── settings.py          # get_settings() — cached settings from .env
│   ├── db/
│   │   ├── connection.py        # Async engine + get_db() FastAPI dependency
│   │   ├── init_db.py           # Table initialisation on startup
│   │   ├── models/              # SupplyModel, DemandModel, NetworkModel,
│   │   │                        #   SimulationRequestModel, SimulationResultModel,
│   │   │                        #   AssetParametersModel, WeatherProfileModel
│   │   └── repositories/        # SupplyRepositoryImpl, DemandRepositoryImpl,
│   │                            #   NetworkRepositoryImpl, SimulationRepositoryImpl,
│   │                            #   WeatherProfileRepositoryImpl
│   ├── external/
│   │   └── open_meteo_provider.py  # ILoadProfileProvider via Open-Meteo API
│   ├── wind/                    # PyPSAWindAdapter, WindTurbineRepositoryImpl
│   ├── nuclear/                 # NuclearRepositoryImpl
│   └── simulation/
│       ├── pypsa_adapter.py     # AbstractGridSimulation + SimulationConfig/Result
│       ├── network_builder.py   # PyPSANetworkBuilder (runs PyPSA in ThreadPoolExecutor)
│       └── objectives/          # Pluggable optimization strategies:
│                                #   MinCostStrategy, MinEmissionsStrategy,
│                                #   MaxRenewableStrategy
│
└── api/v1/
    ├── dependencies.py          # DI wiring — the only place where api imports infra
    ├── schemas/                 # Pydantic v2 response schemas
    ├── endpoints/               # referential, supply, demand, network, simulation
    └── router.py                # Aggregates all endpoint routers

energy-dashboard/                # Nuxt 3 frontend
├── app/
│   ├── components/              # Vue components (features/, ui/)
│   ├── composables/             # Shared logic — api.ts and others
│   ├── stores/                  # Pinia stores (simulation.ts, ...)
│   └── pages/                   # Nuxt pages

main.py                          # Root entry point — re-exports app for uvicorn
pyproject.toml                   # Project metadata and dependencies
.env.example                     # Environment variable template — copy to .env
```

---

## Optimization objectives

Simulations accept an `optimization_objective` parameter:

| Value | Strategy |
|---|---|
| `min_cost` | Minimize total generation cost |
| `min_emissions` | Minimize CO₂ emissions (penalizes fossil/nuclear, favors renewables) |
| `max_renewable` | Maximize renewable generation share |

---

## Weather data

Solar irradiance and wind speed profiles come from KNMI weather data ingested into the `weather_profile` table (station Groningen Eelde, `06280`). The simulation engine automatically resolves profiles for the requested date range.

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
          │   ├─ OptimizationStrategy (min_cost / min_emissions / max_renewable)
          │   ├─ WeatherProfileRepositoryImpl  (solar irradiance)
          │   ├─ WindTurbineRepositoryImpl      (KNMI wind profiles)
          │   └─ NuclearRepositoryImpl          (reactor constraints)
          ├─ SimulationRepositoryImpl ──────────┐
          └─ OpenMeteoProvider                  └─ AsyncSession shared via get_db()
```
