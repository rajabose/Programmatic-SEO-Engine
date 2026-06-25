#!/usr/bin/env python3
"""
csv_to_sqlite.py — Load products.csv into the SQLite products table.

Idempotent: re-running updates changed fields, skips unchanged rows.

Usage (from vanchai-seo-engine/):
    python scripts/csv_to_sqlite.py
    python scripts/csv_to_sqlite.py --csv path/to/products.csv
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "db" / "seo_engine.db"
SQL_PATH = Path(__file__).parent.parent / "db" / "schema.sql"

# Column name in CSV → column name in DB
CSV_TO_DB = {
    "vendorArticleNumber": "vendor_article_number",
    "vendorArticleName":   "vendor_article_name",
    "material":            "material",
    "productDetails":      "product_details",
    "productType":         "product_type",
    "amazonUrl":           "amazon_url",
    "myntraUrl":           "myntra_url",
    "nykaaUrl":            "nykaa_url",
    "wixUrl":              "wix_url",
    "imageUrl":            "image_url",
    "price":               "price",
    "category":            "category",
    "category_url":        "category_url",
    "json_ld":             "json_ld",
}


def ensure_schema(conn: sqlite3.Connection):
    if not SQL_PATH.exists():
        sys.exit(f"ERROR: schema file not found: {SQL_PATH}")
    conn.executescript(SQL_PATH.read_text())
    conn.commit()


def load_csv(csv_path: Path) -> list[dict]:
    rows = []
    seen = set()
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = row.get("vendorArticleName", "").strip()
            sku  = row.get("vendorArticleNumber", "").strip()
            if not name or name.startswith("http") or name.startswith("Key ["):
                continue
            key = f"{sku}|{name}"
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def upsert_products(conn: sqlite3.Connection, rows: list[dict]) -> tuple[int, int]:
    inserted = updated = 0
    for row in rows:
        db_row = {db_col: row.get(csv_col, "").strip()
                  for csv_col, db_col in CSV_TO_DB.items()}
        db_row["updated_at"] = "datetime('now')"  # placeholder — handled below

        # Check if row exists
        existing = conn.execute(
            "SELECT id FROM products WHERE vendor_article_number=? AND vendor_article_name=?",
            (db_row["vendor_article_number"], db_row["vendor_article_name"]),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE products SET
                    material=?, product_details=?, product_type=?,
                    amazon_url=?, myntra_url=?, nykaa_url=?, wix_url=?,
                    image_url=?, price=?, category=?, category_url=?, json_ld=?,
                    updated_at=datetime('now')
                   WHERE id=?""",
                (
                    db_row["material"], db_row["product_details"], db_row["product_type"],
                    db_row["amazon_url"], db_row["myntra_url"], db_row["nykaa_url"],
                    db_row["wix_url"], db_row["image_url"], db_row["price"],
                    db_row["category"], db_row["category_url"], db_row["json_ld"],
                    existing[0],
                ),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO products
                   (vendor_article_number, vendor_article_name, material,
                    product_details, product_type, amazon_url, myntra_url,
                    nykaa_url, wix_url, image_url, price, category, category_url, json_ld)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    db_row["vendor_article_number"], db_row["vendor_article_name"],
                    db_row["material"], db_row["product_details"], db_row["product_type"],
                    db_row["amazon_url"], db_row["myntra_url"], db_row["nykaa_url"],
                    db_row["wix_url"], db_row["image_url"], db_row["price"],
                    db_row["category"], db_row["category_url"], db_row["json_ld"],
                ),
            )
            inserted += 1

    conn.commit()
    return inserted, updated


def main():
    parser = argparse.ArgumentParser(description="Load products CSV into SQLite")
    parser.add_argument("--csv", default="products.csv", help="Path to products CSV")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        sys.exit(
            f"ERROR: {csv_path} not found.\n"
            "Run `python xlsx_to_csv.py <catalogue.xlsx>` first to generate it."
        )

    print(f"[1/3] Connecting to {DB_PATH} …")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    print("[2/3] Ensuring schema …")
    ensure_schema(conn)

    print(f"[3/3] Loading {csv_path} …")
    rows = load_csv(csv_path)
    print(f"      {len(rows)} valid rows read from CSV.")

    inserted, updated = upsert_products(conn, rows)
    conn.close()

    print(f"\nDone. {inserted} inserted, {updated} updated in products table.")
    print(f"DB: {DB_PATH}")


if __name__ == "__main__":
    main()
