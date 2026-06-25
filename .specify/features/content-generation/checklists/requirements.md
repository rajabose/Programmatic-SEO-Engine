# Requirements Checklist: Content Generation (GitHub Pages v1)

**Purpose**: Track implementation completeness against the PRD quality gates and plan requirements  
**Created**: 2026-06-25  
**Feature**: [spec.md](../spec.md) | [plan-github-pages-v1.md](../plan-github-pages-v1.md)

---

## GP-Phase 0 — Demand Validation Gate

- [x] CHK-001 SQLite schema created (`db/schema.sql`) — 5 tables: products, keyword_product_pairs, generated_pages, review_queue, keyword_registry
- [x] CHK-002 `scripts/csv_to_sqlite.py` — idempotent product CSV loader
- [x] CHK-003 `scripts/demand_validator.py` — DataForSEO API, caches to `cache/keyword_volumes.json`, writes validated=1 pairs
- [x] CHK-004 `scripts/keyword_registry.py` — slug collision enforcement with audit + --fix mode
- [x] CHK-005 `generate.py --strict` — refuses to run without validated pairs in DB
- [x] CHK-006 `.env.example` created with OPENAI_API_KEY + DataForSEO credentials

---

## GP-Phase 1 — Quality Gates

- [x] CHK-007 `services/seo_scorer.py` — 0-100 score, threshold ≥80
- [x] CHK-008 `services/uniqueness_checker.py` — TF-IDF cosine similarity ≤20%
- [x] CHK-009 `services/keyword_density.py` — density <3% gate
- [x] CHK-010 `services/word_count_check.py` — informational ≥800w, transactional ≥300w
- [x] CHK-011 `services/link_checker.py` — parallel HEAD requests, 24h SQLite cache
- [x] CHK-012 `services/eeat_enforcer.py` — brand name, article:published_time, platform mention
- [x] CHK-013 `services/quality_gate.py` — `QualityGate.run_all()` orchestrator with routing
- [x] CHK-014 Routing wired into `generate.py` — approved→docs/, 1 fail→review_queue.json, else→blocked.json
- [x] CHK-015 `article:published_time` meta tag added to HTML template
- [x] CHK-016 `.seo-engine/review_queue.json` and `.seo-engine/blocked.json` initialised

---

## GP-Phase 2 — Full JSON-LD + Two-Pass Content

- [x] CHK-017 `build_product_json_ld()` extended — FAQPage (3-5 Q&As) + BreadcrumbList JSON-LD
- [x] CHK-018 `services/rich_results_validator.py` — JSON-LD schema field validation, STRICT_RICH_RESULTS=1 for CI blocking
- [x] CHK-019 `services/content_generator.py` — pass-1 GPT-4o-mini draft + pass-2 GPT-4o validation, cached to `cache/openai/<slug>.html`
- [x] CHK-020 `services/prompt_builder.py` — intent-aware prompts (informational vs transactional), BRAND_VOICE, anti-filler list, keyword density guidance
- [ ] CHK-021 10 sample pages pass Rich Results Test with zero errors
- [ ] CHK-022 FAQ and Breadcrumb schema visible in page source

---

## GP-Phase 3 — Freshness, Sitemap, Observability

- [ ] CHK-023 `services/freshness_checker.py` — price drift >10% or stock change flags page for regen
- [ ] CHK-024 `generate_sitemap.py` updated — priority 0.8 in-stock, 0.3 OOS, omit blocked
- [ ] CHK-025 `.github/workflows/weekly-freshness.yml` — Sunday cron regen + PR
- [ ] CHK-026 `.github/workflows/quality-audit.yml` — every push re-runs gates on all approved pages
- [ ] CHK-027 `scripts/build_admin_dashboard.py` — static `docs/_admin/index.html` (noindex)
- [ ] CHK-028 Repo layout cleaned — cache/, queues moved under `.seo-engine/`

---

## Definition of Done (full v1)

- [ ] All 7 PRD quality gates implemented and enforced on every new page
- [ ] Generation blocked without a validated keyword_product_pairs row
- [ ] Full JSON-LD (Product + Offer + FAQ + Breadcrumb) on every approved page
- [ ] review_queue.json and blocked.json tracked in git
- [ ] Weekly freshness Action runs and opens a PR when prices/stock drift
- [ ] Admin dashboard at discover.vanchai.in/_admin/ (noindex)
- [ ] 10 sample validated pairs deployed live, all passing Rich Results Test
- [ ] No paid services in deploy path (OpenAI + DataForSEO are pay-per-use only)

---

## Notes

- Check items off as completed: `[x]`
- CHK-001 to CHK-016 completed in session of 2026-06-25
- CHK-019, CHK-020 completed in session of 2026-06-25 (phase 2 content pipeline)
- Also fixed in this session: demand_validator category seeds, link_checker SSL retry, xlsx_to_csv CDN URL filter, check_data.py platform URL check, csv_to_sqlite.py bug
- V1 pages in docs/ are 97% similar (modifier-matrix artefact) — will be replaced by Phase 2 regen
