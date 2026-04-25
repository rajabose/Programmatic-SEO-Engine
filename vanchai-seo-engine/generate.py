#!/usr/bin/env python3
"""
generate.py — Vanchai Programmatic SEO Engine
=============================================
Reads the product catalogue CSV, cross-joins every product with
intent modifiers, calls OpenAI GPT-4o-mini to generate a unique
500-word article per page, then writes production-ready HTML files
to the OUTPUT_DIR directory.

Usage:
    python generate.py                        # generate all pages
    python generate.py --batch 1              # generate batch 1 (0-499)
    python generate.py --batch 2              # generate batch 2 (500-999)
    python generate.py --dry-run --limit 5    # test 5 pages without OpenAI
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import openai

from config import (
    BRAND_NAME, BRAND_DOMAIN, DISCOVER_DOMAIN,
    UTM_SOURCE, UTM_MEDIUM, UTM_CAMPAIGN,
    OPENAI_MODEL, OPENAI_MAX_TOKENS,
    OUTPUT_DIR, BATCH_SIZE, INTENT_MODIFIERS, BRAND_VOICE, CSV_FILE,
)

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


def build_page_matrix(products: list[dict]) -> list[dict]:
    """Cross-join each product with all intent modifiers."""
    matrix = []
    for product in products:
        name = product.get("vendorArticleName", "").strip()
        for modifier in INTENT_MODIFIERS:
            matrix.append({"product": product, "modifier": modifier, "keyword": f"{name} {modifier}"})
    return matrix


# ---------------------------------------------------------------------------
# AI Content Generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are an expert home decor content writer for {BRAND_NAME}, 
an Indian sustainable home decor brand. Write in a warm, aspirational, and 
knowledgeable tone focused on {BRAND_VOICE}.

Your output must be a single JSON object with these exact keys:
- "article": a 500-word SEO article (HTML paragraph tags, no h1/h2 tags — those are added by the template)
- "meta_description": a 155-character meta description
- "faq": an array of 3 objects, each with "question" and "answer" keys

Return ONLY the JSON object. No markdown, no explanation."""


def generate_content(keyword: str, product: dict, dry_run: bool = False) -> dict:
    """Call GPT-4o-mini to generate page content. Returns dict with article/meta/faq."""
    if dry_run:
        return {
            "article": f"<p>This is a placeholder article about <strong>{keyword}</strong>. "
                       f"Replace with real content by running without --dry-run.</p>",
            "meta_description": f"Buy {product.get('vendorArticleName', '')} from {BRAND_NAME}. "
                                 f"Sustainable home decor shipped across India.",
            "faq": [
                {"question": f"What is {product.get('vendorArticleName', '')}?",
                 "answer": product.get("productDetails", "A beautiful sustainable home decor product.")[:200]},
                {"question": "Is free shipping available?",
                 "answer": f"Yes, {BRAND_NAME} offers free shipping on orders above ₹499 across India."},
                {"question": "Can I return this product?",
                 "answer": "Please refer to the product page on Vanchai.in for the return policy."},
            ],
        }

    user_msg = f"""Target keyword: "{keyword}"

Product name: {product.get('vendorArticleName', '')}
Material: {product.get('material', '')}
Product details: {product.get('productDetails', '')[:600]}
Category: {product.get('category', product.get('productType', ''))}
Price: ₹{product.get('price', 'N/A')}

Write the article, meta description, and FAQ JSON now."""

    for attempt in range(3):
        try:
            resp = openai.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=OPENAI_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.7,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip possible markdown fences
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt == 2:
                # Fallback on parse failure
                return generate_content(keyword, product, dry_run=True)
            time.sleep(1)
        except openai.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"  [rate limit] waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"  [openai error] {e}")
            if attempt == 2:
                return generate_content(keyword, product, dry_run=True)
            time.sleep(2)


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

def build_faq_json_ld(faq_items: list[dict]) -> str:
    """Build FAQ JSON-LD schema."""
    entities = [
        {"@type": "Question", "name": q["question"],
         "acceptedAnswer": {"@type": "Answer", "text": q["answer"]}}
        for q in faq_items
    ]
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    return json.dumps(schema, ensure_ascii=False)


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
    product_jld = build_product_json_ld(product)
    faq_jld     = build_faq_json_ld(content.get("faq", []))
    meta_desc   = html_escape(content.get("meta_description", "")[:155])
    article     = content.get("article", "")
    faq_items   = content.get("faq", [])
    category_url = product.get("category_url", BRAND_DOMAIN + "/shop")

    # Safe/clean versions for HTML contexts
    safe_keyword  = html_escape(clean_title(keyword))
    safe_name     = html_escape(clean_title(name))

    # OG image — use product image if available, fall back to brand default
    og_image = (img_url if img_url and img_url != "No Image URL"
                else f"{BRAND_DOMAIN}/og-default.jpg")
    # Canonical URL for this discover page (used in OG tags)
    discover_url = f"{DISCOVER_DOMAIN}/{slug}.html"

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
  <!-- JSON-LD: Product Schema -->
  {f'<script type="application/ld+json">{product_jld}</script>' if product_jld else ''}
  <!-- JSON-LD: FAQ Schema -->
  <script type="application/ld+json">{faq_jld}</script>
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
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vanchai Programmatic SEO Generator")
    parser.add_argument("--csv",      default=CSV_FILE,        help="Path to product CSV")
    parser.add_argument("--batch",    type=int, default=None,  help="Batch number to generate (1-based)")
    parser.add_argument("--limit",    type=int, default=None,  help="Hard limit on total pages (for testing)")
    parser.add_argument("--dry-run",  action="store_true",     help="Skip OpenAI calls; use placeholder text")
    parser.add_argument("--delay",    type=float, default=0.3, help="Seconds between API calls (rate limiting)")
    parser.add_argument("--force",    action="store_true",     help="Overwrite already-generated pages")
    args = parser.parse_args()

    # Validate API key unless dry-run
    if not args.dry_run:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: OPENAI_API_KEY env var not set. Use --dry-run to test without API.")
        openai.api_key = api_key

    # Load products
    csv_path = args.csv
    if not Path(csv_path).exists():
        sys.exit(f"ERROR: CSV file not found: {csv_path}")

    print(f"[1/4] Loading products from {csv_path}...")
    products = load_products(csv_path)
    print(f"      {len(products)} unique products loaded.")

    # Build keyword × product matrix
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
    generated = []
    for i, entry in enumerate(matrix, 1):
        product  = entry["product"]
        modifier = entry["modifier"]
        keyword  = entry["keyword"]
        slug     = slugify(keyword)
        html_path = out_dir / f"{slug}.html"

        # Skip if already generated (idempotent re-runs), unless --force
        if html_path.exists() and not args.force:
            generated.append(f"{slug}.html")
            continue

        print(f"  [{i}/{len(matrix)}] {keyword[:70]}...")

        content = generate_content(keyword, product, dry_run=args.dry_run)
        html    = render_html(keyword, product, content, slug, modifier)

        html_path.write_text(html, encoding="utf-8")
        generated.append(f"{slug}.html")

        if not args.dry_run and i < len(matrix):
            time.sleep(args.delay)

    print(f"[4/4] Done. {len(generated)} pages written to ./{OUTPUT_DIR}/")
    print(f"      Run `python generate_sitemap.py` next to build sitemaps.")


if __name__ == "__main__":
    main()
