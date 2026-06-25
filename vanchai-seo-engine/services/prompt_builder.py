#!/usr/bin/env python3
"""
services/prompt_builder.py — Intent-aware prompt factory for Vanchai SEO content.

Classifies each keyword modifier as informational or transactional, then
builds a GPT-4o-mini system+user prompt that will produce content passing
all 7 quality gates.
"""

from __future__ import annotations
import re
from typing import Literal

# Brand voice constraints baked into every prompt
BRAND_VOICE = """
Brand voice: Vanchai is a sustainable Indian home decor brand.
Write in a warm, knowledgeable tone — like an expert friend who decorates with purpose.
Avoid filler phrases: "In today's world", "In conclusion", "It goes without saying",
"As you know", "Look no further", "Are you looking for".
Never use clichés. Never pad. Every sentence must earn its place.
""".strip()

ANTI_FILLER = [
    "in today's world", "in conclusion", "look no further", "are you looking for",
    "it goes without saying", "as you know", "don't hesitate", "feel free to",
    "a wide range of", "second to none", "state of the art",
]

# Modifier → intent classification
_INFORMATIONAL_SIGNALS = [
    "for minimalist", "for boho", "for bedroom", "for modern indian", "for nursery",
    "for office desk", "for terrace", "for meditation", "for pooja", "for study",
    "for kitchen", "for bathroom", "for entrance", "for dining", "for reading",
    "for work from home", "for sustainable", "for coastal", "for instagrammable",
    "for zero-waste", "for earthy", "for japandi", "for wabi-sabi", "for vintage",
    "for ethnic", "for tropical", "for rustic farmhouse", "for luxury", "for budget",
    "for small space", "for rental", "for monsoon", "for summer", "for winter",
    "for new year",
]

_TRANSACTIONAL_SIGNALS = [
    "buy online", "price", "as a unique wedding", "as a housewarming", "as a table",
    "for eco-friendly gifting", "for rustic wedding", "for boho wedding",
    "for wedding mandap", "for bridal shower", "for anniversary gifting",
    "for corporate gifting", "for baby shower", "for birthday", "for diwali",
    "for festive", "for diy floral", "as elegant vase", "as a table centerpiece",
    "for dried flower bouquets", "for floral wreaths", "for shelf styling",
    "for photography", "for flat lay", "for youtube", "for home staging",
    "for cafe", "for airbnb", "under 500", "under 1000", "for affordable",
]

IntentType = Literal["informational", "transactional"]


def classify_intent(modifier: str) -> IntentType:
    lower = modifier.lower()
    if any(s in lower for s in _TRANSACTIONAL_SIGNALS):
        return "transactional"
    if any(s in lower for s in _INFORMATIONAL_SIGNALS):
        return "informational"
    # Default: room/aesthetic modifiers → informational
    return "informational"


def build_prompt(
    keyword: str,
    modifier: str,
    product: dict,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the content generator.

    Args:
        keyword:  Full target keyword (e.g. "dried flowers for minimalist balcony decor")
        modifier: The modifier part (e.g. "for Minimalist Balcony Decor")
        product:  Dict with keys: vendorArticleName, productDetails, material,
                  price, category, wixUrl, amazonUrl, myntraUrl, nykaaUrl
    """
    intent = classify_intent(modifier)
    target_words = 850 if intent == "informational" else 350

    name         = product.get("vendorArticleName", "").strip()
    details      = product.get("productDetails", "").strip()
    material     = product.get("material", "").strip()
    price        = product.get("price", "").strip()
    category     = product.get("category", "").strip().replace("_", " ").title()

    # Platform links for grounding
    platform_links = []
    for label, key in [("Amazon", "amazonUrl"), ("Wix", "wixUrl"),
                        ("Myntra", "myntraUrl"), ("Nykaa", "nykaaUrl")]:
        url = product.get(key, "").strip()
        if url.startswith("http"):
            platform_links.append(f"- {label}: {url}")
    buy_links = "\n".join(platform_links) or "(no platform URLs — skip buy CTA)"

    price_str = f"₹{price}" if price else "price varies"

    system_prompt = f"""{BRAND_VOICE}

Content requirements — MUST satisfy all of these:
1. Word count: {target_words}–{target_words + 100} words total (not counting HTML tags).
2. Target keyword: "{keyword}" — use it 3–5 times naturally. Do NOT repeat it every paragraph.
3. Keyword density: keyword phrase count / total words must be <3%. Self-check before finishing.
4. E-E-A-T signals that MUST appear:
   a. Brand name "Vanchai" at least twice in the body.
   b. Mention at least one purchase platform (Amazon, Myntra, Nykaa, or Wix) with context.
   c. One specific, grounded claim (material, dimension, or sustainability fact from the product data).
5. Content type: {"long-form editorial guide" if intent == "informational" else "product-focused buying guide"}.
6. Output format: HTML fragment only — no <html>, <head>, <body> wrappers. Include:
   - One <h1> with the keyword
   - Two or three <h2> subheadings
   - <p> paragraphs (no bullet-point-only responses)
   - A <section class="faq"> with 3 Q&A pairs in <details><summary> format
   - A <p class="buy-cta"> with platform purchase links (use the real URLs provided)
7. No placeholder text. All facts must come from the product data provided.
"""

    user_prompt = f"""Write a {intent} SEO page for the following.

Target keyword: {keyword}
Intent type: {intent}
Product name: {name}
Category: {category}
Material: {material or "natural / sustainable materials"}
Description: {details or "handcrafted sustainable home decor by Vanchai"}
Price: {price_str}
Purchase links:
{buy_links}

Requirements recap:
- {target_words}–{target_words + 100} words
- Include keyword "{keyword}" 3–5 times
- Include "Vanchai" at least twice
- Mention at least one buy platform
- End with a 3-question FAQ in <details><summary> format
- Output HTML fragment only (no wrapper tags)
"""

    return system_prompt, user_prompt


def validate_prompt_output(html: str, keyword: str) -> list[str]:
    """Pre-checks before running quality gates. Returns list of warnings."""
    warnings = []
    lower = html.lower()
    kw_lower = keyword.lower()

    count = lower.count(kw_lower)
    if count == 0:
        warnings.append(f"keyword '{keyword}' not found in output")
    elif count > 8:
        warnings.append(f"keyword appears {count}x — likely stuffed (max ~5)")

    if "vanchai" not in lower:
        warnings.append("brand name 'Vanchai' missing")

    if not re.search(r"amazon|myntra|nykaa|wix", lower):
        warnings.append("no platform mention found")

    for phrase in ANTI_FILLER:
        if phrase in lower:
            warnings.append(f"filler phrase detected: '{phrase}'")

    return warnings
