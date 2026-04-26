# TASK-LP-001: Initialize Python Project Structure

**Plan ref**: Phase 1, Day 1-2 | **Branch**: `feature/landing-page-generation`  
**Priority**: High | **Estimate**: 6h | **Sprint**: Day 1-2

## What to build
FastAPI project with Poetry, PostgreSQL (SQLAlchemy), Redis, Celery, structlog.

## Directory layout
```
vanchai_seo/
├── app/
│   ├── main.py          # FastAPI entry + lifespan
│   ├── config.py        # Pydantic settings (env-driven)
│   ├── database.py      # SQLAlchemy engine + get_db dep
│   ├── models/          # ORM models + Pydantic schemas
│   ├── services/        # Business logic
│   ├── api/v1/endpoints/
│   └── tasks/           # Celery tasks
├── tests/conftest.py
├── migrations/          # Alembic
├── pyproject.toml
├── docker-compose.yml   # postgres + redis + celery
└── .env.example
```

## Acceptance criteria
- [ ] `poetry install` succeeds
- [ ] `GET /api/v1/health/` returns `{"status":"healthy"}` with DB status
- [ ] `docker-compose up` starts postgres + redis cleanly
- [ ] `pytest tests/` passes
- [ ] pre-commit hooks (black, isort, flake8) installed

## Key deps
`fastapi uvicorn pydantic-settings sqlalchemy alembic psycopg2-binary redis celery structlog`  
dev: `pytest pytest-asyncio httpx black isort flake8`

## Definition of done
All acceptance criteria checked, Docker tested locally, README updated.

## Blocks
TASK-LP-002, TASK-LP-003
