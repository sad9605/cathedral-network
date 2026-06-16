#!/usr/bin/env python3
"""
Community Sensor Network Integration
Ingest data from low-cost community-deployed sensors
"""

import json
import time
import random
import os
from datetime import datetime
from typing import Dict, List, Optional

class CommunitySensorNetwork:
    """
    Ingest data from low-cost community-deployed sensors.
    """
    
    def __init__(self, sensor_config: Optional[Dict] = None):
        self.sensors = sensor_config or {}
        self.sensor_data_history = []
        
        # Default sensors if none provided
        if not self.sensors:
            self.sensors = {
                'SENSOR_WATER_001': {
                    'type': 'water_level',
                    'location': 'Houston, TX',
                    'last_reading': None
                },
                'SENSOR_SEISMIC_001': {
                    'type': 'seismic',
                    'location': 'San Francisco, CA',
                    'last_reading': None
                },
                'SENSOR_TEMP_001': {
                    'type': 'temperature',
                    'location': 'Phoenix, AZ',
                    'last_reading': None
                }
            }
    
    def read_sensor_data(self, sensor_id: str) -> Dict:
        """
        Simulate reading from sensor.
        In production: would use serial, MQTT, or API.
        """
        sensor = self.sensors.get(sensor_id, {})
        sensor_type = sensor.get('type', 'unknown')
        
        # Generate realistic sensor readings
        if sensor_type == 'water_level':
            data = {
                'water_level_cm': random.uniform(10, 500),
                'flow_rate_lps': random.uniform(0, 100),
                'battery_voltage': random.uniform(3.3, 4.2)
            }
        elif sensor_type == 'seismic':
            data = {
                'vibration_mm_s2': random.uniform(0, 50),
                'frequency_hz': random.uniform(0.1, 10),
                'peak_accel_g': random.uniform(0.001, 0.5)
            }
        elif sensor_type == 'temperature':
            data = {
                'temperature_c': random.uniform(-10, 45),
                'humidity_percent': random.uniform(20, 90),
                'pressure_hpa': random.uniform(980, 1030)
            }
        else:
            data = {'value': random.uniform(0, 100)}
        
        return {
            'sensor_id': sensor_id,
            'type': sensor_type,
            'location': sensor.get('location', 'Unknown'),
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'signal_strength': random.randint(1, 5)
        }
    
    def ingest_all_sensors(self) -> List[Dict]:
        """
        Read all configured sensors and ingest.
        """
        sensor_data = []
        for sensor_id in self.sensors.keys():
            try:
                data = self.read_sensor_data(sensor_id)
                sensor_data.append(data)
                
                # Update last reading
                self.sensors[sensor_id]['last_reading'] = data['timestamp']
            except Exception as e:
                print(f"⚠️ Error reading sensor {sensor_id}: {e}")
        
        self.sensor_data_history.extend(sensor_data)
        return sensor_data
    
    def deploy_sensor(self, location: str, sensor_type: str) -> Dict:
        """
        Generate deployment instructions for new sensor.
        """
        sensor_id = f"SENSOR_{sensor_type.upper()}_{int(time.time())}"
        
        instructions = f"""
        📡 SENSOR DEPLOYMENT INSTRUCTIONS
        ================================
        Sensor ID: {sensor_id}
        Type: {sensor_type}
        Location: {location}
        
        Hardware Required:
        - {sensor_type.upper()} sensor module
        - Microcontroller (ESP32 or Arduino)
        - Solar panel + battery backup
        - LoRaWAN or cellular module
        
        Setup Steps:
        1. Mount sensor at {location}
        2. Connect to microcontroller
        3. Configure reporting interval (1 hour)
        4. Test connection to Cathedral network
        5. Register sensor with this ID
        """
        
        deployment = {
            'sensor_id': sensor_id,
            'type': sensor_type,
            'location': location,
            'instructions': instructions,
            'deployed_at': datetime.now().isoformat()
        }
        
        self.sensors[sensor_id] = deployment
        return deployment
    
    def get_status(self) -> Dict:
        """
        Get network status.
        """
        active = sum(1 for s in self.sensors.values() 
                    if s.get('last_reading'))
        return {
            'total_sensors': len(self.sensors),
            'active_sensors': active,
            'last_update': datetime.now().isoformat(),
            'history_length': len(self.sensor_data_history)
        }

# Standalone execution
if __name__ == "__main__":
    print("📡 Community Sensor Network")
    print("=" * 50)
    
    # Initialize network
    network = CommunitySensorNetwork()
    
    # Read all sensors
    print("\n🔍 Reading sensors...")
    sensor_data = network.ingest_all_sensors()
    
    # Display readings
    print(f"\n📊 Sensor Readings ({len(sensor_data)} sensors):")
    for data in sensor_data[:5]:  # Show first 5
        print(f"\n  {data['sensor_id']} ({data['type']}) at {data['location']}:")
        for key, value in list(data['data'].items())[:3]:
            print(f"    {key}: {value:.2f}")
    
    # Deploy new sensor
    print("\n🚀 Deploying new sensor...")
    deployment = network.deploy_sensor("Seattle, WA", "water_level")
    print(f"✅ Deployed: {deployment['sensor_id']}")
    
    # Status
    status = network.get_status()
    print(f"\n📈 Network Status:")
    print(f"  Total: {status['total_sensors']}")
    print(f"  Active: {status['active_sensors']}")
    print(f"  Readings: {status['history_length']}")
    
    # Save data
    with open('sensor_data.json', 'w') as f:
        json.dump({
            'readings': sensor_data,
            'status': status
        }, f, indent=2)
    
    print(f"\n✅ Data saved to sensor_data.json")
