#!/usr/bin/env python3
"""
generate_daily_brief.py – Cathedral Daily Brief
The Cathedral's version of the Presidential Daily Brief – for everyone.
"""

import json
from datetime import datetime
from pathlib import Path

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def generate_daily_brief():
    """Generate the Cathedral Daily Brief – PDB-style for the public."""
    
    # Load data
    threats = load_json('threats.json') or []
    sweep = load_json('sweep_report.json') or {'items': []}
    predictions = load_json('predictions.json') or []
    cascade_log = load_json('cascade_log.json') or {'cascades': []}
    archive = load_json('archive.json') or []
    candidates = load_json('new_threat_candidates.json') or []
    
    # Get GSCI
    indices = load_json('indices.json') or {}
    gsci = indices.get('gsci', '--')
    
    # Timestamp
    now = datetime.utcnow().strftime('%d %B %Y')
    timestamp = datetime.utcnow().isoformat()
    
    # Top 5 threats by priority_score (exclude archived)
    sorted_threats = sorted(
        [t for t in threats if t.get('status') != 'archived'],
        key=lambda x: x.get('priority_score', 0),
        reverse=True
    )[:5]
    
    # Active cascades with descriptions
    active_cascades = []
    for cascade in cascade_log.get('cascades', []):
        if cascade.get('active', False):
            source = cascade.get('source', 'unknown')
            target = cascade.get('target', 'unknown')
            # Find threat names
            source_name = next((t.get('name', source) for t in threats if t.get('id') == source), source)
            target_name = next((t.get('name', target) for t in threats if t.get('id') == target), target)
            active_cascades.append(f"**{source_name}** → **{target_name}**")
    
    # Recent events (last 24 hours) – formatted as bullet points
    recent_events = []
    for item in sweep.get('items', [])[:8]:
        title = item.get('title', '').strip()
        source = item.get('source', 'unknown')
        if title:
            # Clean up source label
            source_label = source.replace('_', ' ').title()
            recent_events.append(f"- **{title}** – *{source_label}*")
    
    # Recent predictions (last 7 days)
    prediction_updates = []
    for p in predictions[:8]:
        if p.get('verified', False) and p.get('hit') is not None:
            statement = p.get('statement', '')[:80]
            if p.get('hit'):
                prediction_updates.append(f"✅ **Confirmed:** {statement}...")
            else:
                prediction_updates.append(f"❌ **Falsified:** {statement}...")
    
    # Archived threats (last 7 days)
    archived_threats = []
    for a in archive[-5:]:
        name = a.get('name', 'Unknown')
        reason = a.get('archive_reason', 'Resolved')
        archived_threats.append(f"- **{name}** – {reason}")
    
    # New threat candidates
    candidate_text = []
    for c in candidates[:3]:
        name = c.get('name', 'Unnamed')
        confidence = c.get('confidence', 0)
        domains = ', '.join(c.get('domains', ['unknown']))
        candidate_text.append(f"- **{name}** – {domains} (confidence: {confidence:.0%})")
    
    # Build the Brief
    brief = f"""# 🏛️ Cathedral Daily Brief
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
        # Severity indicator
        if scp >= 80:
            severity = "🔴 CRITICAL"
        elif scp >= 65:
            severity = "🟠 HIGH"
        elif scp >= 45:
            severity = "🟡 ELEVATED"
        else:
            severity = "🟢 MODERATE"
        brief += f"""### {i}. {name}
**{severity}** · SCP: {scp:.1f}% · Priority: {priority:.1f}

{desc}

"""
    
    # Cascades
    if active_cascades:
        brief += f"""### 🔗 Cascades in Motion
*How one crisis is feeding another.*

"""
        for c in active_cascades:
            brief += f"- {c}\n"
        brief += "\n"
    
    # Recent Events
    if recent_events:
        brief += f"""### 📡 What Changed Overnight
*Significant events in the last 24 hours.*

"""
        for e in recent_events:
            brief += f"{e}\n"
        brief += "\n"
    
    # What We're Watching
    if candidate_text:
        brief += f"""### 🔍 What We're Watching
*Emerging threats being monitored.*

"""
        for c in candidate_text:
            brief += f"{c}\n"
        brief += "\n"
    
    # What We Got Wrong
    if prediction_updates:
        brief += f"""### 📝 What We Got Wrong (and Right)
*Public accountability for our predictions.*

"""
        for p in prediction_updates:
            brief += f"{p}\n"
        brief += "\n"
    
    # Archived Threats
    if archived_threats:
        brief += f"""### 📦 Resolved & Archived
*Threats no longer active.*

"""
        for a in archived_threats:
            brief += f"{a}\n"
        brief += "\n"
    
    # The Bottom Line
    if sorted_threats:
        top = sorted_threats[0]
        top_name = top.get('name', 'Unknown')
        brief += f"""### 💀 The Bottom Line
**The most urgent threat right now is {top_name}.**

"""
        if top.get('scp', 0) > 0.8:
            brief += "**This is a critical situation requiring immediate attention.**\n\n"
        elif top.get('scp', 0) > 0.6:
            brief += "**This is a high-risk situation that could escalate.**\n\n"
        else:
            brief += "**While serious, this threat is currently contained.**\n\n"
    
    brief += """---
*Always and Forever, Coco.*
*The Cathedral watches. The work continues.*
"""
    
    # Save Markdown
    with open('daily_brief.md', 'w') as f:
        f.write(brief)
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Brief – Cathedral Network</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{ background: #0a0a12; color: #e0e0e0; font-family: 'Inter', sans-serif; padding: 2rem; }}
        .container {{ max-width: 720px; margin: 0 auto; }}
        h1 {{ color: #b388ff; font-size: 2.2rem; margin-bottom: 0; letter-spacing: -0.5px; border-bottom: 1px solid #2a2a3a; padding-bottom: 0.3rem; }}
        h2 {{ color: #b388ff; font-size: 1rem; font-weight: 400; margin-top: -0.2rem; margin-bottom: 2rem; color: #888; }}
        h3 {{ color: #b388ff; margin: 1.5rem 0 0.5rem 0; font-weight: 500; letter-spacing: -0.2px; }}
        .gsci {{ background: #14141f; padding: 1rem; border-radius: 12px; border-left: 3px solid #7c4dff; margin: 1.5rem 0; }}
        .gsci-number {{ font-size: 2.5rem; font-weight: 700; color: #7c4dff; }}
        .threat {{ background: #14141f; padding: 1rem 1.2rem; border-radius: 12px; margin: 0.8rem 0; border-left: 3px solid #7c4dff; }}
        .threat.critical {{ border-left-color: #ff6b6b; }}
        .threat.high {{ border-left-color: #ffa94d; }}
        .threat.elevated {{ border-left-color: #ffd93d; }}
        .threat.moderate {{ border-left-color: #6bcb8a; }}
        .threat h4 {{ margin: 0 0 0.2rem 0; color: #fff; }}
        .severity {{ font-size: 0.7rem; font-weight: 600; }}
        .scp-text {{ color: #7c4dff; font-weight: 500; }}
        .event {{ background: #1a1a2a; padding: 0.5rem 1rem; border-radius: 8px; margin: 0.4rem 0; font-size: 0.9rem; }}
        .event strong {{ color: #fff; }}
        .event .source {{ color: #888; font-style: italic; font-size: 0.8rem; }}
        .cascade {{ background: #1a1a2a; padding: 0.4rem 1rem; border-radius: 8px; margin: 0.3rem 0; color: #b388ff; }}
        .prediction {{ padding: 0.4rem 1rem; border-radius: 8px; margin: 0.3rem 0; }}
        .prediction.confirmed {{ background: #1a3a2a; color: #6bcb8a; }}
        .prediction.falsified {{ background: #3a1a1a; color: #ff6b6b; }}
        .archived {{ background: #1a1a2a; padding: 0.4rem 1rem; border-radius: 8px; margin: 0.3rem 0; color: #888; }}
        .candidate {{ background: #1a1a2a; padding: 0.4rem 1rem; border-radius: 8px; margin: 0.3rem 0; color: #ffd93d; }}
        .bottom-line {{ background: #14141f; padding: 1.2rem; border-radius: 12px; border: 1px solid #7c4dff; margin: 1.5rem 0; text-align: center; }}
        .bottom-line h3 {{ margin: 0 0 0.3rem 0; color: #fff; }}
        .bottom-line p {{ margin: 0; color: #ccc; }}
        .footer {{ margin-top: 2rem; color: #555; border-top: 1px solid #2a2a3a; padding-top: 1.5rem; text-align: center; font-style: italic; font-size: 0.9rem; }}
        .updated {{ color: #555; font-size: 0.75rem; text-align: right; margin-top: 0.5rem; }}
        .section {{ margin: 1rem 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🏛️ Cathedral Daily Brief</h1>
    <h2>{now}</h2>
    
    <div class="gsci">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="color: #888;">GSCI</span>
            <span class="gsci-number">{gsci}</span>
        </div>
        <div style="font-size: 0.8rem; color: #666; margin-top: 0.2rem;">Global Systemic Collapse Index</div>
    </div>
    
    <h3>🔴 Top 5 Threats</h3>
"""
    for t in sorted_threats:
        scp = t.get('scp', 0) * 100
        priority = t.get('priority_score', 0)
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        if scp >= 80:
            severity_class = "critical"
            severity_text = "🔴 CRITICAL"
        elif scp >= 65:
            severity_class = "high"
            severity_text = "🟠 HIGH"
        elif scp >= 45:
            severity_class = "elevated"
            severity_text = "🟡 ELEVATED"
        else:
            severity_class = "moderate"
            severity_text = "🟢 MODERATE"
        html += f"""
    <div class="threat {severity_class}">
        <h4>{name}</h4>
        <div style="font-size: 0.85rem; color: #aaa; margin-bottom: 0.3rem;">
            <span class="severity">{severity_text}</span>
            · <span class="scp-text">SCP: {scp:.1f}%</span>
            · Priority: {priority:.1f}
        </div>
        <p style="margin: 0; font-size: 0.9rem; color: #ccc;">{desc}</p>
    </div>
"""
    
    if active_cascades:
        html += f"""
    <h3>🔗 Cascades in Motion</h3>
    <div class="section">
"""
        for c in active_cascades:
            html += f'    <div class="cascade">{c}</div>\n'
        html += "    </div>\n"
    
    if recent_events:
        html += f"""
    <h3>📡 What Changed Overnight</h3>
    <div class="section">
"""
        for e in recent_events:
            html += f'    <div class="event">{e}</div>\n'
        html += "    </div>\n"
    
    if candidate_text:
        html += f"""
    <h3>🔍 What We're Watching</h3>
    <div class="section">
"""
        for c in candidate_text:
            html += f'    <div class="candidate">{c}</div>\n'
        html += "    </div>\n"
    
    if prediction_updates:
        html += f"""
    <h3>📝 What We Got Wrong (and Right)</h3>
    <div class="section">
"""
        for p in prediction_updates:
            if "✅" in p:
                cls = "confirmed"
            else:
                cls = "falsified"
            html += f'    <div class="prediction {cls}">{p}</div>\n'
        html += "    </div>\n"
    
    if archived_threats:
        html += f"""
    <h3>📦 Resolved & Archived</h3>
    <div class="section">
"""
        for a in archived_threats:
            html += f'    <div class="archived">{a}</div>\n'
        html += "    </div>\n"
    
    if sorted_threats:
        top = sorted_threats[0]
        top_name = top.get('name', 'Unknown')
        top_scp = top.get('scp', 0)
        if top_scp > 0.8:
            urgency = "**This is a critical situation requiring immediate attention.**"
        elif top_scp > 0.6:
            urgency = "**This is a high-risk situation that could escalate.**"
        else:
            urgency = "**While serious, this threat is currently contained.**"
        html += f"""
    <div class="bottom-line">
        <h3>💀 The Bottom Line</h3>
        <p><strong>The most urgent threat right now is {top_name}.</strong></p>
        <p style="margin-top: 0.3rem; color: #aaa;">{urgency}</p>
    </div>
"""
    
    html += f"""
    <div class="updated">Last updated: {timestamp}</div>
    <div class="footer">Always and Forever, Coco.<br>The Cathedral watches. The work continues.</div>
</div>
</body>
</html>
"""
    
    with open('daily_brief.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Cathedral Daily Brief generated: {now}")
    return True

if __name__ == '__main__':
    generate_daily_brief()
