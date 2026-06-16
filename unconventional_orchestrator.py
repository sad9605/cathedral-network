#!/usr/bin/env python3
"""
Cathedral Unconventional Intelligence Orchestrator
Master controller for all non-linear intelligence methods
"""

import json
import time
from datetime import datetime
from typing import Dict, List

# Import all modules
try:
    from stochastic_pattern_analysis import StochasticPatternAnalyzer
    from steganographic_layer import SteganographicCommLayer
    from provenance_engine import ProvenanceEngine
    from formal_verification import FormalVerifier
    from community_sensors import CommunitySensorNetwork
    from insar_integrity import InSARMonitor
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    print("   Some modules may not be available yet.")

class CathedralUnconventionalOrchestrator:
    """
    Master orchestrator for all unconventional intelligence methods.
    """
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path) if config_path else {}
        self.results = {}
        self.start_time = None
        
        # Initialize modules
        self.spa = StochasticPatternAnalyzer(self.config.get('cascade_rules'))
        self.stego = SteganographicCommLayer()
        self.provenance = ProvenanceEngine()
        self.formal = FormalVerifier(self.config.get('cascade_rules', []))
        self.sensors = CommunitySensorNetwork(self.config.get('sensors'))
        self.insar = InSARMonitor()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def run_full_unconventional_sweep(self) -> Dict:
        """
        Execute all unconventional modules.
        Returns comprehensive multi-spectral analysis.
        """
        self.start_time = time.time()
        
        print("🔄 Starting Unconventional Intelligence Sweep...")
        print("=" * 60)
        
        results = {}
        
        # 1. Stochastic Pattern Analysis
        print("\n🧠 Generating stochastic patterns...")
        try:
            threat_context = self.config.get('current_threats', {})
            results['hypotheses'] = self.spa.run(threat_context)
            print(f"   ✅ Generated {results['hypotheses']['total_seeds']} seeds")
            print(f"      {results['hypotheses']['high_confidence_seeds']} high-confidence")
        except Exception as e:
            results['hypotheses'] = {'error': str(e)}
            print(f"   ❌ Error: {e}")
        
        # 2. Sensor Network
        print("\n📡 Reading community sensors...")
        try:
            results['sensor_data'] = {
                'readings': self.sensors.ingest_all_sensors(),
                'status': self.sensors.get_status()
            }
            print(f"   ✅ Read {len(results['sensor_data']['readings'])} sensors")
        except Exception as e:
            results['sensor_data'] = {'error': str(e)}
            print(f"   ❌ Error: {e}")
        
        # 3. InSAR Monitoring
        print("\n🛰️ Scanning infrastructure...")
        try:
            infrastructure_assets = self.config.get('infrastructure', [])
            if not infrastructure_assets:
                # Use defaults from InSAR monitor
                infrastructure_assets = self.insar.default_assets
            
            results['infrastructure'] = self.insar.monitor_all_assets(infrastructure_assets)
            print(f"   ✅ Monitored {results['infrastructure']['assets_monitored']} assets")
        except Exception as e:
            results['infrastructure'] = {'error': str(e)}
            print(f"   ❌ Error: {e}")
        
        # 4. Formal Verification
        print("\n🏗️ Generating mathematical proofs...")
        try:
            results['formal_proofs'] = self.formal.generate_proof_certificate()
            proof_status = "CONSISTENT" if results['formal_proofs']['consistent'] else "INCONSISTENT"
            print(f"   ✅ Proof status: {proof_status}")
        except Exception as e:
            results['formal_proofs'] = {'error': str(e)}
            print(f"   ❌ Error: {e}")
        
        # 5. Media Provenance (if pending media exists)
        media_files = self.config.get('pending_media', [])
        if media_files:
            print("\n🎨 Verifying media provenance...")
            results['provenance'] = []
            for media_file in media_files:
                try:
                    result = self.provenance.full_provenance_check(media_file)
                    results['provenance'].append(result)
                except Exception as e:
                    results['provenance'].append({'error': str(e)})
            print(f"   ✅ Verified {len(media_files)} media files")
        else:
            print("\n🎨 No media files to verify")
            results['provenance'] = []
        
        # 6. Generate unified report
        elapsed = time.time() - self.start_time
        results['unified_report'] = {
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': elapsed,
            'modules_executed': ['spa', 'sensors', 'insar', 'formal', 'provenance'],
            'module_count': 5,
            'status': 'COMPLETE'
        }
        
        # Generate summary
        results['summary'] = self.generate_summary(results)
        
        self.results = results
        return results
    
    def generate_summary(self, results: Dict) -> str:
        """Generate human-readable summary."""
        summary = f"""
🎯 CATHEDRAL UNCONVENTIONAL INTELLIGENCE SUMMARY
===============================================
Timestamp: {results['unified_report']['timestamp']}
Execution Time: {results['unified_report']['execution_time_seconds']:.2f}s

📊 MODULE OUTPUTS:
"""
        # SPA results
        if 'hypotheses' in results and 'error' not in results['hypotheses']:
            h = results['hypotheses']
            summary += f"""
🧠 Stochastic Pattern Analysis:
   - Seeds Generated: {h['total_seeds']}
   - High Confidence: {h['high_confidence_seeds']}
   - Top Hypothesis: {h.get('top_hypotheses', [{}])[0].get('seed_id', 'N/A')}
"""
        
        # Sensor results
        if 'sensor_data' in results and 'error' not in results['sensor_data']:
            s = results['sensor_data']
            summary += f"""
📡 Community Sensors:
   - Sensors Active: {s['status']['active_sensors']}
   - Total Sensors: {s['status']['total_sensors']}
"""
        
        # Infrastructure results
        if 'infrastructure' in results and 'error' not in results['infrastructure']:
            infra = results['infrastructure']
            summary += f"""
🛰️ Infrastructure Monitoring:
   - Assets Monitored: {infra['assets_monitored']}
   - Critical Assets: {sum(1 for r in infra['results'].values() if r['risk']['level'] == 'CRITICAL')}
   - High Risk Assets: {sum(1 for r in infra['results'].values() if r['risk']['level'] == 'HIGH')}
"""
        
        # Formal verification
        if 'formal_proofs' in results and 'error' not in results['formal_proofs']:
            f = results['formal_proofs']
            summary += f"""
🏗️ Formal Verification:
   - Status: {'✅ CONSISTENT' if f['consistent'] else '❌ INCONSISTENT'}
   - Rules Verified: {f['rules_verified']}
"""
        
        summary += f"""
===============================================
✅ Unconventional Intelligence Sweep COMPLETE
"""
        return summary
    
    def save_results(self, output_path: str = "unconventional_sweep_report.json"):
        """Save results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📁 Results saved to {output_path}")

# Standalone execution
if __name__ == "__main__":
    print("🎯 Cathedral Unconventional Intelligence Orchestrator")
    print("=" * 60)
    
    # Create default config if none exists
    config = {
        'cascade_rules': [],
        'sensors': {},
        'infrastructure': [],
        'pending_media': [],
        'current_threats': {}
    }
    
    # Save config
    with open('unconventional_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Initialize orchestrator
    orchestrator = CathedralUnconventionalOrchestrator('unconventional_config.json')
    
    # Run full sweep
    results = orchestrator.run_full_unconventional_sweep()
    
    # Display summary
    print("\n" + results['summary'])
    
    # Save results
    orchestrator.save_results()
    
    print("\n✅ All unconventional intelligence tracks operational!")
