#!/usr/bin/env python3
"""
generate_index.py — Category Hub Pages for Vanchai SEO Engine
=============================================================
Generates crawlable category index pages so Googlebot can discover
all 1,360+ SEO landing pages. Also builds a master index page.

Hub structure:
  /docs/category-sola-flowers.html
  /docs/category-dried-botanicals.html
  /docs/category-cotton-textiles.html
  /docs/category-terracotta.html
  /docs/index.html  (master hub, links to all categories)

Usage:
    python generate_index.py
"""

import csv
import re
from pathlib import Path

from config import BRAND_NAME, BRAND_DOMAIN, DISCOVER_DOMAIN, OUTPUT_DIR, INTENT_MODIFIERS, CSV_FILE

# ---------------------------------------------------------------------------
# Category grouping map (material → display category)
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "Sola":                          "Sola Flowers",
    "sola":                          "Sola Flowers",
    "Palm":                          "Dried Botanicals",
    "Pine Cone":                     "Dried Botanicals",
    "Pine":                          "Dried Botanicals",
    "Lotus Pod":                     "Dried Botanicals",
    "Pampas Grass":                  "Dried Botanicals",
    "Pampas Grass and Jute Mat":     "Dried Botanicals",
    "Willow Twisted Stem":           "Dried Botanicals",
    "Willow Twisted Stem and Jute Mat": "Dried Botanicals",
    "Dried Sponge Mushroom":         "Dried Botanicals",
    "Dried Celosia Flower":          "Dried Botanicals",
    "Ovoid Pine":                    "Dried Botanicals",
    "Dune Pampas Grass":             "Dried Botanicals",
    "Jute":                          "Dried Botanicals",
    "Cotton Cushion":                "Cotton Textiles",
    "Cushion Cover":                 "Cotton Textiles",
    "Terracotta":                    "Terracotta",
}

CATEGORY_DESCRIPTIONS = {
    "Sola Flowers": (
        "Handcrafted sola wood flowers, ethically sourced from the tapioca forests of India. "
        "Perfect for bouquets, wreaths, vase arrangements, and sustainable home decor. "
        "Available in 30+ colours and styles."
    ),
    "Dried Botanicals": (
        "Naturally preserved dried flowers, pampas grass, palm leaves, lotus pods, and botanical stems. "
        "Zero-maintenance, everlasting beauty for your home, events, and weddings."
    ),
    "Cotton Textiles": (
        "Handspun and handwoven cotton cushion covers crafted by Indian artisans. "
        "Rustic, modern, and made with love. Washable, durable, and sustainably produced."
    ),
    "Terracotta": (
        "Handmade terracotta mugs, plates, saucers, and diyas. 100% natural clay, unglazed, "
        "eco-friendly, and perfect for sustainable everyday living."
    ),
}

CATEGORY_SLUGS = {
    "Sola Flowers":      "category-sola-flowers",
    "Dried Botanicals":  "category-dried-botanicals",
    "Cotton Textiles":   "category-cotton-textiles",
    "Terracotta":        "category-terracotta",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text)[:120]


def html_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace('"', "&quot;")
            .replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;"))


def load_products(csv_path: str) -> list[dict]:
    products = []
    seen = set()
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = row.get("vendorArticleName", "").strip()
            sku  = row.get("vendorArticleNumber", "").strip()
            if not name or name.startswith("http") or sku in seen:
                continue
            seen.add(sku)
            products.append(row)
    return products


def get_category(product: dict) -> str:
    material = product.get("material", "").strip()
    return CATEGORY_MAP.get(material, "Other")


def page_links_for_product(product: dict) -> list[dict]:
    """Return all intent-modifier page entries for a product."""
    name = product.get("vendorArticleName", "").strip()
    links = []
    for modifier in INTENT_MODIFIERS:
        keyword = f"{name} {modifier}"
        slug    = slugify(keyword)
        links.append({"keyword": keyword, "slug": slug, "modifier": modifier})
    return links


def render_category_page(
    category: str,
    products: list[dict],
    all_categories: dict[str, str],
) -> str:
    """Render a full category hub HTML page."""
    slug        = CATEGORY_SLUGS.get(category, slugify(f"category-{category}"))
    description = CATEGORY_DESCRIPTIONS.get(category, f"Explore {category} products by {BRAND_NAME}.")
    safe_cat    = html_escape(category)
    canonical   = f"{DISCOVER_DOMAIN}/{slug}.html"

    # Build product cards with all modifier links
    product_cards_html = ""
    for product in products:
        name      = html_escape(product.get("vendorArticleName", ""))
        img_url   = product.get("imageUrl", "")
        wix_url   = product.get("wixUrl", BRAND_DOMAIN)
        price     = product.get("price", "")
        img_html  = (
            f'<img src="{html_escape(img_url)}" alt="{name}" loading="lazy" '
            f'width="200" height="200">'
            if img_url and img_url != "No Image URL" else
            '<div class="no-img">🌿</div>'
        )
        price_html = f'<span class="card-price">₹{price}</span>' if price else ""

        # Build modifier links (first 6 for the card, rest in a "see more" section)
        links = page_links_for_product(product)
        shown_links = links[:6]
        link_html = "".join(
            f'<a href="{DISCOVER_DOMAIN}/{l["slug"]}.html" class="kw-link">{html_escape(l["modifier"])}</a>'
            for l in shown_links
        )
        more_html = (
            f'<span class="kw-more">+{len(links)-6} more styles →</span>'
            if len(links) > 6 else ""
        )

        product_cards_html += f"""
      <div class="product-card">
        <a href="{html_escape(wix_url)}" rel="nofollow" class="card-img-link">
          {img_html}
        </a>
        <div class="card-body">
          <h3 class="card-title"><a href="{html_escape(wix_url)}" rel="nofollow">{name}</a></h3>
          {price_html}
          <div class="kw-links">
            {link_html}
            {more_html}
          </div>
        </div>
      </div>"""

    # Other category links
    other_cats_html = "".join(
        f'<a href="{cat_slug}.html" class="cat-link">{html_escape(cat)}</a>'
        for cat, cat_slug in all_categories.items()
        if cat != category
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_cat} — Sustainable Home Decor | {BRAND_NAME}</title>
  <meta name="description" content="{html_escape(description[:155])}">
  <link rel="canonical" href="{canonical}">
  <link rel="preconnect" href="https://static.wixstatic.com">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,-apple-system,sans-serif;color:#2d2d2d;background:#fafaf8;line-height:1.7}}
    a{{color:#5c7a5c;text-decoration:none}}
    .container{{max-width:1060px;margin:0 auto;padding:24px 16px}}
    header{{background:#fff;border-bottom:1px solid #e8e4df;padding:14px 0}}
    header .inner{{max-width:1060px;margin:0 auto;padding:0 16px;display:flex;align-items:center;gap:16px}}
    .logo{{font-weight:700;font-size:1.2rem;color:#3a5a3a}}
    nav a{{color:#555;font-size:.9rem;margin-left:16px}}
    h1{{font-size:1.9rem;font-weight:700;color:#2a3a2a;margin:24px 0 8px}}
    .desc{{color:#555;max-width:700px;margin-bottom:28px;font-size:.97rem}}
    .breadcrumb{{font-size:.82rem;color:#888;margin-bottom:8px}}
    .breadcrumb a{{color:#888}}
    .other-cats{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:32px}}
    .cat-link{{background:#f0f4f0;color:#3a5a3a;padding:7px 16px;border-radius:20px;font-size:.88rem;font-weight:600;border:1.5px solid #c8d8c8}}
    .cat-link:hover{{background:#3a5a3a;color:#fff}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin:8px 0 40px}}
    .product-card{{background:#fff;border:1px solid #e8e4df;border-radius:12px;overflow:hidden;display:flex;flex-direction:column}}
    .card-img-link img,.no-img{{width:100%;height:200px;object-fit:cover;display:block}}
    .no-img{{display:flex;align-items:center;justify-content:center;font-size:3rem;background:#f5f0ea}}
    .card-body{{padding:14px;flex:1;display:flex;flex-direction:column;gap:8px}}
    .card-title{{font-size:.95rem;font-weight:600;color:#2a3a2a;line-height:1.4}}
    .card-title a{{color:inherit}}
    .card-price{{font-weight:700;color:#3a5a3a;font-size:1rem}}
    .kw-links{{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}}
    .kw-link{{background:#f0f4f0;color:#3a5a3a;font-size:.78rem;padding:3px 9px;border-radius:12px;border:1px solid #c8d8c8}}
    .kw-link:hover{{background:#3a5a3a;color:#fff}}
    .kw-more{{font-size:.78rem;color:#888;align-self:center}}
    .section-title{{font-size:1.25rem;font-weight:700;color:#2a3a2a;margin:32px 0 16px;padding-bottom:8px;border-bottom:2px solid #e8e4df}}
    footer{{background:#2a3a2a;color:#bbb;text-align:center;padding:20px;margin-top:40px;font-size:.85rem}}
    footer a{{color:#8db08d}}
    @media(max-width:600px){{h1{{font-size:1.4rem}}.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
<header>
  <div class="inner">
    <a href="{BRAND_DOMAIN}" class="logo">{BRAND_NAME}</a>
    <nav>
      <a href="index.html">All Categories</a>
      <a href="{BRAND_DOMAIN}/shop">Shop</a>
    </nav>
  </div>
</header>

<div class="container">
  <div class="breadcrumb">
    <a href="{BRAND_DOMAIN}">Home</a> &rsaquo;
    <a href="index.html">Discover</a> &rsaquo;
    {safe_cat}
  </div>

  <h1>🌿 {safe_cat}</h1>
  <p class="desc">{html_escape(description)}</p>

  <div class="other-cats">
    <span style="font-size:.88rem;color:#888;align-self:center">Browse:</span>
    {other_cats_html}
  </div>

  <div class="section-title">{len(products)} Products — {len(products) * len(INTENT_MODIFIERS)} Style Guides</div>

  <div class="grid">
    {product_cards_html}
  </div>

  <p style="margin:8px 0 32px;color:#888;font-size:.88rem">
    Showing all {len(products)} {safe_cat.lower()} products with {len(INTENT_MODIFIERS)} style variations each.
    <a href="{BRAND_DOMAIN}/shop">Shop the full collection on Vanchai.in →</a>
  </p>
</div>

<footer>
  <p>&copy; {BRAND_NAME} — Sustainable Home Decor, Made in India.</p>
  <p style="margin-top:6px">
    <a href="{BRAND_DOMAIN}">vanchai.in</a> &nbsp;|&nbsp;
    <a href="index.html">All Guides</a>
  </p>
</footer>
</body>
</html>"""


def render_master_index(categories: dict[str, list[dict]]) -> str:
    """Render the root index.html — the master hub page."""
    total_products = sum(len(v) for v in categories.values())
    total_pages    = total_products * len(INTENT_MODIFIERS)

    cat_cards_html = ""
    emojis = {"Sola Flowers": "🌸", "Dried Botanicals": "🌾", "Cotton Textiles": "🧵", "Terracotta": "🏺"}
    for cat, products in categories.items():
        slug = CATEGORY_SLUGS.get(cat, slugify(f"category-{cat}"))
        desc = CATEGORY_DESCRIPTIONS.get(cat, "")
        emoji = emojis.get(cat, "🌿")
        sample_imgs = [
            p.get("imageUrl", "") for p in products[:3]
            if p.get("imageUrl", "") not in ("", "No Image URL")
        ]
        img_strip = "".join(
            f'<img src="{html_escape(u)}" loading="lazy" width="80" height="80" alt="">'
            for u in sample_imgs
        )
        cat_cards_html += f"""
    <a href="{slug}.html" class="cat-card">
      <div class="cat-emoji">{emoji}</div>
      <h2>{html_escape(cat)}</h2>
      <p>{html_escape(desc[:120])}…</p>
      <div class="img-strip">{img_strip}</div>
      <span class="cat-count">{len(products)} products · {len(products)*len(INTENT_MODIFIERS)} guides</span>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Discover Vanchai — Sustainable Home Decor India</title>
  <meta name="description" content="Explore {total_pages}+ style guides for sustainable home decor: dried flowers, sola wood, terracotta, and handwoven textiles. Made in India by Vanchai.">
  <link rel="canonical" href="{DISCOVER_DOMAIN}/index.html">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,-apple-system,sans-serif;color:#2d2d2d;background:#fafaf8;line-height:1.7}}
    a{{color:#5c7a5c;text-decoration:none}}
    .container{{max-width:960px;margin:0 auto;padding:32px 16px}}
    header{{background:#fff;border-bottom:1px solid #e8e4df;padding:14px 0}}
    header .inner{{max-width:960px;margin:0 auto;padding:0 16px;display:flex;align-items:center;gap:16px}}
    .logo{{font-weight:700;font-size:1.3rem;color:#3a5a3a}}
    nav a{{color:#555;font-size:.9rem;margin-left:16px}}
    .hero{{text-align:center;padding:48px 16px 32px;background:linear-gradient(135deg,#f5f0ea,#e8f0e8)}}
    .hero h1{{font-size:2.2rem;color:#2a3a2a;margin-bottom:12px}}
    .hero p{{color:#555;max-width:560px;margin:0 auto 24px;font-size:1.05rem}}
    .hero .stats{{display:flex;gap:24px;justify-content:center;flex-wrap:wrap}}
    .stat{{background:#fff;padding:12px 24px;border-radius:10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
    .stat .num{{font-size:1.6rem;font-weight:800;color:#3a5a3a}}
    .stat .lbl{{font-size:.82rem;color:#888}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:20px;margin:40px 0}}
    .cat-card{{background:#fff;border:1px solid #e8e4df;border-radius:14px;padding:22px;display:flex;flex-direction:column;gap:10px;transition:box-shadow .15s,transform .15s}}
    .cat-card:hover{{box-shadow:0 6px 24px rgba(0,0,0,.1);transform:translateY(-2px)}}
    .cat-emoji{{font-size:2.2rem}}
    .cat-card h2{{font-size:1.1rem;font-weight:700;color:#2a3a2a}}
    .cat-card p{{font-size:.88rem;color:#666;line-height:1.5}}
    .img-strip{{display:flex;gap:4px;margin-top:4px}}
    .img-strip img{{border-radius:6px;object-fit:cover}}
    .cat-count{{font-size:.8rem;font-weight:600;color:#3a5a3a;margin-top:4px}}
    footer{{background:#2a3a2a;color:#bbb;text-align:center;padding:20px;margin-top:40px;font-size:.85rem}}
    footer a{{color:#8db08d}}
    @media(max-width:600px){{.hero h1{{font-size:1.6rem}}.grid{{grid-template-columns:1fr 1fr}}}}
  </style>
</head>
<body>
<header>
  <div class="inner">
    <a href="{BRAND_DOMAIN}" class="logo">🌿 {BRAND_NAME}</a>
    <nav>
      <a href="{BRAND_DOMAIN}/shop">Shop All</a>
      <a href="{BRAND_DOMAIN}">About</a>
    </nav>
  </div>
</header>

<div class="hero">
  <h1>Discover Sustainable Home Decor</h1>
  <p>Browse {total_pages}+ style guides for natural, eco-friendly home decor. Handcrafted in India, shipped nationwide.</p>
  <div class="stats">
    <div class="stat"><div class="num">{total_products}</div><div class="lbl">Products</div></div>
    <div class="stat"><div class="num">{total_pages}+</div><div class="lbl">Style Guides</div></div>
    <div class="stat"><div class="num">4</div><div class="lbl">Categories</div></div>
    <div class="stat"><div class="num">100%</div><div class="lbl">Natural Materials</div></div>
  </div>
</div>

<div class="container">
  <div class="grid">
    {cat_cards_html}
  </div>

  <p style="text-align:center;color:#888;margin-top:8px;font-size:.9rem">
    All products ship across India &nbsp;·&nbsp;
    <a href="{BRAND_DOMAIN}/shop">Shop on Vanchai.in →</a>
  </p>
</div>

<footer>
  <p>&copy; {BRAND_NAME} — Made with ♥ in India</p>
  <p style="margin-top:6px"><a href="{BRAND_DOMAIN}">vanchai.in</a></p>
</footer>
</body>
</html>"""


def main():
    csv_path = CSV_FILE
    out_dir  = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/3] Loading products...")
    products  = load_products(csv_path)
    print(f"      {len(products)} products loaded.")

    # Group into categories
    cat_groups: dict[str, list[dict]] = {}
    for p in products:
        cat = get_category(p)
        if cat == "Other":
            continue
        cat_groups.setdefault(cat, []).append(p)

    print(f"[2/3] Generating {len(cat_groups)} category pages...")
    all_cat_slugs = {cat: CATEGORY_SLUGS.get(cat, slugify(f"category-{cat}")) for cat in cat_groups}

    for cat, prods in cat_groups.items():
        slug = all_cat_slugs[cat]
        html = render_category_page(cat, prods, all_cat_slugs)
        path = out_dir / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        print(f"      ✅ {slug}.html ({len(prods)} products, {len(prods)*len(INTENT_MODIFIERS)} page links)")

    print("[3/3] Generating master index page...")
    index_html = render_master_index(cat_groups)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")
    print("      ✅ index.html")

    total = sum(len(v) for v in cat_groups.values()) * len(INTENT_MODIFIERS)
    print(f"\nDone. {len(cat_groups)+1} hub pages written to ./{OUTPUT_DIR}/")
    print(f"These pages link to all {total} SEO landing pages.")
    print("\nNext: Run `python generate_sitemap.py` to include hub pages in the sitemap.")


if __name__ == "__main__":
    main()
