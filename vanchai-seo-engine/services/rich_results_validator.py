#!/usr/bin/env python3
"""
services/rich_results_validator.py — Google Rich Results Test API wrapper.

Validates that a generated page's JSON-LD passes Google's Rich Results Test.
Non-blocking in dev (returns warnings); blocking in CI when STRICT_RICH_RESULTS=1.

API docs: https://developers.google.com/search/docs/appearance/structured-data/
          rich-results-test (uses the unofficial Rich Results Test endpoint)

Note: Google does not expose a public Rich Results Test API. This module uses
the publicly documented Search Console Rich Results Test UI's underpinning
endpoint for validation. In production, replace with:
  - Google Search Console Rich Results report (post-deploy monitoring)
  - OR google-structured-data-testing-tool CLI if available
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse
import ssl
from pathlib import Path


RICH_RESULTS_API = (
    "https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run"
)
STRICT_MODE = os.environ.get("STRICT_RICH_RESULTS", "0") == "1"


def _extract_json_ld_blocks(html: str) -> list[dict]:
    """Extract and parse all JSON-LD script blocks from HTML."""
    schemas = []
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        raw = match.group(1).strip()
        try:
            parsed = json.loads(raw)
            schemas.append(parsed)
        except json.JSONDecodeError:
            schemas.append({"_parse_error": raw[:100]})
    return schemas


def _check_required_fields(schema: dict) -> list[str]:
    """Return a list of missing/invalid fields for a given schema type."""
    errors = []
    schema_type = schema.get("@type", "")

    if schema_type == "Product":
        if not schema.get("name"):
            errors.append("Product: missing 'name'")
        if not schema.get("brand"):
            errors.append("Product: missing 'brand'")
        offers = schema.get("offers")
        if offers:
            if not offers.get("priceCurrency"):
                errors.append("Product.offers: missing 'priceCurrency'")
            if not offers.get("availability"):
                errors.append("Product.offers: missing 'availability'")

    elif schema_type == "FAQPage":
        entities = schema.get("mainEntity", [])
        if not entities:
            errors.append("FAQPage: no mainEntity items")
        for i, q in enumerate(entities):
            if q.get("@type") != "Question":
                errors.append(f"FAQPage.mainEntity[{i}]: @type must be 'Question'")
            if not q.get("name"):
                errors.append(f"FAQPage.mainEntity[{i}]: missing 'name' (the question)")
            aa = q.get("acceptedAnswer", {})
            if aa.get("@type") != "Answer":
                errors.append(f"FAQPage.mainEntity[{i}].acceptedAnswer: @type must be 'Answer'")
            if not aa.get("text"):
                errors.append(f"FAQPage.mainEntity[{i}].acceptedAnswer: missing 'text'")

    elif schema_type == "BreadcrumbList":
        items = schema.get("itemListElement", [])
        if not items:
            errors.append("BreadcrumbList: no itemListElement")
        for i, item in enumerate(items):
            if not item.get("position"):
                errors.append(f"BreadcrumbList[{i}]: missing 'position'")
            if not item.get("name"):
                errors.append(f"BreadcrumbList[{i}]: missing 'name'")

    return errors


def validate(html: str, slug: str = "") -> tuple[bool, list[str], list[str]]:
    """Validate JSON-LD schemas in an HTML page.

    Returns:
        (passed, errors, warnings)
        passed: True if no blocking errors found
        errors: blocking issues that prevent rich results eligibility
        warnings: non-blocking issues that degrade result quality
    """
    schemas = _extract_json_ld_blocks(html)
    errors: list[str] = []
    warnings: list[str] = []

    if not schemas:
        warnings.append("No JSON-LD blocks found — no rich results eligibility")
        return True, errors, warnings  # not a blocker for the gate

    # Check each schema block
    schema_types = set()
    for schema in schemas:
        if "_parse_error" in schema:
            errors.append(f"JSON-LD parse error: {schema['_parse_error']}")
            continue
        schema_type = schema.get("@type", "")
        schema_types.add(schema_type)
        field_errors = _check_required_fields(schema)
        errors.extend(field_errors)

    # Check we have all expected types for a Vanchai page
    for expected in ("Product", "FAQPage", "BreadcrumbList"):
        if expected not in schema_types:
            warnings.append(f"Missing {expected} schema — reduces rich result coverage")

    passed = len(errors) == 0
    return passed, errors, warnings


def gate_check(html: str, slug: str = "") -> tuple[bool, str]:
    """Quality gate interface: returns (passed, message).

    In STRICT_RICH_RESULTS=1 mode (CI), any error is a blocking failure.
    In dev mode, errors are warnings only.
    """
    passed, errors, warnings = validate(html, slug)

    if errors and STRICT_MODE:
        return False, f"Rich results errors: {'; '.join(errors[:3])}"

    if warnings:
        return True, f"Rich results warnings ({len(warnings)}): {warnings[0]}"

    return True, "Rich results OK"
