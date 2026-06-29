# Vanchai Programmatic SEO Engine

A demand-validated, quality-gated static page generator for [Vanchai](https://www.vanchai.in) — a sustainable Indian home decor brand. Pages are deployed to `discover.vanchai.in` via GitHub Pages at zero infra cost.

---

## How it works

```
Product XLSX catalogue
        ↓
xlsx_to_csv.py          → products.csv (113 products, CDN URL filtered)
        ↓
scripts/csv_to_sqlite.py → db/seo_engine.db (products table)
        ↓
scripts/demand_validator.py  → DataForSEO API (512 candidates: 8 categories × 64 modifiers)
                               only pairs with ≥100 searches/month → validated=1
        ↓
scripts/keyword_registry.py  → slug collision enforcement (first registered wins)
        ↓
generate.py --strict    → Claude Haiku draft → 7 quality gates → route
                          approved  → docs/     (served by GitHub Pages)
                          1 fail    → .seo-engine/review_queue.json
                          2+ fails  → .seo-engine/blocked.json
```

### 7 Quality Gates (every page must pass)

| Gate | Threshold |
|------|-----------|
| SEO score | ≥ 80 / 100 |
| Content uniqueness | ≤ 20% cosine similarity with existing pages |
| Keyword density | < 3% |
| Word count | ≥ 800w informational / ≥ 300w transactional |
| E-E-A-T signals | brand name + published date + platform mention |
| Platform link liveness | at least one live URL (Amazon / Myntra / Nykaa / Wix) |
| Rich results / JSON-LD | Product + FAQPage + BreadcrumbList schemas valid |

---

## Setup

```bash
cd vanchai-seo-engine
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic openpyxl
cp .env.example .env   # fill in ANTHROPIC_API_KEY + DataForSEO credentials
```

### Run the pipeline

```bash
# 1. Convert catalogue
python3 xlsx_to_csv.py ~/path/to/SEO-Automation-Product-catalogue.xlsx

# 2. Audit data quality
python3 check_data.py

# 3. Load into SQLite
python3 scripts/csv_to_sqlite.py

# 4. Validate keyword demand (costs ~$0.50 for 512 keywords)
python3 scripts/demand_validator.py

# 5. Register slugs
python3 scripts/keyword_registry.py --fix

# 6. Generate pages
python3 generate.py --strict

# 7. Rebuild sitemap
python3 generate_sitemap.py
```

### Test without API credits

```bash
python3 generate.py --strict --dry-run   # runs quality gates on placeholder content
```

---

## Project layout

```
vanchai-seo-engine/
├── generate.py              # core generator — strict mode only
├── generate_sitemap.py      # sitemap + robots.txt builder
├── generate_index.py        # category index + homepage
├── config.py                # brand, UTM, model, modifier constants
├── check_data.py            # pre-flight data quality auditor
├── xlsx_to_csv.py           # XLSX → products.csv converter
├── products.csv             # 113 active products (committed)
├── db/
│   ├── schema.sql           # SQLite schema (5 tables)
│   └── seo_engine.db        # committed — audit trail + demand data
├── scripts/
│   ├── csv_to_sqlite.py     # idempotent CSV → SQLite loader
│   ├── demand_validator.py  # DataForSEO volume check, 512 candidates
│   └── keyword_registry.py  # slug dedup — first registered wins
├── services/
│   ├── quality_gate.py      # QualityGate.run_all() — routes every page
│   ├── seo_scorer.py        # 0–100 SEO score
│   ├── uniqueness_checker.py # TF-IDF cosine similarity (stdlib only)
│   ├── keyword_density.py   # phrase-weighted density gate
│   ├── word_count_check.py  # informational vs transactional thresholds
│   ├── eeat_enforcer.py     # E-E-A-T signal checker
│   ├── link_checker.py      # HEAD request liveness check, 24h cache
│   ├── rich_results_validator.py  # JSON-LD field validation
│   ├── prompt_builder.py    # intent classifier + Claude prompt factory
│   └── content_generator.py # two-pass: Haiku draft → Sonnet fix
├── cache/
│   ├── keyword_volumes.json # DataForSEO cache (committed — avoid re-spend)
│   └── openai/              # Claude content cache per slug (gitignored)
├── .seo-engine/
│   ├── review_queue.json    # pages with 1 recoverable gate failure
│   └── blocked.json         # pages blocked by 2+ failures
└── docs/                    # GitHub Pages output → discover.vanchai.in
```

---

## Environment variables (`.env`)

```
ANTHROPIC_API_KEY=sk-ant-...        # Claude Haiku (draft) + Sonnet (fix pass)
DATAFORSEO_LOGIN=your@email.com     # keyword demand validation
DATAFORSEO_PASSWORD=your_password
```

---

## Spec-kit

All plans, specs, and tasks live in `.specify/`. See `.specify/README.md` for the full structure and reading order.

Active feature: **content-generation** (GitHub Pages v1 plan)
