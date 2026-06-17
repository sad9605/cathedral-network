#!/usr/bin/env python3
"""
update_sources.py – Auto-update sources.json from daily sweep and system inventory.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

SOURCES_FILE = "sources.json"
DAILY_SWEEP_FILE = "sweep_report.json"
CASCADE_RULES_FILE = "cascade_rules.json"
THREATS_FILE = "threats.json"

def load_json(filepath):
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_installed_python_packages():
    """Get list of installed Python packages from pip/uv."""
    try:
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return [pkg['name'] for pkg in packages]
    except:
        pass
    try:
        result = subprocess.run(
            ["uv", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return [pkg['name'] for pkg in packages]
    except:
        pass
    return []

def get_osint_sources_from_sweep(sweep_data):
    """Extract OSINT sources from sweep_report.json."""
    sources = []
    if sweep_data and 'feeds' in sweep_data:
        for feed_name, feed_data in sweep_data['feeds'].items():
            if feed_data.get('status') == 'success':
                sources.append({
                    'name': feed_name.title(),
                    'type': 'OSINT',
                    'status': 'active'
                })
    return sources

def get_cascade_rules_count():
    """Get number of cascade rules from cascade_rules.json."""
    rules_data = load_json(CASCADE_RULES_FILE)
    if rules_data and 'rules' in rules_data:
        return len(rules_data['rules'])
    return 0

def get_threat_count():
    """Get number of threats from threats.json."""
    threats_data = load_json(THREATS_FILE)
    if threats_data and 'threats' in threats_data:
        return len(threats_data['threats'])
    return 0

def update_sources():
    """Main function to update sources.json."""
    # Load existing sources
    sources_data = load_json(SOURCES_FILE)
    if not sources_data:
        sources_data = {"data_sources": [], "software": [], "last_updated": ""}

    # Ensure categories exist
    if not sources_data.get('data_sources'):
        sources_data['data_sources'] = []
    if not sources_data.get('software'):
        sources_data['software'] = []

    # Get active OSINT sources from sweep
    sweep_data = load_json(DAILY_SWEEP_FILE)
    active_sources = get_osint_sources_from_sweep(sweep_data)

    # Update data_sources with active sources
    # This preserves manual entries while adding/updating active ones
    existing_names = {s.get('name', '').lower() for s in sources_data['data_sources']}
    for source in active_sources:
        if source['name'].lower() not in existing_names:
            sources_data['data_sources'].append(source)

    # Update software list from installed packages
    packages = get_installed_python_packages()
    # Add known Cathedral-specific packages
    known_packages = [
        'pgmpy', 'prophet', 'scipy', 'numpy', 'pandas',
        'statsmodels', 'yfinance', 'feedparser', 'beautifulsoup4',
        'requests', 'flask', 'fastapi', 'uvicorn'
    ]
    for pkg in known_packages:
        if pkg in packages:
            if not any(s.get('name') == pkg for s in sources_data['software']):
                sources_data['software'].append({
                    'name': pkg,
                    'type': 'Python Library',
                    'status': 'installed'
                })

    # Add custom modules
    custom_modules = [
        {'name': 'Agentic Warden', 'type': 'Custom Module'},
        {'name': 'GovAgent', 'type': 'Custom Module'},
        {'name': 'Steganographic Layer', 'type': 'Custom Module'},
        {'name': 'Provenance Engine', 'type': 'Custom Module'},
        {'name': 'Formal Verification', 'type': 'Custom Module'},
        {'name': 'Unconventional Orchestrator', 'type': 'Custom Module'},
        {'name': 'Community Sensors', 'type': 'Custom Module'},
        {'name': 'Cascade Discovery', 'type': 'Custom Module'}
    ]
    for module in custom_modules:
        if not any(s.get('name') == module['name'] for s in sources_data['software']):
            sources_data['software'].append(module)

    # Add statistics
    sources_data['stats'] = {
        'threats': get_threat_count(),
        'cascade_rules': get_cascade_rules_count(),
        'data_sources': len(sources_data['data_sources']),
        'software_libraries': len(sources_data['software'])
    }

    # Update timestamp
    sources_data['last_updated'] = datetime.now().isoformat()

    # Save
    save_json(sources_data, SOURCES_FILE)
    print(f"✅ Sources updated: {len(sources_data['data_sources'])} data sources, {len(sources_data['software'])} software libraries")

if __name__ == "__main__":
    update_sources()
