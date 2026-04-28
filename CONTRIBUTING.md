# Contributing to PowerShift

Thank you for considering contributing to PowerShift! This document explains how to get started.

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ with pnpm
- Git

### Local Development

```bash
git clone https://github.com/LenouvelLouis/PowerShift.git
cd PowerShift
cp .env.example .env
docker compose up --build
```

Or manually:

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd energy-dashboard
pnpm install && pnpm dev
```

## Code Standards

### Backend (Python)

- **Linter**: ruff (`ruff check app/`)
- **Architecture**: Clean Architecture (domain / application / infrastructure / api)
- **Async**: all DB operations and endpoints are async
- **Tests**: pytest + httpx for API, pytest-bdd for BDD scenarios
- **Imports**: domain layer must not import from infrastructure or api

### Frontend (TypeScript/Vue)

- **Linter**: ESLint (`pnpm lint`)
- **Type checking**: `pnpm typecheck`
- **Tests**: Vitest + @vue/test-utils (`pnpm test`)
- **Styling**: Tailwind CSS with semantic classes (no hardcoded hex colors)
- **i18n**: all user-facing strings must use `$t()` with keys in `i18n/en.json` and `i18n/fr.json`

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feature/my-feature`
3. **Make your changes** following the code standards above
4. **Run all checks**:
   ```bash
   # Backend
   ruff check app/
   python -m pytest tests/

   # Frontend
   cd energy-dashboard
   pnpm lint && pnpm typecheck && pnpm test
   ```
5. **Commit** with a clear message describing the change
6. **Open a Pull Request** against `main`

## What to Contribute

- Bug fixes
- New asset types (generators, loads, network components)
- New optimization strategies
- Frontend UX improvements
- Translations (add new locales in `energy-dashboard/i18n/`)
- Documentation improvements
- Test coverage improvements

## Architecture Guidelines

- **Backend**: follow Clean Architecture layers. New features should have domain entities, repository interfaces, and infrastructure implementations.
- **Frontend**: components go in `app/components/features/` organized by section. Shared logic goes in `app/composables/`. State goes in Pinia stores.
- **API**: new endpoints go in `app/api/v1/endpoints/`. Use Pydantic schemas for request/response validation.

## Questions?

Open an issue or contact the maintainer.
