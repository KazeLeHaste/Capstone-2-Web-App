#!/usr/bin/env python3
"""
Test script to verify vehicle filtering fix
"""

import requests
import json
from pathlib import Path
import time

def test_vehicle_filtering():
    """Test the vehicle filtering functionality with different configurations"""
    
    base_url = "http://localhost:5000/api"
    
    # Test configuration 1: Only passenger cars
    config1 = {
        "sessionId": f"test_session_{int(time.time())}_passenger_only",
        "timestamp": "2025-09-02T15:00:00.000Z",
        "config": {
            "sumo_begin": 0,
            "sumo_end": 1800,
            "sumo_step_length": 1,
            "sumo_time_to_teleport": 300,
            "sumo_traffic_intensity": 1,
            "enabledVehicles": ["passenger"],  # Only passenger cars
            "vehicleTypes": {
                "passenger": {"enabled": True, "name": "Passenger Cars"},
                "bus": {"enabled": False, "name": "Buses"},
                "truck": {"enabled": False, "name": "Trucks"},
                "motorcycle": {"enabled": False, "name": "Motorcycles"}
            }
        }
    }
    
    # Test configuration 2: All vehicles
    config2 = {
        "sessionId": f"test_session_{int(time.time())}_all_vehicles",
        "timestamp": "2025-09-02T15:00:00.000Z", 
        "config": {
            "sumo_begin": 0,
            "sumo_end": 1800,
            "sumo_step_length": 1,
            "sumo_time_to_teleport": 300,
            "sumo_traffic_intensity": 1,
            "enabledVehicles": ["passenger", "bus", "truck", "motorcycle"],
            "vehicleTypes": {
                "passenger": {"enabled": True, "name": "Passenger Cars"},
                "bus": {"enabled": True, "name": "Buses"},
                "truck": {"enabled": True, "name": "Trucks"},
                "motorcycle": {"enabled": True, "name": "Motorcycles"}
            }
        }
    }
    
    # Test both configurations
    for i, config in enumerate([config1, config2], 1):
        print(f"\n=== Testing Configuration {i}: {config['config']['enabledVehicles']} ===")
        
        # Save configuration
        response = requests.post(f"{base_url}/simulation/save-config", json=config)
        if response.status_code == 200:
            print("✅ Configuration saved successfully")
        else:
            print(f"❌ Failed to save configuration: {response.status_code}")
            continue
        
        # Prepare network
        session_id = config['sessionId']
        network_data = {
            "sessionId": session_id,
            "networkId": "st_dominic_realistic",
            "config": config['config']
        }
        
        response = requests.post(f"{base_url}/simulation/prepare-network", json=network_data)
        if response.status_code == 200:
            print("✅ Network prepared successfully")
            
            # Check the created files
            session_dir = Path(f"backend/sessions/{session_id}")
            if session_dir.exists():
                routes_dir = session_dir / "routes"
                if routes_dir.exists():
                    route_files = list(routes_dir.glob("*.rou.xml"))
                    print(f"📁 Route files created: {[f.name for f in route_files]}")
                    
                    # Check file contents
                    for route_file in route_files:
                        with open(route_file, 'r') as f:
                            content = f.read()
                        
                        # Check if file has real content (not just empty template)
                        has_vehicles = '<vehicle' in content or '<flow' in content
                        has_vtype = '<vType' in content
                        
                        print(f"  {route_file.name}: {'✅ Has content' if has_vehicles or has_vtype else '❌ Empty/template'}")
                    
                    # Check SUMO config
                    sumo_configs = list(session_dir.glob("*.sumocfg"))
                    if sumo_configs:
                        with open(sumo_configs[0], 'r') as f:
                            sumo_content = f.read()
                        
                        print(f"📄 SUMO config references routes: {'route-files' in sumo_content}")
                        
                        # Extract route file references
                        import re
                        route_refs = re.findall(r'routes/[^,\s"]+\.rou\.xml', sumo_content)
                        print(f"   Referenced route files: {route_refs}")
                else:
                    print("❌ No routes directory created")
            else:
                print("❌ Session directory not created")
                
        else:
            print(f"❌ Failed to prepare network: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    test_vehicle_filtering()
