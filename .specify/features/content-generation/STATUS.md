# Feature Status: Content Generation

**Feature Code**: CG  
**Branch**: `feature/content-generation` → merging to `main`  
**Status**: 🔲 Planning — not yet implemented  
**Last Updated**: 2026-04-26

---

## What's Running (Live Code)

None yet. Content generation is currently embedded inline in `vanchai-seo-engine/generate.py` as Python f-string templating — not a dedicated service.

**Proto-implementation** (in `generate.py`):
- Templates are hardcoded string interpolation — product name + keyword injected into HTML strings
- No OpenAI API calls yet
- No quality scoring or E-E-A-T enforcement

---

## Current Strategy

### V1 Approach (in generate.py today)
- Content = HTML template with `{product_name}` and `{keyword}` substitution
- One template for all pages — no intent differentiation
- No SEO scoring, no uniqueness check, no schema beyond basic meta tags

### Planned V2 Architecture (see spec.md + plan.md)
- Dedicated `ContentGenerator` service isolated from page builder
- OpenAI GPT-4o-mini for body copy, GPT-4o for quality validation pass
- Two-tier quality gate: auto-approve → review queue → blocked
- Full JSON-LD injection: Product + Offer + FAQ + Breadcrumb per page
- Uniqueness check against existing page corpus (cosine similarity ≤20%)
- Demand validation upstream — `ContentGenerator` never receives unvalidated pairs

---

## Active Tasks

| Task | File | Status |
|------|------|--------|
| Initialize project structure | `tasks/TASK-CG-001-setup-project.md` | 🔲 Pending |

---

## Key Decisions

- **Demand validation is upstream**: ContentGenerator receives only pre-validated `KeywordProductPair` objects — it never decides whether to generate a page
- **Quality gates are code, not config**: `QualityGate.run_all()` must be called before any page is approved; skipping it is not an option
- **Two-pass generation**: cheap model (4o-mini) generates, capable model (4o) validates — reduces cost while maintaining quality
- **Review queue not silent fail**: Pages that fail one recoverable gate go to human review, not discarded

---

## Dependencies
- Demand Validator (spec not yet created — blocks V2 start)
- Product Catalog Manager (`TASK-LP-002` in landing-page-generation feature)
- OpenAI API key configured in `.env`

---

## Metrics to Watch
- % of generated pages auto-approved vs. review queue vs. blocked
- Average SEO score per batch
- Generation time per page (target: <60s)
- Cost per page (target: ~₹0.15 with GPT-4o-mini)
