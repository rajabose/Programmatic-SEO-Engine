#!/usr/bin/env python3
"""
keyword_registry.py — Enforce one page per slug across all keyword-product pairs.

Scans keyword_product_pairs for slug collisions and registers each validated pair
in keyword_registry. Called automatically by generate.py --strict before emitting
any page. Can also be run standalone to audit or repair the registry.

Usage (from vanchai-seo-engine/):
    python scripts/keyword_registry.py            # audit + register all validated pairs
    python scripts/keyword_registry.py --fix      # register missing, report collisions
    python scripts/keyword_registry.py --check slug-goes-here  # check one slug
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "seo_engine.db"


def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        sys.exit(
            f"ERROR: {DB_PATH} not found.\n"
            "Run csv_to_sqlite.py then demand_validator.py first."
        )
    return sqlite3.connect(DB_PATH)


def is_slug_registered(conn: sqlite3.Connection, slug: str) -> bool:
    return bool(
        conn.execute("SELECT 1 FROM keyword_registry WHERE slug=?", (slug,)).fetchone()
    )


def register_slug(conn: sqlite3.Connection, slug: str, keyword: str, pair_id: int):
    """Register a slug. Raises ValueError if slug is already taken by a different pair."""
    existing = conn.execute(
        "SELECT pair_id FROM keyword_registry WHERE slug=?", (slug,)
    ).fetchone()
    if existing:
        if existing[0] == pair_id:
            return  # already registered to this pair — no-op
        raise ValueError(
            f"Slug collision: '{slug}' already registered to pair_id={existing[0]}; "
            f"attempted by pair_id={pair_id}."
        )
    conn.execute(
        "INSERT INTO keyword_registry (slug, keyword, pair_id) VALUES (?,?,?)",
        (slug, keyword, pair_id),
    )


def audit(conn: sqlite3.Connection) -> dict:
    """Return counts of registered, unregistered, and colliding pairs."""
    validated_pairs = conn.execute(
        "SELECT id, keyword, slug FROM keyword_product_pairs WHERE validated=1"
    ).fetchall()

    registered = unregistered = collisions = 0
    collision_details = []

    for pair_id, keyword, slug in validated_pairs:
        row = conn.execute(
            "SELECT pair_id FROM keyword_registry WHERE slug=?", (slug,)
        ).fetchone()
        if not row:
            unregistered += 1
        elif row[0] == pair_id:
            registered += 1
        else:
            collisions += 1
            collision_details.append(
                f"  slug='{slug}' registered to pair {row[0]}, "
                f"but pair {pair_id} ('{keyword[:60]}') also claims it"
            )

    return {
        "total_validated": len(validated_pairs),
        "registered":      registered,
        "unregistered":    unregistered,
        "collisions":      collisions,
        "collision_details": collision_details,
    }


def register_all_validated(conn: sqlite3.Connection) -> tuple[int, int]:
    """Register all validated pairs that aren't yet in the registry."""
    pairs = conn.execute(
        "SELECT id, keyword, slug FROM keyword_product_pairs WHERE validated=1"
    ).fetchall()

    added = skipped = 0
    for pair_id, keyword, slug in pairs:
        try:
            register_slug(conn, slug, keyword, pair_id)
            added += 1
        except ValueError as e:
            print(f"  [COLLISION] {e}")
            skipped += 1

    conn.commit()
    return added, skipped


def main():
    parser = argparse.ArgumentParser(description="Keyword slug registry manager")
    parser.add_argument("--fix",   action="store_true",
                        help="Register all unregistered validated pairs")
    parser.add_argument("--check", metavar="SLUG",
                        help="Check if a specific slug is registered")
    args = parser.parse_args()

    conn = get_conn()

    if args.check:
        row = conn.execute(
            "SELECT pair_id, keyword, registered_at FROM keyword_registry WHERE slug=?",
            (args.check,),
        ).fetchone()
        if row:
            print(f"REGISTERED: '{args.check}'")
            print(f"  pair_id      : {row[0]}")
            print(f"  keyword      : {row[1]}")
            print(f"  registered_at: {row[2]}")
        else:
            print(f"NOT REGISTERED: '{args.check}'")
        conn.close()
        return

    print("Auditing keyword registry …\n")
    result = audit(conn)

    print(f"  Validated pairs   : {result['total_validated']}")
    print(f"  Registered        : {result['registered']}")
    print(f"  Unregistered      : {result['unregistered']}")
    print(f"  Slug collisions   : {result['collisions']}")

    if result["collision_details"]:
        print("\n  COLLISIONS:")
        for detail in result["collision_details"]:
            print(detail)

    if args.fix:
        if result["unregistered"] > 0:
            print(f"\nRegistering {result['unregistered']} missing pairs …")
            added, skipped = register_all_validated(conn)
            print(f"  Added   : {added}")
            print(f"  Skipped : {skipped} (slug collisions — manual resolution required)")
        else:
            print("\nNothing to register — registry is up to date.")

    conn.close()


if __name__ == "__main__":
    main()
