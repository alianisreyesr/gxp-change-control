# Portfolio Safety and Data Boundary

## Purpose

GxP Change Control Tracker is an educational, portfolio-safe prototype. It demonstrates software-engineering and quality-system concepts using fictional records. It is not a system of record, validated application, production service, or substitute for approved procedures.

## Permitted demonstration use

Use the repository only for activities such as:

- local development and code review;
- portfolio demonstrations and interviews;
- learning about change-control terminology and workflow modeling;
- testing with fictional systems, actors, dates, and rationales;
- evaluating API, validation, database, frontend, CI, and security patterns.

## Prohibited data

Do not enter, import, attach, commit, or transmit:

- personal data or direct/indirect identifiers;
- patient, clinical, laboratory, pharmacovigilance, or manufacturing records;
- employer, customer, supplier, or partner confidential information;
- proprietary procedures, specifications, source code, incidents, deviations, CAPAs, or change records;
- real credentials, tokens, passwords, connection strings, or private keys;
- records governed by GxP, privacy, contractual, export-control, or records-retention obligations.

When an example resembles a real event, rewrite it until it is clearly fictional and cannot be attributed to a person, company, site, product, batch, system, or investigation.

## Non-claims

The project does not claim:

- compliance with 21 CFR Part 11, Annex 11, GAMP, FDA CSA, or any other regulation or guidance;
- validated status or suitability for a regulated intended use;
- approved audit-trail, electronic-signature, access-control, retention, backup, or disaster-recovery capabilities;
- fitness for product release, quality disposition, regulatory submission, inspection response, or business continuity.

Regulatory references in the repository are educational mappings only.

## Safe local operation

- Run the application on a local or explicitly authorized demonstration environment.
- Keep the API and SQLite volume isolated from production networks and shared data stores.
- Use fictional actor identifiers such as `a.reyes` or `q.approver`; do not use real employee IDs.
- Do not expose the development server directly to the public internet.
- Remove local SQLite volumes, logs, exports, and screenshots after a demonstration when they are no longer required.
- Review screenshots before publication to confirm that only synthetic information is visible.

## Repository hygiene

Before every public commit or release:

1. inspect the diff for secrets and proprietary names;
2. confirm that seed data and test fixtures are fictional;
3. run automated security and dependency checks;
4. verify that documentation preserves the non-validated-use boundary;
5. avoid screenshots or artifacts containing local paths, tokens, email addresses, or unrelated account information.

## If real data is added accidentally

Stop using the affected copy of the repository. Remove the data from the working tree and generated artifacts, rotate any exposed credential, and assess whether Git history or published releases also require cleanup. Do not open a public issue containing the sensitive material.
