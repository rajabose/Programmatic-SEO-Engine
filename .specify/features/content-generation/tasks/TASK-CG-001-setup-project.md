# TASK-CG-001: Initialize Content Generation Service

**Plan ref**: Phase 1 | **Branch**: `feature/content-generation`  
**Priority**: High | **Estimate**: 4h

## What to build
Standalone Python service (FastAPI) for content generation — isolated from the LP generation pipeline. Shares the same DB and Redis as LP feature but owns its own endpoints and service layer.

## Stack
Python 3.10+, FastAPI, OpenAI SDK, SQLAlchemy (shared DB), Redis (shared), structlog.  
Reuse `app/config.py`, `app/database.py` from TASK-LP-001.

## Directory additions
```
app/
├── services/
│   └── content_generator.py   # ContentGenerator class
├── api/v1/endpoints/
│   └── content.py             # /content/generate endpoints
└── models/
    └── generated_page.py      # GeneratedPage ORM + schema
```

## Acceptance criteria
- [ ] `POST /api/v1/content/generate` accepts `KeywordProductPair`, returns `GeneratedPage`
- [ ] `ContentGenerator` rejects pairs not carrying `search_volume ≥ 100`
- [ ] OpenAI call wrapped with retry (3x, exponential backoff)
- [ ] Generated page saved to DB with status field
- [ ] `GET /api/v1/content/review-queue` returns pages with status `review_queue`
- [ ] Unit tests with mocked OpenAI client passing

## Definition of done
Single page generated end-to-end in staging, all acceptance criteria checked.

## Blocked by
TASK-LP-001 (shared infra)
