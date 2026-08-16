"""Export retailer listings for human review; never infer acoustic measurements.

Retail marketing prose may provide an observed price, but it cannot establish a
frequency-response profile. This script deliberately does not access Supabase
or call an LLM. A reviewed, exact-name price catalog can then be supplied to
``migrate_to_supabase.py --price-catalog``.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests

RETAILER_ENDPOINTS = [
    {"name": "Concept Kart", "url": "https://conceptkart.com/collections/in-ear-monitors/products.json"},
    {"name": "The Audio Store", "url": "https://www.theaudiostore.in/collections/audiocular/products.json"},
]
MAX_DESCRIPTION_LEN = 2500


def clean_html(raw_html: str) -> str:
    return " ".join(re.sub(r"<.*?>", "", raw_html or "").split())


def fetch_products(base_url: str) -> list[dict]:
    products: list[dict] = []
    for page in range(1, 100):
        response = requests.get(f"{base_url}?limit=250&page={page}", timeout=15)
        response.raise_for_status()
        batch = response.json().get("products", [])
        if not batch:
            return products
        products.extend(batch)
        time.sleep(0.5)
    raise RuntimeError("Retailer pagination exceeded the safety limit.")


def _listing(product: dict, retailer: dict) -> dict | None:
    name = str(product.get("title") or "").strip()
    if not name:
        return None
    variants = product.get("variants") or []
    first_variant = variants[0] if variants else {}
    return {
        "name": name,
        "brand": product.get("vendor") or "",
        "price": first_variant.get("price"),
        "currency": "INR",
        "retailer": retailer["name"],
        "source_url": f"{retailer['url']}?handle={product.get('handle', '')}",
        "description": clean_html(product.get("body_html", ""))[:MAX_DESCRIPTION_LEN],
        "review_status": "unreviewed",
        "acoustic_profile_source": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export retailer listings for manual catalog review.")
    parser.add_argument("--output", default="retailer_catalog_review.json")
    args = parser.parse_args()

    listings: list[dict] = []
    for retailer in RETAILER_ENDPOINTS:
        try:
            listings.extend(filter(None, (_listing(product, retailer) for product in fetch_products(retailer["url"]))))
        except requests.RequestException as exc:
            print(f"Failed to fetch {retailer['name']}: {exc}")

    output = Path(args.output).resolve()
    output.write_text(json.dumps(listings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(listings)} unreviewed listings to {output}. No database records were changed.")


if __name__ == "__main__":
    main()
