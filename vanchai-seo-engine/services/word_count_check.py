#!/usr/bin/env python3
"""
word_count_check.py — Word count gate.

Transactional page (has price + ≥1 platform link): ≥ 300 words.
Informational page (everything else):               ≥ 800 words.
"""

import re

INFORMATIONAL_MIN = 800
TRANSACTIONAL_MIN = 300

_PLATFORM_DOMAINS = ('vanchai.in', 'amazon.in', 'myntra.com', 'nykaa.com')


def _extract_text(html: str) -> str:
    text = re.sub(r'<(script|style|head|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _is_transactional(html: str) -> bool:
    has_price    = bool(re.search(r'₹\s*\d+', html))
    has_platform = any(d in html for d in _PLATFORM_DOMAINS)
    return has_price and has_platform


def check(html: str) -> tuple[int, str, bool]:
    """Return (word_count, page_type, passed)."""
    count     = len(_extract_text(html).split())
    page_type = 'transactional' if _is_transactional(html) else 'informational'
    min_words = TRANSACTIONAL_MIN if page_type == 'transactional' else INFORMATIONAL_MIN
    return count, page_type, count >= min_words
