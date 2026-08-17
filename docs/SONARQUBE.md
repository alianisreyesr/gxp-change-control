# SonarQube / SonarCloud integration

## Default: SonarCloud (recommended for public portfolio)

Free for public open-source repos. No server to host.

### One-time setup

1. Create account at [sonarcloud.io](https://sonarcloud.io) (GitHub login).
2. **Analyze new project** → import `alianisreyesr/gxp-change-control`.
3. Copy:
   - **Organization key** (often your GH user/org)
   - **Project key** (e.g. `alianisreyesr_gxp-change-control`)
4. Create a **token** (My Account → Security → Generate token).
5. In the GitHub repo → **Settings → Secrets and variables → Actions**:
   - Secret **`SONAR_TOKEN`** = the token
   - Optional variables:
     - `SONAR_ORGANIZATION`
     - `SONAR_PROJECT_KEY`
     - `SONAR_HOST_URL` (only for self-hosted SonarQube)

### Workflow

`.github/workflows/sonar.yml`

| Step | Purpose |
|------|--------|
| Full checkout (`fetch-depth: 0`) | New code / blame |
| pytest + `coverage.xml` | Python coverage on Sonar |
| `sonarqube-scan-action` | Upload analysis |
| Quality Gate action | Fail CI if gate fails |

If **`SONAR_TOKEN` is missing**, the job is **skipped** (forks stay green).

### Config file

`sonar-project.properties` — sources, exclusions, coverage paths.

## Self-hosted SonarQube

1. Run SonarQube (Docker/K8s).
2. Set Actions variable **`SONAR_HOST_URL`** = `https://your-sonar.example.com`
3. Set **`SONAR_TOKEN`** from that server.
4. Align `sonar.projectKey` with the project on your instance.

```bash
# Example local server (not for production secrets)
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

## Local scan (optional)

```bash
pip install -r requirements.txt
pytest tests/ --cov=app --cov-report=xml

# With SonarScanner CLI installed and SONAR_TOKEN exported:
sonar-scanner \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.token=$SONAR_TOKEN
```

## Portfolio note

Quality gates improve engineering hygiene (bugs, smells, coverage). This is **not** a validated GxP computer system.
