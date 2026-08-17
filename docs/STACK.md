# Modern stack (2026-oriented)

## Backend
- **Python 3.11+** · **FastAPI** · **Pydantic v2** · **SQLite** (portfolio; Postgres-ready design)
- **Uvicorn** ASGI server
- OpenAPI at `/docs`

## Frontend (trending defaults)
- **React 19**
- **Vite 6**
- **TypeScript**
- **Tailwind CSS 3**
- **TanStack Query v5** (server state)
- **React Router 7**
- **Lucide React** icons
- **clsx** utilities

> shadcn/ui-style patterns (owned components + Tailwind) without locking the repo to a specific CLI snapshot — easy to run `npx shadcn@latest init` later if desired.

## Run locally

```bash
# API
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs

# UI
cd frontend && npm install && npm run dev
# http://127.0.0.1:5173
```
