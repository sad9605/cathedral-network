#!/usr/bin/env python3
"""
generate_archive.py – Creates archive entries from daily sweep logs.
"""

import json
from datetime import datetime
from pathlib import Path

SWEEP_REPORT = "sweep_report.json"
ARCHIVE_DIR = "archive/"

def generate_archive():
    if not Path(SWEEP_REPORT).exists():
        print("No sweep report found.")
        return
    
    with open(SWEEP_REPORT) as f:
        sweep = json.load(f)
    
    timestamp = sweep.get('timestamp', datetime.now().isoformat())
    date = timestamp.split('T')[0]
    
    # Create archive entry
    archive_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Archive – {date}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 2rem; }}
        h1 {{ color: #5e2d8e; }}
    </style>
    </head>
    <body>
        <h1>Ground Truth – {date}</h1>
        <pre>{json.dumps(sweep, indent=2)}</pre>
        <footer><a href="../archive.html">Back to Archive</a></footer>
    </body>
    </html>
    """
    
    Path(ARCHIVE_DIR).mkdir(exist_ok=True)
    archive_path = f"{ARCHIVE_DIR}{date}.html"
    with open(archive_path, 'w') as f:
        f.write(archive_content)
    print(f"Generated archive: {archive_path}")

if __name__ == "__main__":
    generate_archive()
