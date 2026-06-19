#!/usr/bin/env python3
"""
record_scp_history.py – Append daily SCP values to history file.
"""

import json
from datetime import datetime
from pathlib import Path

THREATS_FILE = "threats.json"
HISTORY_FILE = "scp_history.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else []

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    if not threats:
        print("No threats found.")
        return

    scp_map = {}
    for t in threats:
        tid = t.get('id')
        if tid:
            scp_map[tid] = t.get('scp', 0.5)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "scp": scp_map
    }

    history = load_json(HISTORY_FILE, [])
    history.append(entry)
    # Keep last 365 days to avoid bloat
    if len(history) > 365:
        history = history[-365:]

    save_json(history, HISTORY_FILE)
    print(f"✅ SCP history updated: {len(scp_map)} threats logged.")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
record_scp_history.py – Append daily SCP values to history file.
"""

import json
from datetime import datetime
from pathlib import Path

THREATS_FILE = "threats.json"
HISTORY_FILE = "scp_history.json"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else []

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    threats_data = load_json(THREATS_FILE, {})
    threats = threats_data.get('threats', [])
    if not threats:
        print("No threats found.")
        return

    scp_map = {}
    for t in threats:
        tid = t.get('id')
        if tid:
            scp_map[tid] = t.get('scp', 0.5)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "scp": scp_map
    }

    history = load_json(HISTORY_FILE, [])
    history.append(entry)
    # Keep last 365 days to avoid bloat
    if len(history) > 365:
        history = history[-365:]

    save_json(history, HISTORY_FILE)
    print(f"✅ SCP history updated: {len(scp_map)} threats logged.")

if __name__ == "__main__":
    main()
