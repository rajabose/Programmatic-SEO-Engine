#!/usr/bin/env python3
"""
generate.py — Vanchai Programmatic SEO Engine
=============================================
Reads the product catalogue CSV, cross-joins every product with
intent modifiers, calls Claude (Haiku for drafts, Sonnet for fixes)
to generate a unique article per page, then writes production-ready
HTML files to the OUTPUT_DIR directory.

Usage:
    python generate.py                        # generate all pages (legacy modifier matrix)
    python generate.py --strict               # demand-validated pairs only (recommended)
    python generate.py --batch 1              # generate batch 1 (0-499)
    python generate.py --batch 2              # generate batch 2 (500-999)
    python generate.py --dry-run --limit 5    # test 5 pages without Claude API

--strict mode requires:
    1. python scripts/csv_to_sqlite.py
    2. python scripts/demand_validator.py
    3. python scripts/keyword_registry.py --fix
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic as _anthropic

from services.quality_gate import QualityGate
from services.prompt_builder import classify_intent, BRAND_VOICE, ANTI_FILLER
from services.content_generator import _load_cache as _load_content_cache, _save_cache as _save_content_cache

from config import (
    BRAND_NAME, BRAND_DOMAIN, DISCOVER_DOMAIN,
    UTM_SOURCE, UTM_MEDIUM, UTM_CAMPAIGN,
    CLAUDE_DRAFT_MODEL, CLAUDE_VALIDATE_MODEL, CLAUDE_MAX_TOKENS,
    OUTPUT_DIR, BATCH_SIZE, INTENT_MODIFIERS, BRAND_VOICE, CSV_FILE,
)

# Module-level client — initialised in main() after key is validated
_claude: _anthropic.Anthropic | None = None

DB_PATH           = Path(__file__).parent / "db" / "seo_engine.db"
REVIEW_QUEUE_PATH = Path(__file__).parent / ".seo-engine" / "review_queue.json"
BLOCKED_PATH      = Path(__file__).parent / ".seo-engine" / "blocked.json"

def slugify(text: str) -> str:
    """Convert arbitrary text into a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:120]  # cap at 120 chars


def utm(url: str, content: str = "") -> str:
    """Append UTM parameters to a marketplace URL."""
    if not url or url in ("NA", "N/A", ""):
        return ""
    sep = "&" if "?" in url else "?"
    params = (
        f"utm_source={UTM_SOURCE}"
        f"&utm_medium={UTM_MEDIUM}"
        f"&utm_campaign={UTM_CAMPAIGN}"
    )
    if content:
        params += f"&utm_content={slugify(content)}"
    return f"{url}{sep}{params}"


def build_product_json_ld(product: dict) -> str:
    """Build a valid Product JSON-LD from clean CSV fields.

    The source spreadsheet's json_ld column contains unescaped quote characters
    embedded in product-name strings (e.g. 'Tail Cone"- Set of 5'), which makes
    the raw JSON unparseable. Building the schema from scratch from the individual
    clean fields guarantees a valid, injectable JSON-LD on every page.
    """
    name     = product.get("vendorArticleName", "").strip()
    sku      = product.get("vendorArticleNumber", "").strip()
    desc     = product.get("productDetails", "").strip()[:500]
    img_url  = product.get("imageUrl", "").strip()
    price    = product.get("price", "").strip()
    wix_url  = product.get("wixUrl", "").strip()

    if not name:
        return ""

    schema: dict = {
        "@context": "https://schema.org/",
        "@type":    "Product",
        "name":     name,
        "brand":    {"@type": "Brand", "name": BRAND_NAME},
    }

    if sku and sku not in ("N/A", ""):
        schema["sku"] = sku
    if desc:
        schema["description"] = desc
    if img_url and img_url != "No Image URL":
        schema["image"] = img_url

    if wix_url:
        offer: dict = {
            "@type":        "Offer",
            "url":          wix_url,
            "priceCurrency": "INR",
            "availability": "https://schema.org/InStock",
            "seller":       {"@type": "Organization", "name": BRAND_NAME,
                             "sameAs": BRAND_DOMAIN},
        }
        if price:
            try:
                offer["price"] = str(float(price))
            except ValueError:
                pass
        schema["offers"] = offer

    try:
        return json.dumps(schema, ensure_ascii=False)
    except Exception:
        return ""


def build_faqpage_json_ld(faq_items: list[dict]) -> str:
    """Build FAQPage JSON-LD from a list of {question, answer} dicts."""
    if not faq_items:
        return ""
    entities = [
        {
            "@type": "Question",
            "name": item.get("question", ""),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.get("answer", ""),
            },
        }
        for item in faq_items
        if item.get("question") and item.get("answer")
    ]
    if not entities:
        return ""
    schema = {
        "@context": "https://schema.org",
        "@type":    "FAQPage",
        "mainEntity": entities,
    }
    try:
        return json.dumps(schema, ensure_ascii=False)
    except Exception:
        return ""


def build_breadcrumb_json_ld(
    keyword: str,
    category: str,
    category_url: str,
    page_url: str,
) -> str:
    """Build BreadcrumbList JSON-LD: Home → Category → Page."""
    category_label = category.replace("_", " ").title() if category else "Collection"
    schema = {
        "@context": "https://schema.org",
        "@type":    "BreadcrumbList",
        "itemListElement": [
            {
                "@type":    "ListItem",
                "position": 1,
                "name":     "Home",
                "item":     BRAND_DOMAIN,
            },
            {
                "@type":    "ListItem",
                "position": 2,
                "name":     category_label,
                "item":     category_url or f"{BRAND_DOMAIN}/shop",
            },
            {
                "@type":    "ListItem",
                "position": 3,
                "name":     keyword.title(),
                "item":     page_url,
            },
        ],
    }
    try:
        return json.dumps(schema, ensure_ascii=False)
    except Exception:
        return ""


def load_products(csv_path: str) -> list[dict]:
    """Load and deduplicate products from the CSV file."""
    seen = set()
    products = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row.get("vendorArticleNumber", "").strip()
            name = row.get("vendorArticleName", "").strip()
            # Skip rows with broken/missing names
            if not name or name.startswith("http") or name.startswith("Key ["):
                continue
            key = f"{sku}|{name}"
            if key in seen:
                continue
            seen.add(key)
            products.append(row)
    return products


def load_validated_pairs(csv_path: str) -> list[dict]:
    """
    --strict mode: load only demand-validated pairs from SQLite.
    Each pair is enriched with full product data from the CSV so the
    rest of the pipeline (content generation, HTML render) is unchanged.
    """
    if not DB_PATH.exists():
        sys.exit(
            "ERROR: --strict requires the demand-validation DB.\n"
            "Run these scripts first:\n"
            "  python scripts/csv_to_sqlite.py\n"
            "  python scripts/demand_validator.py\n"
            "  python scripts/keyword_registry.py --fix"
        )

    # Load product CSV for full field data (DB stores only core fields)
    products_by_name: dict[str, dict] = {}
    if Path(csv_path).exists():
        for p in load_products(csv_path):
            products_by_name[p.get("vendorArticleName", "").strip()] = p

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT kp.id, kp.keyword, kp.modifier, kp.slug, kp.search_volume,
                  p.vendor_article_name, p.vendor_article_number,
                  p.wix_url, p.amazon_url, p.myntra_url, p.nykaa_url,
                  p.image_url, p.price, p.material, p.product_details,
                  p.category, p.category_url
           FROM keyword_product_pairs kp
           JOIN products p ON p.id = kp.product_id
           JOIN keyword_registry kr ON kr.slug = kp.slug
           WHERE kp.validated = 1
           ORDER BY kp.id"""
    ).fetchall()
    conn.close()

    if not rows:
        sys.exit(
            "ERROR: No validated keyword-product pairs found in DB.\n"
            "Run `python scripts/demand_validator.py` to populate them."
        )

    matrix = []
    for r in rows:
        # Build a product dict matching what load_products() returns
        product = products_by_name.get(r["vendor_article_name"], {})
        if not product:
            # Fall back to DB fields if CSV is absent
            product = {
                "vendorArticleNumber": r["vendor_article_number"],
                "vendorArticleName":   r["vendor_article_name"],
                "wixUrl":              r["wix_url"] or "",
                "amazonUrl":           r["amazon_url"] or "",
                "myntraUrl":           r["myntra_url"] or "",
                "nykaaUrl":            r["nykaa_url"] or "",
                "imageUrl":            r["image_url"] or "",
                "price":               r["price"] or "",
                "material":            r["material"] or "",
                "productDetails":      r["product_details"] or "",
                "category":            r["category"] or "",
                "category_url":        r["category_url"] or "",
            }
        matrix.append({
            "product":      product,
            "modifier":     r["modifier"],
            "keyword":      r["keyword"],
            "slug":         r["slug"],
            "search_volume": r["search_volume"],
        })
    return matrix


def build_page_matrix(products: list[dict]) -> list[dict]:
    """Cross-join each product with all intent modifiers (legacy, non-validated)."""
    matrix = []
    for product in products:
        name = product.get("vendorArticleName", "").strip()
        for modifier in INTENT_MODIFIERS:
            matrix.append({"product": product, "modifier": modifier, "keyword": f"{name} {modifier}"})
    return matrix


# ---------------------------------------------------------------------------
# AI Content Generation
# ---------------------------------------------------------------------------

def _build_system_prompt(keyword: str, modifier: str) -> str:
    intent = classify_intent(modifier)
    target_words = 700 if intent == "informational" else 280
    anti_filler_list = ", ".join(f'"{p}"' for p in ANTI_FILLER[:6])
    return f"""{BRAND_VOICE}

You are an expert content writer for {BRAND_NAME}, a sustainable Indian home decor brand.
Intent for this page: {intent}.
Target keyword: "{keyword}" — include it naturally 3–5 times. Keyword density must stay <3%.

Your output must be a single JSON object with these EXACT keys:
- "article": {target_words}–{target_words + 80} words of HTML content.
  Use <p>, <h2>, <ul> tags. No <h1> (the template adds it). Do NOT start every paragraph with the keyword.
  Include brand name "Vanchai" at least twice. Mention at least one buy platform (Amazon/Myntra/Nykaa/Wix).
- "meta_description": 120–155 characters. Include the keyword once.
- "faq": array of exactly 3 objects, each with "question" and "answer" (plain text, not HTML).

Forbidden phrases: {anti_filler_list}.
Return ONLY the JSON object. No markdown fences, no explanation."""


def generate_content(keyword: str, product: dict, modifier: str = "",
                     dry_run: bool = False, slug: str = "") -> dict:
    """Generate page content via GPT-4o-mini with intent-aware prompts. Returns dict."""
    if dry_run:
        # Minimal placeholder — enough to test gate routing, clearly labelled
        name = product.get("vendorArticleName", keyword)
        details = product.get("productDetails", "")
        intent = classify_intent(modifier) if modifier else "informational"
        target_words = 700 if intent == "informational" else 280
        padding = f" Discover {keyword} from Vanchai." * (target_words // 10)
        return {
            "article": (
                f"<p>[DRY RUN — no OpenAI content]</p>"
                f"<p>This page is about {keyword}. Vanchai offers sustainable home decor "
                f"across Amazon, Myntra, Nykaa, and Wix. {details[:200]}</p>"
                f"<p>{padding[:300]}</p>"
            ),
            "meta_description": (
                f"Shop {keyword} from Vanchai — sustainable Indian home decor. "
                f"Free shipping across India."
            )[:155],
            "faq": [
                {"question": f"What is {keyword}?",
                 "answer": f"A category of sustainable home decor from Vanchai."},
                {"question": "Is free shipping available?",
                 "answer": f"{BRAND_NAME} offers free shipping on orders above ₹499 across India."},
                {"question": f"Where can I buy {keyword} in India?",
                 "answer": "Available on Amazon, Myntra, Nykaa, and Vanchai.in."},
            ],
        }

    # Check content cache first (avoids re-billing on re-runs)
    if slug:
        cached_html = _load_content_cache(slug)
        if cached_html:
            return _html_to_content_dict(cached_html, keyword, product)

    system_prompt = _build_system_prompt(keyword, modifier)

    name     = product.get("vendorArticleName", "").strip()
    details  = product.get("productDetails", "").strip()[:500]
    material = product.get("material", "").strip()
    price    = product.get("price", "").strip()
    category = product.get("category", "").strip()

    platform_lines = []
    for label, key in [("Amazon", "amazonUrl"), ("Wix", "wixUrl"),
                        ("Myntra", "myntraUrl"), ("Nykaa", "nykaaUrl")]:
        url = product.get(key, "").strip()
        if url.startswith("http"):
            platform_lines.append(f"  {label}: {url}")

    user_msg = f"""Target keyword: "{keyword}"
Modifier / page intent: {modifier}
Product: {name}
Material: {material or "natural / sustainable"}
Description: {details or "Handcrafted sustainable home decor."}
Category: {category}
Price: {"₹" + price if price else "see product page"}
Purchase links:
{chr(10).join(platform_lines) or "  (none provided)"}

Write the JSON now."""

    for attempt in range(3):
        try:
            msg = _claude.messages.create(
                model=CLAUDE_DRAFT_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            content = json.loads(raw)

            # Save to content cache for idempotent re-runs
            if slug:
                combined = (f"<!-- cached -->\n<article>{content.get('article','')}</article>\n"
                            f"<!-- meta:{content.get('meta_description','')[:155]} -->")
                _save_content_cache(slug, combined)

            return content
        except json.JSONDecodeError:
            if attempt == 2:
                return generate_content(keyword, product, modifier=modifier,
                                        dry_run=True, slug=slug)
            time.sleep(1)
        except _anthropic.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"  [rate limit] waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"  [claude error] {e}")
            if attempt == 2:
                return generate_content(keyword, product, modifier=modifier,
                                        dry_run=True, slug=slug)
            time.sleep(2)


def _html_to_content_dict(html: str, keyword: str, product: dict) -> dict:
    """Parse cached HTML fragment back to content dict for render_html()."""
    article_match = re.search(r"<article>(.*?)</article>", html, re.DOTALL)
    meta_match    = re.search(r"<!-- meta:(.*?) -->", html, re.DOTALL)
    article = article_match.group(1).strip() if article_match else ""
    meta    = meta_match.group(1).strip()    if meta_match    else ""
    return {
        "article":          article,
        "meta_description": meta or f"Shop {keyword} from {BRAND_NAME}.",
        "faq": [
            {"question": f"What is {keyword}?",
             "answer": "A sustainable home decor product from Vanchai."},
            {"question": "Where can I buy it?",
             "answer": "Available on Amazon, Myntra, Nykaa, and Vanchai.in."},
            {"question": "Is free shipping available?",
             "answer": f"{BRAND_NAME} offers free shipping on orders above ₹499."},
        ],
    }


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

def html_escape(text: str) -> str:
    """Escape special characters safe for HTML attributes and text."""
    return (text
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def clean_title(text: str) -> str:
    """Remove stray quote characters from product names for clean SERP display.

    Product names in the Vanchai catalogue have two types of \":
    - After digits: inch measurements (e.g. 21\", 30\" x 50\") — preserved
    - Elsewhere: data-entry typos (e.g. 'Tail Cone\"- Set of') — removed
    """
    # Remove \" that is NOT preceded by a digit (it's a typo, not a measurement)
    return re.sub(r'(?<!\d)"', "", text).strip()


def render_html(keyword: str, product: dict, content: dict, slug: str, modifier: str = "") -> str:
    """Render a complete HTML page for one keyword × product combination."""
    name        = product.get("vendorArticleName", keyword)
    img_url     = product.get("imageUrl", "")
    price       = product.get("price", "")
    wix_url     = utm(product.get("wixUrl", ""), "wix_cta")
    amazon_url  = utm(product.get("amazonUrl", ""), "amazon_cta")
    myntra_url  = utm(product.get("myntraUrl", ""), "myntra_cta")
    nykaa_url   = utm(product.get("nykaaUrl", ""), "nykaa_cta")
    canonical   = product.get("wixUrl", BRAND_DOMAIN)
    faq_items    = content.get("faq", [])
    category_url = product.get("category_url", BRAND_DOMAIN + "/shop")
    meta_desc    = html_escape(content.get("meta_description", "")[:155])
    article      = content.get("article", "")

    # JSON-LD schemas
    discover_url  = f"{DISCOVER_DOMAIN}/{slug}.html"
    product_jld   = build_product_json_ld(product)
    faq_jld       = build_faqpage_json_ld(faq_items)
    breadcrumb_jld = build_breadcrumb_json_ld(
        keyword=keyword,
        category=product.get("category", ""),
        category_url=category_url,
        page_url=discover_url,
    )

    # Safe/clean versions for HTML contexts
    safe_keyword = html_escape(clean_title(keyword))
    pub_date     = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+05:30')

    # OG image — use product image if available, fall back to brand default
    og_image = (img_url if img_url and img_url != "No Image URL"
                else f"{BRAND_DOMAIN}/og-default.jpg")

    # Build FAQ HTML
    faq_html = ""
    for item in faq_items:
        faq_html += f"""
        <div class="faq-item">
          <h3 class="faq-q">{item.get('question','')}</h3>
          <p class="faq-a">{item.get('answer','')}</p>
        </div>"""

    # Build purchase buttons
    buy_buttons = f'<a href="{wix_url}" class="btn btn-primary" rel="nofollow sponsored">Shop on Vanchai.in</a>\n' if wix_url else ""
    if amazon_url:
        buy_buttons += f'    <a href="{amazon_url}" class="btn btn-secondary" rel="nofollow sponsored">View on Amazon</a>\n'
    if myntra_url:
        buy_buttons += f'    <a href="{myntra_url}" class="btn btn-secondary" rel="nofollow sponsored">Shop on Myntra</a>\n'
    if nykaa_url:
        buy_buttons += f'    <a href="{nykaa_url}" class="btn btn-secondary" rel="nofollow sponsored">Shop on Nykaa</a>\n'

    price_html = f'<p class="price">₹{price}</p>' if price else ""
    img_html   = f'<img src="{html_escape(img_url)}" alt="{safe_keyword}" loading="lazy" width="500" height="500">' if img_url and img_url != "No Image URL" else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_keyword} | {BRAND_NAME}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{canonical}">
  <!-- Preconnect for performance -->
  <link rel="preconnect" href="https://static.wixstatic.com">
  <!-- SEO & Indexing -->
  <meta name="robots" content="index, follow">
  <!-- Open Graph — WhatsApp, LinkedIn, Facebook previews -->
  <meta property="og:type"        content="product">
  <meta property="og:title"       content="{safe_keyword}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:url"         content="{discover_url}">
  <meta property="og:image"       content="{html_escape(og_image)}">
  <meta property="og:site_name"   content="{BRAND_NAME}">
  <!-- Twitter Card -->
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{safe_keyword}">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image"       content="{html_escape(og_image)}">
  <!-- E-E-A-T: publication date signal -->
  <meta property="article:published_time" content="{pub_date}">
  <!-- JSON-LD: Product Schema -->
  {f'<script type="application/ld+json">{product_jld}</script>' if product_jld else ''}
  <!-- JSON-LD: FAQPage Schema -->
  {f'<script type="application/ld+json">{faq_jld}</script>' if faq_jld else ''}
  <!-- JSON-LD: BreadcrumbList Schema -->
  {f'<script type="application/ld+json">{breadcrumb_jld}</script>' if breadcrumb_jld else ''}
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,-apple-system,sans-serif;color:#2d2d2d;background:#fafaf8;line-height:1.7}}
    a{{color:#5c7a5c;text-decoration:none}}
    .container{{max-width:860px;margin:0 auto;padding:24px 16px}}
    header{{background:#fff;border-bottom:1px solid #e8e4df;padding:14px 0}}
    header .inner{{max-width:860px;margin:0 auto;padding:0 16px;display:flex;align-items:center;gap:16px}}
    header .logo{{font-weight:700;font-size:1.2rem;color:#3a5a3a;letter-spacing:.5px}}
    header nav a{{color:#555;font-size:.9rem;margin-left:16px}}
    h1{{font-size:1.8rem;font-weight:700;color:#2a3a2a;margin:24px 0 12px;line-height:1.3}}
    .breadcrumb{{font-size:.82rem;color:#888;margin-bottom:8px}}
    .breadcrumb a{{color:#888}}
    .product-hero{{display:flex;gap:24px;margin:24px 0;flex-wrap:wrap}}
    .product-hero img{{width:100%;max-width:340px;height:340px;object-fit:cover;border-radius:10px;flex-shrink:0}}
    .hero-info{{flex:1;min-width:220px}}
    .price{{font-size:1.4rem;font-weight:700;color:#3a5a3a;margin:8px 0 16px}}
    .purchase-section{{background:#f0f4f0;border-radius:12px;padding:20px;margin:24px 0}}
    .purchase-section h2{{font-size:1.1rem;margin-bottom:14px;color:#2a3a2a}}
    .btn{{display:inline-block;padding:11px 22px;border-radius:6px;font-weight:600;font-size:.92rem;margin:5px 6px 5px 0;transition:opacity .15s}}
    .btn-primary{{background:#3a5a3a;color:#fff}}
    .btn-secondary{{background:#fff;color:#3a5a3a;border:1.5px solid #3a5a3a}}
    .btn:hover{{opacity:.88}}
    .article-body{{margin:24px 0}}
    .article-body p{{margin-bottom:14px;font-size:1rem}}
    .faq-section{{margin:32px 0}}
    .faq-section>h2{{font-size:1.3rem;margin-bottom:18px;color:#2a3a2a}}
    .faq-item{{border-bottom:1px solid #e8e4df;padding:14px 0}}
    .faq-q{{font-weight:600;margin-bottom:6px;font-size:.98rem}}
    .faq-a{{color:#555;font-size:.93rem}}
    .back-link{{margin:24px 0;font-size:.9rem}}
    footer{{background:#2a3a2a;color:#bbb;text-align:center;padding:20px 16px;margin-top:40px;font-size:.85rem}}
    footer a{{color:#8db08d}}
    @media(max-width:600px){{h1{{font-size:1.4rem}}.product-hero img{{max-width:100%;height:260px}}}}
  </style>
</head>
<body>
<header>
  <div class="inner">
    <a href="{BRAND_DOMAIN}" class="logo">{BRAND_NAME}</a>
    <nav>
      <a href="{BRAND_DOMAIN}/shop">Shop</a>
      <a href="{category_url}">Category</a>
    </nav>
  </div>
</header>

<div class="container">
  <div class="breadcrumb">
    <a href="{BRAND_DOMAIN}">Home</a> &rsaquo;
    <a href="{category_url}">Collection</a> &rsaquo;
    {safe_keyword}
  </div>

  <h1>{safe_keyword}</h1>

  <div class="product-hero">
    {img_html}
    <div class="hero-info">
      <p style="color:#666;font-size:.92rem;margin-bottom:8px">{html_escape(product.get('material',''))}</p>
      {price_html}
      <p style="font-size:.9rem;color:#555">{html_escape(product.get('productDetails','')[:300])}{'...' if len(product.get('productDetails',''))>300 else ''}</p>
    </div>
  </div>

  <div class="purchase-section">
    <h2>🛒 Purchase Intent — Where to Buy</h2>
    {buy_buttons}
  </div>

  <div class="article-body">
    {article}
  </div>

  <div class="faq-section">
    <h2>Frequently Asked Questions</h2>
    {faq_html}
  </div>

  <p class="back-link">← <a href="{BRAND_DOMAIN}/shop">Browse all {BRAND_NAME} products</a></p>

  <!-- Internal linking: related style guides for this product -->
  <div style="margin:32px 0 16px;padding:20px;background:#f5f0ea;border-radius:12px">
    <h2 style="font-size:1.05rem;color:#2a3a2a;margin-bottom:12px">More {html_escape(clean_title(name.split('|')[0].strip()[:40]))} Style Guides</h2>
    <div style="display:flex;flex-wrap:wrap;gap:8px">
      {"".join(
        f'<a href="{DISCOVER_DOMAIN}/{slugify(name + " " + m)}.html" style="background:#fff;color:#3a5a3a;font-size:.82rem;padding:5px 12px;border-radius:14px;border:1px solid #c8d8c8;text-decoration:none">{html_escape(m)}</a>'
        for m in INTENT_MODIFIERS[:10]
        if m not in modifier
      )}
    </div>
  </div>
</div>

<footer>
  <p>&copy; {BRAND_NAME} — Sustainable Home Decor, Made in India.</p>
  <p style="margin-top:6px"><a href="{BRAND_DOMAIN}">vanchai.in</a> &nbsp;|&nbsp; <a href="{BRAND_DOMAIN}/shop">Shop</a></p>
</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Queue helpers (T-CG-036)
# ---------------------------------------------------------------------------

def _append_to_queue(path: Path, slug: str, keyword: str, result) -> None:
    """Append a gate result entry to a JSON queue file (review_queue or blocked)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append({
        'slug':             slug,
        'keyword':          keyword,
        'routing':          result.routing,
        'seo_score':        result.seo_score,
        'word_count':       result.word_count,
        'uniqueness_score': round(result.uniqueness_score, 3),
        'failures': [
            {'gate': c.name, 'message': c.message, 'recoverable': c.recoverable}
            for c in result.checks if not c.passed
        ],
        'queued_at': datetime.now(timezone.utc).isoformat(),
    })
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding='utf-8')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vanchai Programmatic SEO Generator")
    parser.add_argument("--csv",      default=CSV_FILE,        help="Path to product CSV")
    parser.add_argument("--strict",   action="store_true",     help="Only generate demand-validated pairs (requires DB)")
    parser.add_argument("--batch",    type=int, default=None,  help="Batch number to generate (1-based)")
    parser.add_argument("--limit",    type=int, default=None,  help="Hard limit on total pages (for testing)")
    parser.add_argument("--dry-run",  action="store_true",     help="Skip OpenAI calls; use placeholder text")
    parser.add_argument("--delay",    type=float, default=0.3, help="Seconds between API calls (rate limiting)")
    parser.add_argument("--force",    action="store_true",     help="Overwrite already-generated pages")
    args = parser.parse_args()

    # Initialise Claude client unless dry-run
    global _claude
    if not args.dry_run:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: ANTHROPIC_API_KEY env var not set. Use --dry-run to test without API.")
        _claude = _anthropic.Anthropic(api_key=api_key)

    csv_path = args.csv

    if args.strict:
        # --strict: load only demand-validated pairs from SQLite
        print("[1/4] --strict mode: loading validated keyword-product pairs from DB …")
        matrix = load_validated_pairs(csv_path)
        total = len(matrix)
        print(f"      {total} validated pairs loaded (≥100 searches/month, registered in keyword_registry).")
    else:
        # Legacy mode: raw modifier matrix (non-validated, constitution violation)
        print("WARNING: running without --strict generates pages from an unvalidated modifier matrix.")
        print("         This violates the constitution's demand-first rule. Use --strict for production.\n")

        if not Path(csv_path).exists():
            sys.exit(f"ERROR: CSV file not found: {csv_path}")

        print(f"[1/4] Loading products from {csv_path}...")
        products = load_products(csv_path)
        print(f"      {len(products)} unique products loaded.")

        print("[2/4] Building keyword matrix...")
        matrix = build_page_matrix(products)
        total = len(matrix)
        print(f"      {total} pages to generate ({len(products)} products × {len(INTENT_MODIFIERS)} modifiers).")

    # Apply batch slicing
    if args.batch is not None:
        start = (args.batch - 1) * BATCH_SIZE
        end   = start + BATCH_SIZE
        matrix = matrix[start:end]
        print(f"      Batch {args.batch}: pages {start+1}–{min(end, total)} of {total}.")

    if args.limit:
        matrix = matrix[:args.limit]
        print(f"      Limit applied: generating {len(matrix)} pages.")

    # Prepare output directory
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate pages
    print(f"[3/4] Generating {len(matrix)} HTML pages...")
    generated     = []
    review_count  = 0
    blocked_count = 0

    for i, entry in enumerate(matrix, 1):
        product  = entry["product"]
        modifier = entry["modifier"]
        keyword  = entry["keyword"]
        # In --strict mode, use the canonical slug from the DB to avoid drift
        slug      = entry.get("slug") or slugify(keyword)
        html_path = out_dir / f"{slug}.html"

        # Skip already-generated pages on idempotent re-runs (unless --force)
        if html_path.exists() and not args.force:
            generated.append(f"{slug}.html")
            continue

        print(f"  [{i}/{len(matrix)}] {keyword[:70]}...", flush=True)

        content = generate_content(keyword, product, modifier=modifier,
                                   dry_run=args.dry_run, slug=slug)
        html    = render_html(keyword, product, content, slug, modifier)

        # ── Quality gates (T-CG-036) ────────────────────────────────────────
        gate = QualityGate.run_all(
            html=html, keyword=keyword, product=product,
            docs_dir=out_dir, db_path=DB_PATH, current_slug=slug,
        )

        if gate.routing == 'approved':
            html_path.write_text(html, encoding="utf-8")
            generated.append(f"{slug}.html")
            print(f"    ✓ approved  SEO:{gate.seo_score}  words:{gate.word_count}")
        elif gate.routing == 'review_queue':
            _append_to_queue(REVIEW_QUEUE_PATH, slug, keyword, gate)
            failed_msg = gate.failures[0].message if gate.failures else '?'
            print(f"    ↷ review    {failed_msg}")
            review_count += 1
        else:
            _append_to_queue(BLOCKED_PATH, slug, keyword, gate)
            reasons = ' | '.join(c.message for c in gate.failures)
            print(f"    ✗ blocked   {reasons}")
            blocked_count += 1
        # ────────────────────────────────────────────────────────────────────

        if not args.dry_run and i < len(matrix):
            time.sleep(args.delay)

    print(f"\n[4/4] Done.")
    print(f"      Approved     : {len(generated)} pages → ./{OUTPUT_DIR}/")
    print(f"      Review queue : {review_count} pages → .seo-engine/review_queue.json")
    print(f"      Blocked      : {blocked_count} pages → .seo-engine/blocked.json")
    if generated:
        print(f"      Run `python generate_sitemap.py` to rebuild sitemaps.")


if __name__ == "__main__":
    main()
