#!/usr/bin/env python3
"""
eeat_enforcer.py — E-E-A-T signal gate.

Required signals:
  1. Brand name present in page text.
  2. <meta property="article:published_time"> tag present.
  3. At least one source platform mentioned (Wix/Amazon/Myntra/Nykaa).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from config import BRAND_NAME
except ImportError:
    BRAND_NAME = "Vanchai"

_PLATFORM_MENTIONS = ('Vanchai', 'Amazon', 'Myntra', 'Nykaa', 'vanchai.in')


def _extract_text(html: str) -> str:
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def check(html: str) -> tuple[bool, list[str]]:
    """Return (passed, list_of_missing_signals)."""
    missing: list[str] = []
    text = _extract_text(html)

    if BRAND_NAME.lower() not in text.lower():
        missing.append(f'brand name "{BRAND_NAME}" absent from page text')

    if not re.search(r'article:published_time', html, re.I):
        missing.append('missing <meta property="article:published_time">')

    if not any(p in html for p in _PLATFORM_MENTIONS):
        missing.append('no platform mention (Wix/Amazon/Myntra/Nykaa)')

    return len(missing) == 0, missing
