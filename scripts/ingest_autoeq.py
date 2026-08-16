"""Apply only human-approved, exact AutoEq measurement matches to Supabase."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import get_client
from backend.features import extract_features
from backend.normalize import load_fr_csv, deviation_from_target, standard_grid

AUTOEQ_RAW_URL = "https://raw.githubusercontent.com/jaakkopasanen/AutoEq/master/"


def load_approved_matches(path: str) -> list[dict]:
    """Require an explicit source path for every approved database product."""
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("Approved match file must contain a JSON array.")
    approved: list[dict] = []
    for entry in entries:
        if (isinstance(entry, dict) and entry.get("review_status") == "approved"
                and isinstance(entry.get("iem_name"), str)
                and isinstance(entry.get("autoeq_path"), str)
                and entry["autoeq_path"].startswith("measurements/")):
            approved.append(entry)
    return approved


def fetch_measurement(path: str) -> str:
    url = AUTOEQ_RAW_URL + urllib.parse.quote(path, safe="/")
    request = urllib.request.Request(url, headers={"User-Agent": "AcousticSearch"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reviewed AutoEq matches.")
    parser.add_argument("--approved-matches", required=True, help="JSON array approved by a human reviewer")
    parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()
    if os.environ.get("APP_ENV", "development").lower() in {"prod", "production"} and not args.confirm_production:
        parser.error("Production writes require --confirm-production.")

    matches = load_approved_matches(args.approved_matches)
    client = get_client()
    target = load_fr_csv(PROJECT_ROOT / "data" / "sample_data" / "targets" / "Harman in-ear 2019.csv", name="Harman target")
    grid = standard_grid()
    updated = 0

    for match in matches:
        name, autoeq_path = match["iem_name"], match["autoeq_path"]
        try:
            measurement = fetch_measurement(autoeq_path)
            with tempfile.NamedTemporaryFile("w", suffix=".csv", encoding="utf-8", delete=False) as handle:
                handle.write(measurement)
                temp_path = handle.name
            try:
                fr_data = load_fr_csv(temp_path)
                frequency, deviation = deviation_from_target(fr_data, target, grid_hz=grid)
                measured = extract_features(frequency, deviation)
            finally:
                os.unlink(temp_path)

            response = client.table("iems").select("features").eq("name", name).execute()
            if not response.data:
                print(f"Skipped {name}: no exact database product name.")
                continue
            features = dict(response.data[0].get("features") or {})
            features.update(measured)
            features["acoustic_profile_source"] = "autoeq"
            features["acoustic_profile_path"] = autoeq_path
            client.table("iems").update({"features": features}).eq("name", name).execute()
            updated += 1
            print(f"Updated {name} from approved AutoEq path {autoeq_path}.")
        except Exception as exc:
            print(f"Failed to process {name}: {exc}")
    print(f"Completed: {updated} approved measurement updates.")


if __name__ == "__main__":
    main()
