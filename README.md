# GxP Change Control Tracker

<div align="center">

![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=flat&logo=vite&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3-38BDF8?style=flat&logo=tailwindcss&logoColor=white)
![TanStack Query](https://img.shields.io/badge/TanStack%20Query-5-FF4154?style=flat)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![Status](https://img.shields.io/badge/Status-MVP-brightgreen?style=flat)

**Change Control · Impact Assessment · Approvals · Activity Log · Portfolio-safe**

[Stack](docs/STACK.md) · [Roadmap](docs/ROADMAP.md) · [Regulatory references](docs/REGULATORY_REFERENCES.md) · [Español](#español--resumen)

</div>

---

> **Data boundary:** Synthetic data only. **Not** validated software. **Not** for regulated decisions.

---

## What you get (MVP)

Workflow for GxP-style **change control**:

`draft → impact assessment → pending approval → approved → implementing → verification → closed`

- Create change requests  
- Record impact (validated state / Part 11 / data integrity / training / SOPs flags)  
- Approve / reject  
- Advance implementation stages  
- Append-only **activity log** (attributable actor + server timestamps)

## Modern stack (2026-oriented)

| Layer | Choices |
|-------|---------|
| UI | **React 19** · **Vite 6** · **TypeScript** · **Tailwind CSS** · **TanStack Query v5** · **React Router 7** · Lucide |
| API | **FastAPI** · **Pydantic v2** · SQLite · OpenAPI `/docs` |
| Patterns | Server state via Query · owned Tailwind components (shadcn-style) · CORS for local Vite |

See [docs/STACK.md](docs/STACK.md).

## Quick start

```bash
git clone https://github.com/alianisreyesr/gxp-change-control.git
cd gxp-change-control

# API
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs

# UI (new terminal)
cd frontend
npm install
npm run dev
# → http://127.0.0.1:5173
```

Vite proxies `/api` → FastAPI automatically.

## Español — resumen

MVP de **control de cambios GxP** con React 19 + FastAPI. Datos sintéticos. Documentación principal en inglés.

## Sister projects

- [Quality Deviation Risk Monitor](https://github.com/alianisreyesr/quality-deviation-risk-monitor)
- [CSV Evidence Tracker](https://github.com/alianisreyesr/csv-evidence-tracker)
- [CSA Assurance Planner](https://github.com/alianisreyesr/csa-assurance-planner)
- [Data Integrity Case File](https://github.com/alianisreyesr/data-integrity-case-file)

---

**Built by [Alianis Reyes-Reyes](https://www.linkedin.com/in/alianis-reyes-reyes/)** · UPRM · Former Eli Lilly Intern
