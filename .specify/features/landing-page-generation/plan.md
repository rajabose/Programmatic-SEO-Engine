# Plan: Landing Page Generation (Python Stack)

**Spec**: [spec.md](spec.md) | **Sprint**: 1–6 (6 weeks) | **Output**: demand-validated pages on `discover.vanchai.in`

---

## Phase 1 — Foundation (Week 1)

**Goal**: Runnable FastAPI app, DB + Redis, health check.

| Day | Task | Ticket |
|-----|------|--------|
| 1-2 | Poetry project, FastAPI, SQLAlchemy, Redis, Docker Compose | TASK-LP-001 |
| 3-4 | Product, Category, LandingPage, Job SQLAlchemy models + Alembic migrations | TASK-LP-002 |
| 5 | Celery setup, health endpoint, test suite skeleton | TASK-LP-001 |

**Exit criteria**: `docker-compose up` → all services healthy, `pytest` green.

---

## Phase 2 — Data Layer (Week 2)

**Goal**: Unified product catalog synced from all platforms.

| Day | Task | Ticket |
|-----|------|--------|
| 1-2 | Wix + Amazon platform clients (async httpx) | TASK-LP-002 |
| 3-4 | Myntra scraper + Nykaa client | TASK-LP-002 |
| 5 | `CatalogManager` service — dedup, sync log, stats endpoint | TASK-LP-002 |

**Exit criteria**: `POST /catalog/sync/wix` fetches and persists ≥1 product without duplicates on re-run.

---

## Phase 3 — Demand Validation (Week 3)

**Goal**: No page is generated without a keyword that passes the demand gate.

| Component | Detail |
|-----------|--------|
| `DemandValidator` | Calls keyword API (Ahrefs / DataForSEO), caches 24h in Redis |
| Gate | ≥100 searches/month AND distinct intent (dedup synonyms) |
| `KeywordProductPair` | Output model — only pairs that passed validation enter generation |
| DB table | `keyword_pairs` — stores validated pairs with volume + intent |

**Exit criteria**: Validated pairs table populated; unvalidated input rejected with 422.

---

## Phase 4 — Content Generation (Week 4)

**Goal**: Quality-gated HTML pages from validated pairs.

| Component | Detail |
|-----------|--------|
| `ContentGenerator` | GPT-4o-mini draft → GPT-4o quality pass → `QualityGate.run_all()` |
| Quality gates | SEO ≥80, uniqueness ≤20%, schema valid, links live, E-E-A-T present |
| Output routing | approved / review_queue / blocked |
| Batch API | `POST /content/generate/batch`, configurable daily limit (default 100) |

**Exit criteria**: Single page generated <60s, all 7 quality gates exercised in tests.  
**Ticket**: TASK-LP-003

---

## Phase 5 — Page Builder & Deploy (Week 5)

**Goal**: Static HTML with full schema + Core Web Vitals, deployed to GitHub Pages / S3.

| Component | Detail |
|-----------|--------|
| `PageBuilder` | Jinja2 → optimised HTML; LCP <2.5s, CLS <0.1 |
| JSON-LD | Product + Offer + FAQ + Breadcrumb on every page |
| UTM links | Pre-built per platform on all CTA links |
| Deploy | GitHub Actions → `docs/` commit (GitHub Pages) or S3 + CloudFront |
| Sitemap | Auto-updated; out-of-stock pages priority 0.3 |

**Exit criteria**: 10 approved pages live on `discover.vanchai.in`, passing Google Rich Results Test.

---

## Phase 6 — Monitoring & Prune (Week 6)

**Goal**: Continuous quality signal; prune pages that don't earn traffic.

| Component | Detail |
|-----------|--------|
| GSC integration | Fetch clicks, impressions, rank daily via API |
| 90-day prune queue | Pages with 0 clicks after 90 days → review (improve or delete) |
| Price freshness | Re-generate if product price changes >10% or goes out of stock |
| Merchant Center feed | Auto-generated XML alongside sitemaps |

**Exit criteria**: GSC dashboard shows indexed pages and first organic clicks.

---

## Stack reference

| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| API | FastAPI + Uvicorn |
| Task queue | Celery + Redis |
| DB | PostgreSQL + SQLAlchemy + Alembic |
| Templates | Jinja2 |
| LLM | OpenAI GPT-4o-mini (gen) + GPT-4o (validation) |
| Hosting | GitHub Pages (static) or S3 + CloudFront |
| Monitoring | Google Search Console API |

---

## Risks

| Risk | Mitigation |
|------|-----------|
| OpenAI rate limits | Request queue + Redis token-bucket limiter |
| Platform API changes | Abstraction layer per client; monitor for 4xx spikes |
| Google algorithm update changes quality thresholds | Constitution v2 review cycle; gates are configurable in config |
| Demand data staleness | Re-validate pairs every 90 days |
