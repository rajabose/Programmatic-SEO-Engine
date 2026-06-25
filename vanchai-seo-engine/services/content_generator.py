#!/usr/bin/env python3
"""
services/content_generator.py — Two-pass AI content generation for Vanchai SEO pages.

Pass 1: GPT-4o-mini generates a draft (fast, cheap ~₹0.10/page).
Pass 2: GPT-4o validates and fixes gate failures if the draft fails quality checks.

Output is cached to cache/openai/<slug>.html to avoid re-generating on reruns.
Cache is gitignored — rebuild by deleting the cache entry.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from services.prompt_builder import build_prompt, validate_prompt_output, classify_intent

CACHE_DIR = Path(__file__).parent.parent / "cache" / "openai"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DRAFT_MODEL    = "claude-haiku-4-5-20251001"  # pass 1 — fast, cheap
VALIDATE_MODEL = "claude-sonnet-4-6"           # pass 2 — only on gate failure


def _cache_key(slug: str) -> Path:
    return CACHE_DIR / f"{slug}.html"


def _load_cache(slug: str) -> str | None:
    path = _cache_key(slug)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _save_cache(slug: str, html: str):
    _cache_key(slug).write_text(html, encoding="utf-8")


def _call_claude(system: str, user: str, model: str) -> str:
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("anthropic package not installed. Run: pip install anthropic")

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def generate(
    keyword: str,
    modifier: str,
    product: dict,
    slug: str,
    force: bool = False,
) -> tuple[str, str, int]:
    """Generate or retrieve cached HTML content for the given keyword-product pair.

    Returns:
        (html, source, pass_number) where source is 'cache' | 'pass1' | 'pass2'
        and pass_number is 1 or 2.
    """
    if not force:
        cached = _load_cache(slug)
        if cached:
            return cached, "cache", 1

    system_prompt, user_prompt = build_prompt(keyword, modifier, product)

    # Pass 1 — draft
    draft_html = _call_claude(system_prompt, user_prompt, DRAFT_MODEL)
    warnings = validate_prompt_output(draft_html, keyword)

    if not warnings:
        _save_cache(slug, draft_html)
        return draft_html, "pass1", 1

    # Pass 2 — fix failures
    fix_prompt = f"""The following HTML content failed these pre-checks:
{chr(10).join(f"- {w}" for w in warnings)}

Original content:
{draft_html}

Fix ONLY the listed issues. Keep all correct content. Return the fixed HTML fragment only.
Target keyword: "{keyword}"
Word count target: {850 if classify_intent(modifier) == 'informational' else 350}–{950 if classify_intent(modifier) == 'informational' else 450} words.
"""
    fixed_html = _call_claude(system_prompt, fix_prompt, VALIDATE_MODEL)
    _save_cache(slug, fixed_html)
    return fixed_html, "pass2", 2


def generate_dry_run(
    keyword: str,
    modifier: str,
    product: dict,
    slug: str,
) -> str:
    """Return template HTML without calling OpenAI (for testing quality gates)."""
    intent = classify_intent(modifier)
    name    = product.get("vendorArticleName", "Product").strip()
    details = product.get("productDetails", "Sustainable home decor by Vanchai.").strip()
    price   = product.get("price", "")
    price_str = f"₹{price}" if price else ""

    # Platform links
    links_html = ""
    for label, key in [("Amazon", "amazonUrl"), ("Wix", "wixUrl"),
                        ("Myntra", "myntraUrl"), ("Nykaa", "nykaaUrl")]:
        url = product.get(key, "").strip()
        if url.startswith("http"):
            links_html += f'<a href="{url}" target="_blank" rel="noopener">{label}</a> | '
    links_html = links_html.rstrip(" |")

    target_words = 850 if intent == "informational" else 350
    # Minimal template — enough words to test gates, clearly labelled as dry-run
    filler = " ".join([f"Discover the {keyword} collection from Vanchai."] * (target_words // 10))

    return f"""<h1>{keyword.title()}</h1>
<p class="dry-run-notice">[DRY RUN — no OpenAI content]</p>
<h2>About {name[:60]}</h2>
<p>{details}</p>
<p>Looking for {keyword}? Vanchai offers this and more on Amazon and other platforms.
Explore handcrafted sustainable decor from Vanchai today.</p>
<h2>Why Choose Vanchai</h2>
<p>Vanchai is committed to sustainable Indian home decor. Our products are crafted with
care using natural materials. {filler[:300]}</p>
<h2>Styling Tips</h2>
<p>This product works beautifully as {modifier.lower()}.
{keyword.title()} brings a natural, earthy warmth to any space.</p>
<section class="faq">
<details><summary>What is {keyword}?</summary>
<p>It is a category of sustainable home decor items available from Vanchai.</p></details>
<details><summary>Where can I buy {keyword} in India?</summary>
<p>Available on Amazon, Myntra, Nykaa, and Vanchai's own store.</p></details>
<details><summary>How to style {keyword}?</summary>
<p>Use it {modifier.lower()} for an instant style upgrade.</p></details>
</section>
<p class="buy-cta">{price_str} — Buy now: {links_html or "check Vanchai.in"}</p>
"""
