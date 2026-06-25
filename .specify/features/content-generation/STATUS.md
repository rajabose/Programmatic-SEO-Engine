# Feature Status: Content Generation

**Feature Code**: CG  
**Active Plan**: `plan-github-pages-v1.md` (zero-cost static build)  
**Status**: 🟡 In Progress — Phase 2 in progress  
**Last Updated**: 2026-06-25

---

## Phase Progress

| Phase | Description | Status |
|-------|-------------|--------|
| GP-Phase 0 | Stop doorway-page bleed — demand validation gate | ✅ Complete |
| GP-Phase 1 | Seven quality gates as importable modules | ✅ Complete |
| GP-Phase 2 | Full JSON-LD + two-pass OpenAI content | 🔲 Next |
| GP-Phase 3 | Freshness, OOS-aware sitemap, observability | 🔲 Pending |

---

## What's Running (Live Code)

| File | Purpose | Status |
|------|---------|--------|
| `generate.py` | Core generator — now gated on validated pairs (`--strict`) | ✅ Updated |
| `db/schema.sql` + `db/seo_engine.db` | SQLite demand validation store | ✅ Live |
| `scripts/csv_to_sqlite.py` | Load product CSV into SQLite | ✅ Built |
| `scripts/demand_validator.py` | DataForSEO keyword volume validation | ✅ Built |
| `scripts/keyword_registry.py` | Slug collision enforcement | ✅ Built |
| `services/quality_gate.py` | `QualityGate.run_all()` orchestrator | ✅ Built |
| `services/seo_scorer.py` | 0-100 SEO score gate | ✅ Built |
| `services/uniqueness_checker.py` | TF-IDF cosine similarity gate (≤20%) | ✅ Built |
| `services/keyword_density.py` | Keyword density gate (<3%) | ✅ Built |
| `services/word_count_check.py` | Word count gate (800w / 300w) | ✅ Built |
| `services/link_checker.py` | Platform link liveness gate | ✅ Built |
| `services/eeat_enforcer.py` | E-E-A-T signal gate | ✅ Built |
| `.seo-engine/review_queue.json` | Pages pending human review | ✅ Live |
| `.seo-engine/blocked.json` | Pages blocked by gates | ✅ Live |

---

## Current Architecture (GP v1)

```
Products CSV → csv_to_sqlite.py → SQLite products table
                                         ↓
                          demand_validator.py (DataForSEO API)
                                         ↓ validated=1
                          keyword_registry.py (slug dedup)
                                         ↓
generate.py --strict → QualityGate.run_all()
                              ↓           ↓           ↓
                          approved    review_queue  blocked
                           docs/      .seo-engine/  .seo-engine/
```

---

## Key Decisions

- **Active plan is GP v1** (GitHub Pages zero-cost), not the FastAPI plan in `plan.md`
- **`--strict` is the production mode** — legacy modifier matrix is kept for reference only
- **Quality gates are code, not config**: `QualityGate.run_all()` runs on every new page
- **Category-based keyword seeds**: demand_validator uses 8 category→seed mappings (e.g. DRIED_PLANT→"dried flowers") instead of full product names. 512 searchable candidates (was 7,232 unsearchable).
- **97% similarity confirmed**: V1 modifier-matrix pages are near-duplicate — uniqueness gate correctly blocks them
- **Pipeline validated**: End-to-end test with 5 force-validated pairs — all correctly blocked. Gates work.
- **Two-pass generation deferred to Phase 2**: Phase 1 gates detect quality issues; Phase 2 fixes the root cause with intent-aware prompts

---

## What Phase 2 Will Deliver

- `services/prompt_builder.py` — intent-aware prompts (informational vs. transactional) so pages are genuinely differentiated
- `services/content_generator.py` — GPT-4o-mini draft + GPT-4o validation pass, cached to `cache/openai/`
- Extended `build_product_json_ld()` — FAQPage + BreadcrumbList JSON-LD
- `services/rich_results_validator.py` — Google Rich Results Test API validation

---

## Dependencies

- OpenAI API key in `.env` (Phase 2)
- DataForSEO credentials in `.env` (Phase 0 — demand validator)
- Product catalogue XLSX → run `xlsx_to_csv.py` first

---

## Metrics to Watch

- % of generated pages auto-approved vs. review queue vs. blocked
- Average SEO score per batch (target: ≥80)
- Uniqueness score distribution (target: ≤20% per page)
- Generation time per page (target: <60s with two-pass OpenAI)
- Cost per page (target: ~₹0.15 with GPT-4o-mini)
