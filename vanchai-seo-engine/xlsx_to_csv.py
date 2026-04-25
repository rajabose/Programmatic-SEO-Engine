#!/usr/bin/env python3
"""
xlsx_to_csv.py — Convert the Vanchai product catalogue XLSX to CSV
===================================================================
Run this ONCE before running generate.py.

Usage:
    pip install openpyxl
    python xlsx_to_csv.py SEO-Automation-Product-catalogue.xlsx
"""

import csv
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("Install openpyxl: pip install openpyxl")

from config import CSV_FILE

COLUMNS = [
    "vendorArticleNumber", "vendorArticleName", "material",
    "productDetails", "productType", "amazonUrl", "myntraUrl",
    "nykaaUrl", "wixUrl", "imageUrl", "price", "category",
    "category_url", "json_ld",
]


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python xlsx_to_csv.py <path_to_xlsx>")

    xlsx_path = sys.argv[1]
    out_path  = Path(CSV_FILE)

    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        sys.exit("Worksheet is empty.")

    header = [str(c).strip() if c else "" for c in rows[0]]
    print(f"Header columns found: {header}")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()

        skipped = 0
        written = 0
        seen    = set()

        for row_vals in rows[1:]:
            row = dict(zip(header, row_vals))
            # Map to clean column names
            record = {
                "vendorArticleNumber": str(row.get("vendorArticleNumber") or row.get("vendorArticleNumber\xa0") or "").strip(),
                "vendorArticleName":   str(row.get("vendorArticleName") or "").strip(),
                "material":            str(row.get("material") or "").strip(),
                "productDetails":      str(row.get("productDetails") or "").strip(),
                "productType":         str(row.get("productType") or "").strip(),
                "amazonUrl":           str(row.get("amazonUrl") or "").strip(),
                "myntraUrl":           str(row.get("myntraUrl") or "").strip(),
                "nykaaUrl":            str(row.get("nykaaUrl") or "").strip(),
                "wixUrl":              str(row.get(" wixUrl") or row.get("wixUrl") or "").strip(),
                "imageUrl":            str(row.get("imageUrl") or "").strip(),
                "price":               str(row.get("price") or "").strip(),
                "category":            str(row.get("category") or "").strip(),
                "category_url":        str(row.get("category_url") or "").strip(),
                "json_ld":             str(row.get("json_ld") or "").strip(),
            }

            name = record["vendorArticleName"]
            sku  = record["vendorArticleNumber"]

            # Skip broken rows
            if not name or name.startswith("http") or "Not Found" in name or name.startswith("Key ["):
                skipped += 1
                continue
            if record["json_ld"] in ("#REF!", "#N/A", ""):
                record["json_ld"] = ""

            # Deduplicate by sku+name
            key = f"{sku}|{name}"
            if key in seen:
                skipped += 1
                continue
            seen.add(key)

            writer.writerow(record)
            written += 1

    print(f"\nDone. {written} products written to {out_path}  ({skipped} rows skipped).")


if __name__ == "__main__":
    main()
