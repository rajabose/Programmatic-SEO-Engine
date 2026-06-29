# .specify — Vanchai Programmatic SEO Engine

Feature-level documentation using the SpecKit methodology. The constitution defines non-negotiable rules; feature folders track everything else.

---

## Current structure

```
.specify/
├── constitution/
│   └── project-constitution.md        # vision, quality gate thresholds, non-negotiables
├── feature.json                        # active_feature pointer
├── features/
│   ├── content-generation/            # ACTIVE — GitHub Pages v1 pipeline
│   │   ├── STATUS.md                  # phase progress + live code inventory
│   │   ├── spec.md                    # what to build + acceptance criteria
│   │   ├── plan.md                    # original FastAPI plan (superseded)
│   │   ├── plan-github-pages-v1.md    # ACTIVE PLAN — zero-cost static pipeline
│   │   ├── checklists/
│   │   │   └── requirements.md        # CHK-001 to CHK-028 implementation checklist
│   │   └── tasks/
│   │       └── tasks.md               # GP-Phase task tracker (inline — no task files)
│   ├── landing-page-generation/       # reference — initial V1 modifier-matrix approach
│   │   ├── STATUS.md
│   │   ├── spec.md
│   │   ├── plan.md                    # tasks tracked inline in this file (no task files)
│   │   └── tasks/                     # legacy task files — not the active pattern
│   │       ├── tasks.md
│   │       ├── TASK-LP-001-setup-python-project.md
│   │       ├── TASK-LP-002-product-catalog-sync.md
│   │       └── TASK-LP-003-content-generation-service.md
│   └── brand-auth-portal/             # parked — brand login portal concept
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md
│       ├── contracts/
│       │   └── api-endpoints.md
│       └── checklists/
│           └── requirements.md
└── templates/
    ├── spec-template.md
    ├── plan-template.md
    ├── tasks-template.md
    ├── constitution-template.md
    └── checklist-template.md
```

---

## Feature status

| Feature | Status | Active plan |
|---------|--------|-------------|
| `content-generation` | 🟡 In progress — Phase 2 complete, Phase 3 next | `plan-github-pages-v1.md` |
| `landing-page-generation` | 📦 Reference — V1 modifier-matrix approach | `plan.md` |
| `brand-auth-portal` | ⏸ Parked | `plan.md` |

Active feature is set in `feature.json` → `"active_feature": "content-generation"`.

---

## Spec-kit conventions

### File roles

| File | Purpose |
|------|---------|
| `constitution/project-constitution.md` | Project-wide non-negotiables — read before anything else |
| `features/{name}/STATUS.md` | What is live today, phase progress, key decisions |
| `features/{name}/spec.md` | What to build — user stories, acceptance criteria |
| `features/{name}/plan*.md` | Phase-by-phase implementation approach |
| `features/{name}/checklists/requirements.md` | Implementation checklist with CHK-NNN items |
| `features/{name}/tasks/tasks.md` | Task tracker — inline list of GP-Phase tasks |

### Task tracking convention

For `content-generation`, tasks are tracked **inline in `tasks/tasks.md`** using GP-Phase task IDs (T-CG-024, T-CG-025, …). There are no individual task files per item — the plan file and checklist are the source of truth.

For `landing-page-generation`, individual task files (`TASK-LP-NNN-*.md`) exist from the original setup. This pattern is **not followed for new features** — use `tasks.md` instead.

### Checklist convention

CHK items in `checklists/requirements.md` map directly to implementable units:
- `[ ]` — not started
- `[x]` — complete
- Phases group related CHK items (GP-Phase 0, 1, 2, 3)

---

## Reading order (new contributor)

1. `constitution/project-constitution.md` — understand the non-negotiables
2. `features/content-generation/STATUS.md` — what phase we're in and what's live
3. `features/content-generation/plan-github-pages-v1.md` — the active build plan
4. `features/content-generation/checklists/requirements.md` — pick up an open CHK item
5. `../README.md` (root) — how to run the pipeline locally

---

## Commit convention

```
feat: implement GP-Phase 1 — seven quality gates
fix: demand_validator SSL retry for macOS environments
docs: update content-generation STATUS.md phase progress
```
