#!/usr/bin/env python3
"""
generate_sitemap.py — Sitemap Builder for Vanchai SEO Engine
============================================================
Scans the docs/ output directory, chunks URLs into sitemaps of
max 5,000 links each (as per PRD), and writes a sitemap index.

Usage:
    python generate_sitemap.py
"""

import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from config import DISCOVER_DOMAIN, OUTPUT_DIR

CHUNK_SIZE    = 5000
TODAY         = date.today().isoformat()
SITEMAP_INDEX = "sitemap_index.xml"


def build_url_set(urls: list[str]) -> ET.Element:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        u = ET.SubElement(urlset, "url")
        ET.SubElement(u, "loc").text = url
        ET.SubElement(u, "lastmod").text = TODAY
        ET.SubElement(u, "changefreq").text = "monthly"
        ET.SubElement(u, "priority").text = "0.7"
    return urlset


def write_pretty(element: ET.Element, path: Path):
    ET.indent(element, space="  ")
    tree = ET.ElementTree(element)
    with open(path, "wb") as f:
        tree.write(f, xml_declaration=True, encoding="utf-8")


def main():
    out_dir = Path(OUTPUT_DIR)
    if not out_dir.exists():
        print(f"ERROR: Output directory '{OUTPUT_DIR}' not found. Run generate.py first.")
        return

    html_files = sorted(out_dir.glob("*.html"))
    # Include all pages EXCEPT 404 (which should never be indexed)
    # index.html and category pages are valuable crawl targets — include them
    urls = [
        f"{DISCOVER_DOMAIN}/{f.name}"
        for f in html_files
        if f.name != "404.html"
    ]

    if not urls:
        print("No HTML files found in output directory.")
        return

    print(f"Found {len(urls)} pages. Chunking into sitemaps of {CHUNK_SIZE}...")

    chunks = [urls[i:i + CHUNK_SIZE] for i in range(0, len(urls), CHUNK_SIZE)]
    sitemap_files = []

    for idx, chunk in enumerate(chunks, 1):
        fname = f"sitemap_{idx}.xml"
        path  = out_dir / fname
        urlset = build_url_set(chunk)
        write_pretty(urlset, path)
        sitemap_files.append(fname)
        print(f"  Written: {fname} ({len(chunk)} URLs)")

    # Build sitemap index
    index = ET.Element("sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for fname in sitemap_files:
        sm = ET.SubElement(index, "sitemap")
        ET.SubElement(sm, "loc").text = f"{DISCOVER_DOMAIN}/{fname}"
        ET.SubElement(sm, "lastmod").text = TODAY

    write_pretty(index, out_dir / SITEMAP_INDEX)
    print(f"\nSitemap index written: {OUTPUT_DIR}/{SITEMAP_INDEX}")
    print(f"Total: {len(urls)} URLs across {len(chunks)} sitemap(s).")
    print(f"\nSubmit to Google Search Console: {DISCOVER_DOMAIN}/{SITEMAP_INDEX}")


if __name__ == "__main__":
    main()
