# Roadmap — GxP Change Control

## Phase 0 — Documentation (current)
- [x] Repository + bilingual README
- [x] Regulatory references (FDA / GAMP themes)
- [ ] Glossary (change control, validated state, like-for-like, etc.)

## Phase 1 — Domain & API
- [ ] Pydantic models: ChangeRequest, ImpactAssessment, Approval, ImplementationTask, Verification
- [ ] SQLite schema + seed synthetic changes
- [ ] FastAPI routes: CRUD-ish workflow transitions
- [ ] Append-only activity / audit log

## Phase 2 — Frontend
- [ ] Queue of open changes
- [ ] Impact checklist UI
- [ ] Approval and close-out screens

## Phase 3 — Hardening
- [ ] pytest suite + CI
- [ ] Docker Compose
- [ ] SECURITY.md · LICENSE · portfolio safety page

## Design principles
1. Synthetic data only
2. Explainable status transitions (no hidden state)
3. Server-side timestamps
4. Explicit non-claims of regulatory compliance
