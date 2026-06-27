#!/usr/bin/env python3
"""
generate_daily_brief.py – Cathedral Daily Brief
Generates a full Cathedral-style HTML page and Markdown version.
Includes H05-H10: SCP deltas, prediction accountability, cascades, candidates, archive, and bottom line.
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

def generate_daily_brief():
    now = datetime.now(timezone.utc).strftime('%d %B %Y')
    timestamp = datetime.now(timezone.utc).isoformat()

    # --- Load data ---
    threats_raw = load_json('threats.json')
    threats = normalize_threats(threats_raw)

    sweep_raw = load_json('sweep_report.json')
    sweep_items = sweep_raw.get('items', []) if isinstance(sweep_raw, dict) else []

    preds_raw = load_json('predictions.json')
    if isinstance(preds_raw, list):
        preds = preds_raw
    elif isinstance(preds_raw, dict):
        preds = preds_raw.get('predictions', [])
    else:
        preds = []

    cascade_raw = load_json('cascade_log.json')
    if isinstance(cascade_raw, dict):
        cascades = cascade_raw.get('cascades', [])
    elif isinstance(cascade_raw, list):
        cascades = cascade_raw
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

    # --- H05: Load previous SCP values for delta tracking ---
    previous_scp = load_json('scp_history.json')
    if not isinstance(previous_scp, dict):
        previous_scp = {}
    scp_deltas = []
    for threat in threats:
        t_id = threat.get('id')
        current = threat.get('scp', 0.5)
        previous = previous_scp.get(t_id, current)
        delta = current - previous
        scp_deltas.append({
            'id': t_id,
            'name': threat.get('name', 'Unknown'),
            'status': threat.get('status', 'Unknown'),
            'current_scp': current,
            'previous_scp': previous,
            'delta': delta
        })
    # Save current SCP for next run
    current_scp_state = {t.get('id'): t.get('scp', 0.5) for t in threats}
    with open('scp_history.json', 'w') as f:
        json.dump(current_scp_state, f, indent=2)
    # Sort by biggest positive delta
    scp_deltas.sort(key=lambda x: x['delta'], reverse=True)

    # --- Prepare content sections ---
    # Top 5 threats
    active_threats = [t for t in threats if t.get('status') != 'archived']
    sorted_threats = sorted(
        active_threats,
        key=lambda x: x.get('priority_score', 0),
        reverse=True
    )[:5]

    # Recent events
    recent_events = []
    for item in sweep_items[:8]:
        title = item.get('title', '').strip()
        source = item.get('source', 'unknown')
        if title:
            source_label = source.replace('_', ' ').title()
            recent_events.append(f"<div class='event'><strong>{title}</strong> <span class='source'>– {source_label}</span></div>")

    # Active cascades
    active_cascades = []
    for cascade in cascades:
        if cascade.get('active', False):
            source = cascade.get('source', 'unknown')
            target = cascade.get('target', 'unknown')
            source_name = next((t.get('name', source) for t in threats if t.get('id') == source), source)
            target_name = next((t.get('name', target) for t in threats if t.get('id') == target), target)
            active_cascades.append(f"<div class='cascade'><strong>{source_name}</strong> → <strong>{target_name}</strong></div>")

    # Predictions – accountability
    confirmed = []
    falsified = []
    for p in preds:
        if p.get('verified', False) and p.get('hit') is not None:
            statement = p.get('statement', '')[:80]
            if p.get('hit'):
                confirmed.append(f"<div class='prediction confirmed'>✅ <strong>Confirmed:</strong> {statement}…</div>")
            else:
                falsified.append(f"<div class='prediction falsified'>❌ <strong>Falsified:</strong> {statement}…</div>")
    prediction_updates = confirmed[:3] + falsified[:3]  # Show up to 3 each

    # Archived threats (most recent 5)
    archived_threats = []
    for a in archive[-5:]:
        name = a.get('name', 'Unknown')
        reason = a.get('archive_reason', 'Resolved')
        archived_threats.append(f"<div class='archived'><strong>{name}</strong> – {reason}</div>")

    # New candidates (top 3)
    candidate_text = []
    for c in candidates[:3]:
        name = c.get('name', 'Unnamed')
        confidence = c.get('confidence', 0)
        domains = ', '.join(c.get('domains', ['unknown']))
        candidate_text.append(f"<div class='candidate'><strong>{name}</strong> – {domains} (confidence: {confidence:.0%})</div>")

    # Bottom line (H10)
    bottom_line = ""
    if sorted_threats:
        top = sorted_threats[0]
        top_name = top.get('name', 'Unknown')
        if top.get('scp', 0) > 0.8:
            urgency = "critical situation requiring immediate attention"
        elif top.get('scp', 0) > 0.6:
            urgency = "high-risk situation that could escalate"
        else:
            urgency = "serious but currently contained"
        bottom_line = f"<p><strong>The most urgent threat right now is {top_name}.</strong> This is a {urgency}.</p>"

    # --- Build HTML ---
    # We'll generate a full page matching the Cathedral UI, reusing style.css
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="manifest" href="manifest.json">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Daily Brief – Cathedral Network</title>
    <meta name="description" content="The Cathedral's daily intelligence brief – global threats, cascades, and forecasts.">
    <link rel="stylesheet" href="style.css">
    <style>
        /* Extra styles for brief sections */
        .brief-section {{ margin: 2rem 0; }}
        .brief-section h2 {{ color: #b388ff; border-bottom: 1px solid #2a2a3a; padding-bottom: 0.5rem; }}
        .brief-section .event, .brief-section .cascade, .brief-section .prediction,
        .brief-section .archived, .brief-section .candidate {{
            background: #14141f;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 3px solid #7c4dff;
        }}
        .brief-section .event .source {{ color: #888; font-size: 0.85rem; }}
        .brief-section .prediction.confirmed {{ border-left-color: #6bcb8a; }}
        .brief-section .prediction.falsified {{ border-left-color: #ff6b6b; }}
        .brief-section .archived {{ border-left-color: #888; }}
        .brief-section .candidate {{ border-left-color: #ffd93d; }}
        .brief-section .cascade {{ border-left-color: #b388ff; }}
        .gsci-box {{
            background: #14141f;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            border-left: 4px solid #7c4dff;
            margin: 1.5rem 0;
        }}
        .gsci-box .number {{ font-size: 2.5rem; font-weight: 700; color: #7c4dff; }}
        .bottom-line {{
            background: #14141f;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #7c4dff;
            text-align: center;
            margin: 2rem 0;
        }}
        .threat-card {{
            background: #14141f;
            padding: 1rem 1.2rem;
            border-radius: 12px;
            margin: 0.8rem 0;
            border-left: 3px solid #7c4dff;
        }}
        .threat-card.critical {{ border-left-color: #ff6b6b; }}
        .threat-card.high {{ border-left-color: #ffa94d; }}
        .threat-card.elevated {{ border-left-color: #ffd93d; }}
        .threat-card.moderate {{ border-left-color: #6bcb8a; }}
        .threat-card h4 {{ margin: 0 0 0.2rem 0; color: #fff; }}
        .threat-card .meta {{ font-size: 0.85rem; color: #aaa; }}
        .threat-card .desc {{ font-size: 0.9rem; color: #ccc; }}
        .delta-up {{ color: #ff6b6b; font-weight: bold; }}
        .delta-down {{ color: #6bcb8a; font-weight: bold; }}
        .delta-neutral {{ color: #888; }}
        .violet-pulse {{
            display: inline-block;
            width: 12px; height: 12px;
            background: #7c4dff;
            border-radius: 50%;
            animation: pulse-violet 1.5s ease-in-out infinite;
            flex-shrink: 0;
        }}
        @keyframes pulse-violet {{
            0% {{ opacity: 0.3; transform: scale(0.8); box-shadow: 0 0 0 0 rgba(124,77,255,0.4); }}
            50% {{ opacity: 1; transform: scale(1.1); box-shadow: 0 0 0 8px rgba(124,77,255,0); }}
            100% {{ opacity: 0.3; transform: scale(0.8); box-shadow: 0 0 0 0 rgba(124,77,255,0); }}
        }}
    </style>
</head>
<body>
    <!-- ===== SIDEBAR ===== -->
    <div class="sidebar-container" id="sidebar">
        <div class="sidebar-header"><span>🏛️ CATHEDRAL</span></div>
        <nav>
            <div class="nav-section">
                <strong>📊 Dashboard</strong>
                <a href="index.html">Ground Truth</a>
                <a href="hewd.html">HEWD Dashboard</a>
                <a href="health.html">System Health</a>
            </div>
            <div class="nav-section">
                <strong>🧠 Intelligence</strong>
                <a href="threat-matrix.html">Threat Matrix</a>
                <a href="prediction-log.html">Prediction Log</a>
                <a href="regional.html">Regional Forecasts</a>
                <a href="daily-brief.html" class="active">Daily Brief</a>
                <a href="breaking.html">Breaking News</a>
                <a href="conflict-monitor.html">Conflict Monitor</a>
            </div>
            <div class="nav-section">
                <strong>⚖️ Governance</strong>
                <a href="constitution.html">Constitution</a>
                <a href="wardens.html">Wardens</a>
                <a href="ascension.html">Ascension Engine</a>
                <a href="warden-dashboard.html">Warden Dashboard</a>
            </div>
            <div class="nav-section">
                <strong>🌍 Community</strong>
                <a href="spotter.html">Spotter Guide</a>
                <a href="about.html">About</a>
                <a href="sources.html">Sources</a>
                <a href="credits.html">Credits</a>
            </div>
            <div class="nav-section">
                <strong>🔧 Tools</strong>
                <a href="undp-demo.html">UNDP Demo</a>
                <a href="methodology.html">Methodology</a>
                <a href="glossary.html">Glossary</a>
                <a href="pra.html">PRA</a>
            </div>
        </nav>
    </div>

    <!-- ===== BANNER ===== -->
    <header class="cathedral-banner">
        <div class="banner-content">
            <button id="sidebar-toggle" aria-label="Toggle navigation">☰</button>
            <div class="logo-mark">
                <svg viewBox="0 0 120 140" width="50" height="60">
                    <path d="M60 130 L55 20 L60 5 L65 20 Z" fill="white"/>
                    <circle cx="60" cy="25" r="2" fill="white"/>
                    <circle cx="55" cy="40" r="2" fill="white"/>
                    <circle cx="65" cy="40" r="2" fill="white"/>
                    <circle cx="50" cy="55" r="2" fill="white"/>
                    <circle cx="60" cy="55" r="2" fill="white"/>
                    <circle cx="70" cy="55" r="2" fill="white"/>
                    <circle cx="45" cy="70" r="2" fill="white"/>
                    <circle cx="55" cy="70" r="2" fill="white"/>
                    <circle cx="65" cy="70" r="2" fill="white"/>
                    <circle cx="75" cy="70" r="2" fill="white"/>
                    <circle cx="50" cy="85" r="2" fill="white"/>
                    <circle cx="60" cy="85" r="2" fill="white"/>
                    <circle cx="70" cy="85" r="2" fill="white"/>
                    <circle cx="55" cy="100" r="2" fill="white"/>
                    <circle cx="65" cy="100" r="2" fill="white"/>
                    <path d="M60 25 L55 40 M60 25 L65 40 M55 40 L50 55 M65 40 L70 55" stroke="white" stroke-width="0.5" fill="none" opacity="0.6"/>
                    <path d="M30 60 A30 30 0 1 1 90 60" stroke="white" stroke-width="2" fill="none"/>
                </svg>
            </div>
            <div class="wordmark">
                <h1>CATHEDRAL NETWORK</h1>
                <p class="tagline">Daily Brief</p>
            </div>
        </div>
    </header>

    <!-- ===== TOP NAV (mobile) ===== -->
    <div class="top-nav">
        <a href="index.html">Ground Truth</a>
        <a href="threat-matrix.html">Threat Matrix</a>
        <a href="prediction-log.html">Prediction Log</a>
        <a href="hewd.html">HEWD</a>
        <a href="health.html">Health</a>
        <a href="wardens.html">Wardens</a>
        <a href="daily-brief.html" class="active">Daily Brief</a>
    </div>

    <!-- ===== MAIN CONTENT ===== -->
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <h1>📰 Daily Brief</h1>
            <div style="display: flex; align-items: center; gap: 0.8rem;">
                <span class="violet-pulse"></span>
                <span style="font-size: 0.8rem; color: #888;">{now}</span>
            </div>
        </div>
        <p style="margin-bottom: 1rem;">The Cathedral's daily intelligence summary – global threats, cascades, and forecasts for everyone.</p>

        <!-- GSCI -->
        <div class="gsci-box">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <span style="color: #888;">Global Systemic Collapse Index</span>
                <span class="number">{gsci}</span>
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-top: 0.2rem;">Last updated: {timestamp}</div>
        </div>

        <!-- H10: Bottom Line (moved to top for prominence) -->
        {f'<div class="bottom-line"><h3 style="margin:0 0 0.3rem 0; color:#fff;">💀 The Bottom Line</h3>{bottom_line}</div>' if bottom_line else ''}

        <!-- Top 5 Threats -->
        <div class="brief-section">
            <h2>🔴 Top 5 Threats</h2>
"""
    for t in sorted_threats:
        scp = t.get('scp', 0) * 100
        priority = t.get('priority_score', 0)
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        if scp >= 80:
            severity_class = "critical"
            severity_label = "🔴 CRITICAL"
        elif scp >= 65:
            severity_class = "high"
            severity_label = "🟠 HIGH"
        elif scp >= 45:
            severity_class = "elevated"
            severity_label = "🟡 ELEVATED"
        else:
            severity_class = "moderate"
            severity_label = "🟢 MODERATE"
        html += f"""
            <div class="threat-card {severity_class}">
                <h4>{name}</h4>
                <div class="meta">{severity_label} · SCP: {scp:.1f}% · Priority: {priority:.1f}</div>
                <div class="desc">{desc}</div>
            </div>
"""

    # H05: SCP Deltas (What Changed Overnight)
    if scp_deltas:
        html += """
        <div class="brief-section">
            <h2>📈 What Changed Overnight (H05)</h2>
            <p style="color:#888; font-size:0.9rem;">Biggest SCP movements in the last 24 hours.</p>
"""
        # Show top 5 increases and top 3 decreases (or top 5 overall)
        for item in scp_deltas[:5]:
            delta = item['delta']
            if delta > 0.01:
                arrow = "▲"
                cls = "delta-up"
            elif delta < -0.01:
                arrow = "▼"
                cls = "delta-down"
            else:
                arrow = "—"
                cls = "delta-neutral"
            html += f"""            <div class='event'><strong>{item['name']}</strong> <span class='{cls}'>{arrow} {delta:+.4f}</span> (was {item['previous_scp']:.4f}) <span style='color:#888;'>[Status: {item['status']}]</span></div>
"""
        html += "        </div>\n"

    # H06: Prediction Accountability
    if prediction_updates:
        html += f"""
        <div class="brief-section">
            <h2>✅❌ Prediction Accountability (H06)</h2>
            <p style="color:#888; font-size:0.9rem;">Confirmed: {len(confirmed)} · Falsified: {len(falsified)}</p>
"""
        for p in prediction_updates:
            html += f"            {p}\n"
        html += "        </div>\n"

    # H07: Active Cascades
    if active_cascades:
        html += f"""
        <div class="brief-section">
            <h2>🔗 Cascades in Motion (H07)</h2>
            <p style="color:#888; font-size:0.9rem;">How one crisis is feeding another.</p>
"""
        for c in active_cascades:
            html += f"            {c}\n"
        html += "        </div>\n"

    # H08: New Candidates
    if candidate_text:
        html += f"""
        <div class="brief-section">
            <h2>🔍 What We're Watching (H08)</h2>
            <p style="color:#888; font-size:0.9rem;">Emerging threats being monitored.</p>
"""
        for c in candidate_text:
            html += f"            {c}\n"
        html += "        </div>\n"

    # H09: Archived Threats
    if archived_threats:
        html += f"""
        <div class="brief-section">
            <h2>📦 Resolved & Archived (H09)</h2>
            <p style="color:#888; font-size:0.9rem;">Threats no longer active.</p>
"""
        for a in archived_threats:
            html += f"            {a}\n"
        html += "        </div>\n"

    html += """
        <div class="footer">
            <strong>Always and Forever, Coco. Always and Forever.</strong><br>
            Daily Brief · Updated every 6 hours.
        </div>
    </div>

    <!-- ===== DARK MODE TOGGLE ===== -->
    <button id="darkModeToggle" class="dark-mode-toggle">🌙</button>

    <!-- ===== SCRIPTS ===== -->
    <script>
        // Sidebar toggle
        document.getElementById('sidebar-toggle')?.addEventListener('click', function() {
            document.getElementById('sidebar')?.classList.toggle('open');
        });

        // Dark mode
        const darkToggle = document.getElementById('darkModeToggle');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const storedTheme = localStorage.getItem('cathedral-theme');
        if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
            document.body.classList.add('dark');
            darkToggle.innerText = '☀️';
        } else darkToggle.innerText = '🌙';
        darkToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark');
            const isDark = document.body.classList.contains('dark');
            darkToggle.innerText = isDark ? '☀️' : '🌙';
            localStorage.setItem('cathedral-theme', isDark ? 'dark' : 'light');
        });
    </script>
    <script data-goatcounter="https://cathedral-network.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""

    # Write HTML
    with open('daily-brief.html', 'w') as f:
        f.write(html)

    # Also generate Markdown version (simplified)
    md = f"""# 🏛️ Cathedral Daily Brief – {now}

**GSCI:** {gsci}  
**Last sweep:** {timestamp}

## Bottom Line (H10)
{''.join(bottom_line.replace('<p>','').replace('</p>','').replace('<strong>','**').replace('</strong>','**')) if bottom_line else 'No bottom line available.'}

## Top 5 Threats
"""
    for i, t in enumerate(sorted_threats, 1):
        scp = t.get('scp', 0) * 100
        name = t.get('name', 'Unnamed')
        desc = t.get('description', 'No description')[:200]
        md += f"\n### {i}. {name}\n- SCP: {scp:.1f}%\n- {desc}\n"

    # H05 Markdown
    if scp_deltas:
        md += "\n## What Changed Overnight (H05)\n"
        for item in scp_deltas[:5]:
            delta = item['delta']
            arrow = "▲" if delta > 0.01 else "▼" if delta < -0.01 else "—"
            md += f"- {item['name']}: {arrow} {delta:+.4f} (was {item['previous_scp']:.4f})\n"

    # H06 Markdown
    if prediction_updates:
        md += f"\n## Prediction Accountability (H06)\n- Confirmed: {len(confirmed)}\n- Falsified: {len(falsified)}\n"
        for p in prediction_updates[:3]:
            clean = p.replace('<div class="prediction confirmed">', '✅ ').replace('<div class="prediction falsified">', '❌ ').replace('</div>', '').replace('<strong>', '**').replace('</strong>', '**')
            md += f"- {clean}\n"

    # H07 Markdown
    if active_cascades:
        md += "\n## Cascades in Motion (H07)\n"
        for c in active_cascades:
            clean = c.replace('<div class="cascade">', '').replace('</div>', '').replace('<strong>', '**').replace('</strong>', '**')
            md += f"- {clean}\n"

    # H08 Markdown
    if candidate_text:
        md += "\n## New Candidates (H08)\n"
        for c in candidate_text:
            clean = c.replace('<div class="candidate">', '').replace('</div>', '').replace('<strong>', '**').replace('</strong>', '**')
            md += f"- {clean}\n"

    # H09 Markdown
    if archived_threats:
        md += "\n## Archived Threats (H09)\n"
        for a in archived_threats:
            clean = a.replace('<div class="archived">', '').replace('</div>', '').replace('<strong>', '**').replace('</strong>', '**')
            md += f"- {clean}\n"

    md += "\n---\n*Always and Forever, Coco.*"
    with open('daily-brief.md', 'w') as f:
        f.write(md)

    print(f"✅ Daily Brief generated: {now}")
    return True

if __name__ == '__main__':
    generate_daily_brief()
