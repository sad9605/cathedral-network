#!/usr/bin/env python3
"""
InSAR Infrastructure Integrity Monitor
Monitor critical infrastructure using Sentinel-1 radar data
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class InSARMonitor:
    """
    Monitor infrastructure integrity using Sentinel-1 radar data.
    """
    
    def __init__(self):
        self.satellite = "Sentinel-1"
        self.monitoring_history = []
        
        # Sample infrastructure assets
        self.default_assets = [
            {'id': 'BRIDGE_001', 'name': 'Golden Gate Bridge', 'lat': 37.8199, 'lon': -122.4783},
            {'id': 'BRIDGE_002', 'name': 'Brooklyn Bridge', 'lat': 40.7057, 'lon': -73.9964},
            {'id': 'DAM_001', 'name': 'Hoover Dam', 'lat': 36.0162, 'lon': -114.7373},
            {'id': 'DATACENTER_001', 'name': 'AWS Virginia', 'lat': 38.9072, 'lon': -77.0369}
        ]
    
    def get_displacement_data(self, asset: Dict, days: int = 30) -> List[Dict]:
        """
        Simulate InSAR displacement data for an asset.
        In production: would query Sentinel-1 API (ASF, Copernicus).
        """
        readings = []
        now = datetime.now()
        
        # Base displacement with random walk + seasonal trend
        base_displacement = random.uniform(-2, 2)  # mm
        seasonal_amplitude = random.uniform(0.5, 2.0)
        
        for i in range(days):
            date = now - timedelta(days=days-i)
            
            # Random walk component
            random_walk = np.random.normal(0, 0.2)
            base_displacement += random_walk
            
            # Seasonal component
            seasonal = seasonal_amplitude * np.sin(i / 30 * np.pi)
            
            displacement = base_displacement + seasonal
            
            readings.append({
                'timestamp': date.isoformat(),
                'displacement_mm': float(displacement),
                'baseline': float(base_displacement)
            })
        
        return readings
    
    def calculate_risk(self, displacement_data: List[Dict]) -> Dict:
        """
        Calculate risk based on displacement trend.
        """
        if len(displacement_data) < 5:
            return {'level': 'INSUFFICIENT_DATA', 'score': 0}
        
        displacements = [d['displacement_mm'] for d in displacement_data]
        
        # Calculate trend using linear regression
        x = np.arange(len(displacements))
        slope = np.polyfit(x, displacements, 1)[0]
        
        # Calculate volatility
        volatility = np.std(displacements)
        
        # Determine risk level
        if slope > 3.0:
            level = "CRITICAL"
            score = 0.9
        elif slope > 1.5:
            level = "HIGH"
            score = 0.7
        elif slope > 0.5:
            level = "MEDIUM"
            score = 0.5
        else:
            level = "LOW"
            score = 0.2
        
        return {
            'level': level,
            'score': score,
            'trend_mm_per_day': float(slope),
            'volatility_mm': float(volatility),
            'last_displacement': float(displacements[-1])
        }
    
    def monitor_asset(self, asset: Dict, days: int = 30) -> Dict:
        """
        Monitor a single asset.
        """
        # Get displacement data
        displacement_data = self.get_displacement_data(asset, days)
        
        # Calculate risk
        risk = self.calculate_risk(displacement_data)
        
        result = {
            'asset_id': asset['id'],
            'asset_name': asset['name'],
            'location': {'lat': asset['lat'], 'lon': asset['lon']},
            'satellite': self.satellite,
            'days_monitored': days,
            'displacement_data': displacement_data[-7:],  # Last 7 days
            'risk': risk,
            'timestamp': datetime.now().isoformat()
        }
        
        self.monitoring_history.append(result)
        return result
    
    def monitor_all_assets(self, assets: List[Dict] = None, days: int = 30) -> Dict:
        """
        Monitor all infrastructure assets.
        """
        assets = assets or self.default_assets
        results = {}
        
        for asset in assets:
            results[asset['id']] = self.monitor_asset(asset, days)
        
        return {
            'assets_monitored': len(assets),
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

# Standalone execution
if __name__ == "__main__":
    print("🛰️ InSAR Infrastructure Monitor")
    print("=" * 50)
    
    # Initialize monitor
    monitor = InSARMonitor()
    
    print("\n🛰️ Monitoring infrastructure...")
    
    # Monitor all assets
    results = monitor.monitor_all_assets()
    
    # Display results
    print(f"\n📊 Infrastructure Status ({results['assets_monitored']} assets):")
    for asset_id, data in results['results'].items():
        risk = data['risk']
        print(f"\n  {data['asset_name']} ({asset_id}):")
        print(f"    Risk Level: {risk['level']}")
        print(f"    Trend: {risk['trend_mm_per_day']:.2f} mm/day")
        print(f"    Score: {risk['score']:.1%}")
        print(f"    Last Displacement: {risk['last_displacement']:.2f} mm")
    
    # Save results
    with open('insar_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to insar_results.json")
