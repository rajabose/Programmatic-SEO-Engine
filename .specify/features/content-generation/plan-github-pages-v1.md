# Plan v1 (GitHub Pages): Content Generation — Vanchai

**Status**: Active — zero-cost rollout
**Spec**: [spec.md](spec.md) | **Tasks**: [tasks/tasks.md](tasks/tasks.md)
**Brand**: Vanchai only (single-tenant)
**Live domain**: `discover.vanchai.in` → GitHub Pages (CNAME in `vanchai-seo-engine/docs/`)
**Supersedes**: [plan.md](plan.md) — the FastAPI/Postgres/Celery/Redis architecture in `plan.md` is preserved as the future-state target and re-activates only when a §Graduation trigger fires.

---

> **Why this plan exists**: The original `plan.md` assumes a hosted stack (FastAPI + Postgres + Celery + Redis) that costs real money to run. The PRD's seven quality gates, demand validation, schema injection, and freshness regeneration do not actually require a running server — they run perfectly well at **build time** as Python scripts. This plan keeps deployment cost at **$0** by mapping every PRD requirement onto static-site primitives: SQLite committed to the repo, JSON files for queues, GitHub Actions as the scheduler, and `docs/` → GitHub Pages as the deploy target.

---

## Architecture (zero-cost mapping of the PRD stack)

| PRD layer | Spec choice | v1 replacement | Cost |
|---|---|---|---|
| API server | FastAPI | Python CLI scripts in `scripts/`, invoked by Actions or developer | $0 |
| Datastore | Postgres (`generated_pages`, `review_queue`) | SQLite at `db/seo_engine.db`, committed to repo | $0 |
| Queue / worker | Celery + Redis | GitHub Actions matrix jobs + `workflow_dispatch` | $0 (2k min/mo free) |
| Generation cache | Redis (`sha256(product+kw)`) | `cache/openai/<sha256>.json` (gitignored, restored via `actions/cache`) | $0 |
| Review queue | DB table + UI | `review_queue.json` + PR-based human review (merge = approve) | $0 |
| Schema validation | Google Rich Results Test | Same API, called at build time before commit | $0 |
| Static deploy | S3 + CloudFront | `docs/` → GitHub Pages w/ CNAME `discover.vanchai.in` | $0 |
| Catalog sync | Live `CatalogManager` service | `xlsx_to_csv.py` + new `csv_to_sqlite.py` (manual XLSX export) | $0 |
| Demand validation | Ahrefs / DataForSEO + Redis 24h cache | DataForSEO pay-per-use + `cache/keyword_volumes.json` | ~$10 / 15k keywords |
| Observability | Hosted dashboards / logs | Git history + GH Actions logs + static `docs/_admin/` page | $0 |

**Hard ceilings on GitHub Pages**: 1 GB repo size, 10 GB/mo bandwidth (soft), 10 builds/hr, 100 GB/mo Actions minutes (private). At ~15 KB/page × 1,360 pages = ~20 MB, you have headroom for ~50k pages before any ceiling bites.

---

## Phase 0 — Stop the doorway-page bleed (3 days)

**Goal**: Prevent `generate.py` from emitting pages that the PRD's own anti-pattern table forbids. Today's matrix (every product × all 65 `INTENT_MODIFIERS`) is exactly the pattern the spec calls "blocked." Demand validation must gate generation **before** any quality-gate work downstream is worth doing.

| Task | What |
|------|------|
| **T-CG-024** | SQLite schema: `products`, `keyword_product_pairs`, `generated_pages`, `review_queue`, `keyword_registry` |
| **T-CG-025** | `scripts/csv_to_sqlite.py` — load `products.csv` into `products` table |
| **T-CG-026** | `scripts/demand_validator.py` — DataForSEO call, caches results, writes pairs with `search_volume ≥ 100` to `keyword_product_pairs` |
| **T-CG-027** | `scripts/keyword_registry.py` — enforce one page per keyword; reject slug collisions |
| **T-CG-028** | Gate `generate.py` on `keyword_product_pairs.validated = true`; refuse to run from raw `INTENT_MODIFIERS` |

**Exit**: `generate.py --strict` only emits pages backed by a validated pair in the DB. The 65-modifier matrix is no longer the source of truth.

---

## Phase 1 — Seven quality gates as importable modules (week 1–2)

**Goal**: Every page that lands in `docs/` has provably passed all 7 PRD gates. Pages that fail one recoverable gate go to `review_queue.json`; pages that fail blocking gates go to `blocked.json`. Both files are committed — the audit trail is the git history.

| Task | What |
|------|------|
| **T-CG-029** | `services/quality_gate.py` — `QualityGate.run_all(page) -> GateResult` orchestrator |
| **T-CG-030** | `services/seo_scorer.py` — 0-100 score: title length, meta length, H1 presence, keyword in first 100w, internal links count |
| **T-CG-031** | `services/uniqueness_checker.py` — TF-IDF cosine similarity vs corpus in `docs/`; SQLite stores corpus matrix; ≤ 20% overlap |
| **T-CG-032** | `services/keyword_density.py` — < 3% gate |
| **T-CG-033** | `services/word_count_check.py` — informational ≥ 800; transactional = "has price + ≥1 platform link live + ≥ 300 words" (concrete definition for the spec's "product-complete") |
| **T-CG-034** | `services/link_checker.py` — async HEAD requests on Wix/Amazon/Myntra/Nykaa URLs; 24h cache in SQLite; sets `in_stock` flag |
| **T-CG-035** | `services/eeat_enforcer.py` — template-level: brand name, `<meta property="article:published_time">`, source platform |
| **T-CG-036** | Routing in `generate.py`: 0 fail → write to `docs/`; 1 recoverable fail → `review_queue.json`; else → `blocked.json` |

**Exit**: 10 sample pages run through `QualityGate.run_all()`; gate pass/fail counts visible in Actions log.

---

## Phase 2 — Full JSON-LD + two-pass content (week 3)

**Goal**: Close the agentic-shopping gap. Today's `build_product_json_ld()` emits Product + Offer only. The PRD requires Product + Offer + FAQ + Breadcrumb on every approved page, validated against Google Rich Results Test.

| Task | What |
|------|------|
| **T-CG-037** | Extend `build_product_json_ld()` → also emit `FAQPage` (3–5 Q&As from the OpenAI call) + `BreadcrumbList` |
| **T-CG-038** | `services/rich_results_validator.py` — calls Google Rich Results Test API; blocks commit if any approved page errors |
| **T-CG-039** | `services/content_generator.py` — refactor `generate.py`'s OpenAI call into pass-1 (4o-mini draft) + pass-2 (4o validation: returns pass/fail + reason); cache both passes |
| **T-CG-040** | `services/prompt_builder.py` — intent-aware (informational vs transactional) template; carries `BRAND_VOICE`; anti-filler phrase list ("in today's world", "look no further", "perfect for anyone") |

**Exit**: 10 sample pages pass Rich Results Test with zero errors; FAQ + Breadcrumb schema present on each.

---

## Phase 3 — Freshness, OOS-aware sitemap, observability (week 4)

**Goal**: Keep deployed pages aligned with live pricing/stock without a server. A weekly GitHub Action diffs the current catalog, regenerates affected pages, and opens a PR for review.

| Task | What |
|------|------|
| **T-CG-041** | `services/freshness_checker.py` — diff current catalog vs `last_seen` snapshot in SQLite; flag pages where price drifted > 10% or stock changed |
| **T-CG-042** | Update `generate_sitemap.py` — `priority=0.8` in-stock approved, `0.3` OOS, omit blocked |
| **T-CG-043** | `.github/workflows/weekly-freshness.yml` — Sunday cron: runs freshness check + regenerates flagged pages + opens PR |
| **T-CG-044** | `.github/workflows/quality-audit.yml` — every push to `main`: re-run `check_data.py` + `QualityGate` on all approved pages; fail CI if any page now fails a gate |
| **T-CG-045** | `scripts/build_admin_dashboard.py` — renders `docs/_admin/index.html` (with `<meta name="robots" content="noindex">`): batch stats, gate pass rates, blocked list |
| **T-CG-046** | Move `cache/`, `review_queue.json`, `blocked.json` under `.seo-engine/`; keep `db/seo_engine.db` committed for auditability |

**Exit**: A weekly Action keeps prices/stock fresh; the admin dashboard surfaces the metrics named in `STATUS.md`'s "Metrics to Watch."

---

## Stack (v1)

| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| Datastore | SQLite (`db/seo_engine.db`), committed |
| LLM | GPT-4o-mini (draft) + GPT-4o (validation) via `openai` SDK |
| Cache | Local JSON in `cache/openai/`, restored via `actions/cache` |
| Validation | Google Rich Results Test API, DataForSEO Keyword Difficulty API |
| Scheduler | GitHub Actions (`workflow_dispatch` + `schedule`) |
| Deploy | `docs/` → GitHub Pages with `vanchai-seo-engine/docs/CNAME` |
| Observability | Git history + Actions logs + static `docs/_admin/` page |

---

## Repo layout (target after Phase 3)

```
vanchai-seo-engine/
├── config.py
├── generate.py                  # gated on validated pairs (T-CG-028)
├── generate_index.py
├── generate_sitemap.py          # OOS-aware (T-CG-042)
├── check_data.py
├── xlsx_to_csv.py
├── products.csv
├── scripts/
│   ├── csv_to_sqlite.py
│   ├── demand_validator.py
│   ├── keyword_registry.py
│   └── build_admin_dashboard.py
├── services/
│   ├── quality_gate.py
│   ├── seo_scorer.py
│   ├── uniqueness_checker.py
│   ├── keyword_density.py
│   ├── word_count_check.py
│   ├── link_checker.py
│   ├── eeat_enforcer.py
│   ├── content_generator.py
│   ├── prompt_builder.py
│   ├── rich_results_validator.py
│   └── freshness_checker.py
├── db/
│   └── seo_engine.db            # committed
├── .seo-engine/
│   ├── review_queue.json
│   ├── blocked.json
│   └── cache/                   # gitignored
└── docs/                        # served by GitHub Pages
    ├── _admin/index.html        # noindex'd dashboard
    ├── index.html
    ├── category-*.html
    └── <slug>.html × N
```

---

## Risks (v1-specific)

| Risk | Mitigation |
|------|-----------|
| OpenAI cost spirals during regeneration | Phase 1 caches every prompt → response by `sha256(product+kw)`; only changed pairs hit the API |
| Repo size grows past 1 GB | At ~15 KB/page we can hold ~50k pages; alert at 500 MB |
| GitHub Actions monthly minute cap (2k free / 3k paid) | Freshness job is weekly; full regen is a manual `workflow_dispatch` |
| DataForSEO API key in repo | Stored in GitHub Actions secret, never in `db/seo_engine.db` |
| Rich Results Test API rate-limited | Validate only changed/new pages, not the full corpus, per build |
| Static-only = no real-time review queue | Acceptable for one-brand single-pipeline scale. Revisit at Graduation |

---

## Graduation (when v1 stops being enough)

Move to the FastAPI plan in `plan.md` when **any one** of these fires:

1. **Second brand onboarded** beyond Vanchai (multi-tenancy requires per-brand isolation)
2. **User-submitted content** (reviews, ratings, Q&A) — can't be static
3. **Repo size exceeds 500 MB**, or sitemap exceeds 50k URLs (GitHub Pages soft ceilings)
4. **Need sub-minute regeneration** (e.g., flash-sale price sync) — Actions cron is too coarse

Until one of these triggers fires, v1 is the canonical implementation.

---

## Definition of done (v1)

- [ ] All 7 PRD quality gates implemented as Python modules and enforced in `generate.py`
- [ ] Generation blocked without a validated `keyword_product_pairs` row
- [ ] Full JSON-LD (Product + Offer + FAQ + Breadcrumb) on every approved page
- [ ] `review_queue.json` and `blocked.json` populated and tracked in git
- [ ] Weekly freshness Action runs and opens a PR when prices/stock drift
- [ ] Admin dashboard renders at `discover.vanchai.in/_admin/` with `noindex`
- [ ] 10 sample validated pairs deployed live, all passing Rich Results Test
- [ ] No paid services in the deploy path (OpenAI + DataForSEO are pay-per-use, not subscriptions)
