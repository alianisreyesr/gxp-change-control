# Security Policy

## Supported versions

| Version | Support status |
|---|---|
| `1.0.x` | Current portfolio baseline; security fixes considered on a best-effort basis |
| `< 1.0` | Historical development snapshots; not supported |

This is a portfolio and learning project, not a hosted service or validated product. No service-level commitment is provided.

## Reporting a vulnerability

Do **not** open a public issue containing exploit details, credentials, personal data, confidential information, or regulated records.

Preferred reporting path:

1. Use GitHub private vulnerability reporting for this repository when the **Report a vulnerability** option is available under the Security tab.
2. If private reporting is unavailable, contact the maintainer through the LinkedIn profile linked in the README and request a private communication channel. Do not include sensitive technical details in the initial public or social message.

A useful report includes:

- affected commit, tag, endpoint, or component;
- reproducible steps using synthetic data only;
- observed and expected behavior;
- potential impact and prerequisite access;
- proposed remediation, if known;
- confirmation that no real, proprietary, personal, or regulated data was used.

The maintainer will assess the report, determine whether it is in scope, and document remediation where appropriate. Public disclosure should occur only after a fix or mitigation is available and sensitive details have been removed.

## In-scope examples

- bypass of server-side workflow-state checks;
- SQL injection or unsafe query construction;
- exposure of activity, approval, or assessment data outside the intended API behavior;
- cross-site scripting or unsafe rendering in the frontend;
- dependency or container vulnerabilities affecting the shipped code path;
- leakage of repository or workflow secrets;
- ways to falsify attributable actors or server-generated timestamps through supported interfaces.

## Out-of-scope examples

- claims that the prototype lacks production features already identified in the roadmap;
- attacks requiring modification of the local SQLite file or source tree by an administrator of the host;
- denial-of-service testing against infrastructure not explicitly authorized for testing;
- social engineering, spam, or testing against third-party accounts;
- findings based on real employer, patient, student, customer, or regulated data;
- requests to certify the software as compliant, validated, or production-ready.

## Secrets and data handling

- Never commit tokens, passwords, private keys, connection strings, or real credentials.
- Use only synthetic records and fictional actors.
- Do not paste vulnerability evidence containing personal, proprietary, employer, or regulated information.
- Rotate any secret immediately if it is accidentally exposed, then remove it from history where feasible.
- Treat generated SQLite files, build artifacts, and logs as disposable demonstration data.

## Security controls in the repository

The repository currently includes:

- Pydantic and JSON Schema validation;
- parameterized SQLite statements;
- explicit workflow transitions;
- attributable-actor restrictions;
- server-generated UTC timestamps;
- Bandit, `pip-audit`, `npm audit`, CodeQL, and optional Sonar analysis;
- a non-root API container.

These controls reduce common development risks. They do not provide authentication, authorization, electronic signatures, protected audit storage, secure hosting, formal threat modeling, penetration testing, or regulatory validation.
