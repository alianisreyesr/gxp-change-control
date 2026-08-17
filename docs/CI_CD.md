# CI/CD — GxP Change Control

The repository uses GitHub Actions as a technical quality gate. It does not deploy to a regulated or production environment.

## CI workflow — `.github/workflows/ci.yml`

| Job | Gate |
|---|---|
| **backend** | Python 3.12, 68 pytest tests at the v1.0.0 baseline, coverage XML artifact |
| **frontend** | Node 22, dependency installation, TypeScript type check, Vite production build |
| **sast** | Bandit, `pip-audit`, and `npm audit --audit-level=high` |
| **docker** | Build the non-root API image after backend and SAST succeed |
| **summary** | Fail unless backend, frontend, SAST, and Docker all succeed |

The workflow runs on pushes and pull requests targeting `main` or `master`. Concurrency cancellation prevents stale runs for the same ref from consuming resources after a newer commit arrives.

## CodeQL — `.github/workflows/codeql.yml`

CodeQL analyzes:

- Python;
- JavaScript/TypeScript;
- the `security-extended` query suite.

It runs on pushes, pull requests, and a weekly schedule. Findings appear in the repository Security area when GitHub code scanning is available.

## Sonar — `.github/workflows/sonar.yml`

The Sonar workflow is credential-aware:

- with `SONAR_TOKEN`, it generates backend coverage, installs the frontend, runs the scan, and evaluates the quality gate;
- without `SONAR_TOKEN`, it records a successful, explicit skip rather than failing the repository.

Repository variables can override the Sonar host, project key, and organization. See [SONARQUBE.md](SONARQUBE.md).

## Local verification

```bash
# Backend
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=xml

# Frontend
cd frontend
npm install
npm run typecheck
npm run build
npm audit --audit-level=high

# Python security checks, from repository root
cd ..
pip install "bandit[toml]" pip-audit
bandit -r app -c bandit.yaml -ll
pip-audit -r requirements.txt --progress-spinner off

# Container
docker compose build
```

## Release evidence

Before creating a release tag:

1. all required CI jobs on the release commit should be successful;
2. CodeQL should complete for both language matrices;
3. Sonar execution or credential-aware skip should be documented accurately;
4. application, frontend, Sonar, changelog, and release versions should agree;
5. the release notes should restate the synthetic-data and non-validated-use boundary.

## Design notes

- No registry push or production deployment occurs by default.
- The runtime image uses a non-root user.
- The Compose profile persists only synthetic demonstration data.
- CI evidence demonstrates software-engineering discipline; it is not an approved validation package.
