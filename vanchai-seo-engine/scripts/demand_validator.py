#!/usr/bin/env python3
"""
demand_validator.py — Validate keyword-product pairs via DataForSEO search volume.

Reads all products from SQLite, generates candidate keyword × modifier pairs,
fetches search volumes (cached), and writes pairs with ≥100 searches/month to
keyword_product_pairs with validated=1.

Credentials via environment variables (or .env file):
    DATAFORSEO_LOGIN    your DataForSEO login email
    DATAFORSEO_PASSWORD your DataForSEO API password

Usage (from vanchai-seo-engine/):
    python scripts/demand_validator.py
    python scripts/demand_validator.py --min-volume 100 --dry-run
    python scripts/demand_validator.py --keyword "specific keyword to check"
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import ssl
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


def _ssl_ctx():
    """Return a no-verify SSL context for macOS dev environments where system
    certs aren't linked to Python. Production CI uses the default context."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Load .env if present (no external deps required)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DB_PATH    = Path(__file__).parent.parent / "db" / "seo_engine.db"
CACHE_PATH = Path(__file__).parent.parent / "cache" / "keyword_volumes.json"
SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"

DATAFORSEO_API = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
LOCATION_CODE  = 2356   # India
LANGUAGE_CODE  = "en"
BATCH_SIZE     = 100    # keywords per DataForSEO request
MIN_VOLUME_DEFAULT = 100


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:120]


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_cache(cache: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def dataforseo_auth() -> str:
    login    = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")
    if not login or not password:
        sys.exit(
            "ERROR: DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD env vars required.\n"
            "Set them in .env or export them before running.\n"
            "Use --dry-run to test without credentials."
        )
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    return f"Basic {token}"


def fetch_volumes(keywords: list[str], auth_header: str) -> dict[str, int]:
    """Call DataForSEO and return {keyword: search_volume}."""
    payload = json.dumps([{
        "keywords":      keywords,
        "location_code": LOCATION_CODE,
        "language_code": LANGUAGE_CODE,
    }]).encode()

    req = urllib.request.Request(
        DATAFORSEO_API,
        data=payload,
        headers={
            "Authorization": auth_header,
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    data = None
    for ctx in (None, _ssl_ctx()):
        try:
            kw = {"context": ctx} if ctx else {}
            with urllib.request.urlopen(req, timeout=30, **kw) as resp:
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            sys.exit(f"DataForSEO HTTP {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLError):
                continue  # retry with no-verify context
            sys.exit(f"DataForSEO connection error: {e.reason}")
    if data is None:
        sys.exit("DataForSEO SSL error — could not connect after retry")

    volumes: dict[str, int] = {}
    for task in data.get("tasks", []):
        if task.get("status_code") != 20000:
            print(f"  [warn] task error: {task.get('status_message', 'unknown')}")
            continue
        for result in task.get("result", []) or []:
            for item in result.get("items", []) or []:
                kw = item.get("keyword", "").lower()
                sv = item.get("search_volume") or 0
                volumes[kw] = sv

    return volumes


# Short, human-readable keyword seed per product category.
# These are what people actually type into Google — not the full product title.
CATEGORY_SEEDS = {
    "DRIED_PLANT":            "dried flowers",
    "ARTIFICIAL_PLANT":       "artificial plants for home",
    "BASKET":                 "handmade wicker baskets",
    "BLANKET":                "handwoven cotton blankets",
    "CANDLE_HOLDER":          "decorative candle holders",
    "COOKING_CONTAINER":      "terracotta cooking pots",
    "DECORATIVE_PILLOW_COVER": "boho pillow covers",
    "DRINKING_CUP":           "handmade ceramic cups",
}
DEFAULT_SEED = "sustainable home decor"


def get_products(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, vendor_article_name, category FROM products ORDER BY id"
    ).fetchall()
    return [{"id": r[0], "name": r[1], "category": r[2] or ""} for r in rows]


def build_candidates(products: list[dict], modifiers: list[str]) -> list[dict]:
    """Cross-join keyword_seed × modifiers, deduplicated.

    Each (seed, modifier) pair is unique — multiple products in the same category
    share a slug, and keyword_registry.py picks the first product to register it.
    """
    seen_slugs: set[str] = set()
    pairs = []
    for p in products:
        seed = CATEGORY_SEEDS.get(p["category"].upper(), DEFAULT_SEED)
        for mod in modifiers:
            kw   = f"{seed} {mod}"
            slug = slugify(kw)
            if slug in seen_slugs:
                # Different product, same keyword — register association but skip
                # duplicate keyword (demand only needs to be checked once per kw)
                continue
            seen_slugs.add(slug)
            pairs.append({
                "product_id": p["id"],
                "keyword":    kw,
                "modifier":   mod,
                "slug":       slug,
            })
    return pairs


def upsert_pair(conn: sqlite3.Connection, pair: dict, volume: int,
                min_volume: int, source: str = "dataforseo"):
    """Insert or update a keyword_product_pair row."""
    validated = 1 if volume >= min_volume else 0
    existing = conn.execute(
        "SELECT id, validated FROM keyword_product_pairs WHERE slug=?",
        (pair["slug"],),
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE keyword_product_pairs SET
               search_volume=?, validated=?, validation_source=?, validated_at=datetime('now')
               WHERE id=?""",
            (volume, validated, source, existing[0]),
        )
    else:
        conn.execute(
            """INSERT INTO keyword_product_pairs
               (product_id, keyword, modifier, slug, search_volume, validated,
                validation_source, validated_at)
               VALUES (?,?,?,?,?,?,?,datetime('now'))""",
            (pair["product_id"], pair["keyword"], pair["modifier"],
             pair["slug"], volume, validated, source),
        )


def main():
    parser = argparse.ArgumentParser(description="Validate keyword demand via DataForSEO")
    parser.add_argument("--min-volume", type=int, default=MIN_VOLUME_DEFAULT,
                        help="Minimum monthly searches to mark pair as validated (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use cached volumes only; skip DataForSEO API calls")
    parser.add_argument("--keyword", default=None,
                        help="Validate a single keyword instead of the full matrix")
    args = parser.parse_args()

    if not DB_PATH.exists():
        sys.exit(
            f"ERROR: {DB_PATH} not found.\n"
            "Run `python scripts/csv_to_sqlite.py` first."
        )

    conn = sqlite3.connect(DB_PATH)

    # Ensure schema exists (idempotent)
    if SCHEMA_PATH.exists():
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()

    # Import INTENT_MODIFIERS from config
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import INTENT_MODIFIERS

    print("[1/5] Loading products from DB …")
    products = get_products(conn)
    if not products:
        sys.exit("ERROR: No products in DB. Run csv_to_sqlite.py first.")
    print(f"      {len(products)} products loaded.")

    print("[2/5] Building candidate pairs …")
    if args.keyword:
        candidates = [{"product_id": p["id"],
                       "keyword":    args.keyword,
                       "modifier":   args.keyword,
                       "slug":       slugify(args.keyword)}
                      for p in products]
    else:
        candidates = build_candidates(products, INTENT_MODIFIERS)
    print(f"      {len(candidates)} candidate pairs.")

    print("[3/5] Loading keyword volume cache …")
    cache = load_cache()
    uncached = [c["keyword"] for c in candidates if c["keyword"].lower() not in cache]
    print(f"      {len(cache)} cached | {len(uncached)} need API lookup.")

    if uncached and not args.dry_run:
        auth = dataforseo_auth()
        print(f"[4/5] Fetching volumes from DataForSEO ({len(uncached)} keywords, "
              f"batches of {BATCH_SIZE}) …")
        fetched = 0
        for i in range(0, len(uncached), BATCH_SIZE):
            batch = uncached[i: i + BATCH_SIZE]
            print(f"      Batch {i // BATCH_SIZE + 1}: {len(batch)} keywords …", end=" ", flush=True)
            volumes = fetch_volumes(batch, auth)
            for kw in batch:
                cache[kw.lower()] = volumes.get(kw.lower(), 0)
            fetched += len(batch)
            print(f"done ({fetched}/{len(uncached)})")
            save_cache(cache)
            if i + BATCH_SIZE < len(uncached):
                time.sleep(0.5)  # be polite to the API
    elif uncached and args.dry_run:
        print("[4/5] --dry-run: skipping API calls; uncached keywords get volume=0.")
        for kw in uncached:
            cache[kw.lower()] = 0
    else:
        print("[4/5] All keywords cached — no API calls needed.")

    save_cache(cache)

    print("[5/5] Writing validated pairs to DB …")
    inserted = updated = validated_count = 0
    for pair in candidates:
        volume = cache.get(pair["keyword"].lower(), 0)
        existing = conn.execute(
            "SELECT id FROM keyword_product_pairs WHERE slug=?", (pair["slug"],)
        ).fetchone()

        upsert_pair(conn, pair, volume, args.min_volume)

        if existing:
            updated += 1
        else:
            inserted += 1
        if volume >= args.min_volume:
            validated_count += 1

    conn.commit()
    conn.close()

    print(f"\nDone.")
    print(f"  Pairs inserted  : {inserted}")
    print(f"  Pairs updated   : {updated}")
    print(f"  Validated (≥{args.min_volume}/mo): {validated_count} / {len(candidates)}")
    print(f"  Cache saved to  : {CACHE_PATH}")
    if args.dry_run:
        print("\n  NOTE: --dry-run used. Run without --dry-run to fetch real volumes.")


if __name__ == "__main__":
    main()
