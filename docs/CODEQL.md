# CodeQL configuration

## Triggers

| Event | When | Query suite |
|-------|------|-------------|
| `push` / `pull_request` | `main` | `security-extended` |
| **`schedule`** | **Mondays 06:00 UTC** | `security-extended` **+** `security-and-quality` |
| `workflow_dispatch` | Manual (Actions tab) | Choose suite |

Cron: `0 6 * * 1`

## Languages

Matrix:

- `python` → `app/`
- `javascript-typescript` → `frontend/src/`

Scoped by `.github/codeql/codeql-config.yml`.

## Permissions

- `security-events: write` — upload SARIF to **Security → Code scanning**
- Works on **public** repos with GitHub Code Scanning enabled (default for public)

## Weekly vs PR scans

- **PR/push:** faster, security-focused (`security-extended`)
- **Weekly:** deeper suite including quality rules (`security-and-quality`) so the Security tab stays fresh without slowing every PR

## Manual run

GitHub → **Actions** → **CodeQL** → **Run workflow** → pick query suite.

## Local (optional)

Install [CodeQL CLI](https://codeql.github.com/docs/codeql-cli/) if you need offline packs; CI is the source of truth for this portfolio repo.
