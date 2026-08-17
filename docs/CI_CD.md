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

## Controlled release — `.github/workflows/release.yml`

The release workflow is intentionally idempotent and release-commit driven:

1. A candidate commit on `main` must use a subject beginning with `release:`.
2. The workflow inspects GitHub Actions runs for that exact commit SHA.
3. `CI`, `CodeQL`, and `SonarQube / SonarCloud` must all be completed successfully.
4. The application version is read from `APP_VERSION` in `app/main.py`.
5. A matching notes file must exist at `docs/releases/v<version>.md`.
6. GitHub CLI creates the tag and release at the verified SHA using the workflow's scoped `GITHUB_TOKEN`.
7. Existing releases are detected and left unchanged, so repeated workflow events are safe.

The workflow listens to `push`, `workflow_run`, and manual-dispatch events. Early events exit without publishing while another required workflow is still running; a later completion event reevaluates the same SHA.

Permissions are limited to read access for Actions metadata and write access for repository contents, which GitHub requires to create the tag and release.

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

Before publishing a release tag:

1. all required CI jobs on the release commit must be successful;
2. CodeQL must complete for both language matrices;
3. Sonar execution or credential-aware skip must complete successfully;
4. application, frontend, Sonar, changelog, and release versions must agree;
5. a version-matched release-notes file must restate the synthetic-data and non-validated-use boundary;
6. the resulting GitHub release must target the exact SHA evaluated by the gates.

The existing health test enforces version agreement across the API, frontend package, Sonar project configuration, and changelog.

## Design notes

- No registry push or production deployment occurs by default.
- The runtime image uses a non-root user.
- The Compose profile persists only synthetic demonstration data.
- The release is a portfolio software baseline, not an approved validation package.
- CI evidence demonstrates software-engineering discipline; it does not establish regulatory compliance or validated status.
