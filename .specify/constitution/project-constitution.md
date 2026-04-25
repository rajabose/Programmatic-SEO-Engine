# Vanchai Programmatic SEO Engine - Project Constitution

## Vision
Build a demand-validated, quality-first programmatic SEO engine that generates only pages with proven search intent, complies with Google's Helpful Content guidelines, and is structured for agentic shopping experiences — driving qualified traffic to Wix D2C, Amazon, Myntra, and Nykaa platforms.

---

## Why Programmatic SEO Must Earn Its Pages

Generating thousands of pages from a product × modifier matrix is a token waste and an SEO liability. Google's Helpful Content system actively demotes sites where a large proportion of content exists to rank, not to help. Thin, templated pages with no unique data produce:

- Duplicate content penalties
- Index bloat that dilutes domain authority
- Wasted crawl budget on low-value URLs
- No real user or AI agent value

**Rule**: Every generated page must justify its existence with distinct search demand and unique data. No page is created without a validated long-tail keyword and real product differentiation.

**How page count is determined**: Pages are not counted from SKUs alone. Page count = the number of valid (product × long-tail keyword) combinations that pass demand validation. A 10-product catalog with 50 validated long-tail keywords can justify 200+ pages if each combination has distinct intent and real search volume. A 1,000-product catalog with only 5 relevant keywords justifies 5,000 pages at most. The keyword side of the equation matters as much as the product side.

---

## Core Principles

### 1. Demand-First Generation
- Only generate pages for long-tail keywords with verified search volume (≥100 searches/month)
- Page count = valid (product × long-tail keyword) pairs that pass demand validation — no fixed SKU threshold
- Use real data sources: Google Search Console, Ahrefs, SEMrush, Google Keyword Planner
- No page is created from a modifier matrix without demand validation
- Each keyword must represent a distinct user intent — synonyms and near-duplicates are deduplicated before generation

### 2. Content Differentiation
- Each landing page must have ≥3 unique data points compared to sibling pages
  (e.g. different product specs, price tier, use case, material, customer reviews)
- Duplicate or near-duplicate pages are blocked before generation
- Content similarity check against existing pages: max 20% overlap

### 3. Google Helpful Content Compliance
- Content must answer the user's query, not just contain the keyword
- E-E-A-T signals required: brand identity, product expertise, author/source signals
- No doorway pages: every page must have standalone value beyond just ranking
- Content length appropriate to query intent (informational: 800+ words, transactional: product data + buying context)
- Follow Google's product review guidelines: real attributes, comparison context, pros/cons where applicable

### 4. Agentic Shopping Readiness
- Pages must be structured for AI shopping agents (Google AI Overviews, Perplexity, Amazon Rufus, future agents)
- Full Product JSON-LD schema: name, brand, SKU, price, availability, condition, image, reviews, specifications
- Offer schema with platform-specific pricing and availability
- Conversational FAQ JSON-LD that mirrors natural language queries AI agents receive
- Google Merchant Center compatible data feed for shopping graph inclusion
- Breadcrumb and SiteNavigation schema for contextual understanding

### 5. Platform Integration
- Drive qualified traffic (not raw traffic) to Wix D2C, Amazon, Myntra, Nykaa
- UTM parameters on all outbound links for attribution tracking
- Platform-specific CTAs based on product availability and pricing
- No broken platform links: availability checked before page is published

### 6. Technical Excellence
- Python 3.10+ as core language
- Static HTML output served from GitHub Pages or S3 + CloudFront
- Page load time <2s (Core Web Vitals: LCP, CLS, FID)
- Mobile-first templates
- Automated quality gate before any page is deployed

---

## Architecture Overview

### Revised Data Flow
```
Search Demand Data (GSC / Keyword API)
  → Demand Validation Gate (≥100 searches/month, distinct intent)
        ↓ Pass
  Product Catalog (500+ SKUs)
  → Attribute Mapping (category, spec, price tier, use case)
  → Keyword ↔ Product Matching (only genuine combinations)
  → Uniqueness Check (block near-duplicates)
        ↓ Pass
  Content Generation (OpenAI — quality-gated prompt)
  → SEO Scoring (>80/100 required)
  → Helpful Content Check (E-E-A-T, doorway page signals)
  → Schema Markup (Product, Offer, FAQ, Breadcrumb)
        ↓ Pass all gates
  Static Page Build (Jinja2 → HTML)
  → Deployment to discover.vanchai.in
  → Sitemap + Merchant Center feed update
  → Google Search Console monitoring
  → Pages that don't rank in 90 days → review queue (prune or improve)
```

### Key Components
1. **Demand Validator**: Filters keyword-product pairs to only those with real search intent
2. **Product Catalog Manager**: Unified catalog from Wix, Amazon, Myntra, Nykaa — minimum 500 SKUs
3. **Uniqueness Checker**: Blocks near-duplicate pages before generation
4. **Content Generator**: OpenAI-powered generation with quality-gated prompts
5. **SEO + Compliance Engine**: Scoring, E-E-A-T signals, doorway page detection
6. **Schema Builder**: Full Product/Offer/FAQ/Breadcrumb JSON-LD
7. **Page Builder**: Static HTML with Core Web Vitals optimization
8. **Deployment Pipeline**: GitHub Pages / S3 + CloudFront
9. **Performance Monitor**: GSC integration, rank tracking, prune queue

---

## Agency Process Benchmarks

### Standard Agency Workflow (What We're Automating)

Agencies follow a repeatable 8-step workflow. This engine automates or enhances each step:

| Step | Task | Agency Tools | This Engine |
|---|---|---|---|
| 1 | Keyword Research | Ahrefs, SEMrush, Google Keyword Planner | Automated demand validation via API — hours not weeks |
| 2 | Data Collection | Airtable, Google Sheets, Clay (scraping) | Product catalog sync from Wix, Amazon, Myntra, Nykaa |
| 3 | Database Building | Airtable, Google Sheets | PostgreSQL product + keyword pair database |
| 4 | Template Design | Webflow, WordPress CMS | Jinja2 static templates with intent-specific layouts |
| 5 | Content Generation | OpenAI GPT-4, Claude, Perplexity, SEOmatic | GPT-4o-mini with quality-gated prompts |
| 6 | Image Generation | DALL-E 3, Midjourney, Bannerbear | Product images from catalog; DALL-E 3 for missing images |
| 7 | Publishing | Zapier, Make.com (automation to CMS) | Direct deploy to GitHub Pages / S3 + CloudFront |
| 8 | Analytics / Indexing | Google Search Console | GSC integration — rank tracking, prune queue, 90-day review |

### Where This Engine Beats Agency Workflow

| Dimension | Agency | This Engine |
|---|---|---|
| Speed | 1-3 days/article | Minutes/page |
| Cost | ₹1,500–₹8,000/article | ~₹0.15/page (GPT-4o-mini) |
| Schema markup | Often skipped | Full Product + Offer + FAQ JSON-LD, every page |
| Demand validation | Done manually, often skipped | Gate before generation — no unvalidated page created |
| Merchant Center feed | Separate manual process | Auto-generated alongside pages |
| Quality gate | Human editor (subjective) | Automated score gates + human spot-check queue |
| Performance review | Monthly report | Continuous GSC monitoring, 90-day prune cycle |

### What Agencies Do That This Engine Must Also Match
- **Topical authority**: Category hub pages (pillar), not just product leaf pages
- **Internal linking**: Pillar → cluster architecture, not just sitemap links
- **Content freshness**: Price updates, review counts, availability reflected in pages
- **Competitor gap analysis**: Identify keywords competitors rank for that we don't have pages for

---

## Quality Gates (All Must Pass Before Publish)

| Gate | Threshold | Action on Fail |
|---|---|---|
| Search demand | ≥100 searches/month | Skip page, log to unmet-demand queue |
| Content uniqueness | ≤20% overlap with existing pages | Block, flag for manual review |
| SEO score | ≥80/100 | Regenerate once, then human queue |
| Content length | ≥800 words (informational), product data complete (transactional) | Regenerate |
| E-E-A-T signals | Brand name, product source, publication date present | Enforce in template |
| Schema validity | Passes Google Rich Results Test | Block deploy |
| Core Web Vitals | LCP <2.5s, CLS <0.1 | Optimize before deploy |
| Broken links | Zero broken platform URLs | Skip, alert |

---

## Success Metrics (Revised)

### Quality Over Quantity
- **Target pages**: Only demand-validated pages — quality floor, no arbitrary count target
- **Index ratio**: ≥80% of published pages indexed by Google within 30 days
- **Helpful Content signal**: Zero manual actions or algorithmic downgrades
- **Content uniqueness**: ≥90% across all published pages

### Search Performance
- **Keyword ranking**: ≥30% of target keywords reach top 20 within 90 days
- **Organic clicks**: Measurable via Google Search Console monthly
- **Click-through rate**: ≥3% average for ranked pages
- **Bounce rate**: ≤45% (signal of content relevance)

### Agentic Shopping
- **Rich result eligibility**: 100% of pages pass Google Rich Results Test
- **Merchant Center**: Product feed live and approved
- **AI Overview appearances**: Track via GSC search appearance filters
- **Schema coverage**: Product + Offer + FAQ on 100% of pages

### Platform Conversion
- **Traffic to Wix D2C**: Measurable via UTM attribution
- **Cross-platform clicks**: Amazon, Myntra, Nykaa UTM tracked
- **Conversion rate**: ≥2% click-to-platform from landing page

### Technical
- **Page load time**: <2 seconds (LCP)
- **Core Web Vitals**: All green
- **API uptime**: 99.9%
- **Python code coverage**: ≥85%

---

## Governance

### Decision Making
- **Page generation decisions**: Demand Validator must pass — not overridable without explicit override log
- **Technical decisions**: Lead Developer
- **Feature prioritization**: Product Owner
- **Architecture changes**: Team consensus

### Review Process
- All specs require peer review
- Constitution changes require team approval
- Monthly performance review: prune pages not gaining traction after 90 days
- Quarterly audit of quality gate thresholds vs Google algorithm updates

### Documentation
- Keep specs in sync with implementation
- Update constitution when Google guidelines change
- Version control all specifications and templates

---

**Constitution Version**: 2.0.0
**Last Updated**: 2026-04-24
**Supersedes**: v1.0.0 (product × modifier matrix approach, arbitrary 13,000 page target)
**Approved By**: Development Team
