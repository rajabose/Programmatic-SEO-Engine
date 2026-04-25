# Spec: Content Generation

## Feature Overview
**Name**: Content Generation  
**Branch**: `feature/content-generation`  
**Status**: Revised  
**Priority**: High  
**Owner**: Development Team  
**Depends on**: Demand Validator, Product Catalog Manager, Uniqueness Checker

---

## Purpose
Generate SEO landing pages that are individually justified by real search demand, contain genuinely unique product data, comply with Google's Helpful Content guidelines, and are structured for agentic shopping experiences. Pages are not generated in bulk from a matrix — they are generated one-by-one for validated keyword-product pairs only.

---

## User Stories

### Story 1: Demand-Validated Single Page Generation
As a content pipeline, I want to generate a landing page only after a keyword-product pair has passed demand validation, so that every deployed page has real search intent behind it.

**Acceptance Criteria:**
- Input: validated `KeywordProductPair` object (search_volume ≥100, intent_type, product_id)
- Output: fully formed HTML page with schema markup
- Blocked if: uniqueness check fails (>20% overlap with existing pages)
- Generation time: <60 seconds per page
- SEO score: ≥80/100 before the page is accepted

### Story 2: Quality-Gated Batch Generation
As a content manager, I want to run batch generation for a catalog of validated keyword-product pairs, with automatic quality gates, so that only pages that pass all checks are deployed.

**Acceptance Criteria:**
- Input: list of validated `KeywordProductPair` objects
- Each page passes all quality gates independently before deployment
- Failed pages go to a review queue, not deployed silently
- Progress tracking per batch
- Daily generation budget: configurable (default: 100 pages/day to stay under token budget)

### Story 3: Agentic Shopping Content Structure
As a landing page, I need to be structured so that AI shopping agents (Google AI Overviews, Perplexity, Amazon Rufus) can extract product information accurately, so that the brand appears in agentic search results.

**Acceptance Criteria:**
- Full Product JSON-LD: name, brand, SKU, price, currency, availability, condition, image, description
- Offer schema: per-platform pricing and availability where available
- FAQ JSON-LD: 3-5 conversational questions matching natural language shopping queries
- Breadcrumb schema reflecting category hierarchy
- Passes Google Rich Results Test with zero errors

### Story 4: E-E-A-T Signal Enforcement
As a content page, I need to demonstrate Experience, Expertise, Authoritativeness, and Trustworthiness signals so that Google's quality systems do not classify the page as unhelpful.

**Acceptance Criteria:**
- Brand name and source platform prominently identified
- Publication date and last-updated date present in page and schema
- Product sourced from verified catalog with real attributes (price, specs, images)
- No keyword-stuffed headings — content answers real user questions
- Content mentions product in context of real use cases, not just lists attributes

### Story 5: Content Freshness
As a deployed page, I need to reflect current pricing, availability, and inventory status so that users and AI agents receive accurate information.

**Acceptance Criteria:**
- Price and availability pulled from live catalog at generation time
- Pages flagged for regeneration when product price changes >10% or goes out of stock
- "Last updated" timestamp updated on regeneration
- Out-of-stock pages deprioritized in sitemap (priority: 0.3 vs 0.8 for in-stock)

---

## What NOT to Generate (Anti-Patterns)

These patterns are explicitly blocked. They produce Google penalties or wasted spend:

| Anti-Pattern | Why Blocked |
|---|---|
| Product × modifier matrix without demand validation | Creates doorway pages; Google penalizes |
| Near-duplicate pages (same product, synonym keyword) | Duplicate content penalty; dilutes domain |
| Pages for keywords <100 searches/month | No meaningful traffic; wastes crawl budget |
| Pages without real product data (just AI filler) | Thin content; fails Helpful Content system |
| More than one page targeting the same keyword | Keyword cannibalization; pages compete against each other |
| Pages where the CTA platform link is unavailable | Broken user journey; hurts conversion and trust |

---

## Content Structure Per Page

### Informational Intent (e.g. "best boho wall decor ideas")
```
H1: Keyword-matched, natural language
Introduction (100 words): confirms user intent, sets up the article
Product context section (200 words): what makes this product relevant to the query
Use case / styling section (200 words): real-world application, E-E-A-T
Product specifications (structured list): material, dimensions, weight, care
Buying section: platform CTAs with price, availability
FAQ (3 questions): conversational, schema-marked
Internal links: 2-3 related category or product pages
```

### Transactional Intent (e.g. "buy pampas grass decor online")
```
H1: Keyword-matched, includes brand or product type
Product hero: image, title, price range, availability badges
Key attributes (structured specs): the facts a buyer needs
Platform options: Wix D2C (primary) + Amazon + Myntra + Nykaa with prices
Why this product: 150-word buying justification, not generic filler
FAQ (3 questions): buying-specific (shipping, returns, sizing)
Related products: 3 internal links to similar SKUs
```

---

## Technical Specification

### Input Model
```python
class KeywordProductPair(BaseModel):
    keyword: str                    # validated, ≥100 searches/month
    search_volume: int              # monthly searches
    intent_type: Literal["informational", "transactional", "navigational"]
    product_id: str                 # links to Product in catalog
    product_name: str
    category: str
    unique_attributes: list[str]    # attributes that differentiate this page
    platform_availability: dict[str, PlatformListing]  # wix, amazon, myntra, nykaa
    
class PlatformListing(BaseModel):
    url: str
    price: float
    currency: str = "INR"
    in_stock: bool
    utm_url: str                    # pre-built UTM link
```

### Output Model
```python
class GeneratedPage(BaseModel):
    page_id: str
    keyword: str
    slug: str                       # URL slug derived from keyword
    html: str                       # full static HTML
    title: str                      # <title> tag content
    meta_description: str           # ≤155 characters
    canonical_url: str
    schema_markup: dict             # JSON-LD payload
    seo_score: int                  # must be ≥80 to pass
    uniqueness_score: float         # must be ≤0.20 overlap
    word_count: int
    generation_time_ms: int
    quality_gates_passed: list[str]
    status: Literal["approved", "review_queue", "blocked"]
```

### API Endpoints
```yaml
POST /api/v1/content/generate
  Description: Generate one page for a validated keyword-product pair
  Request: KeywordProductPair
  Response: GeneratedPage

POST /api/v1/content/generate/batch
  Description: Queue batch generation for a list of validated pairs
  Request:
    pairs: list[KeywordProductPair]
    daily_limit: int (default: 100)
  Response:
    batch_id: string
    total_pairs: int
    estimated_completion: datetime

GET /api/v1/content/batch/{batch_id}/status
  Response:
    approved: int
    review_queue: int
    blocked: int
    in_progress: int
    results: list[GeneratedPage summary]

GET /api/v1/content/review-queue
  Description: Pages that failed one quality gate and need human decision
  Response: list[GeneratedPage with gate_failures]

POST /api/v1/content/review-queue/{page_id}/approve
POST /api/v1/content/review-queue/{page_id}/discard
```

### Generation Prompt Design
The prompt is structured to enforce Helpful Content principles, not just SEO:

```python
GENERATION_PROMPT = """
You are writing a landing page for {brand_name}, a D2C home decor brand.

Product: {product_name}
Category: {category}
Target keyword: {keyword}
User intent: {intent_type}
Unique attributes of this product: {unique_attributes}

Guidelines:
- Write for the user first, not for search engines
- Answer the real question behind the keyword
- Use the product's actual attributes — do not invent specifications
- Mention real use cases, not generic filler phrases
- Do not repeat the keyword more than once per paragraph
- Avoid phrases like "in today's world", "look no further", or "perfect for anyone"
- Content must be distinct from a page about {similar_product_name} — 
  differentiate by: {differentiating_factors}

Output:
- title (max 60 characters)
- meta_description (max 155 characters)  
- h1 (natural, keyword-inclusive)
- body (structured per intent_type template)
- faq (3 questions + answers, conversational tone)
"""
```

---

## Quality Gates (Enforced in Code, Not Optional)

```python
class QualityGate:
    def run_all(self, page: GeneratedPage, existing_pages: list[str]) -> GateResult:
        gates = [
            self.check_seo_score(page),           # ≥80
            self.check_uniqueness(page, existing_pages),  # ≤20% overlap
            self.check_word_count(page),           # ≥800 informational, product-complete transactional
            self.check_schema_validity(page),      # Google Rich Results Test API
            self.check_eeat_signals(page),         # brand, date, source present
            self.check_platform_links(page),       # all CTA URLs return 200
            self.check_keyword_density(page),      # no keyword stuffing (<3%)
        ]
        
        failures = [g for g in gates if not g.passed]
        
        if len(failures) == 0:
            return GateResult(status="approved")
        elif len(failures) == 1 and failures[0].recoverable:
            return GateResult(status="review_queue", failures=failures)
        else:
            return GateResult(status="blocked", failures=failures)
```

---

## Agency Process Context

Traditional SEO agencies charge ₹30,000–₹1,50,000/month for content workflows that:
- Take 2-4 weeks to produce 20–40 articles
- Often skip schema markup and agentic readiness
- Rarely validate keyword demand before assigning briefs
- Don't enforce uniqueness gates — writers produce similar content for similar keywords

**This engine's advantage**: page count grows from validated (product × long-tail keyword) combinations, not from an arbitrary SKU threshold. A 10-product catalog with 50 validated long-tail keywords can produce 200+ justified pages. Quality-gated pages consistently outperform a large thin-content site and avoid the Helpful Content penalty that has wiped out many D2C brands' organic traffic since 2023.

---

## Dependencies
- Demand Validator service (upstream, must run first)
- Product Catalog Manager (product data source)
- Uniqueness Checker (cosine similarity against existing page corpus)
- OpenAI API (GPT-4o-mini for generation, GPT-4o for quality check)
- Google Rich Results Test API (schema validation)
- SEO scoring library (internal)

## Risks & Mitigation

| Risk | Mitigation |
|---|---|
| OpenAI generates content that fails quality gates | Two-pass: generate with 4o-mini, validate with 4o; retry once before human queue |
| Google algorithm update changes what "helpful" means | Monthly constitution review; quality gate thresholds adjustable in config |
| Demand data is stale (seasonal products) | Re-validate demand every 90 days; prune or refresh pages below threshold |
| Platform URLs break after page is live | Weekly link health check; auto-update or flag for review |
| Schema markup rejected by Google | Validate before deploy using Rich Results Test API; block deploy on failure |

## Definition of Done
- [ ] All quality gates implemented and enforced (not optional)
- [ ] Generation blocked without passing demand validation
- [ ] Full JSON-LD schema on every page (Product + Offer + FAQ + Breadcrumb)
- [ ] Review queue UI for human decisions on borderline pages
- [ ] API endpoints tested with both passing and failing inputs
- [ ] Performance: <60s per page generation
- [ ] Documentation updated
- [ ] Deployed to staging with sample validated pairs

## Related Specs
- Demand Validation Spec (new — to be created)
- Product Catalog Spec
- SEO Scoring Spec
- Merchant Center Feed Spec (new — to be created)
