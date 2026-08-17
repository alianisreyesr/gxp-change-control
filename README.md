# GxP Change Control Tracker

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-20232A?style=flat&logo=react&logoColor=61DAFB)
![Status](https://img.shields.io/badge/Status-Scaffold-orange?style=flat)

**Change Control · Validated State · Impact Assessment · 21 CFR Part 11 themes · ALCOA+**

*Portfolio-safe prototype — synthetic data only*

[Roadmap](docs/ROADMAP.md) · [Regulatory references](docs/REGULATORY_REFERENCES.md) · [Español](#español--resumen)

</div>

---

> **Data boundary:** All records are fictional. This is **not** validated software and must not be used for regulated decisions or production change control.

---

## What this is

A full-stack prototype of a **GxP change control** workflow for computerized systems and quality processes:

1. **Request** — describe the change and business justification  
2. **Impact assessment** — validated state, Part 11 / data integrity, training, SOPs  
3. **Approval** — role-based decision points (illustrative)  
4. **Implementation** — tasks and evidence links  
5. **Post-change verification** — confirm intended state before close  

Built for learning **Quality Data Engineering / CSV / IT Compliance** patterns — the same language used when systems move from “working code” to “controlled change.”

**Stack (planned):** Python · FastAPI · Pydantic · SQLite · React (Vite) · Docker · GitHub Actions

---

## Why change control matters

In regulated environments, an unrecorded change to a validated system can invalidate assurance evidence. Industry frameworks (e.g., ISPE GAMP 5) and regulations expect **documented evaluation of impact** before and after changes. This repo models that lifecycle with transparent, inspectable records (synthetic only).

Related portfolio projects:

| Project | Focus |
|---------|--------|
| [Quality Deviation Risk Monitor](https://github.com/alianisreyesr/quality-deviation-risk-monitor) | Deviation prioritization + audit trail |
| [CSV Evidence Tracker](https://github.com/alianisreyesr/csv-evidence-tracker) | RTM · IQ/OQ/PQ evidence |
| [CSA Assurance Planner](https://github.com/alianisreyesr/csa-assurance-planner) | Risk-based software assurance |
| [Data Integrity Case File](https://github.com/alianisreyesr/data-integrity-case-file) | ALCOA+ investigation workspace |

---

## Current status

| Area | Status |
|------|--------|
| Documentation & regulatory map | ✅ In progress |
| Domain model (change request, impact, approval) | 🔜 Next |
| API + SQLite | 🔜 |
| React reviewer UI | 🔜 |
| Tests + CI | 🔜 |
| Docker | 🔜 |

See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Español — resumen

Prototipo de **control de cambios GxP** (datos sintéticos): solicitud → evaluación de impacto → aprobación → implementación → verificación post-cambio. No es software validado. Documentación principal en **inglés**; este bloque resume el propósito en español.

---

## License

MIT (to be added with first code drop)

---

**Built by [Alianis Reyes-Reyes](https://www.linkedin.com/in/alianis-reyes-reyes/)** · Information Systems @ UPRM · Former Eli Lilly Intern
