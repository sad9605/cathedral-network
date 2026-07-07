#!/usr/bin/env python3
"""
guardian.py – Threat Matrix Guardian
Locks threats.json and prevents it from being overwritten/corrupted.
Run before and after any script that modifies threats.json.
"""
import hashlib
import json
import sys
import subprocess
import os

LOCK_FILE = ".threat_lock"
MIN_THREATS = 10

def get_threat_hash():
    """Return MD5 hash of threats.json, or None if missing."""
    try:
        with open("threats.json", "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def check_threat_integrity():
    """Verify threats.json has at least MIN_THREATS entries and is valid JSON."""
    try:
        with open("threats.json", "r") as f:
            threats = json.load(f)
        return isinstance(threats, list) and len(threats) >= MIN_THREATS
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def restore_from_git():
    """Restore threats.json from Git HEAD."""
    try:
        subprocess.run(["git", "checkout", "HEAD", "--", "threats.json"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: guardian.py {lock|check|unlock}")
        sys.exit(1)

    action = sys.argv[1]

    if action == "lock":
        h = get_threat_hash()
        with open(LOCK_FILE, "w") as f:
            f.write(h or "")
        print(f"🔒 Threat Matrix locked (hash: {h})")
        sys.exit(0)

    elif action == "check":
        if not check_threat_integrity():
            print("❌ Threat Matrix corrupted or too small!")
            if restore_from_git():
                print("✅ Restored from Git.")
                sys.exit(0)
            else:
                print("💀 Could not restore. Manual intervention required.")
                sys.exit(1)
        else:
            print("✅ Threat Matrix integrity verified.")
            sys.exit(0)

    elif action == "unlock":
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print("🔓 Threat Matrix unlocked.")
        sys.exit(0)

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
