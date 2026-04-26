# .specify — Programmatic SEO Engine

Feature-level documentation using the SpecKit methodology.

## Structure

```
.specify/
├── constitution/
│   └── project-constitution.md   # Project-wide principles + quality gates
├── features/
│   ├── landing-page-generation/
│   │   ├── STATUS.md             # Live code + current strategy
│   │   ├── spec.md               # What to build + acceptance criteria
│   │   ├── plan.md               # Phase-by-phase implementation plan
│   │   └── tasks/
│   │       ├── TASK-LP-001-setup-python-project.md
│   │       ├── TASK-LP-002-product-catalog-sync.md
│   │       └── TASK-LP-003-content-generation-service.md
│   └── content-generation/
│       ├── STATUS.md
│       ├── spec.md
│       ├── plan.md
│       └── tasks/
│           └── TASK-CG-001-setup-project.md
└── templates/
    ├── spec-template.md
    ├── plan-template.md
    ├── tasks-template.md
    ├── constitution-template.md
    └── checklist-template.md
```

## Hierarchy

| Level | File | Purpose |
|-------|------|---------|
| Project | `constitution/` | Vision, principles, quality gate thresholds |
| Feature | `features/{name}/STATUS.md` | What's running today + strategy direction |
| Feature | `features/{name}/spec.md` | What to build, user stories, acceptance criteria |
| Feature | `features/{name}/plan.md` | Phase-by-phase implementation approach |
| Task | `features/{name}/tasks/TASK-{CODE}-{NNN}-*.md` | Specific work items with acceptance criteria |

## Reading order (new team member)

1. `constitution/project-constitution.md` — why we build what we build
2. `features/landing-page-generation/STATUS.md` — what's live right now
3. `features/landing-page-generation/spec.md` — V2 requirements
4. `features/landing-page-generation/plan.md` — implementation phases
5. Pick up a `TASK-LP-*` ticket

## Branch strategy

```
main (shared docs + live V1 code)
├── feature/landing-page-generation   (V2 FastAPI stack)
└── feature/content-generation        (AI generation service)
```

## Task naming

`TASK-{FEATURE_CODE}-{NNN}-{description}.md`

| Feature | Code |
|---------|------|
| landing-page-generation | LP |
| content-generation | CG |
| demand-validation | DV (planned) |
| merchant-center-feed | MC (planned) |

## Git commit convention

```
TASK-LP-001: Add FastAPI health check endpoint
TASK-CG-001: Scaffold ContentGenerator service stub
```
