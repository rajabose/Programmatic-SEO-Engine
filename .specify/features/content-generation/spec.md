# Spec: Content Generation

**Status**: Planning | **Priority**: High | **Branch**: `feature/content-generation`  
**Depends on**: Demand Validator → Product Catalog Manager → Uniqueness Checker

## Purpose
Generate SEO pages justified by real search demand, containing unique product data, compliant with Google Helpful Content guidelines, and structured for AI shopping agents. Pages are generated one-by-one for validated pairs — never bulk from a matrix.

---

## User Stories

### US1 — Demand-Validated Single Page (P1)
Generate a landing page only after a `KeywordProductPair` passes demand validation.

**Acceptance criteria**:
- Input: validated pair (search_volume ≥100, intent_type, product_id, unique_attributes, platform_availability)
- Output: HTML + full JSON-LD (Product, Offer, FAQ, Breadcrumb)
- Blocked if uniqueness >20% overlap with existing pages
- SEO score ≥80 required before approval
- Generation time <60s

### US2 — Quality-Gated Batch (P2)
Batch generation with per-page quality gates; failures go to review queue, not silent deploy.

**Acceptance criteria**:
- `daily_limit` configurable (default 100)
- Batch status: approved / review_queue / blocked counts
- Review queue populated for single-gate failures

### US3 — Agentic Shopping Structure (P2)
Pages structured so AI shopping agents (Google AI Overviews, Perplexity, Rufus) extract product info accurately.

**Acceptance criteria**:
- Full Product JSON-LD: name, brand, SKU, price, availability, condition, image
- Offer schema per-platform where available
- FAQ JSON-LD: 3-5 conversational questions
- Breadcrumb schema
- Passes Google Rich Results Test with zero errors

### US4 — E-E-A-T Enforcement (P2)
Pages demonstrate Experience, Expertise, Authoritativeness, Trustworthiness.

**Acceptance criteria**:
- Brand name, publication date, source platform present in page + schema
- Product attributes from verified catalog (no invented specs)
- Content answers real user questions, not keyword-stuffed headings

### US5 — Content Freshness (P3)
Deployed pages reflect current pricing and availability.

**Acceptance criteria**:
- Price/availability from live catalog at generation time
- Regeneration triggered when price changes >10% or goes out of stock
- Out-of-stock: sitemap priority 0.3 (vs 0.8 in-stock)

---

## Anti-patterns (blocked)

| Pattern | Why |
|---------|-----|
| Matrix without demand validation | Doorway pages → Google penalty |
| Near-duplicate pages (synonym keywords) | Duplicate content penalty |
| Keywords <100 searches/month | No meaningful traffic |
| AI filler without real product data | Fails Helpful Content system |
| Multiple pages targeting same keyword | Cannibalization |
| Page with all CTA links unavailable | Broken user journey |

---

## Content structure

**Informational** (`"best boho wall decor ideas"`):  
H1 → Intro (100w) → Product context (200w) → Use case/styling (200w) → Specs list → Platform CTAs → FAQ (3q) → Internal links

**Transactional** (`"buy pampas grass decor online"`):  
H1 → Product hero (image, price, availability) → Key attributes → Platform options (Wix primary + others) → 150w buying justification → FAQ (3q, buying-specific) → Related products (3 links)

---

## Data models

**Input**
```
KeywordProductPair:
  keyword, search_volume (≥100), intent_type, product_id, product_name, category,
  unique_attributes[], platform_availability {wix|amazon|myntra|nykaa: url, price, in_stock, utm_url}
```

**Output**
```
GeneratedPage:
  page_id, keyword, slug, html, title (≤60), meta_description (≤155),
  canonical_url, schema_markup, seo_score (≥80), uniqueness_score (≤0.20),
  word_count, generation_time_ms, quality_gates_passed[],
  status: approved | review_queue | blocked
```

---

## Quality gates

| Gate | Threshold |
|------|-----------|
| SEO score | ≥ 80/100 |
| Uniqueness | ≤ 20% overlap |
| Word count | ≥ 800 info / product-complete transactional |
| Schema validity | Google Rich Results Test: zero errors |
| E-E-A-T | brand, pub date, source present |
| Platform links | CTA URLs return HTTP 200 |
| Keyword density | < 3% |

Routing: 0 failures → `approved` / 1 recoverable failure → `review_queue` / else → `blocked`

---

## Generation prompt principles
- Write for user first, not search engines
- Use actual product attributes — never invent specs
- Mention real use cases, not filler phrases
- ≤1 keyword per paragraph
- Avoid: "in today's world", "look no further", "perfect for anyone"

---

## Dependencies
- Demand Validator (upstream gate — must run first)
- Product Catalog Manager (product data)
- Uniqueness Checker (cosine similarity vs existing pages)
- OpenAI: GPT-4o-mini (generation) + GPT-4o (quality pass)
- Google Rich Results Test API

---

## Definition of done
- [ ] All 7 quality gates enforced in code — not optional
- [ ] Generation blocked without demand-validated input
- [ ] Full JSON-LD on every approved page
- [ ] Review queue functional
- [ ] Staging: 10 sample pairs end-to-end
- [ ] <60s per page, ≥85% test coverage
