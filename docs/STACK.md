# Technology Stack

The stack is intentionally small enough to inspect end to end while still demonstrating a modern full-stack delivery pattern.

## Backend

| Component | Version / role |
|---|---|
| **Python** | 3.11+ runtime target; Python 3.12 in CI |
| **FastAPI** | 0.139.2 — API routing, OpenAPI, dependency injection |
| **Starlette** | 1.3.1 — ASGI foundation and test client integration |
| **Pydantic** | 2.10.3 — request, response, and domain validation |
| **Uvicorn** | 0.32.1 — local ASGI server |
| **SQLite** | Portfolio persistence for changes, assessments, approvals, and activity evidence |
| **pytest / pytest-cov** | 9.1.1 / 7.0.0 — automated behavior and coverage checks |

Database access uses the Python standard library `sqlite3` module with parameterized statements, explicit foreign-key enforcement, transaction boundaries, and a small startup migration helper.

## Frontend

| Component | Version / role |
|---|---|
| **React** | 19 — reviewer interface |
| **Vite** | 6 — local development and production build |
| **TypeScript** | 5.7 — static type checking |
| **Tailwind CSS** | 3.4 — owned utility-based presentation |
| **TanStack Query** | 5 — server-state loading, mutation, and invalidation |
| **React Router** | 7 — list, create, and detail routes |
| **Ajv** | 8 — Draft 2020-12 JSON Schema validation |
| **ajv-formats** | 3 — date and date-time format validation |
| **Lucide React / clsx** | Icons and conditional class composition |

The frontend retrieves request schemas from the API and falls back to version-controlled local copies so the validation behavior remains inspectable when the API is unavailable.

## API and validation contracts

- FastAPI OpenAPI UI: `/docs`
- ReDoc: `/redoc`
- Exported JSON Schemas: `/schemas/{name}` and the `schemas/` directory
- Stable validation errors: HTTP 422 with structured field locations
- Primary timestamps: timezone-aware ISO 8601, normalized to UTC
- Local wall-time helpers: IANA zones with explicit fold/gap handling

## DevSecOps

| Control | Implementation |
|---|---|
| Backend verification | pytest + coverage |
| Frontend verification | `tsc --noEmit` + Vite build |
| Python SAST | Bandit |
| Dependency review | `pip-audit` + `npm audit` |
| Semantic analysis | CodeQL for Python and JavaScript/TypeScript |
| Optional quality analysis | SonarCloud or SonarQube when repository credentials are configured |
| Reproducibility | Dockerfile + Docker Compose API profile |
| Aggregate gate | GitHub Actions CI summary job |

## Run locally

```bash
# API
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# UI, in another terminal
cd frontend
npm install
npm run dev
```

Or build the API container:

```bash
docker compose up --build
```

## Production boundary

The stack choices support a local portfolio demonstration. They do not by themselves provide authentication, validated-state management, electronic signatures, protected audit storage, high availability, governed deployment, or formal validation. See [PORTFOLIO_SAFETY.md](PORTFOLIO_SAFETY.md) and [ROADMAP.md](ROADMAP.md).
