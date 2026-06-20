#!/usr/bin/env python3
"""
generate_archive_index.py – Create archive_index.json from existing archive files.
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

def main():
    archives = []
    archive_path = Path(ARCHIVE_DIR)

    if archive_path.exists():
        # Look for all .html and .json files in the archive directory
        for f in sorted(archive_path.glob("*.html")):
            # Extract date from filename (assuming format YYYY-MM-DD.html)
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

    with open(INDEX_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Archive index generated: {len(archives)} archives")

if __name__ == "__main__":
    main()
