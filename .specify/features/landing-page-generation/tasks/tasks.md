# Tasks: Landing Page Generation

**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Generated**: 2026-04-26

---

## Phase 1 — Setup (shared infrastructure)

- [ ] T001 Initialize Poetry project, create `vanchai_seo/` directory structure per plan.md
- [ ] T002 [P] Add core Python dependencies to `pyproject.toml` (fastapi, uvicorn, sqlalchemy, alembic, redis, celery, structlog, pydantic-settings)
- [ ] T003 [P] Add dev dependencies (pytest, pytest-asyncio, httpx, black, isort, flake8)
- [ ] T004 Create `docker-compose.yml` with postgres + redis + api + celery services
- [ ] T005 [P] Create `.env.example` with all required variables
- [ ] T006 [P] Configure pre-commit hooks in `.pre-commit-config.yaml` (black, isort, flake8)

**Checkpoint**: `poetry install` succeeds, `docker-compose up` starts all services.

---

## Phase 2 — Foundational (blocks all user stories)

- [ ] T007 Create `app/config.py` — Pydantic `Settings` class reading from `.env`
- [ ] T008 Create `app/database.py` — SQLAlchemy engine, `SessionLocal`, `Base`, `get_db` dependency
- [ ] T009 Create `app/main.py` — FastAPI app with lifespan, CORS middleware, error handler
- [ ] T010 [P] Create `app/api/v1/endpoints/health.py` — `GET /api/v1/health/` with DB check
- [ ] T011 Create Alembic config and `migrations/env.py`
- [ ] T012 [P] Create `tests/conftest.py` with test DB session fixture

**Checkpoint**: `GET /api/v1/health/` returns `{"status":"healthy"}`, `pytest tests/` green.

---

## Phase 3 — User Story 1: Demand-Validated Page Generation (Priority: P1) 🎯 MVP

**Goal**: A single validated `KeywordProductPair` produces an approved static HTML page.
**Independent test**: POST one validated pair → receive `GeneratedPage` with `status: approved`.

- [ ] T013 [P] [US1] Create `app/models/keyword_pair.py` — `KeywordProductPair` Pydantic model + `PlatformListing` sub-model
- [ ] T014 [P] [US1] Create `app/models/generated_page.py` — `GeneratedPage` SQLAlchemy model + Pydantic schema
- [ ] T015 [US1] Create Alembic migration for `generated_pages` table
- [ ] T016 [US1] Create `app/services/uniqueness_checker.py` — cosine similarity check vs existing pages corpus (≤20% overlap)
- [ ] T017 [US1] Create `app/services/seo_scorer.py` — score HTML page 0-100 (title, meta, headers, density, length, links)
- [ ] T018 [US1] Create `app/services/quality_gate.py` — `QualityGate.run_all()` enforcing all 7 gates, returns `GateResult`
- [ ] T019 [US1] Create `app/services/schema_builder.py` — builds Product + Offer + FAQ + Breadcrumb JSON-LD from `KeywordProductPair`
- [ ] T020 [US1] Create `app/services/page_builder.py` — Jinja2 renders `templates/landing_page.html` with schema injection
- [ ] T021 [US1] Create `templates/landing_page.html` — mobile-first template, informational + transactional layout variants
- [ ] T022 [US1] Create `app/services/content_generator.py` — OpenAI GPT-4o-mini draft + GPT-4o quality pass (2-pass), Redis cache
- [ ] T023 [US1] Create `app/api/v1/endpoints/content.py` — `POST /api/v1/content/generate` endpoint
- [ ] T024 [US1] Wire endpoint into `app/main.py` router

**Checkpoint**: `POST /api/v1/content/generate` with a valid pair returns approved page with JSON-LD in < 60s.

---

## Phase 4 — User Story 2: Quality-Gated Batch Generation (Priority: P2)

**Goal**: A list of validated pairs processes through the pipeline; each page independently gated.
**Independent test**: POST 5 pairs → batch status shows breakdown of approved/review_queue/blocked.

- [ ] T025 [P] [US2] Create `app/models/batch.py` — `GenerationBatch` SQLAlchemy model (batch_id, status counts, daily_limit)
- [ ] T026 [US2] Create Alembic migration for `generation_batches` table
- [ ] T027 [US2] Create `app/tasks/generate_page_task.py` — Celery task wrapping single-page generation
- [ ] T028 [US2] Add `POST /api/v1/content/generate/batch` endpoint with `daily_limit` param (default 100)
- [ ] T029 [US2] Add `GET /api/v1/content/batch/{batch_id}/status` endpoint
- [ ] T030 [US2] Add `GET /api/v1/content/review-queue` endpoint
- [ ] T031 [US2] Add `POST /api/v1/content/review-queue/{id}/approve` and `/discard` endpoints

**Checkpoint**: Batch of 5 pairs runs via Celery; review-queue endpoint returns pages with status `review_queue`.

---

## Phase 5 — User Story 3: Platform CTAs with UTM Attribution (Priority: P2)

**Goal**: Each approved page links to all available platforms with pre-built UTM links.
**Independent test**: Generated page HTML contains correct UTM links; all return HTTP 200.

- [ ] T032 [P] [US3] Create `app/services/utm_builder.py` — builds UTM URLs per platform from `PlatformListing`
- [ ] T033 [US3] Create `app/services/link_checker.py` — async HEAD requests to all CTA URLs, returns status per platform
- [ ] T034 [US3] Integrate `link_checker` into `QualityGate.check_platform_links()` in `quality_gate.py`
- [ ] T035 [US3] Update `templates/landing_page.html` to render per-platform CTAs (skip unavailable platforms)

**Checkpoint**: Page HTML contains only live UTM links; `check_platform_links` gate fails if all platforms down.

---

## Phase 6 — User Story 4: Content Freshness (Priority: P3)

**Goal**: Deployed pages reflect current pricing; stale pages flagged for regeneration.
**Independent test**: Price change > 10% on a product triggers regeneration flag in DB.

- [ ] T036 [P] [US4] Add `last_price`, `last_updated`, `needs_regen` fields to `GeneratedPage` model + migration
- [ ] T037 [US4] Create `app/services/freshness_checker.py` — compares current catalog price to `last_price`; sets `needs_regen=True` when drift > 10%
- [ ] T038 [US4] Create `app/tasks/freshness_check_task.py` — scheduled Celery beat task (daily)
- [ ] T039 [US4] Update sitemap priority logic in `app/services/sitemap_builder.py`: in-stock → 0.8, out-of-stock → 0.3

**Checkpoint**: Freshness task runs, sets `needs_regen=True` for a product with price change, sitemap priorities correct.

---

## Final Phase — Polish & Cross-Cutting Concerns

- [ ] T040 [P] Add structlog logging to all services (request IDs, gate results, generation time)
- [ ] T041 [P] Add Redis token-bucket rate limiter for OpenAI calls in `content_generator.py`
- [ ] T042 Write `docs/api.md` summary of all endpoints with request/response examples
- [ ] T043 [P] Add `Makefile` with `make dev`, `make test`, `make migrate`, `make generate`
- [ ] T044 Run full end-to-end smoke test: 10 validated pairs → verify all approved pages pass Google Rich Results Test
- [ ] T045 Update `STATUS.md` with current implementation state

---

## Dependencies & Execution Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 MVP)
                                          ↘ Phase 4 (US2) — can start after Phase 3 complete
                                          ↘ Phase 5 (US3) — can start after Phase 3 complete
                                          ↘ Phase 6 (US4) — can start after Phase 3 complete
All user story phases → Polish
```

### MVP Scope
Complete **Phase 1 + Phase 2 + Phase 3 only** = working single-page generation. Stop and validate before adding batch/freshness.

### Parallel opportunities within Phase 3
```
T013 (KeywordProductPair model) — parallel with T014 (GeneratedPage model)
T016 (uniqueness_checker)       — parallel with T017 (seo_scorer)
T018 (quality_gate)             — depends on T016, T017
T019 (schema_builder)           — parallel with T021 (template)
T020 (page_builder)             — depends on T019, T021
T022 (content_generator)        — parallel with T020
T023 (endpoint)                 — depends on T022, T020, T018
```
