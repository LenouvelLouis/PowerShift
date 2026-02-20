# ISEP Project API

Clean FastAPI skeleton — ready to extend with future features.

---

## Stack

| Technology | Role |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| Pydantic-settings | Environment variable management |
| Pytest + httpx | Testing |

---

## Local setup

### Requirements

- Python 3.11+
- `pip`

### Steps

```bash
# 1. Clone the repo
git clone <repo-url>
cd <repo-name>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env as needed

# 5. Start the development server
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).
Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Tests

```bash
pytest
pytest -v   # verbose
```

---

## Available endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/health` | API health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## Project structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + health check
│   ├── config.py        # Settings (pydantic-settings)
│   ├── routers/         # Future FastAPI routers
│   ├── models/          # Future ORM / data models
│   ├── schemas/         # Future Pydantic schemas (I/O)
│   └── services/        # Future services / business logic
├── tests/
│   └── test_health.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Coming soon

<!-- Features will be documented here as they are added -->
