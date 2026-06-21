#!/usr/bin/env python3
"""
indices.py – Regional and Threat Indices for Cathedral Network
Implements: NTS, CII, DVI, WMI, CDR
"""

import math
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from cathedral_math import (
    nts_score,
    conflict_intensity_index,
    disinformation_vulnerability_index,
    wealth_mobility_index,
    cable_disruption_risk,
    nts_band
)

REGIONS = [
    'North America', 'Central America', 'Latin America',
    'Europe', 'Baltic', 'Russia', 'Caucasus',
    'Middle East', 'North Africa', 'West Africa',
    'Central Africa', 'East Africa', 'Southern Africa',
    'South Asia', 'Southeast Asia', 'East Asia',
    'Oceania', 'Pacific Islands', 'Arctic & Antarctic',
    'Central Asia'
]

def load_threats():
    """Load threats.json if available."""
    if Path('threats.json').exists():
        with open('threats.json', 'r') as f:
            return json.load(f).get('threats', [])
    return []

def compute_regional_index(threats: List[Dict], region: str) -> Dict:
    """
    Compute all indices for a specific region.
    """
    region_threats = [t for t in threats if t.get('country') == region]
    
    # DS for region
    from cathedral_math import compute_ds
    ds = compute_ds(region_threats)
    
    # NSI (simplified – uses domain scores)
    nsi = ds + sum(t.get('scp', 0) for t in region_threats) / len(region_threats) if region_threats else 0
    
    # NTS
    nts = nts_score(ds, nsi)
    
    # CII (simplified)
    cii = conflict_intensity_index(
        fatalities=sum(t.get('fatalities', 0) for t in region_threats),
        displacement=sum(t.get('displaced', 0) for t in region_threats),
        structural=sum(t.get('structural_score', 0) for t in region_threats)
    )
    
    # DVI (simplified)
    dvi = disinformation_vulnerability_index(
        trust=100 - nts,
        polarization=sum(t.get('polarization', 0) for t in region_threats),
        media_literacy=70,
        incidents=sum(t.get('disinfo_incidents', 0) for t in region_threats)
    )
    
    return {
        'region': region,
        'ds': ds,
        'nsi': nsi,
        'nts': nts,
        'nts_band': nts_band(nts),
        'cii': cii,
        'dvi': dvi,
        'wmi': wealth_mobility_index(50, 30, False),
        'cdr': cable_disruption_risk(20, False, 30),
        'threat_count': len(region_threats),
        'last_updated': datetime.now().isoformat()
    }

def generate_regional_indices():
    """Generate indices for all regions and save to JSON."""
    threats = load_threats()
    results = []
    for region in REGIONS:
        result = compute_regional_index(threats, region)
        results.append(result)
    
    output = {
        'last_updated': datetime.now().isoformat(),
        'regions': results
    }
    
    with open('regional_indices.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Regional indices saved for {len(results)} regions")
    return results
    # After computing regional_scores
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "regions": regional_scores
    }
    save_json(output_data, "indices.json")
    print(f"✅ Regional indices saved to indices.json")

if __name__ == "__main__":
    generate_regional_indices()


