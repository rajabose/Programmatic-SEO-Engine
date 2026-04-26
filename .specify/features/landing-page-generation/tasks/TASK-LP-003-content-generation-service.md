# TASK-LP-003: AI Content Generation Service

**Plan ref**: Phase 2, Day 3-5 | **Branch**: `feature/landing-page-generation`  
**Priority**: High | **Estimate**: 10h | **Sprint**: Day 5 – Sprint 2 Day 1

## What to build
`ContentGenerator` service: receives a validated `KeywordProductPair`, calls OpenAI, runs quality gates, returns `GeneratedPage`.

## Input / output
```python
# Input (must already be demand-validated)
KeywordProductPair(keyword, search_volume, intent_type, product_id, unique_attributes, platform_availability)

# Output
GeneratedPage(page_id, keyword, slug, html, title, meta_description, schema_markup,
              seo_score, uniqueness_score, word_count, status)
# status: "approved" | "review_queue" | "blocked"
```

## Generation flow
1. Build prompt (intent-aware: informational vs transactional template)
2. Call GPT-4o-mini → draft content
3. Call GPT-4o → quality validation pass
4. Run `QualityGate.run_all()` — SEO score ≥80, uniqueness ≤20%, schema valid, links live
5. Route to `approved` / `review_queue` / `blocked`
6. Cache result in Redis keyed by `(product_id, keyword)`

## Quality gates (all enforced in code)
| Gate | Threshold |
|------|-----------|
| SEO score | ≥ 80/100 |
| Uniqueness | ≤ 20% overlap with existing pages |
| Word count | ≥ 800 (informational), product-complete (transactional) |
| Schema | passes Google Rich Results Test API |
| E-E-A-T | brand name, pub date, source platform present |
| Platform links | all CTA URLs return HTTP 200 |
| Keyword density | < 3% |

## API endpoints
```
POST /api/v1/content/generate             # single page
POST /api/v1/content/generate/batch       # queued, daily_limit param
GET  /api/v1/content/batch/{id}/status
GET  /api/v1/content/review-queue
POST /api/v1/content/review-queue/{id}/approve
POST /api/v1/content/review-queue/{id}/discard
```

## Acceptance criteria
- [ ] Single page generated in < 60s
- [ ] Quality gates block pages that don't pass — not silently skipped
- [ ] Review queue populated for single-gate failures
- [ ] Full JSON-LD on every approved page (Product + Offer + FAQ + Breadcrumb)
- [ ] Redis cache hit avoids duplicate generation
- [ ] Batch endpoint supports configurable daily limit (default 100)

## Definition of done
Integration test with real OpenAI key, all quality gates exercised (pass + fail cases), deployed to staging.

## Blocked by
TASK-LP-001, TASK-LP-002
