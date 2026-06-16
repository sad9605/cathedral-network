#!/usr/bin/env python3
# from mcp_gate import mcp_tool_gate
# from agent_ops_cockpit.ops.guardrails import tool_privilege_check
"""
daily-sweep.py – Cathedral Network OSINT Aggregator v2
Ingests all sources from the manual sweep: news, disasters, conflict, disease,
cybersecurity, alternative data, and passive RSS.
"""

import json
import requests
import feedparser
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
import re
import socks
import socket
import requests
from bs4 import BeautifulSoup
import time

def fetch_darkweb_ahmia(keywords: list = None):
    """
    Query Ahmia.fi (Tor search engine) for dark web content.
    Uses Tor SOCKS5 proxy.
    """
    if keywords is None:
        keywords = ["cathedral", "threat", "collapse", "warning", "crisis", "Hormuz", "Ebola", "famine"]
    
    # Configure Tor proxy
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket
    
    results = []
    for keyword in keywords[:5]:  # limit to 5 keywords to avoid long runtime
        try:
            # Search Ahmia
            search_url = f"https://ahmia.fi/search/?q={keyword}"
            response = requests.get(search_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract .onion links
                links = soup.find_all('a', href=True)
                onion_links = [a['href'] for a in links if '.onion' in a['href']]
                results.append({
                    'keyword': keyword,
                    'onion_links': onion_links[:5],  # limit
                    'count': len(onion_links),
                    'source': 'ahmia'
                })
            time.sleep(2)  # be polite
        except Exception as e:
            print(f"  Dark web search error ({keyword}): {e}")
            results.append({'keyword': keyword, 'error': str(e), 'source': 'ahmia'})
    
    return {'source': 'DarkWeb (Ahmia)', 'status': 'success', 'results': results}

import praw
import os
from datetime import datetime, timedelta

def fetch_reddit_osint(subreddits: list = None, keywords: list = None):
    """
    Fetch recent posts and comments from selected subreddits.
    Free tier – no API key required for read-only access.
    """
    if subreddits is None:
        subreddits = ['worldnews', 'geopolitics', 'preppers', 'collapse', 'OSINT']
    if keywords is None:
        keywords = ['crisis', 'warning', 'collapse', 'shortage', 'blackout', 'Hormuz', 'Ebola']
    
    results = []
    
    try:
        # Use Reddit's free read-only API
        import requests
        for subreddit in subreddits[:3]:  # limit to 3 for speed
            try:
                url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
                headers = {'User-Agent': 'Cathedral-Network-OSINT-Sweep/1.0'}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    for post in posts:
                        title = post.get('data', {}).get('title', '')
                        # Check for keywords
                        for kw in keywords:
                            if kw.lower() in title.lower():
                                results.append({
                                    'subreddit': subreddit,
                                    'title': title[:200],
                                    'url': post.get('data', {}).get('url', ''),
                                    'keyword': kw,
                                    'timestamp': datetime.fromtimestamp(
                                        post.get('data', {}).get('created_utc', 0)
                                    ).isoformat()
                                })
                                break
                time.sleep(1)  # be polite
            except Exception as e:
                print(f"  Reddit fetch error ({subreddit}): {e}")
                results.append({'subreddit': subreddit, 'error': str(e)})
    except Exception as e:
        print(f"  Reddit collector error: {e}")
    
    return {'source': 'Reddit OSINT', 'status': 'success', 'results': results[:20]}
from mastodon import Mastodon

def fetch_mastodon_timeline(keywords: list = None):
    """
    Fetch public timeline from Mastodon instances.
    """
    if keywords is None:
        keywords = ['crisis', 'warning', 'collapse', 'shortage', 'blackout']
    
    results = []
    instances = ['mastodon.social', 'mastodon.xyz', 'chaos.social']
    
    for instance in instances[:2]:  # limit to 2 instances
        try:
            mastodon = Mastodon(
                api_base_url=f'https://{instance}',
                version_check_mode='none'
            )
            timeline = mastodon.timeline_public(local=False, limit=20)
            for post in timeline:
                content = post.get('content', '')
                for kw in keywords:
                    if kw.lower() in content.lower():
                        results.append({
                            'instance': instance,
                            'content': content[:200],
                            'url': post.get('url', ''),
                            'keyword': kw,
                            'timestamp': post.get('created_at', '').isoformat() if post.get('created_at') else ''
                        })
                        break
            time.sleep(1)
        except Exception as e:
            print(f"  Mastodon fetch error ({instance}): {e}")
    
    return {'source': 'Mastodon', 'status': 'success', 'results': results[:20]}

from mastodon import Mastodon

def fetch_mastodon_timeline(keywords: list = None):
    """
    Fetch public timeline from Mastodon instances.
    """
    if keywords is None:
        keywords = ['crisis', 'warning', 'collapse', 'shortage', 'blackout']
    
    results = []
    instances = ['mastodon.social', 'mastodon.xyz', 'chaos.social']
    
    for instance in instances[:2]:  # limit to 2 instances
        try:
            mastodon = Mastodon(
                api_base_url=f'https://{instance}',
                version_check_mode='none'
            )
            timeline = mastodon.timeline_public(local=False, limit=20)
            for post in timeline:
                content = post.get('content', '')
                for kw in keywords:
                    if kw.lower() in content.lower():
                        results.append({
                            'instance': instance,
                            'content': content[:200],
                            'url': post.get('url', ''),
                            'keyword': kw,
                            'timestamp': post.get('created_at', '').isoformat() if post.get('created_at') else ''
                        })
                        break
            time.sleep(1)
        except Exception as e:
            print(f"  Mastodon fetch error ({instance}): {e}")
    
    return {'source': 'Mastodon', 'status': 'success', 'results': results[:20]}

# ----------------------------------------------------------------------
# Configuration
SWEEP_REPORT = "sweep_report.json"
GROUND_TRUTH = "ground_truth_summary.md"
THREATS_FILE = "threats.json"   # not directly read here, but for context

# ----------------------------------------------------------------------
# Helper functions
def fetch_feed(url: str, timeout=15) -> List[Dict]:
    """Fetch an RSS feed and return list of entries."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"  Feed error: {feed.bozo_exception}")
            return []
        return feed.entries
    except Exception as e:
        print(f"  Feed fetch error: {e}")
        return []

def fetch_json(url: str, timeout=15) -> Dict:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Cathedral-Network/1.0"})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# ----------------------------------------------------------------------
# 1. News & Press Wire RSS feeds (most provide RSS)
def fetch_news_rss() -> Dict[str, List[str]]:
    """Aggregate headlines from major news RSS feeds."""
    feeds = {
        "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
        "Reuters": "https://www.reuters.com/rssfeed/topNews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "France 24": "https://www.france24.com/en/france-24-live-news/rss",
        "Deutsche Welle": "https://rss.dw.com/rdf/xml/allnews",
        "Sky News": "https://feeds.skynews.com/feeds/rss/home.xml",
        "NHK World": "https://www3.nhk.or.jp/rss/news/cat0.xml",
        "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "South China Morning Post": "https://www.scmp.com/rss/2/feed",
        "Africa News": "https://www.africanews.com/feed/"
    }
    results = {}
    for name, url in feeds.items():
        entries = fetch_feed(url)
        headlines = [entry.get('title', '') for entry in entries[:5]]  # top 5
        results[name] = headlines
        time.sleep(0.5)  # be polite
    return results

# ----------------------------------------------------------------------
# 2. Official Disasters & Climate (already present)
def fetch_gdacs() -> Dict:
    """GDACS RSS feed."""
    url = "https://www.gdacs.org/xml/rss_40.xml"
    entries = fetch_feed(url)
    return {"source": "GDACS", "status": "success" if entries else "error", "alerts": len(entries)}

def fetch_usgs() -> Dict:
    """USGS real-time earthquakes (past day)."""
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    data = fetch_json(url)
    if "features" in data:
        return {"source": "USGS", "status": "success", "earthquakes": len(data["features"])}
    return {"source": "USGS", "status": "error", "error": data.get("error")}

def fetch_reliefweb_rss() -> Dict:
    """ReliefWeb RSS feed (no API key needed)."""
    url = "https://reliefweb.int/updates/rss.xml"
    entries = fetch_feed(url)
    return {"source": "ReliefWeb", "status": "success" if entries else "error", "reports": len(entries)}

# NASA FIRMS – requires API key for direct access; we can scrape or use alternate?
# For now, placeholder.
def fetch_firms():
    return {"source": "NASA FIRMS", "status": "simulated", "note": "API key required for real fire data"}

# IEA/EIA – public data via EIA API (requires key). Placeholder.
def fetch_eia():
    return {"source": "EIA", "status": "simulated", "note": "EIA API key not configured"}

# Floodlist – no API, we can scrape or skip
def fetch_floodlist():
    return {"source": "Floodlist", "status": "simulated", "note": "No machine‑readable feed"}

# ----------------------------------------------------------------------
# 3. Conflict & Military
def fetch_gdelt():
    """GDELT – we use the daily summary CSV (free, no key)."""
    url = "https://api.gdeltproject.org/api/v2/summary/summary?format=csv&d=1"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            # just record that we got data; too large to parse fully here
            return {"source": "GDELT", "status": "success", "note": "CSV summary fetched"}
        else:
            return {"source": "GDELT", "status": "error", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"source": "GDELT", "status": "error", "error": str(e)}

def fetch_acled():
    """ACLED – requires API key. Placeholder."""
    # Get key from environment variable ACLED_API_KEY
    api_key = None  # os.environ.get("ACLED_API_KEY")
    if api_key:
        # real fetch here
        return {"source": "ACLED", "status": "success", "simulated": False}
    return {"source": "ACLED", "status": "error", "error": "API key not set (register at acleddata.com)"}

def fetch_opensky():
    """OpenSky Network – live military aircraft (limited to non‑sensitive)."""
    url = "https://opensky-network.org/api/states/all"
    data = fetch_json(url)
    if "states" in data:
        return {"source": "OpenSky", "status": "success", "aircraft": len(data["states"])}
    return {"source": "OpenSky", "status": "error"}

def fetch_kalshi_odds():
    """Kalshi – get top markets odds (free, no key for read)."""
    url = "https://kalshi.com/api/v2/markets"
    data = fetch_json(url)
    if "markets" in data:
        # just return count
        return {"source": "Kalshi", "status": "success", "markets": len(data["markets"])}
    return {"source": "Kalshi", "status": "error"}

# Other military sources: ADS-B Exchange (requires API), DOD releases (RSS) – add later

# ----------------------------------------------------------------------
# 4. Disease Outbreaks
def fetch_who_don():
    """WHO Disease Outbreak News – RSS."""
    url = "https://www.who.int/rss/feeds/en/feeds-disease-outbreak-news.xml"
    entries = fetch_feed(url)
    return {"source": "WHO DON", "status": "success" if entries else "error", "reports": len(entries)}

def fetch_promed():
    """ProMED-Mail RSS."""
    url = "https://www.promedmail.org/rss.php"
    entries = fetch_feed(url)
    return {"source": "ProMED", "status": "success" if entries else "error", "reports": len(entries)}

# GeoSentinel 2.0 – not an API, but we can attempt their public page
def fetch_geosentinel():
    return {"source": "GeoSentinel", "status": "simulated", "note": "No public API; use ProMED/WHO instead"}

# ----------------------------------------------------------------------
# 5. AI & Cybersecurity
def fetch_aiid():
    """AI Incident Database – public API."""
    url = "https://incidentdatabase.ai/api/incidents?limit=10"
    data = fetch_json(url)
    if "incidents" in data:
        return {"source": "AIID", "status": "success", "incidents": len(data["incidents"])}
    return {"source": "AIID", "status": "error"}

def fetch_github_advisories():
    """GitHub Security Advisories – public."""
    url = "https://api.github.com/advisories?per_page=10"
    data = fetch_json(url)
    if isinstance(data, list):
        return {"source": "GitHub Advisories", "status": "success", "advisories": len(data)}
    return {"source": "GitHub Advisories", "status": "error"}

def fetch_cyber_news():
    """Cybersecurity news RSS (Krebs, BleepingComputer)."""
    feeds = {
        "KrebsOnSecurity": "https://krebsonsecurity.com/feed/",
        "BleepingComputer": "https://www.bleepingcomputer.com/feed/"
    }
    results = {}
    for name, url in feeds.items():
        entries = fetch_feed(url)
        results[name] = {"entries": len(entries)}
    return {"source": "Cyber News", "status": "success", "feeds": results}

# ----------------------------------------------------------------------
# 6. Alternative Data & Early Signals
def fetch_cloudflare_radar():
    """Cloudflare Radar – internet outages (needs API key for full, but we can check public page)."""
    # Public page: https://radar.cloudflare.com/outages
    # No API without key. Placeholder.
    return {"source": "Cloudflare Radar", "status": "simulated", "note": "API key required"}

def fetch_wikipedia_pageviews():
    """Wikipedia Pageview API – free, no key."""
    # Example: top pageviews for last day
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/06/14"
    data = fetch_json(url)
    if "items" in data:
        return {"source": "Wikipedia", "status": "success", "top_views": len(data["items"])}
    return {"source": "Wikipedia", "status": "error"}

def fetch_currency_flows():
    """USD/JPY and CHF/USD as safe‑haven proxies."""
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    data = fetch_json(url)
    if "rates" in data:
        jpy = data["rates"].get("JPY")
        chf = data["rates"].get("CHF")
        return {"source": "Currency", "status": "success", "USD_JPY": jpy, "USD_CHF": chf}
    return {"source": "Currency", "status": "error"}

# ----------------------------------------------------------------------
# 7. Passive & Bulk RSS (WorldMonitor, GlobalPulse) – simulated
def fetch_worldmonitor():
    return {"source": "WorldMonitor", "status": "simulated", "note": "WorldMonitor is a static dashboard, not an API"}

# ----------------------------------------------------------------------
# Main sweep orchestrator
def main():
    print("Starting daily OSINT sweep (expanded version)...")
    sweep_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feeds": {
            "gdacs": fetch_gdacs(),
            "usgs": fetch_usgs(),
            "reliefweb": fetch_reliefweb_rss(),
            "promed": fetch_promed(),
            "darkweb": fetch_darkweb_ahmia(),    # NEW
            "reddit": fetch_reddit_osint(),      # NEW
            "mastodon": fetch_mastodon_timeline(), # NEW
            # ... existing feeds ...
        }
    }
    # ... rest of main() ...

def main():
    print("Starting daily OSINT sweep (expanded version)...")
    sweep_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feeds": {
            "news_rss": fetch_news_rss(),
            "gdacs": fetch_gdacs(),
            "usgs": fetch_usgs(),
            "reliefweb": fetch_reliefweb_rss(),
            "nasa_firms": fetch_firms(),
            "eia": fetch_eia(),
            "gdelt": fetch_gdelt(),
            "acled": fetch_acled(),
            "opensky": fetch_opensky(),
            "kalshi": fetch_kalshi_odds(),
            "who_don": fetch_who_don(),
            "promed": fetch_promed(),
            "aiid": fetch_aiid(),
            "github_advisories": fetch_github_advisories(),
            "cyber_news": fetch_cyber_news(),
            "wikipedia_pageviews": fetch_wikipedia_pageviews(),
            "currency_flows": fetch_currency_flows(),
            "cloudflare_radar": fetch_cloudflare_radar(),
            "worldmonitor": fetch_worldmonitor()
        },
        "threats_summary": {}  # loaded from threats.json later
    }

    # Optionally load threat count from threats.json
    if Path(THREATS_FILE).exists():
        with open(THREATS_FILE, 'r') as f:
            threats_data = json.load(f)
            sweep_data["threats_summary"] = {
                "threat_count": len(threats_data.get("threats", [])),
                "last_updated": threats_data.get("last_updated")
            }

    with open(SWEEP_REPORT, 'w') as f:
        json.dump(sweep_data, f, indent=2)
    print(f"Saved sweep report to {SWEEP_REPORT}")

    # Generate ground truth summary (simple markdown from news headlines)
    with open(GROUND_TRUTH, 'w') as f:
        f.write(f"# Ground Truth Summary – {sweep_data['timestamp']}\n\n")
        f.write("## Top News Headlines (selected)\n")
        for source, headlines in sweep_data["feeds"].get("news_rss", {}).items():
            f.write(f"**{source}**:\n")
            for h in headlines[:3]:
                f.write(f"- {h}\n")
            f.write("\n")
        f.write("## Disaster and Conflict Alerts\n")
        for feed in ["gdacs", "usgs", "reliefweb", "opensky"]:
            data = sweep_data["feeds"].get(feed, {})
            status = data.get("status", "unknown")
            f.write(f"- {feed}: {status}\n")
    print(f"Saved summary to {GROUND_TRUTH}")

if __name__ == "__main__":
    main()
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass
