# Feature Status: Landing Page Generation

**Feature Code**: LP  
**Branch**: `feature/landing-page-generation` → merging to `main`  
**Status**: ✅ V1 Live — iterating toward demand-validated V2  
**Last Updated**: 2026-04-26

---

## What's Running (Live Code)

| Script | Location | Purpose |
|--------|----------|---------|
| `generate.py` | `vanchai-seo-engine/generate.py` | Core engine: cross-joins products × keywords → static HTML pages |
| `config.py` | `vanchai-seo-engine/config.py` | Brand/UTM settings — single source of truth for site-wide variables |
| `generate_sitemap.py` | `vanchai-seo-engine/generate_sitemap.py` | Builds chunked XML sitemaps from `docs/` output |
| `generate_index.py` | `vanchai-seo-engine/generate_index.py` | Builds category index and homepage |
| `check_data.py` | `vanchai-seo-engine/check_data.py` | Validates CSV catalog before generation run |
| `xlsx_to_csv.py` | `vanchai-seo-engine/xlsx_to_csv.py` | Pre-processes product XLSX into generation-ready CSV |

**Output**: `vanchai-seo-engine/docs/` — static HTML served via GitHub Pages at `discover.vanchai.in`

---

## Current Strategy

### V1 (Live)
- Simple product × modifier matrix without demand validation
- ~13 pages generated from 1 product × keyword list
- Deployed to GitHub Pages as static HTML
- Jinja2-style string interpolation in Python (no real template engine yet)

### V2 Direction (Planned — see spec.md + plan.md)
- Demand-first: keyword-product pairs must pass ≥100 searches/month gate
- FastAPI + Celery + PostgreSQL stack replacing the single-script approach
- OpenAI GPT-4o-mini for content instead of pure templating
- Full JSON-LD schema (Product, Offer, FAQ, Breadcrumb) on every page
- Quality gates enforced before deploy

---

## Active Tasks

| Task | File | Status |
|------|------|--------|
| Initialize Python project | `tasks/TASK-LP-001-setup-python-project.md` | 🔲 Pending |
| Product catalog sync | `tasks/TASK-LP-002-product-catalog-sync.md` | 🔲 Pending |
| AI content generation service | `tasks/TASK-LP-003-content-generation-service.md` | 🔲 Pending |

---

## Key Decisions

- **Python over Node**: Python chosen for ML/data ecosystem (pandas, scrapy, openai SDK)
- **Static HTML output**: GitHub Pages hosting keeps costs at zero
- **Demand-first pivot**: V1 generated pages without validation — V2 blocks generation without real search volume
- **Quality gate = code, not process**: Gates enforced in `QualityGate` class, not reviewable steps

---

## Metrics to Watch
- Pages indexed by Google (track via GSC)
- Organic clicks on `discover.vanchai.in`
- % of generated pages that pass quality gates on first run
