#!/usr/bin/env python3
"""
generate_archive_index.py – Create or update archive_index.json from archive files.
Ensures no duplicates – uses (date, file) as unique key.
"""

import json
import os
from pathlib import Path
from datetime import datetime

ARCHIVE_DIR = "archive"
INDEX_FILE = "archive_index.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    archive_path = Path(ARCHIVE_DIR)
    if not archive_path.exists():
        print("No archive directory found. Creating empty index.")
        save_json({"timestamp": datetime.now().isoformat(), "total": 0, "archives": []}, INDEX_FILE)
        return

    # Gather all .html files in the archive directory
    files = sorted(archive_path.glob("*.html"))
    archives = []
    seen = set()

    for f in files:
        # Extract date from filename (assuming YYYY-MM-DD.html)
        date_str = f.stem
        try:
            dt = datetime.fromisoformat(date_str)
            # Look for corresponding JSON
            json_file = archive_path / f"{date_str}.json"
            data = load_json(json_file, {})
            threats = data.get('threats', 0)
            gsci = data.get('gsci', None)
            predictions = data.get('predictions', 0)
        except:
            threats = 0
            gsci = None
            predictions = 0

        key = (dt.isoformat(), f.name)  # unique key
        if key not in seen:
            seen.add(key)
            archives.append({
                "date": dt.isoformat(),
                "file": f.name,
                "threats": threats,
                "gsci": gsci,
                "predictions": predictions,
                "summary": f"Archive from {dt.strftime('%d %b %Y')}"
            })

    # Sort by date (newest first)
    archives.sort(key=lambda x: x['date'], reverse=True)

    output = {
        "timestamp": datetime.now().isoformat(),
        "total": len(archives),
        "archives": archives
    }

    save_json(output, INDEX_FILE)
    print(f"✅ Archive index generated: {len(archives)} unique archives")

if __name__ == "__main__":
    main()
