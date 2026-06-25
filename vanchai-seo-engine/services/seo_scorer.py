#!/usr/bin/env python3
"""
seo_scorer.py — Score a generated HTML page 0-100 against standard SEO criteria.

Gate threshold: ≥ 80 to pass.

Rubric (100 pts total):
  Title present            10
  Title 30-65 chars        10
  Keyword in title         10
  Meta description present 10
  Meta description 120-160 10
  H1 present               15
  Keyword in first 100w    10
  Internal links ≥ 2       10
  Image with alt text       5
  JSON-LD schema present   10
"""

import re

THRESHOLD = 80


def _extract_text(html: str) -> str:
    text = re.sub(r'<(script|style|head|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def score(html: str, keyword: str) -> tuple[int, dict[str, int]]:
    """Return (total 0-100, breakdown dict)."""
    pts: dict[str, int] = {}
    kw = keyword.lower()

    # Title (30 pts)
    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
    if title_m:
        title = title_m.group(1).strip()
        pts['title_present']    = 10
        pts['title_length']     = 10 if 30 <= len(title) <= 65 else 5
        pts['keyword_in_title'] = 10 if kw in title.lower() else 0
    else:
        pts['title_present'] = pts['title_length'] = pts['keyword_in_title'] = 0

    # Meta description (20 pts)
    meta_m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']'
        r'|<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
        html, re.I,
    )
    if meta_m:
        meta = (meta_m.group(1) or meta_m.group(2) or '').strip()
        pts['meta_present'] = 10
        pts['meta_length']  = 10 if 120 <= len(meta) <= 160 else (5 if meta else 0)
    else:
        pts['meta_present'] = pts['meta_length'] = 0

    # H1 (15 pts)
    pts['h1_present'] = 15 if re.search(r'<h1[^>]*>', html, re.I) else 0

    # Keyword in first 100 words (10 pts)
    text = _extract_text(html)
    first_100 = ' '.join(text.split()[:100]).lower()
    pts['keyword_in_first_100'] = 10 if kw in first_100 else 0

    # Internal links ≥ 2 (10 pts)
    int_links = re.findall(r'href=["\'][^"\']*vanchai[^"\']*["\']', html, re.I)
    pts['internal_links'] = 10 if len(int_links) >= 2 else (5 if int_links else 0)

    # Image with alt text (5 pts)
    pts['image_with_alt'] = 5 if re.search(r'<img[^>]+alt=["\'][^"\']+["\']', html, re.I) else 0

    # JSON-LD schema (10 pts)
    pts['has_schema'] = 10 if 'application/ld+json' in html else 0

    return sum(pts.values()), pts
