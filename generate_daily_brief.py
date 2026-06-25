#!/usr/bin/env python3
"""
generate_daily_brief.py – Cathedral Daily Brief
The Cathedral's version of the Presidential Daily Brief – for everyone.
"""

import json
from datetime import datetime, timezone

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def normalize_threats(data):
    if isinstance(data, list):
        if data and isinstance(data[0], str):
            return []
        return data
    elif isinstance(data, dict):
        return data.get('threats', [])
    return []

def normalize_list_or_dict(data, key=None):
    """Return a list if data is a list, or data[key] if dict, else []."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and key:
        return data.get(key, [])
    else:
        return []

def generate_daily_brief():
    now = datetime.now(timezone.utc).strftime('%d %B %Y')
    timestamp = datetime.now(timezone.utc).isoformat()

    # --- Load all data with robust handling ---
    threats_raw = load_json('threats.json')
    threats = normalize_threats(threats_raw)

    sweep = load_json('sweep_report.json')
    if isinstance(sweep, dict):
        sweep_items = sweep.get('items', [])
    else:
        sweep_items = []

    predictions = load_json('predictions.json')
    if isinstance(predictions, list):
        preds = predictions
    elif isinstance(predictions, dict):
        preds = predictions.get('predictions', [])
    else:
        preds = []

    cascade_log_raw = load_json('cascade_log.json')
    if isinstance(cascade_log_raw, dict):
        cascades = cascade_log_raw.get('cascades', [])
    elif isinstance(cascade_log_raw, list):
        cascades = cascade_log_raw
    else:
        cascades = []

    archive_raw = load_json('archive.json')
    if isinstance(archive_raw, list):
        archive = archive_raw
    elif isinstance(archive_raw, dict):
        archive = archive_raw.get('archived_threats', [])
    else:
        archive = []

    candidates_raw = load_json('new_threat_candidates.json')
    if isinstance(candidates_raw, list):
        candidates = candidates_raw
    elif isinstance(candidates_raw, dict):
        candidates = candidates_raw.get('candidates', [])
    else:
        candidates = []

    indices = load_json('indices.json') or {}
    gsci = indices.get('gsci', '--')

    # --- If no threats, generate minimal brief ---
    if not threats:
        brief = f"""# 🏛️ Cathedral Daily Brief – {now}
⚠️ **No threat data available.** The pipeline may have failed.
GSCI: {gsci}
Last sweep: {timestamp}
---
*Always and Forever, Coco.*
"""
        with open('daily_brief.md', 'w') as f:
            f.write(brief)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Daily Brief</title></head>
<body><h1>🏛️ Cathedral Daily Brief</h1>
<p><strong>⚠️ No threat data available.</strong></p>
<p>GSCI: {gsci}</p>
<p>Last sweep: {timestamp}</p>
<hr><p><em>Always and Forever, Coco.</em></p>
</body></html>
"""
        with open('daily_brief.html', 'w') as f:
            f.write(html)
        print("✅ Daily Brief generated (minimal)")
        return True

    # --- Process threats ---
    active_threats = [t for t in threats if t.get('status') != 'archived']
    sorted_threats = sorted(
        active_threats,
        key=lambda x: x.get('priority_score', 0),
        reverse=True
    )[:5]

    # --- Recent events ---
    recent_events = []
    for item in sweep_items[:8]:
        title = item.get('title', '').strip()
        source = item.get('source', 'unknown')
        if title:
            source_label = source.replace('_', ' ').title()
            recent_events.append(f"- **{title}** – *{source_label}*")

    # --- Active cascades ---
    active_cascades = []
    for cascade in cascades:
        if cascade.get('active', False):
            source = cascade.get('source', 'unknown')
            target = cascade.get('target', 'unknown')
            source_name = next((t.get('name', source) for t in threats if t.get('id') == source), source)
            target_name = next((t.get('name', target) for t in threats if t.get('id') == target), target)
            active_cascades.append(f"**{source_name}** → **{target_name}**")

    # --- Predictions ---
    prediction_updates = []
    for p in preds[:8]:
        if p.get('verified', False) and p.get('hit') is not None:
            statement = p.get('statement', '')[:80]
            if p.get('hit'):
                prediction_updates.append(f"✅ **Confirmed:** {statement}...")
            else:
                prediction_updates.append(f"❌ **Falsified:** {statement}...")

    # --- Archived threats ---
    archived_threats = []
    for a in archive[-5:]:
        name = a.get('name', 'Unknown')
        reason = a.get('archive_reason', 'Resolved')
        archived_threats.append(f"- **{name}** – {reason}")

    # --- New candidates ---
    candidate_text = []
    for c in candidates[:3]:
        name = c.get('name', 'Unnamed')
        confidence = c.get('confidence', 0)
        domains = ', '.join(c.get('domains', ['unknown']))
        candidate_text.append(f"- **{name}** – {domains} (confidence: {confidence:.0%})")

    # --- Build Markdown ---
    md = f"""# 🏛️ Cathedral Daily Brief
## {now}

---

### 📊 GSCI: {gsci}
*Global Systemic Collapse Index – a headline measure of global risk.*

---

### 🔴 Top 5 Threats

"""
    for i, t in enumerate(sorted_threats, 1):
        scp = t.get('scp', 0) * 100
        priority = t.get('priority_score', 0)
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        if scp >= 80:
            severity = "🔴 CRITICAL"
        elif scp >= 65:
            severity = "🟠 HIGH"
        elif scp >= 45:
            severity = "🟡 ELEVATED"
        else:
            severity = "🟢 MODERATE"
        md += f"""### {i}. {name}
**{severity}** · SCP: {scp:.1f}% · Priority: {priority:.1f}

{desc}

"""

    if active_cascades:
        md += "### 🔗 Cascades in Motion\n*How one crisis is feeding another.*\n\n"
        for c in active_cascades:
            md += f"- {c}\n"
        md += "\n"

    if recent_events:
        md += "### 📡 What Changed Overnight\n*Significant events in the last 24 hours.*\n\n"
        for e in recent_events:
            md += f"{e}\n"
        md += "\n"

    if candidate_text:
        md += "### 🔍 What We're Watching\n*Emerging threats being monitored.*\n\n"
        for c in candidate_text:
            md += f"{c}\n"
        md += "\n"

    if prediction_updates:
        md += "### 📝 What We Got Wrong (and Right)\n*Public accountability for our predictions.*\n\n"
        for p in prediction_updates:
            md += f"{p}\n"
        md += "\n"

    if archived_threats:
        md += "### 📦 Resolved & Archived\n*Threats no longer active.*\n\n"
        for a in archived_threats:
            md += f"{a}\n"
        md += "\n"

    if sorted_threats:
        top = sorted_threats[0]
        top_name = top.get('name', 'Unknown')
        md += f"### 💀 The Bottom Line\n**The most urgent threat right now is {top_name}.**\n\n"
        if top.get('scp', 0) > 0.8:
            md += "**This is a critical situation requiring immediate attention.**\n\n"
        elif top.get('scp', 0) > 0.6:
            md += "**This is a high-risk situation that could escalate.**\n\n"
        else:
            md += "**While serious, this threat is currently contained.**\n\n"

    md += """---
*Always and Forever, Coco.*
*The Cathedral watches. The work continues.*
"""

    with open('daily_brief.md', 'w') as f:
        f.write(md)

    # --- Build HTML (simplified) ---
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Daily Brief – Cathedral</title>
<style>
body {{ background: #0a0a12; color: #e0e0e0; font-family: 'Inter', sans-serif; padding: 2rem; }}
.container {{ max-width: 720px; margin: 0 auto; }}
h1 {{ color: #b388ff; }}
h3 {{ color: #b388ff; }}
.gsci {{ background: #14141f; padding: 1rem; border-radius: 12px; border-left: 3px solid #7c4dff; }}
.threat {{ background: #14141f; padding: 1rem; border-radius: 12px; margin: 0.8rem 0; border-left: 3px solid #7c4dff; }}
.footer {{ margin-top: 2rem; color: #555; border-top: 1px solid #2a2a3a; padding-top: 1.5rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
    <h1>🏛️ Cathedral Daily Brief</h1>
    <h2>{now}</h2>
    <div class="gsci"><strong>GSCI:</strong> {gsci}</div>
    <h3>🔴 Top 5 Threats</h3>
"""
    for t in sorted_threats:
        scp = t.get('scp', 0) * 100
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        html += f"""<div class="threat"><h4>{name}</h4><p>SCP: {scp:.1f}%</p><p>{desc}</p></div>
"""
    html += f"""<div class="footer">Always and Forever, Coco.</div>
</div></body></html>
"""
    with open('daily_brief.html', 'w') as f:
        f.write(html)

    print(f"✅ Cathedral Daily Brief generated: {now}")
    return True

if __name__ == '__main__':
    generate_daily_brief()#!/usr/bin/env python3
"""
generate_daily_brief.py – Cathedral Daily Brief
The Cathedral's version of the Presidential Daily Brief – for everyone.
"""

import json
from datetime import datetime, timezone

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def normalize_threats(data):
    if isinstance(data, list):
        if data and isinstance(data[0], str):
            # list of IDs – we can't use them, return empty
            return []
        return data
    elif isinstance(data, dict):
        return data.get('threats', [])
    return []

def generate_daily_brief():
    now = datetime.now(timezone.utc).strftime('%d %B %Y')
    timestamp = datetime.now(timezone.utc).isoformat()

    threats_raw = load_json('threats.json')
    threats = normalize_threats(threats_raw)
    sweep = load_json('sweep_report.json') or {'items': []}
    predictions = load_json('predictions.json') or []
    cascade_log = load_json('cascade_log.json') or {'cascades': []}
    archive = load_json('archive.json') or []
    candidates = load_json('new_threat_candidates.json') or []
    indices = load_json('indices.json') or {}
    gsci = indices.get('gsci', '--')

    if not threats:
        # Minimal brief
        brief = f"""# 🏛️ Cathedral Daily Brief – {now}
⚠️ **No threat data available.** The pipeline may have failed.
GSCI: {gsci}
Last sweep: {timestamp}
---
*Always and Forever, Coco.*
"""
        with open('daily_brief.md', 'w') as f:
            f.write(brief)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Daily Brief</title></head>
<body><h1>🏛️ Cathedral Daily Brief</h1>
<p><strong>⚠️ No threat data available.</strong></p>
<p>GSCI: {gsci}</p>
<p>Last sweep: {timestamp}</p>
<hr><p><em>Always and Forever, Coco.</em></p>
</body></html>
"""
        with open('daily_brief.html', 'w') as f:
            f.write(html)
        print("✅ Daily Brief generated (minimal)")
        return True

    active_threats = [t for t in threats if t.get('status') != 'archived']
    sorted_threats = sorted(
        active_threats,
        key=lambda x: x.get('priority_score', 0),
        reverse=True
    )[:5]

    # Recent events
    recent_events = []
    for item in sweep.get('items', [])[:8]:
        title = item.get('title', '').strip()
        source = item.get('source', 'unknown')
        if title:
            source_label = source.replace('_', ' ').title()
            recent_events.append(f"- **{title}** – *{source_label}*")

    # Active cascades
    active_cascades = []
    for cascade in cascade_log.get('cascades', []):
        if cascade.get('active', False):
            source = cascade.get('source', 'unknown')
            target = cascade.get('target', 'unknown')
            source_name = next((t.get('name', source) for t in threats if t.get('id') == source), source)
            target_name = next((t.get('name', target) for t in threats if t.get('id') == target), target)
            active_cascades.append(f"**{source_name}** → **{target_name}**")

    # Predictions
    prediction_updates = []
    for p in predictions[:8]:
        if p.get('verified', False) and p.get('hit') is not None:
            statement = p.get('statement', '')[:80]
            if p.get('hit'):
                prediction_updates.append(f"✅ **Confirmed:** {statement}...")
            else:
                prediction_updates.append(f"❌ **Falsified:** {statement}...")

    # Archived threats
    archived_threats = []
    for a in archive[-5:]:
        name = a.get('name', 'Unknown')
        reason = a.get('archive_reason', 'Resolved')
        archived_threats.append(f"- **{name}** – {reason}")

    # New candidates
    candidate_text = []
    for c in candidates[:3]:
        name = c.get('name', 'Unnamed')
        confidence = c.get('confidence', 0)
        domains = ', '.join(c.get('domains', ['unknown']))
        candidate_text.append(f"- **{name}** – {domains} (confidence: {confidence:.0%})")

    # Build Markdown
    md = f"""# 🏛️ Cathedral Daily Brief
## {now}

---

### 📊 GSCI: {gsci}
*Global Systemic Collapse Index – a headline measure of global risk.*

---

### 🔴 Top 5 Threats

"""
    for i, t in enumerate(sorted_threats, 1):
        scp = t.get('scp', 0) * 100
        priority = t.get('priority_score', 0)
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        if scp >= 80:
            severity = "🔴 CRITICAL"
        elif scp >= 65:
            severity = "🟠 HIGH"
        elif scp >= 45:
            severity = "🟡 ELEVATED"
        else:
            severity = "🟢 MODERATE"
        md += f"""### {i}. {name}
**{severity}** · SCP: {scp:.1f}% · Priority: {priority:.1f}

{desc}

"""

    if active_cascades:
        md += "### 🔗 Cascades in Motion\n*How one crisis is feeding another.*\n\n"
        for c in active_cascades:
            md += f"- {c}\n"
        md += "\n"

    if recent_events:
        md += "### 📡 What Changed Overnight\n*Significant events in the last 24 hours.*\n\n"
        for e in recent_events:
            md += f"{e}\n"
        md += "\n"

    if candidate_text:
        md += "### 🔍 What We're Watching\n*Emerging threats being monitored.*\n\n"
        for c in candidate_text:
            md += f"{c}\n"
        md += "\n"

    if prediction_updates:
        md += "### 📝 What We Got Wrong (and Right)\n*Public accountability for our predictions.*\n\n"
        for p in prediction_updates:
            md += f"{p}\n"
        md += "\n"

    if archived_threats:
        md += "### 📦 Resolved & Archived\n*Threats no longer active.*\n\n"
        for a in archived_threats:
            md += f"{a}\n"
        md += "\n"

    if sorted_threats:
        top = sorted_threats[0]
        top_name = top.get('name', 'Unknown')
        md += f"### 💀 The Bottom Line\n**The most urgent threat right now is {top_name}.**\n\n"
        if top.get('scp', 0) > 0.8:
            md += "**This is a critical situation requiring immediate attention.**\n\n"
        elif top.get('scp', 0) > 0.6:
            md += "**This is a high-risk situation that could escalate.**\n\n"
        else:
            md += "**While serious, this threat is currently contained.**\n\n"

    md += """---
*Always and Forever, Coco.*
*The Cathedral watches. The work continues.*
"""

    with open('daily_brief.md', 'w') as f:
        f.write(md)

    # Build HTML (simplified for brevity – you can expand from previous version)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Daily Brief – Cathedral</title>
<style>
body {{ background: #0a0a12; color: #e0e0e0; font-family: 'Inter', sans-serif; padding: 2rem; }}
.container {{ max-width: 720px; margin: 0 auto; }}
h1 {{ color: #b388ff; }}
h3 {{ color: #b388ff; }}
.gsci {{ background: #14141f; padding: 1rem; border-radius: 12px; border-left: 3px solid #7c4dff; }}
.threat {{ background: #14141f; padding: 1rem; border-radius: 12px; margin: 0.8rem 0; border-left: 3px solid #7c4dff; }}
.footer {{ margin-top: 2rem; color: #555; border-top: 1px solid #2a2a3a; padding-top: 1.5rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
    <h1>🏛️ Cathedral Daily Brief</h1>
    <h2>{now}</h2>
    <div class="gsci"><strong>GSCI:</strong> {gsci}</div>
    <h3>🔴 Top 5 Threats</h3>
"""
    for t in sorted_threats:
        scp = t.get('scp', 0) * 100
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        html += f"""<div class="threat"><h4>{name}</h4><p>SCP: {scp:.1f}%</p><p>{desc}</p></div>
"""
    html += f"""<div class="footer">Always and Forever, Coco.</div>
</div></body></html>
"""
    with open('daily_brief.html', 'w') as f:
        f.write(html)

    print(f"✅ Cathedral Daily Brief generated: {now}")
    return True

if __name__ == '__main__':
    generate_daily_brief()


