#!/usr/bin/env python3
"""
check_data.py — Pre-flight Data Quality Auditor
================================================
Run this before generate.py to catch bad rows, missing fields,
broken URLs, and data issues that will hurt SEO or cause errors.

Usage:
    python check_data.py
    python check_data.py --csv products.csv --fix   # auto-patch fixable issues
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

from config import CSV_FILE

REQUIRED_FIELDS  = ["vendorArticleName"]
PLATFORM_FIELDS  = ["wixUrl", "amazonUrl", "myntraUrl", "nykaaUrl"]  # at least one required
WARN_FIELDS      = ["imageUrl", "price", "productDetails"]
URL_FIELDS       = ["wixUrl", "amazonUrl", "myntraUrl", "nykaaUrl", "category_url"]


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_-]+", "-", text)[:120]


def is_valid_url(url: str) -> bool:
    return bool(url and url.startswith("http") and " " not in url)


def validate_json_ld(raw: str) -> tuple[bool, str]:
    if not raw or raw in ("#REF!", "#N/A", ""):
        return False, "empty"
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", raw)
    try:
        json.loads(cleaned)
        return True, "ok"
    except Exception as e:
        return False, str(e)[:60]


def run_audit(csv_path: str) -> dict:
    issues = defaultdict(list)
    warnings = defaultdict(list)
    rows_total = 0
    slugs_seen = set()

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            rows_total += 1
            sku  = row.get("vendorArticleNumber", f"row_{i}").strip()
            name = row.get("vendorArticleName", "").strip()

            # ── Critical issues ────────────────────────────────────────────
            for field in REQUIRED_FIELDS:
                val = row.get(field, "").strip()
                if not val or val.startswith("http") and field == "vendorArticleName":
                    issues["missing_required"].append(f"{sku}: missing '{field}'")

            # ── Duplicate slug detection ───────────────────────────────────
            # Downgraded to warning — keyword_registry.py first-registered-wins
            # so variant products are silently skipped at generation time.
            if name:
                slug = slugify(name)
                if slug in slugs_seen:
                    warnings["duplicate_slug"].append(f"{sku}: slug collision on '{name[:50]}'")
                slugs_seen.add(slug)

            # ── At least one platform URL required ────────────────────────
            if not any(is_valid_url(row.get(f, "")) for f in PLATFORM_FIELDS):
                issues["no_platform_url"].append(f"{sku}: no valid platform URL (wix/amazon/myntra/nykaa)")

            # ── URL validation ─────────────────────────────────────────────
            for field in URL_FIELDS:
                val = row.get(field, "").strip()
                if val and val not in ("NA", "N/A") and not is_valid_url(val):
                    issues["bad_url"].append(f"{sku}: invalid {field} → '{val[:60]}'")

            # ── JSON-LD validation ─────────────────────────────────────────
            jld_raw = row.get("json_ld", "").strip()
            ok, reason = validate_json_ld(jld_raw)
            if not ok and reason == "empty":
                warnings["missing_json_ld"].append(sku)
            elif not ok:
                # Invalid JSON-LD degrades rich snippets but generate.py handles it gracefully
                # Caused by unescaped quotes in product names within the JSON string values
                warnings["invalid_json_ld"].append(f"{sku}: {reason[:50]}")

            # ── Warnings ───────────────────────────────────────────────────
            for field in WARN_FIELDS:
                val = row.get(field, "").strip()
                if not val or val in ("No Image URL", "NA", "N/A", "Key [price] Not Found", "Key [description] Not Found"):
                    warnings[f"missing_{field}"].append(sku)

            # ── Price format ───────────────────────────────────────────────
            price = row.get("price", "").strip()
            if price and price not in ("", "Key [price] Not Found"):
                try:
                    float(price)
                except ValueError:
                    issues["bad_price"].append(f"{sku}: price='{price}'")

            # ── Short description ──────────────────────────────────────────
            desc = row.get("productDetails", "").strip()
            if desc and len(desc) < 50 and "Not Found" not in desc:
                warnings["short_description"].append(f"{sku}: {len(desc)} chars")

    return {"rows": rows_total, "issues": issues, "warnings": warnings}


def print_report(result: dict):
    rows    = result["rows"]
    issues  = result["issues"]
    warnings = result["warnings"]

    total_issues   = sum(len(v) for v in issues.values())
    total_warnings = sum(len(v) for v in warnings.values())

    print("=" * 60)
    print(f"  VANCHAI DATA QUALITY AUDIT REPORT")
    print("=" * 60)
    print(f"  Rows scanned : {rows}")
    print(f"  ❌ Issues    : {total_issues}")
    print(f"  ⚠️  Warnings : {total_warnings}")
    print("=" * 60)

    if total_issues == 0:
        print("\n✅  No critical issues found. Data is clean.\n")
    else:
        print("\n❌  CRITICAL ISSUES (will break generation or harm SEO):\n")
        for category, items in issues.items():
            print(f"  [{category.upper()}] — {len(items)} instance(s):")
            for item in items[:10]:
                print(f"    • {item}")
            if len(items) > 10:
                print(f"    … and {len(items)-10} more")
            print()

    if total_warnings > 0:
        print("\n⚠️  WARNINGS (degraded SEO, not blockers):\n")
        warn_order = [
            ("missing_imageUrl",        "Missing product images"),
            ("missing_price",           "Missing prices"),
            ("missing_productDetails",  "Missing descriptions"),
            ("missing_amazonUrl",       "No Amazon URL"),
            ("missing_json_ld",         "Missing JSON-LD schema"),
            ("invalid_json_ld",         "Invalid JSON-LD — generate.py handles gracefully"),
            ("short_description",       "Very short descriptions (<50 chars)"),
            ("duplicate_slug",          "Duplicate product names (variants) — keyword_registry keeps first, skips rest"),
        ]
        for key, label in warn_order:
            items = warnings.get(key, [])
            if items:
                skus = ", ".join(str(x) for x in items[:8])
                extra = f" … +{len(items)-8} more" if len(items) > 8 else ""
                print(f"  ⚠️  {label}: {len(items)} products")
                print(f"     SKUs: {skus}{extra}\n")

    # Summary table
    print("─" * 60)
    missing_imgs  = len(warnings.get("missing_imageUrl", []))
    missing_price = len(warnings.get("missing_price", []))
    missing_desc  = len(warnings.get("missing_productDetails", []))
    missing_jld   = len(warnings.get("missing_json_ld", []))

    print(f"  Products with full data  : {rows - max(missing_imgs, missing_price)}/{rows}")
    print(f"  Products ready to launch : {rows - total_issues}/{rows}")
    print("─" * 60)

    if total_issues > 0:
        print("\n  Fix critical issues in the XLSX and re-run xlsx_to_csv.py.\n")
    else:
        print("\n  ✅  Run `python generate.py` to build your pages.\n")


def main():
    parser = argparse.ArgumentParser(description="Vanchai data quality auditor")
    parser.add_argument("--csv", default=CSV_FILE, help="Path to products CSV")
    args = parser.parse_args()

    csv_path = args.csv
    if not Path(csv_path).exists():
        sys.exit(f"ERROR: File not found: {csv_path}")

    print(f"\nAuditing {csv_path} …\n")
    result = run_audit(csv_path)
    print_report(result)

    # Exit with error code if critical issues found
    if result["issues"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
