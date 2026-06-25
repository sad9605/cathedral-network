#!/usr/bin/env python3
"""
telegram_fetcher.py – Fetch OSINT intelligence from Telegram channels.
Requires Telethon and API credentials.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Check if Telethon is available
try:
    from telethon import TelegramClient, sync, events
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Telethon not installed. Install with: pip install telethon")

# Telegram API credentials (set as environment variables)
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
PHONE = os.environ.get('TELEGRAM_PHONE')

# Channels to monitor (public OSINT channels)
CHANNELS = [
    'osint_x',              # OSINT X
    'intelt_news',          # IntelT News
    'war_insider',          # War Insider
    'geo_observer',         # Geo Observer
    'defense_news',         # Defense News
    'ukraine_war',          # Ukraine War updates
    'middle_east_alert',    # Middle East alerts
]

OUTPUT_FILE = "telegram_data.json"

def fetch_telegram():
    if not TELEGRAM_AVAILABLE or not all([API_ID, API_HASH, PHONE]):
        return {"status": "missing credentials or Telethon"}

    client = TelegramClient('session_name', API_ID, API_HASH)
    client.start(phone=PHONE)

    messages = []
    for channel_name in CHANNELS:
        try:
            entity = client.get_entity(channel_name)
            for msg in client.get_messages(entity, limit=5):
                if msg.text:
                    messages.append({
                        "channel": channel_name,
                        "date": msg.date.isoformat(),
                        "text": msg.text[:500]
                    })
        except Exception as e:
            print(f"Error fetching {channel_name}: {e}")

    client.disconnect()
    return {"source": "Telegram", "channels": CHANNELS, "messages": messages}

def main():
    print("📱 Fetching Telegram OSINT feeds...")
    data = {
        "timestamp": datetime.now().isoformat(),
        "telegram": fetch_telegram()
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Telegram data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
