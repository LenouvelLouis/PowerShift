# CLAUDE.md — Energy Grid Project

## Project Overview

Full-stack energy grid simulation platform:
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy async, NeonDB (PostgreSQL), PyPSA
- **Frontend**: Nuxt 3, Vue 3, TypeScript, @nuxt/ui, Pinia, TanStack Query
- **DB**: NeonDB serverless PostgreSQL (asyncpg driver)
- **Weather data**: KNMI weather profiles ingested into `weather_profile` table

---

## Dev Commands

### Backend
```bash
uvicorn main:app --reload        # start API at http://localhost:8000
pytest                           # run tests
pytest -v                        # verbose
ruff check app/                  # lint
ruff format app/                 # format
```

### Frontend (from energy-dashboard/)
```bash
pnpm dev                         # start frontend at http://localhost:3000
pnpm typecheck                   # type check
pnpm lint                        # lint
pnpm build                       # production build
```

---

## Clean Architecture — Layer Rules

The codebase follows strict Clean Architecture. **Never violate these boundaries:**

```
domain/          ← zero external dependencies (no FastAPI, no SQLAlchemy, no httpx)
application/     ← depends on domain only
infrastructure/  ← implements domain interfaces; imports SQLAlchemy, asyncpg, httpx
api/             ← depends on application and infrastructure via DI (dependencies.py)
```

### Rules per layer

**`domain/`**
- Only plain Python — no ORM, no framework imports
- Entities in `domain/entities/`, interfaces (ABCs) in `domain/interfaces/`
- New domain logic → new entity or extend existing one here first

**`application/`**
- DTOs in `application/dtos/`, services in `application/services/`
- Services orchestrate use cases — no direct DB access
- No infrastructure imports allowed

**`infrastructure/`**
- ORM models in `infrastructure/db/models/`
- Repository implementations in `infrastructure/db/repositories/`
- Each repository implements the corresponding `domain/interfaces/` ABC
- External API clients in `infrastructure/external/`

**`api/v1/`**
- `dependencies.py` is the **only** file that imports infrastructure
- Pydantic schemas in `api/v1/schemas/` (separate from domain entities)
- Endpoints only call application services — never repositories directly

---

## Database Rules

- Database is **NeonDB serverless PostgreSQL** — always async (asyncpg)
- Use `AsyncSession` everywhere — never sync SQLAlchemy sessions
- Connection string is in `.env` as `DATABASE_URL`
- **Never hardcode credentials** — always use `get_settings()`
- Migrations via raw SQL or Alembic — never `Base.metadata.create_all()` in production code
- `weather_profile` table is the source of truth for meteorological data (KNMI ingested)

---

## Code Conventions

### Python (backend)
- Type hints on every function signature
- Pydantic v2 for all schemas
- `async/await` throughout — no sync I/O in async context
- Repository pattern: one class per aggregate, implements its interface ABC
- No business logic in endpoints or repositories — it belongs in use cases/services
- Settings via `get_settings()` from `infrastructure/secrets/settings.py` (cached)

### TypeScript (frontend)
- Composables for all shared logic — no logic in page components
- TanStack Query for all API calls — no raw fetch in components
- Pinia stores only for truly global state
- `pnpm typecheck` must pass before any commit

---

## What NOT to Do

- **No mock databases in tests** — use aiosqlite in-memory SQLite or a real test DB
- **No Co-Authored-By in commits** — Florian MANGIN is sole committer
- **No `create_all()` calls** outside of test fixtures
- **No sync SQLAlchemy** — this is a fully async codebase
- **No infrastructure imports in domain or application layers**
- **No logic in API endpoints** — endpoints delegate to services only
- **No new files without a clear purpose** — don't create helpers for one-time use
- **No speculative abstractions** — implement what the task requires, nothing more
- **Don't touch unrelated code** — a bug fix doesn't need surrounding cleanup
- **Don't add docstrings or comments** to code you didn't change
- **No error handling for impossible scenarios** — trust internal guarantees

---

