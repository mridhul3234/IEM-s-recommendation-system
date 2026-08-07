"""
ingest_autoeq.py

Connects to AutoEQ GitHub repository, searches for matching raw measurement CSVs 
for IEMs currently in Supabase, and updates their acoustic profiles using true data.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from difflib import SequenceMatcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_client
from normalize import load_fr_csv, deviation_from_target, standard_grid
from features import extract_features, to_vector
from embed import embed_texts

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fetch_autoeq_tree():
    url = "https://api.github.com/repos/jaakkopasanen/AutoEq/git/trees/master?recursive=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'AcousticSearch'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        # Filter to just raw measurements for in-ears
        csv_files = [f['path'] for f in data.get('tree', []) 
                     if f['path'].startswith('measurements/') 
                     and '/data/in-ear/' in f['path']
                     and f['path'].endswith('.csv')]
        return csv_files
    except Exception as e:
        print(f"Failed to fetch AutoEQ tree: {e}")
        return []

def main():
    print("Fetching AutoEQ measurement tree...")
    autoeq_files = fetch_autoeq_tree()
    print(f"Found {len(autoeq_files)} measurement CSVs in AutoEQ.")
    
    # Pre-parse names for faster matching
    # path is like measurements/crinacle/data/in-ear/Moondrop Blessing 2.csv
    autoeq_entries = []
    for path in autoeq_files:
        basename = os.path.basename(path).replace('.csv', '')
        autoeq_entries.append({'name': basename, 'path': path})
        
    client = get_client()
    
    print("Fetching existing IEMs from Supabase...")
    # Fetch all IEMs
    # Supabase select limits to 1000 by default, our dataset is ~500
    response = client.table("iems").select("name, features, description").execute()
    iems = response.data
    print(f"Loaded {len(iems)} IEMs from Supabase.")
    
    target_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "targets", "Harman in-ear 2019.csv")
    target = load_fr_csv(target_path, name="Harman target")
    grid = standard_grid()
    
    matched_count = 0
    for iem in iems:
        db_name = iem['name']
        
        # Simple fuzzy match against AutoEq DB
        best_match = None
        best_score = 0
        
        for entry in autoeq_entries:
            score = similarity(db_name, entry['name'])
            if score > best_score:
                best_score = score
                best_match = entry
                
        # Threshold for match
        if best_score > 0.75:
            print(f"Match found for '{db_name}' -> AutoEQ '{best_match['name']}' (Score: {best_score:.2f})")
            
            # Download raw CSV
            raw_url = f"https://raw.githubusercontent.com/jaakkopasanen/AutoEq/master/{urllib.parse.quote(best_match['path'])}"
            try:
                req = urllib.request.Request(raw_url, headers={'User-Agent': 'AcousticSearch'})
                csv_data = urllib.request.urlopen(req).read().decode('utf-8')
                
                # Write to temp file
                tmp_path = "temp_fr.csv"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(csv_data)
                
                # Extract true features
                fr_data = load_fr_csv(tmp_path)
                freq, deviation = deviation_from_target(fr_data, target, grid_hz=grid)
                true_features = extract_features(freq, deviation)
                
                # Merge true features with existing (like price)
                new_features = iem['features']
                for k, v in true_features.items():
                    new_features[k] = v
                new_features['acoustic_profile_source'] = 'autoeq'
                
                # Update DB
                client.table("iems").update({"features": new_features}).eq("name", db_name).execute()
                matched_count += 1
                
                os.remove(tmp_path)
                print("  Successfully updated DB with true measurement data.")
                
            except Exception as e:
                print(f"  Error processing AutoEQ data for {db_name}: {e}")
                
    print(f"\nDone! Updated {matched_count} IEMs with true AutoEQ data.")

if __name__ == "__main__":
    main()
