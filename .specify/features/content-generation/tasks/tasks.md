# Tasks: Content Generation

**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Generated**: 2026-04-26

> **Blocked by**: Landing Page Generation Phase 1–3 must be complete (shared infra + DB).

---

## Phase 1 — Setup (extend LP infra)

- [ ] T001 Add `generated_pages` table fields for content service (verify migration from LP feature covers `status`, `seo_score`, `uniqueness_score`)
- [ ] T002 [P] Add `OPENAI_API_KEY`, `OPENAI_MODEL_GEN`, `OPENAI_MODEL_VALIDATE` to `.env.example` and `app/config.py`

**Checkpoint**: `app/config.py` loads model names; DB migration runs cleanly.

---

## Phase 2 — Foundational

- [ ] T003 Create `app/models/schemas/content.py` — `KeywordProductPair`, `PlatformListing`, `GeneratedPage` Pydantic schemas (re-export if already in LP feature)
- [ ] T004 Create `app/services/prompt_builder.py` — builds intent-aware prompts (informational vs transactional template) from `KeywordProductPair`

**Checkpoint**: `prompt_builder.build(pair)` returns correctly structured prompt string.

---

## Phase 3 — User Story 1: Demand-Validated Single Page (Priority: P1) 🎯 MVP

**Goal**: POST one validated pair → GeneratedPage with status approved/review_queue/blocked.
**Independent test**: Unit test with mocked OpenAI returns approved page with all 7 gates passing.

- [ ] T005 [P] [US1] Create `app/services/openai_client.py` — async OpenAI wrapper with 3x exponential backoff, token-bucket rate limiter
- [ ] T006 [US1] Create `app/services/content_generator.py` — pass-1 (4o-mini draft) + pass-2 (4o quality validation) orchestration
- [ ] T007 [US1] Integrate `QualityGate.run_all()` from LP feature into content_generator output routing
- [ ] T008 [US1] Add Redis cache in `content_generator.py`: key = `sha256(product_id + keyword)`
- [ ] T009 [US1] Create `app/api/v1/endpoints/content.py` — `POST /api/v1/content/generate`
- [ ] T010 [US1] Wire endpoint into `app/main.py` (if not already added by LP feature)

**Checkpoint**: End-to-end POST generates page in < 60s; cache hit returns instantly on repeat.

---

## Phase 4 — User Story 2: Quality-Gated Batch (Priority: P2)

**Goal**: Batch of validated pairs processes; each independently gated; review queue populated.
**Independent test**: Batch of 3 pairs → 1 approved, 1 review_queue, 1 blocked (use test fixtures).

- [ ] T011 [P] [US2] Create `app/tasks/content_generate_task.py` — Celery task per pair, configurable `daily_limit`
- [ ] T012 [US2] Add `POST /api/v1/content/generate/batch` with `pairs[]` + `daily_limit` params
- [ ] T013 [US2] Add `GET /api/v1/content/batch/{id}/status`
- [ ] T014 [US2] Add `GET /api/v1/content/review-queue` (filter: status = review_queue)
- [ ] T015 [US2] Add `POST /api/v1/content/review-queue/{id}/approve` and `/discard`

**Checkpoint**: Batch endpoint queues tasks; status endpoint reflects approved/blocked/review_queue counts.

---

## Phase 5 — User Story 3: Agentic Shopping Structure (Priority: P2)

**Goal**: Every approved page carries full JSON-LD; passes Google Rich Results Test.
**Independent test**: Validate generated HTML via Rich Results Test API — zero errors.

- [ ] T016 [P] [US3] Create `app/services/schema_builder.py` — Product + Offer + FAQ + Breadcrumb JSON-LD from pair data
- [ ] T017 [US3] Create `app/services/rich_results_validator.py` — calls Google Rich Results Test API, returns pass/fail
- [ ] T018 [US3] Integrate `rich_results_validator` into `QualityGate.check_schema_validity()`
- [ ] T019 [US3] Add schema injection to page template (if not done in LP feature)

**Checkpoint**: `rich_results_validator.validate(html)` passes on a sample generated page.

---

## Final Phase — Polish

- [ ] T020 [P] Structured logging in `content_generator.py`: log generation time, model used, gate results, cache hit/miss
- [ ] T021 [P] Add unit tests for `prompt_builder`, `content_generator` (mocked OpenAI), `schema_builder`
- [ ] T022 Update `STATUS.md` — mark V2 content generation as in-progress with component completion status
- [ ] T023 Update `feature.json` to point to `content-generation` when switching active feature

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 MVP)
                                          ↘ Phase 4 (US2)  — after Phase 3
                                          ↘ Phase 5 (US3)  — after Phase 3
All phases → Polish
```

### MVP Scope
Phase 1 + 2 + 3 only = single-page generation with quality gates. Batch + Rich Results can follow.
