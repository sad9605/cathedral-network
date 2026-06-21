#!/usr/bin/env python3
"""
fetch_breaking_news.py – Automatically fetch breaking news from OSINT feeds.
Updates breaking_news.json for the Breaking News page.
"""

import json
import re
import time
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# ---------- Config ----------
OUTPUT_FILE = "breaking_news.json"
MAX_ITEMS = 20  # keep latest 20
RELEVANCE_KEYWORDS = [
    "ceasefire", "peace", "treaty", "agreement", "aid", "vaccine", "breakthrough",
    "famine", "drought", "flood", "earthquake", "hurricane", "conflict", "war",
    "sanctions", "refugee", "displacement", "crisis", "emergency", "rescue",
    "reconstruction", "diplomatic", "humanitarian", "corridor", "evacuation"
]
SENTIMENT_POSITIVE = [
    "ceasefire", "peace", "treaty", "agreement", "aid", "vaccine", "breakthrough",
    "reconstruction", "diplomatic", "rescue", "corridor", "recovery"
]
SENTIMENT_NEGATIVE = [
    "famine", "drought", "flood", "earthquake", "hurricane", "conflict", "war",
    "sanctions", "refugee", "displacement", "crisis", "emergency", "attack", "killed"
]

# ---------- Feeds ----------
FEEDS = [
    {"name": "ReliefWeb", "url": "https://api.reliefweb.int/v1/disasters?format=json", "type": "api"},
    {"name": "GDACS", "url": "https://www.gdacs.org/xml/rss.xml", "type": "rss"},
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "type": "rss"},
    {"name": "Reuters", "url": "https://www.reutersagency.com/feed/?best-topic=top-news&country=global", "type": "rss"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "rss"},
]

# ---------- Helpers ----------
def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def is_relevant(title, description):
    text = (title + " " + description).lower()
    for kw in RELEVANCE_KEYWORDS:
        if kw in text:
            return True
    return False

def classify_sentiment(title, description):
    text = (title + " " + description).lower()
    pos_score = sum(1 for w in SENTIMENT_POSITIVE if w in text)
    neg_score = sum(1 for w in SENTIMENT_NEGATIVE if w in text)
    if pos_score > neg_score:
        return "Positive"
    elif neg_score > pos_score:
        return "Negative"
    else:
        return "Neutral"

def fetch_rss_feed(url):
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:20]:
            entries.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", datetime.now().strftime("%Y-%m-%d")),
                "source": url
            })
        return entries
    except Exception as e:
        print(f"  RSS error for {url}: {e}")
        return []

def fetch_api_feed(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entries = []
        # ReliefWeb format: data.data
        if "data" in data:
            for item in data["data"][:20]:
                fields = item.get("fields", {})
                entries.append({
                    "title": fields.get("name", ""),
                    "description": fields.get("description", ""),
                    "link": item.get("href", ""),
                    "published": fields.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "source": url
                })
        else:
            # fallback
            entries = [{"raw": data}]
        return entries
    except Exception as e:
        print(f"  API error for {url}: {e}")
        return []

# ---------- Main ----------
def fetch_breaking_news():
    print("📰 Fetching breaking news...")
    all_entries = []
    for feed in FEEDS:
        print(f"  Fetching {feed['name']}...")
        if feed["type"] == "rss":
            entries = fetch_rss_feed(feed["url"])
        else:
            entries = fetch_api_feed(feed["url"])
        for e in entries:
            # Skip if missing title
            if not e.get("title"):
                continue
            # Relevance filter
            if not is_relevant(e.get("title", ""), e.get("description", "")):
                continue
            # Classify sentiment
            category = classify_sentiment(e.get("title", ""), e.get("description", ""))
            # For impact, we can use simple rules: Critical if mention "famine", "war", etc.
            text = (e.get("title", "") + " " + e.get("description", "")).lower()
            if any(w in text for w in ["famine", "war", "attack", "earthquake", "hurricane"]):
                impact = "Critical"
            elif any(w in text for w in ["ceasefire", "aid", "vaccine", "breakthrough"]):
                impact = "High"
            else:
                impact = "Medium"
            # Build item
            all_entries.append({
                "title": e.get("title", ""),
                "description": e.get("description", "")[:300],
                "link": e.get("link", ""),
                "date": e.get("published", datetime.now().strftime("%Y-%m-%d")),
                "source": feed["name"],
                "category": category,
                "impact": impact
            })
        time.sleep(0.5)

    # Deduplicate by title
    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Sort by date descending (try to parse)
    try:
        unique.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
    except:
        pass  # keep as is

    # Limit to latest
    latest = unique[:MAX_ITEMS]

    output = {
        "timestamp": datetime.now().isoformat(),
        "items": latest
    }

    save_json(output, OUTPUT_FILE)
    print(f"✅ Breaking news updated: {len(latest)} items")

if __name__ == "__main__":
    fetch_breaking_news()
