#!/usr/bin/env python3
"""
Generate HTML dashboard from sweep reports
"""

import json
from datetime import datetime

def generate_html_dashboard():
    """Create a readable HTML dashboard from JSON data."""
    
    # Load data
    try:
        with open('sweep_report.json', 'r') as f:
            sweep = json.load(f)
    except:
        sweep = {'events': [], 'watchlist_hits': []}
    
    try:
        with open('threats.json', 'r') as f:
            threats = json.load(f)
    except:
        threats = {}
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Cathedral Dashboard</title>
    <style>
        body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff88; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ border-bottom: 2px solid #00ff88; padding-bottom: 10px; }}
        .section {{ background: #1a1a1a; border: 1px solid #00ff88; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .event {{ border-left: 3px solid #ff8800; padding: 10px; margin: 10px 0; background: #222; }}
        .threat {{ border-left: 3px solid #ff0044; padding: 10px; margin: 10px 0; background: #222; }}
        .timestamp {{ color: #888; font-size: 0.8em; }}
        .high {{ color: #ff0044; font-weight: bold; }}
        .medium {{ color: #ff8800; font-weight: bold; }}
        .low {{ color: #00ff88; font-weight: bold; }}
        pre {{ background: #111; padding: 10px; overflow-x: auto; }}
        .stats {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .stat-box {{ background: #1a1a1a; border: 1px solid #00ff88; padding: 15px; border-radius: 8px; min-width: 150px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ CATHEDRAL DASHBOARD</h1>
            <div class="timestamp">Generated: {datetime.now().isoformat()}</div>
        </div>
        
        <div class="section">
            <h2>📊 Statistics</h2>
            <div class="stats">
                <div class="stat-box">Events: {len(sweep.get('events', []))}</div>
                <div class="stat-box">Watchlist Hits: {len(sweep.get('watchlist_hits', []))}</div>
                <div class="stat-box">Threats Tracked: {len(threats.get('threats', {}))}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>⚠️ Watchlist Hits</h2>
            {''.join([f"""
            <div class="event">
                <strong>{hit.get('title', 'Unknown')}</strong>
                <div>Source: {hit.get('source', 'N/A')}</div>
                <div>Priority: <span class="{hit.get('priority', 'low').lower()}">{hit.get('priority', 'Unknown')}</span></div>
                <div class="timestamp">{hit.get('timestamp', '')}</div>
            </div>
            """ for hit in sweep.get('watchlist_hits', [])[:10]])}
            {'' if sweep.get('watchlist_hits') else '<div>No watchlist hits</div>'}
        </div>
        
        <div class="section">
            <h2>🔥 Active Threats</h2>
            {''.join([f"""
            <div class="threat">
                <strong>{threat_id}: {threat.get('name', 'Unnamed')}</strong>
                <div>Probability: {threat.get('probability', 0):.2%}</div>
                <div>Status: {threat.get('status', 'Unknown')}</div>
                <div>Priority Score: {threat.get('priority_score', 0):.2f}</div>
            </div>
            """ for threat_id, threat in threats.get('threats', {}).items()][:10])}
            {'' if threats.get('threats') else '<div>No threats tracked</div>'}
        </div>
        
        <div class="section">
            <h2>📋 Raw JSON (Last 10 Events)</h2>
            <pre>{json.dumps(sweep.get('events', [])[-10:], indent=2)[:2000]}...</pre>
        </div>
    </div>
</body>
</html>
"""
    
    with open('dashboard.html', 'w') as f:
        f.write(html)
    
    print("✅ Dashboard generated: dashboard.html")
    print("   Open in browser: open dashboard.html")

if __name__ == "__main__":
    generate_html_dashboard()
