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

---

# Active Path — GitHub Pages v1 (Vanchai, zero-cost)

**Plan**: [../plan-github-pages-v1.md](../plan-github-pages-v1.md)
**Status**: Active — supersedes T001–T023 above until a §Graduation trigger fires
**Brand**: Vanchai only
**Deploy target**: `vanchai-seo-engine/docs/` → GitHub Pages → `discover.vanchai.in`

> The FastAPI-stack tasks above (T001–T023) remain valid for future graduation. The tasks below run every PRD requirement at build time as Python scripts + SQLite-in-repo + GitHub Actions. No hosted services.

---

## GP-Phase 0 — Stop the doorway-page bleed ✅ COMPLETE (2026-06-25)

**Goal**: Demand validation gates `generate.py`. The 65-modifier × every-product matrix is the PRD's #1 anti-pattern; close it before building gates downstream.
**Independent test**: `generate.py` refuses to emit a page for a pair not present in `keyword_product_pairs` with `validated=true`.

- [x] T-CG-024 [GP0] Add SQLite schema in `db/schema.sql`: `products`, `keyword_product_pairs`, `generated_pages`, `review_queue`, `keyword_registry`
- [x] T-CG-025 [P] [GP0] Create `scripts/csv_to_sqlite.py` — load `products.csv` into `products` table; idempotent on re-run
- [x] T-CG-026 [GP0] Create `scripts/demand_validator.py` — DataForSEO API call, caches to `cache/keyword_volumes.json`, writes pairs with `search_volume ≥ 100` to `keyword_product_pairs`
- [x] T-CG-027 [GP0] Create `scripts/keyword_registry.py` — enforce one page per keyword; reject slug collisions before they reach the generator
- [x] T-CG-028 [GP0] Gate `generate.py` on `keyword_product_pairs.validated = true`; add `--strict` flag; refuse to run from raw `INTENT_MODIFIERS`

**Checkpoint**: ✅ `python generate.py --strict --dry-run` exits with clear error "No validated keyword-product pairs found in DB."

---

## GP-Phase 1 — Seven quality gates as importable modules ✅ COMPLETE (2026-06-25)

**Goal**: Every page in `docs/` has provably passed all 7 PRD gates. Failures land in `review_queue.json` or `blocked.json`, committed to git.

- [x] T-CG-029 [GP1] `services/quality_gate.py` — `QualityGate.run_all() -> GateResult` with routing logic
- [x] T-CG-030 [GP1] `services/seo_scorer.py` — 0-100 score (title, meta, H1, keyword in first 100w, internal links, schema)
- [x] T-CG-031 [GP1] `services/uniqueness_checker.py` — stdlib TF-IDF cosine vs docs/ corpus; ≤20% overlap
- [x] T-CG-032 [GP1] `services/keyword_density.py` — phrase-weighted density <3% gate
- [x] T-CG-033 [GP1] `services/word_count_check.py` — informational ≥800w, transactional ≥300w+price+link
- [x] T-CG-034 [GP1] `services/link_checker.py` — parallel HEAD requests (ThreadPoolExecutor), 24h SQLite cache, blocking when all URLs dead
- [x] T-CG-035 [GP1] `services/eeat_enforcer.py` — brand name, article:published_time, platform mention; template updated
- [x] T-CG-036 [GP1] Routing in `generate.py` — approved→docs/, 1 recoverable→review_queue.json, else→blocked.json; `_append_to_queue()` helper added

**Checkpoint**: ✅ Tested on existing V1 pages. Uniqueness gate correctly flags 97% similarity between modifier-matrix siblings. All 6 gates produce correct pass/fail signals and routing works end-to-end.

---

## GP-Phase 2 — Full JSON-LD + two-pass content (week 3)

**Goal**: Close the agentic-shopping gap. Product + Offer + FAQ + Breadcrumb on every approved page, validated against Google Rich Results Test.
**Independent test**: 10 generated pages pass Rich Results Test API with zero errors.

- [ ] T-CG-037 [GP2] Extend `build_product_json_ld()` in `generate.py` — also emit `FAQPage` (3-5 Q&As from OpenAI) + `BreadcrumbList`
- [ ] T-CG-038 [GP2] Create `services/rich_results_validator.py` — calls Google Rich Results Test API; blocks commit if any approved page errors
- [ ] T-CG-039 [GP2] Create `services/content_generator.py` — refactor `generate.py`'s OpenAI call into pass-1 (4o-mini draft) + pass-2 (4o validation pass/fail+reason); cache both passes to `cache/openai/`
- [ ] T-CG-040 [P] [GP2] Create `services/prompt_builder.py` — intent-aware (informational vs transactional) template; carries `BRAND_VOICE`; anti-filler phrase list

**Checkpoint**: `python -m services.rich_results_validator docs/<sample>.html` exits 0 on a generated page; FAQ and Breadcrumb schema visible in page source.

---

## GP-Phase 3 — Freshness, OOS-aware sitemap, observability (week 4)

**Goal**: Keep deployed pages aligned with live pricing/stock without a server. Weekly GitHub Action diffs catalog, regenerates affected pages, opens a PR.
**Independent test**: Manually mutate a price in `products.csv` by > 10%, run the freshness Action, confirm a PR opens with the regenerated page.

- [ ] T-CG-041 [GP3] Create `services/freshness_checker.py` — diff current catalog vs `last_seen` snapshot in SQLite; flag pages where price drifted > 10% or stock changed
- [ ] T-CG-042 [GP3] Update `generate_sitemap.py` — `priority=0.8` in-stock approved, `0.3` OOS, omit blocked from sitemap entirely
- [ ] T-CG-043 [GP3] Add `.github/workflows/weekly-freshness.yml` — Sunday cron: runs freshness check + regenerates flagged pages + opens PR
- [ ] T-CG-044 [GP3] Add `.github/workflows/quality-audit.yml` — every push to `main`: re-runs `check_data.py` + `QualityGate` on all approved pages; fails CI if any page now fails a gate
- [ ] T-CG-045 [P] [GP3] Create `scripts/build_admin_dashboard.py` — renders `docs/_admin/index.html` with `<meta name="robots" content="noindex">`: batch stats, gate pass rates, blocked list
- [ ] T-CG-046 [GP3] Repo cleanup: move `cache/`, `review_queue.json`, `blocked.json` under `.seo-engine/`; keep `db/seo_engine.db` committed; add `.seo-engine/cache/` to `.gitignore`

**Checkpoint**: Sunday cron fires successfully on a manual `workflow_dispatch`; admin dashboard accessible at `discover.vanchai.in/_admin/` and is `noindex`'d.

---

## GP Dependencies

```
GP-Phase 0 (demand gate)
  └─→ GP-Phase 1 (quality gates) ──┐
  └─→ GP-Phase 2 (schema + two-pass) ──→ GP-Phase 3 (freshness + obs)
```

GP-Phase 1 and GP-Phase 2 can run in parallel after GP-Phase 0 closes. GP-Phase 3 depends on both.

### GP MVP Scope
GP-Phase 0 + GP-Phase 1 = a safe-to-deploy generator that refuses to emit doorway pages and enforces all 7 gates. JSON-LD completeness (GP-Phase 2) and freshness (GP-Phase 3) can land in follow-up PRs.
