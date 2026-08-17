# CI/CD — GxP Change Control

## Pipeline (GitHub Actions)

Workflow: `.github/workflows/ci.yml`

| Job | What |
|-----|------|
| **backend** | Python 3.12 · `pytest` + coverage XML artifact |
| **frontend** | Node 22 · `tsc --noEmit` · `vite build` · dist artifact |
| **docker** | Build API image (no push) with Buildx + GHA cache |
| **summary** | Fails if any required job failed |

Triggers: `push` / `pull_request` to `main`.

## Local equivalents

```bash
# Backend
pip install -r requirements.txt
pytest tests/ -v --cov=app

# Frontend
cd frontend && npm install && npx tsc --noEmit && npx vite build

# Docker API
docker compose up --build
# → http://127.0.0.1:8000/health
# → http://127.0.0.1:8000/docs
```

## Design notes (portfolio)

- No deployment secrets or production registry push (safe default).
- Image runs as non-root `appuser`.
- Synthetic SQLite data under `/app/data` volume.
- Extend later: CD to GHCR on tag, Playwright smoke, coverage gate.
