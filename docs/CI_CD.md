# CI/CD — GxP Change Control

## Pipeline (GitHub Actions)

### CI — `.github/workflows/ci.yml`

| Job | What |
|-----|------|
| **backend** | Python 3.12 · pytest + coverage |
| **frontend** | Node 22 · tsc · vite build |
| **sast** | Bandit · pip-audit · npm audit (see [SAST.md](SAST.md)) |
| **docker** | Build API image (after backend + sast) |
| **summary** | Aggregate gate |

### CodeQL — `.github/workflows/codeql.yml`

Semantic SAST for **python** and **javascript-typescript** (`security-extended`), weekly schedule.

## Local

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=app

cd frontend && npm install && npm run build

docker compose up --build

# SAST
pip install bandit[toml] pip-audit
bandit -r app -c bandit.yaml -ll
pip-audit -r requirements.txt
```

## Design notes

- No production deploy secrets / registry push by default.
- Non-root container user.
- Synthetic data only.
