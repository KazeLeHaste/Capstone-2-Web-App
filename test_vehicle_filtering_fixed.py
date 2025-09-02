#!/usr/bin/env python3
"""
Test script to verify vehicle filtering works correctly after the fix.
This tests the complete workflow including the reordered file processing.
"""

import requests
import json
import time
import os
from pathlib import Path

# Test configuration
BASE_URL = 'http://localhost:5000/api'
SESSION_ID = f'test_fixed_filtering_{int(time.time())}'

def test_vehicle_filtering():
    print(f"Testing vehicle filtering fix with session: {SESSION_ID}")
    
    # Step 1: Save configuration with only passenger vehicles
    config_data = {
        'sessionId': SESSION_ID,
        'timestamp': '2025-09-02T16:30:00.000Z',
        'config': {
            'sumo_begin': 0,
            'sumo_end': 120,
            'sumo_step_length': 1,
            'sumo_time_to_teleport': 300,
            'sumo_traffic_intensity': 1,
            'enabledVehicles': ['passenger'],  # Only passenger cars
            'vehicleTypes': {
                'passenger': {'enabled': True, 'name': 'Passenger Cars'},
                'bus': {'enabled': False, 'name': 'Buses'},
                'truck': {'enabled': False, 'name': 'Trucks'},
                'motorcycle': {'enabled': False, 'name': 'Motorcycles'}
            }
        }
    }
    
    print("Step 1: Saving configuration...")
    response = requests.post(f"{BASE_URL}/simulation/save-config", json=config_data)
    if response.status_code != 200:
        print(f"❌ Config save failed: {response.text}")
        return False
    print("✅ Configuration saved successfully")
    
    # Step 2: Setup network
    print("Step 2: Setting up network...")
    setup_data = {
        'sessionId': SESSION_ID,
        'networkId': 'st_dominic_realistic.net',
        'networkPath': r'C:\Users\kgaqu\OneDrive\Documents\4th Year\Capstone 2\v10\backend\networks\st_dominic_realistic\st_dominic_realistic.net.xml',
        'config': config_data['config']
    }
    
    response = requests.post(f"{BASE_URL}/simulation/setup-network", json=setup_data)
    if response.status_code != 200:
        print(f"❌ Network setup failed: {response.text}")
        return False
    print("✅ Network setup successful")
    
    # Step 3: Verify session files
    session_path = Path(f"backend/sessions/{SESSION_ID}")
    print(f"Step 3: Checking session files in {session_path}")
    
    # Check network file
    network_files = list(session_path.glob("*.net.xml"))
    if not network_files:
        print("❌ No network files found")
        return False
    print(f"✅ Network file found: {network_files[0].name}")
    
    # Check route files - should only have passenger
    routes_dir = session_path / "routes"
    if not routes_dir.exists():
        print("❌ Routes directory not found")
        return False
    
    route_files = list(routes_dir.glob("*.rou.xml"))
    print(f"✅ Found route files: {[f.name for f in route_files]}")
    
    expected_routes = ['osm.passenger.rou.xml']
    found_routes = [f.name for f in route_files]
    
    if set(found_routes) != set(expected_routes):
        print(f"❌ Route files mismatch. Expected: {expected_routes}, Found: {found_routes}")
        return False
    print("✅ Correct route files created (passenger only)")
    
    # Check SUMO config
    sumo_config_files = list(session_path.glob("*.sumocfg"))
    if not sumo_config_files:
        print("❌ SUMO config file not found")
        return False
    
    sumo_config = sumo_config_files[0]
    print(f"✅ SUMO config found: {sumo_config.name}")
    
    # Parse SUMO config to verify contents
    with open(sumo_config, 'r') as f:
        config_content = f.read()
    
    print("Step 4: Verifying SUMO config contents...")
    
    # Check network file reference
    actual_network_name = network_files[0].name
    if f'value="{actual_network_name}"' not in config_content:
        print(f"❌ SUMO config doesn't reference correct network file: {actual_network_name}")
        print(f"Config content snippet: {config_content[:500]}")
        return False
    print(f"✅ SUMO config correctly references network file: {actual_network_name}")
    
    # Check route files reference
    if 'routes/osm.passenger.rou.xml' not in config_content:
        print("❌ SUMO config doesn't reference passenger route file")
        return False
    
    # Check that disabled vehicle routes are NOT referenced
    disabled_routes = ['osm.bus.rou.xml', 'osm.truck.rou.xml', 'osm.motorcycle.rou.xml']
    for disabled_route in disabled_routes:
        if disabled_route in config_content:
            print(f"❌ SUMO config incorrectly references disabled route: {disabled_route}")
            return False
    
    print("✅ SUMO config correctly references only enabled vehicle routes")
    
    print(f"\n🎉 All tests passed! Vehicle filtering is working correctly.")
    print(f"Session created: {SESSION_ID}")
    return True

if __name__ == '__main__':
    success = test_vehicle_filtering()
    if success:
        print("\n✅ Test completed successfully - vehicle filtering fix verified!")
    else:
        print("\n❌ Test failed - issues still exist")
