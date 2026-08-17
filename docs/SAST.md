# SAST — Static Application Security Testing

Portfolio prototype. These checks demonstrate a **security-aware CI** mindset (aligned with controlled SDLC themes, not a validated GxP tool).

## Tools in this repo

| Tool | Scope | Where |
|------|--------|--------|
| **Bandit** | Python source anti-patterns (SQL, shells, hard-coded secrets patterns, etc.) | `sast` job · `bandit.yaml` |
| **pip-audit** | Known vulns in Python dependencies | `sast` job |
| **npm audit** | Known vulns in frontend deps (`audit-level=high`) | `sast` job |
| **CodeQL** | Semantic SAST (Python + JS/TS), `security-extended` queries | `.github/workflows/codeql.yml` |

## CI wiring

- **CI workflow** (`.github/workflows/ci.yml`): job **`sast`** is required; **docker** waits on `backend` + `sast`.
- **CodeQL**: separate workflow on push/PR + weekly schedule; results appear under GitHub **Security** tab (public repos).

## Local commands

```bash
pip install bandit[toml] pip-audit
bandit -r app -c bandit.yaml -ll
pip-audit -r requirements.txt

cd frontend && npm audit --audit-level=high
```

## Policy notes

- Bandit excludes `tests/` (test helpers may use patterns not shipped to prod).
- `npm audit` fails on **high**+ only (noise control for a portfolio app).
- No claim of “secure validated system” — synthetic change-control demo only.
- Extend later: Semgrep rulesets, container image scan (Trivy/Grype), secret scanning (gitleaks).
