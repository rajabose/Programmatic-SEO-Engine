#!/usr/bin/env python3
"""
link_checker.py — Platform link liveness gate.

Extracts Wix / Amazon / Myntra / Nykaa hrefs from HTML,
checks each with a HEAD request, caches results 24 h in SQLite.

Gate pass conditions:
  - No platform URLs found in page → pass (nothing to check)
  - At least one URL responds → pass
  - All URLs present but all dead → BLOCKING fail
"""

import re
import sqlite3
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

CACHE_HOURS     = 24
REQUEST_TIMEOUT = 5   # seconds per HEAD request

_PATTERNS: dict[str, str] = {
    'wix':    r'href=["\']([^"\']*vanchai\.in[^"\']*)["\']',
    'amazon': r'href=["\']([^"\']*amazon\.[^"\']*)["\']',
    'myntra': r'href=["\']([^"\']*myntra\.com[^"\']*)["\']',
    'nykaa':  r'href=["\']([^"\']*nykaa\.com[^"\']*)["\']',
}


def _ensure_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS link_cache (
            url         TEXT    PRIMARY KEY,
            status_code INTEGER NOT NULL DEFAULT 0,
            live        INTEGER NOT NULL DEFAULT 0,
            checked_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _get_cached(conn: sqlite3.Connection, url: str) -> tuple[bool, int] | None:
    cutoff = (datetime.utcnow() - timedelta(hours=CACHE_HOURS)).isoformat()
    row = conn.execute(
        "SELECT live, status_code FROM link_cache WHERE url=? AND checked_at > ?",
        (url, cutoff),
    ).fetchone()
    return (bool(row[0]), row[1]) if row else None


def _store(conn: sqlite3.Connection, url: str, status: int, live: bool):
    conn.execute(
        "INSERT OR REPLACE INTO link_cache (url, status_code, live, checked_at) "
        "VALUES (?,?,?,datetime('now'))",
        (url, status, int(live)),
    )
    conn.commit()


import ssl as _ssl


def _no_verify_ctx() -> _ssl.SSLContext:
    """SSL context that skips cert verification — used as fallback for dev environments."""
    ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return ctx


def _is_ssl_error(exc: Exception) -> bool:
    """Return True if exception is an SSL error (possibly wrapped in URLError)."""
    if isinstance(exc, _ssl.SSLError):
        return True
    if isinstance(exc, urllib.error.URLError):
        return isinstance(exc.reason, _ssl.SSLError)
    return False


def _head(url: str) -> tuple[int, bool]:
    for ctx in (None, _no_verify_ctx()):
        # Pass 1: default SSL (CI/production).
        # Pass 2: no-verify SSL (macOS dev without certs installed).
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'VanchaiSEOBot/1.0 (+https://discover.vanchai.in)')
            kw = {"context": ctx} if ctx else {}
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, **kw) as resp:
                return resp.status, resp.status < 400
        except urllib.error.HTTPError as e:
            return e.code, e.code < 400
        except Exception as e:
            if _is_ssl_error(e):
                continue  # retry with no-verify context
            return 0, False
    return 0, False


def check(
    html: str,
    db_path: Path = Path(__file__).parent.parent / 'db' / 'seo_engine.db',
) -> tuple[dict[str, dict], bool]:
    """
    Return (results_per_platform, any_live).
    results_per_platform: {platform: {url, status, live, cached}}
    any_live: True if at least one URL responds successfully.
    """
    # Extract first matching URL per platform
    urls: dict[str, str] = {}
    for platform, pattern in _PATTERNS.items():
        m = re.search(pattern, html, re.I)
        if m:
            urls[platform] = m.group(1)

    if not urls:
        return {}, True  # no URLs = vacuously pass

    conn = sqlite3.connect(db_path) if db_path.exists() else None
    if conn:
        _ensure_table(conn)

    results: dict[str, dict] = {}
    to_fetch: dict[str, str] = {}

    for platform, url in urls.items():
        cached = _get_cached(conn, url) if conn else None
        if cached is not None:
            live, status = cached
            results[platform] = {'url': url, 'status': status, 'live': live, 'cached': True}
        else:
            to_fetch[platform] = url

    if to_fetch:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_head, url): (platform, url)
                       for platform, url in to_fetch.items()}
            for future in as_completed(futures):
                platform, url = futures[future]
                try:
                    status, live = future.result()
                except Exception:
                    status, live = 0, False
                results[platform] = {'url': url, 'status': status, 'live': live, 'cached': False}
                if conn:
                    _store(conn, url, status, live)

    if conn:
        conn.close()

    any_live = any(r['live'] for r in results.values())
    return results, any_live
