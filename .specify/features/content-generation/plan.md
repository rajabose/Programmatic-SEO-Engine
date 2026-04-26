# Plan: Content Generation Service (Python)

**Spec**: [spec.md](spec.md) | **Sprint**: 1–3 (3 weeks) | **Blocked by**: LP Phase 1–3 complete

> This service is downstream of Demand Validation. It receives only pre-validated `KeywordProductPair` objects — never raw keywords.

---

## Phase 1 — Service Scaffold (Week 1)

**Goal**: FastAPI service wired into shared LP infra, `GeneratedPage` model, stub endpoint.

| Day | Task | Ticket |
|-----|------|--------|
| 1-2 | `GeneratedPage` SQLAlchemy model + Pydantic schema, Alembic migration | TASK-CG-001 |
| 3-4 | `POST /content/generate` endpoint (stub — returns mock page) | TASK-CG-001 |
| 5 | `GET /content/review-queue`, `approve/discard` endpoints | TASK-CG-001 |

**Exit criteria**: Stub endpoint accepts `KeywordProductPair`, persists a `GeneratedPage` with status `review_queue`.

---

## Phase 2 — Generation Pipeline (Week 2)

**Goal**: Real OpenAI generation with two-pass quality validation.

| Component | Detail |
|-----------|--------|
| `ContentGenerator` | Builds intent-aware prompt (informational vs transactional template) |
| Pass 1 | GPT-4o-mini: draft title, meta, body, FAQ |
| Pass 2 | GPT-4o: quality validation — returns pass/fail + reason |
| `QualityGate.run_all()` | 7 gates (see spec.md) — must all run before approval |
| Redis cache | Key = `sha256(product_id + keyword)` — avoids duplicate generation |
| Retry | 3x exponential backoff on OpenAI errors before sending to review queue |

**Exit criteria**: End-to-end page generated <60s; all 7 gates exercised in unit tests (pass + fail cases).

---

## Phase 3 — Batch & Schema (Week 3)

**Goal**: Batch generation, full JSON-LD, review queue UI hooks.

| Component | Detail |
|-----------|--------|
| Batch API | `POST /content/generate/batch` — Celery task per pair, configurable `daily_limit` (default 100) |
| `GET /content/batch/{id}/status` | approved / review_queue / blocked counts |
| JSON-LD builder | Product + Offer + FAQ + Breadcrumb injected by `SchemaBuilder` |
| Schema validation | Calls Google Rich Results Test API — blocks deploy on failure |
| Sitemap priority | In-stock approved pages: 0.8 / out-of-stock: 0.3 |

**Exit criteria**: Batch of 10 validated pairs processed, all approved pages pass Rich Results Test.

---

## Stack

| Layer | Choice |
|-------|--------|
| API | FastAPI (shared with LP feature) |
| LLM | GPT-4o-mini (gen) + GPT-4o (validation) |
| Queue | Celery + Redis |
| DB | PostgreSQL — `generated_pages` + `review_queue` tables |
| Schema | Google Rich Results Test API |
| Cache | Redis — generation cache + token-bucket rate limiter |

---

## Risks

| Risk | Mitigation |
|------|-----------|
| OpenAI rate limits | Redis token-bucket limiter; batch size configurable |
| Quality gate false positives block good pages | Gates are configurable thresholds in `config.py`; review queue is the escape hatch |
| Rich Results Test API downtime | Cache last-known result; warn on deploy rather than hard-block |
