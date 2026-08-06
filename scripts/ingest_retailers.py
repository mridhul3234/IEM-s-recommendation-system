import os
import sys
import re
import time
import requests

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_client, upsert_iem
from infer import infer_target_profile
from embed import embed_texts

RETAILER_ENDPOINTS = [
    {
        "name": "Concept Kart",
        "url": "https://conceptkart.com/collections/in-ear-monitors/products.json"
    },
    {
        "name": "The Audio Store",
        "url": "https://www.theaudiostore.in/collections/audiocular/products.json"
    }
]

MAX_DESCRIPTION_LEN = 2500

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Remove extra whitespaces
    return " ".join(cleantext.split())

def fetch_products(base_url):
    all_products = []
    page = 1
    while True:
        url = f"{base_url}?limit=250&page={page}"
        print(f"Fetching {url}...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            products = data.get("products", [])
            if not products:
                break
            all_products.extend(products)
            page += 1
            time.sleep(0.5) # Be polite
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            break
    return all_products

def main():
    print("Connecting to Supabase...")
    try:
        client = get_client()
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return

    # Fetch existing IEMs to avoid re-processing or re-embedding
    print("Fetching existing IEM names for deduplication...")
    existing_iems = set()
    try:
        # Note: If the table gets very large, this might need pagination.
        resp = client.table("iems").select("name").execute()
        existing_iems = {row["name"] for row in resp.data}
    except Exception as e:
        print(f"Failed to fetch existing IEMs: {e}")

    processed_names_in_run = set()

    for retailer in RETAILER_ENDPOINTS:
        print(f"\n--- Processing Retailer: {retailer['name']} ---")
        products = fetch_products(retailer["url"])
        print(f"Found {len(products)} products at {retailer['name']}")

        for p in products:
            name = p.get("title", "").strip()
            if not name:
                continue
                
            if name in existing_iems or name in processed_names_in_run:
                print(f"Skipping '{name}' (already processed/exists)")
                continue
                
            print(f"\nProcessing '{name}'...")
            
            raw_desc = p.get("body_html", "")
            description = clean_html(raw_desc)
            if len(description) > MAX_DESCRIPTION_LEN:
                description = description[:MAX_DESCRIPTION_LEN] + "..."
                
            # If description is totally empty, give a default
            if not description:
                description = f"{name} by {p.get('vendor', 'Unknown')}."

            price = None
            variants = p.get("variants", [])
            if variants and len(variants) > 0:
                price = variants[0].get("price")
                
            vendor = p.get("vendor", "")
            tags = p.get("tags", [])
            
            print("  Inferring acoustic profile via Gemini...")
            # We call the existing infer_target_profile function
            inferred_features = infer_target_profile(description)
            
            # Augment features with metadata and tags
            features = inferred_features.copy()
            features["price"] = price
            features["brand"] = vendor
            features["tags"] = tags
            features["retailer"] = retailer["name"]
            features["acoustic_profile_source"] = "llm_estimated"
            
            print("  Generating embedding...")
            embeddings = embed_texts([description])
            if embeddings.shape[0] > 0:
                emb = embeddings[0]
            else:
                print("  Failed to generate embedding, skipping.")
                continue
                
            print("  Upserting to Supabase...")
            try:
                upsert_iem(
                    client=client,
                    name=name,
                    description=description,
                    features=features,
                    embedding=emb
                )
                processed_names_in_run.add(name)
                print(f"  Successfully ingested {name}")
            except Exception as e:
                print(f"  Failed to upsert {name}: {e}")

if __name__ == "__main__":
    main()
