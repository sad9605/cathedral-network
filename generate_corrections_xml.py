#!/usr/bin/env python3
"""
generate_corrections_xml.py – Generate corrections.xml RSS feed from predictions and cascade logs.
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

PREDICTIONS_FILE = "predictions.json"
CASCADE_LOG_FILE = "cascade_log.json"
OUTPUT_FILE = "corrections.xml"

def load_json(filepath, default=None):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def main():
    predictions = load_json(PREDICTIONS_FILE, {})
    cascade_log = load_json(CASCADE_LOG_FILE, [])

    # Build RSS feed
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    title = ET.SubElement(channel, "title")
    title.text = "Cathedral Network – Corrections Feed (Law III)"

    link = ET.SubElement(channel, "link")
    link.text = "https://sad9605.github.io/cathedral-network/"

    description = ET.SubElement(channel, "description")
    description.text = "Real‑time error logging and recalibrations. Every miss is logged publicly."

    # Add confirmed predictions (as corrections)
    for p in predictions.get('confirmed', [])[-20:]:
        item = ET.SubElement(channel, "item")
        title_elem = ET.SubElement(item, "title")
        title_elem.text = f"✅ Confirmed: {p.get('id')} – {p.get('description', '')[:80]}"
        link_elem = ET.SubElement(item, "link")
        link_elem.text = f"https://sad9605.github.io/cathedral-network/prediction-log.html#{p.get('id')}"
        desc = ET.SubElement(item, "description")
        desc.text = f"Prediction confirmed on {p.get('date', 'unknown')}. Evidence: {p.get('evidence', 'N/A')}"
        pub_date = ET.SubElement(item, "pubDate")
        pub_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Add falsified predictions
    for p in predictions.get('falsified', [])[-20:]:
        item = ET.SubElement(channel, "item")
        title_elem = ET.SubElement(item, "title")
        title_elem.text = f"❌ Falsified: {p.get('id')} – {p.get('description', '')[:80]}"
        link_elem = ET.SubElement(item, "link")
        link_elem.text = f"https://sad9605.github.io/cathedral-network/prediction-log.html#{p.get('id')}"
        desc = ET.SubElement(item, "description")
        desc.text = f"Prediction falsified on {p.get('date', 'unknown')}. Reason: {p.get('reason', 'N/A')}"
        pub_date = ET.SubElement(item, "pubDate")
        pub_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Add cascade activations (as corrections/events)
    for entry in cascade_log[-20:]:
        item = ET.SubElement(channel, "item")
        title_elem = ET.SubElement(item, "title")
        title_elem.text = f"🔄 Cascade: {entry.get('source', '')} → {entry.get('target', '')}"
        link_elem = ET.SubElement(item, "link")
        link_elem.text = "https://sad9605.github.io/cathedral-network/threat-matrix.html"
        desc = ET.SubElement(item, "description")
        desc.text = f"SCP boost: {entry.get('boost', 0):.3f} on {entry.get('timestamp', 'unknown')}"
        pub_date = ET.SubElement(item, "pubDate")
        pub_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Write to file
    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ Corrections RSS feed written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
