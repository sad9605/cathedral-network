#!/usr/bin/env python3
import json
import logging
import os
import time
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------------------------------
# CONFIGURATION
# ------------------------------
SINCE = datetime.now(timezone.utc) - timedelta(hours=24)
JSON_OUT = "sweep_report.json"
MD_OUT = "ground_truth_summary.md"
LOG_FILE = "sweep.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

WATCHLIST = [
    "ai escape", "zero-day", "bioweapon", "data centre stress", "grid failure",
    "cascade", "nuclear incident", "food shortage", "cyber attack"
]

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def fetch_rss(url: str, max_entries: int = 50) -> List[Dict]:
    try:
        feed = feedparser.parse(url)
        entries = []
        for e in feed.entries[:max_entries]:
            pub = None
            if hasattr(e, 'published_parsed') and e.published_parsed:
                pub = datetime.fromtimestamp(time.mktime(e.published_parsed), tz=timezone.utc)
            elif hasattr(e, 'updated_parsed') and e.updated_parsed:
                pub = datetime.fromtimestamp(time.mktime(e.updated_parsed), tz=timezone.utc)
            if pub and pub >= SINCE:
                entries.append({
                    'title': e.get('title', ''),
                    'link': e.get('link', ''),
                    'summary': e.get('summary', ''),
                    'published': pub.isoformat()
                })
        return entries
    except Exception as ex:
        logging.error(f"RSS error {url}: {ex}")
        return []

def fetch_json_api(url: str, params: Dict = None, timeout: int = 30) -> Optional[Any]:
    try:
        resp = session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as ex:
        logging.error(f"JSON error {url}: {ex}")
        return None

def filter_watchlist(text: str) -> List[str]:
    text_lower = text.lower()
    return [kw for kw in WATCHLIST if kw in text_lower]

# ------------------------------
# SOURCE FUNCTIONS
# ------------------------------
def fetch_gdacs():
    entries = fetch_rss("https://www.gdacs.org/xml/rss.xml")
    events = []
    for e in entries:
        events.append({
            'source': 'GDACS',
            'title': e['title'],
            'link': e['link'],
            'description': e['summary'],
            'timestamp': e['published'],
            'type': 'disaster',
            'watchlist_matches': filter_watchlist(e['title'])
        })
    return events

def fetch_reliefweb():
    url = "https://api.reliefweb.int/v1/reports"
    params = {
        'appname': 'cathedral-network',
        'limit': 50,
        'filter[field]': 'date.created',
        'filter[value]': json.dumps({'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')})
    }
    data = fetch_json_api(url, params)
    if not data or 'data' not in data:
        return []
    events = []
    for item in data['data']:
        f = item.get('fields', {})
        title = f.get('title', '')
        date_str = f.get('date', {}).get('created', '')
        try:
            pub = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            pub = datetime.now(timezone.utc)
        if pub >= SINCE:
            events.append({
                'source': 'ReliefWeb',
                'title': title,
                'link': f.get('url', ''),
                'description': f.get('body', '')[:500],
                'timestamp': pub.isoformat(),
                'type': 'humanitarian',
                'watchlist_matches': filter_watchlist(title)
            })
    return events

def fetch_ucdp():
    token = os.environ.get('UCDP_API_TOKEN')
    if not token:
        logging.warning("UCDP_API_TOKEN not set. Skipping UCDP.")
        return []
    url = "https://ucdpapi.pcr.uu.se/api/events/1"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        resp = session.get(url, headers=headers, params={'limit': 100}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as ex:
        logging.error(f"UCDP error: {ex}")
        return []
    if not data or 'Result' not in data:
        return []
    events = []
    for item in data['Result']:
        title = f"{item.get('event_type', 'Conflict')} in {item.get('location', '')}"
        date_str = item.get('date_start', '')
        try:
            pub = datetime.fromisoformat(date_str) if date_str else datetime.now(timezone.utc)
        except Exception:
            pub = datetime.now(timezone.utc)
        if pub < SINCE:
            continue
        events.append({
            'source': 'UCDP',
            'title': title,
            'link': "https://ucdp.uu.se/",
            'description': item.get('description', '')[:500],
            'timestamp': pub.isoformat(),
            'type': 'conflict',
            'watchlist_matches': filter_watchlist(title)
        })
    return events

def fetch_gdelt():
    time.sleep(2)  # avoid rate limit
    start = SINCE.strftime("%Y%m%d%H%M%S")
    end = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    url = f"https://api.gdeltproject.org/api/v2/events/events?format=json&mode=raw&maxrecords=200&startdatetime={start}&enddatetime={end}"
    data = fetch_json_api(url)
    if not data or 'events' not in data:
        return []
    events = []
    for item in data['events']:
        title = item.get('event', '') or f"{item.get('actor1name', '')} {item.get('action', '')}"
        date_str = item.get('dateadded', '')
        try:
            pub = datetime.strptime(date_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:
            pub = datetime.now(timezone.utc)
        if pub < SINCE:
            continue
        events.append({
            'source': 'GDELT',
            'title': title[:200],
            'link': "https://www.gdeltproject.org/",
            'description': item.get('description', '')[:500],
            'timestamp': pub.isoformat(),
            'type': 'conflict',
            'watchlist_matches': filter_watchlist(title)
        })
    return events

def fetch_promed():
    entries = fetch_rss("https://www.promedmail.org/rss/ProMED-mail.xml")
    events = []
    for e in entries:
        events.append({
            'source': 'ProMED-mail',
            'title': e['title'],
            'link': e['link'],
            'description': e['summary'],
            'timestamp': e['published'],
            'type': 'biosecurity',
            'watchlist_matches': filter_watchlist(e['title'])
        })
    return events

def fetch_arxiv():
    categories = ['cs.AI', 'cs.LG', 'cs.CY', 'q-bio']
    events = []
    for cat in categories:
        url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&max_results=20"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub = None
            if hasattr(entry, 'published_parsed'):
                pub = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
            if pub and pub >= SINCE:
                events.append({
                    'source': f'arXiv {cat}',
                    'title': entry.title,
                    'link': entry.link,
                    'description': entry.summary,
                    'timestamp': pub.isoformat(),
                    'type': 'research',
                    'watchlist_matches': filter_watchlist(entry.title)
                })
    return events

def fetch_ai_incident_db():
    url = "https://incidentdatabase.ai/api/incidents"
    params = {'limit': 50}
    data = fetch_json_api(url, params=params)
    if not data or 'incidents' not in data:
        return []
    events = []
    for inc in data['incidents']:
        title = inc.get('title', '')
        desc = inc.get('description', '')
        date_str = inc.get('incident_date', '')
        try:
            pub = datetime.fromisoformat(date_str) if date_str else datetime.now(timezone.utc)
        except Exception:
            pub = datetime.now(timezone.utc)
        if pub >= SINCE:
            events.append({
                'source': 'AI Incident DB',
                'title': title,
                'link': inc.get('url', ''),
                'description': desc[:500],
                'timestamp': pub.isoformat(),
                'type': 'ai_safety',
                'watchlist_matches': filter_watchlist(title + " " + desc)
            })
    return events

def fetch_github_advisories():
    url = "https://api.github.com/advisories"
    data = fetch_json_api(url, params={'per_page': 50})
    if not data:
        return []
    events = []
    for adv in data:
        pub = adv.get('published_at', '')
        if pub:
            pub_dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
            if pub_dt >= SINCE:
                events.append({
                    'source': 'GitHub Advisories',
                    'title': adv.get('summary', ''),
                    'link': adv.get('html_url', ''),
                    'description': adv.get('description', '')[:500],
                    'timestamp': pub,
                    'type': 'cybersecurity',
                    'watchlist_matches': filter_watchlist(adv.get('summary', ''))
                })
    return events

def fetch_nvd():
    start = SINCE.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={start}&pubEndDate={end}&resultsPerPage=50"
    time.sleep(1)
    data = fetch_json_api(url)
    if not data or 'vulnerabilities' not in data:
        return []
    events = []
    for vuln in data['vulnerabilities']:
        cve = vuln.get('cve', {})
        desc = cve.get('descriptions', [{}])[0].get('value', '')
        events.append({
            'source': 'NVD',
            'title': cve.get('id', ''),
            'link': f"https://nvd.nist.gov/vuln/detail/{cve.get('id', '')}",
            'description': desc[:500],
            'timestamp': cve.get('published', ''),
            'type': 'cybersecurity',
            'watchlist_matches': filter_watchlist(desc)
        })
    return events

def fetch_eia():
    # Placeholder – skip to avoid 400 errors
    return []

def run_sweep():
    logging.info("Starting daily sweep")
    all_events = []
    for func in [
        fetch_gdacs, fetch_reliefweb, fetch_ucdp, fetch_gdelt, fetch_promed,
        fetch_arxiv, fetch_ai_incident_db, fetch_github_advisories, fetch_nvd, fetch_eia
    ]:
        try:
            events = func()
            all_events.extend(events)
            logging.info(f"{func.__name__}: {len(events)} events")
        except Exception as e:
            logging.error(f"Failed {func.__name__}: {e}")

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'events_total': len(all_events),
        'watchlist_hits': [e for e in all_events if e['watchlist_matches']],
        'events_by_source': {},
        'all_events': all_events
    }
    for e in all_events:
        src = e['source']
        report['events_by_source'][src] = report['events_by_source'].get(src, 0) + 1

    with open(JSON_OUT, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    with open(MD_OUT, 'w') as f:
        f.write("# Cathedral Network Daily Ground Truth\n\n")
        f.write(f"**Sweep timestamp:** {report['timestamp']}\n")
        f.write(f"**Total events:** {report['events_total']}\n")
        f.write(f"**Watchlist hits:** {len(report['watchlist_hits'])}\n\n")
        f.write("## Watchlist Matches\n\n")
        for hit in report['watchlist_hits']:
            f.write(f"- **{hit['source']}** – {hit['title']}\n")
            f.write(f"  - Keywords: {', '.join(hit['watchlist_matches'])}\n")
            f.write(f"  - [Link]({hit['link']})\n\n")
        f.write("## Events by Source\n\n")
        for src, cnt in report['events_by_source'].items():
            f.write(f"- {src}: {cnt}\n")

    logging.info(f"Sweep complete. Saved {JSON_OUT}, {MD_OUT}")

if __name__ == "__main__":
    run_sweep()
