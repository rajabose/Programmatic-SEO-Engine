#!/usr/bin/env python3
"""
keyword_density.py — Keyword density gate.

Keyword density = (phrase_occurrences × phrase_word_count) / total_words.
Gate: must be < 3% to pass.
"""

import re

MAX_DENSITY = 0.03  # 3%


def _extract_text(html: str) -> str:
    text = re.sub(r'<(script|style|head|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def check(html: str, keyword: str) -> tuple[float, int]:
    """Return (density_fraction, total_word_count). Pass when density < MAX_DENSITY."""
    text  = _extract_text(html).lower()
    words = text.split()
    total = len(words)
    if total == 0:
        return 0.0, 0
    kw        = keyword.lower()
    kw_words  = len(kw.split())
    count     = len(re.findall(re.escape(kw), text))
    density   = (count * kw_words) / total
    return density, total
