#!/usr/bin/env python3
"""
arifos_floors.py – AI Thermoregulation for Cathedral.
Auto-adjusts system parameters based on load and threat criticality.
"""

import json
import psutil
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

THREATS_FILE = "threats.json"
CONFIG_FILE = "arifos_config.json"
POLICY_FILE = "agentic_policy.json"

class arifOS:
    def __init__(self):
        self.config = self.load_config()
        self.current_state = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'gsci': 0,
            'threat_count': 0,
            'escalation_count': 0,
            'last_adjustment': None
        }
    
    def load_config(self):
        default_config = {
            'cpu_threshold_high': 80,
            'cpu_threshold_low': 30,
            'memory_threshold_high': 85,
            'gsci_high': 60,
            'gsci_critical': 75,
            'confidence_floor_normal': 0.3,
            'confidence_floor_high_load': 0.6,
            'confidence_floor_critical': 0.9,
            'escalation_timeout_seconds': 300,
            'min_actors_required': 2
        }
        if Path(CONFIG_FILE).exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    def read_system_state(self):
        """Read current system metrics."""
        self.current_state['cpu_usage'] = psutil.cpu_percent(interval=1)
        self.current_state['memory_usage'] = psutil.virtual_memory().percent
        
        if Path(THREATS_FILE).exists():
            with open(THREATS_FILE) as f:
                data = json.load(f)
                self.current_state['gsci'] = data.get('gsci', 50)
                self.current_state['threat_count'] = len(data.get('threats', []))
        return self.current_state
    
    def adjust_policy(self):
        """Adjust agentic policy thresholds based on current state."""
        state = self.read_system_state()
        config = self.config
        
        # Determine load level
        cpu = state['cpu_usage']
        mem = state['memory_usage']
        gsci = state['gsci']
        
        if cpu > config['cpu_threshold_high'] or mem > config['memory_threshold_high']:
            load_level = 'high'
        elif cpu < config['cpu_threshold_low'] and gsci < config['gsci_high']:
            load_level = 'low'
        else:
            load_level = 'normal'
        
        # Adjust confidence floor
        if load_level == 'high':
            confidence_floor = config['confidence_floor_high_load']
            escalation_timeout = config['escalation_timeout_seconds'] * 0.5  # shorter timeout during high load
            min_actors = config['min_actors_required'] + 1
        elif gsci > config['gsci_critical']:
            confidence_floor = config['confidence_floor_critical']
            escalation_timeout = config['escalation_timeout_seconds'] * 1.5
            min_actors = config['min_actors_required'] + 2
        else:
            confidence_floor = config['confidence_floor_normal']
            escalation_timeout = config['escalation_timeout_seconds']
            min_actors = config['min_actors_required']
        
        # Apply adjustments to policy file
        if Path(POLICY_FILE).exists():
            with open(POLICY_FILE) as f:
                policy = json.load(f)
            # Update risk tiers with new thresholds
            for tier in policy.get('risk_tiers', []):
                if tier['tier'] == 'Orange':
                    tier['confidence_threshold'] = confidence_floor
                    tier['timeout_minutes'] = int(escalation_timeout / 60)
                if tier['tier'] == 'Red':
                    tier['requires_quorum'] = min_actors
            
            with open(POLICY_FILE, 'w') as f:
                json.dump(policy, f, indent=2)
        
        self.current_state['last_adjustment'] = {
            'timestamp': datetime.now().isoformat(),
            'load_level': load_level,
            'confidence_floor': confidence_floor,
            'escalation_timeout': escalation_timeout,
            'min_actors': min_actors
        }
        
        logging.info(f"Adjusted policy to {load_level} load (confidence floor: {confidence_floor})")
        return self.current_state['last_adjustment']
    
    def status(self):
        """Return current system status."""
        state = self.read_system_state()
        return {
            'system': state,
            'config': self.config,
            'last_adjustment': self.current_state['last_adjustment']
        }

if __name__ == "__main__":
    arifos = arifOS()
    print("arifOS Floors initialized")
    adjustment = arifos.adjust_policy()
    print(f"Adjustment applied: {adjustment}")
