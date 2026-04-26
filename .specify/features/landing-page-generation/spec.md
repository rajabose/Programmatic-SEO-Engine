# Spec: Landing Page Generation

**Status**: In Progress | **Priority**: High | **Branch**: `feature/landing-page-generation`

## Purpose
Generate demand-validated, SEO-optimised static pages on `discover.vanchai.in` that drive qualified traffic to Wix D2C, Amazon, Myntra, and Nykaa.

> **V1 reality check**: V1 (`vanchai-seo-engine/generate.py`) runs a product × keyword matrix without demand validation. This spec describes V2, which gates every page behind real search intent.

---

## User Stories

### US1 — Demand-Validated Page Generation (P1)
As the content pipeline, generate a landing page only for keyword-product pairs that pass demand validation (≥100 searches/month, distinct intent).

**Acceptance criteria**:
- Input: `KeywordProductPair` (pre-validated — search_volume, intent_type, product_id, platform_availability)
- Output: static HTML + full JSON-LD (Product, Offer, FAQ, Breadcrumb)
- Blocked if uniqueness check fails (>20% overlap with existing pages)
- SEO score ≥80 before approval
- Generation time <60s per page

### US2 — Quality-Gated Batch (P2)
As a content manager, run batch generation for a list of validated pairs — only pages that pass all gates get deployed; failures go to review queue.

**Acceptance criteria**:
- Input: `List[KeywordProductPair]` + `daily_limit` (default 100)
- Each page independently gated before deploy
- Review queue populated for single-gate failures
- Batch status endpoint shows approved / review_queue / blocked counts

### US3 — Platform CTAs (P2)
Each page links to product listings on all available platforms with UTM attribution.

**Acceptance criteria**:
- CTA links pre-built with UTM params per platform
- Link health check (HTTP 200) before page approval
- Out-of-stock platforms omitted from CTA section

### US4 — Content Freshness (P3)
Deployed pages reflect current pricing and availability.

**Acceptance criteria**:
- Price/availability from live catalog at generation time
- Pages flagged for regeneration when price changes >10% or goes out of stock
- `last_updated` timestamp updated on regeneration
- Out-of-stock pages: sitemap priority 0.3 (vs 0.8 in-stock)

---

## What NOT to generate

| Anti-pattern | Why blocked |
|---|---|
| Product × modifier matrix without demand validation | Creates doorway pages |
| Near-duplicate pages (same product, synonym keyword) | Duplicate content penalty |
| Keywords <100 searches/month | No meaningful traffic |
| Pages where all CTA platform links are unavailable | Broken user journey |
| More than one page targeting the same keyword | Keyword cannibalization |

---

## Data models

**Input**
```
KeywordProductPair:
  keyword, search_volume (≥100), intent_type (informational|transactional|navigational),
  product_id, product_name, category, unique_attributes[],
  platform_availability: {wix|amazon|myntra|nykaa: {url, price, currency, in_stock, utm_url}}
```

**Output**
```
GeneratedPage:
  page_id, keyword, slug, html, title (≤60 chars), meta_description (≤155 chars),
  canonical_url, schema_markup, seo_score (≥80 to pass), uniqueness_score (≤0.20),
  word_count, generation_time_ms, quality_gates_passed[],
  status: approved | review_queue | blocked
```

---

## Quality gates (all must pass before deploy)

| Gate | Threshold | On fail |
|------|-----------|---------|
| SEO score | ≥ 80/100 | Regenerate once, then review queue |
| Uniqueness | ≤ 20% overlap | Block + flag |
| Word count | ≥ 800 (informational) / product-complete (transactional) | Regenerate |
| Schema validity | Passes Rich Results Test | Block deploy |
| E-E-A-T signals | Brand, pub date, source present | Enforce in template |
| Platform links | All CTAs return HTTP 200 | Skip unavailable, alert on all-broken |
| Keyword density | < 3% | Regenerate |

---

## Services

| Service | Responsibility |
|---------|----------------|
| `DemandValidator` | Upstream — filters pairs before they reach this pipeline |
| `CatalogManager` | Product data + platform availability |
| `ContentGenerator` | OpenAI two-pass generation (see CG feature) |
| `QualityGate` | Enforces all 7 gates — not optional |
| `PageBuilder` | Jinja2 → optimised HTML, JSON-LD injection |
| `SchemaBuilder` | Product + Offer + FAQ + Breadcrumb JSON-LD |
| `DeployPipeline` | GitHub Pages commit or S3 + CloudFront upload |

---

## API endpoints

```
POST /api/v1/content/generate                    # single page
POST /api/v1/content/generate/batch             # queued batch
GET  /api/v1/content/batch/{id}/status
GET  /api/v1/content/review-queue
POST /api/v1/content/review-queue/{id}/approve
POST /api/v1/content/review-queue/{id}/discard
```

---

## Definition of done
- [ ] All quality gates implemented and enforced (not optional)
- [ ] Generation blocked without passing demand validation
- [ ] Full JSON-LD on every approved page
- [ ] Review queue functional for human decisions
- [ ] Deployed to staging with 10 sample validated pairs
- [ ] Pages pass Google Rich Results Test
- [ ] Code coverage ≥85%
