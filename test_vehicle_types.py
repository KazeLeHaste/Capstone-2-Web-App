#!/usr/bin/env python3
"""
Test script to verify vehicle type configuration is working properly.
This script will send a test configuration to the backend and verify it processes
the enabledVehicles parameter correctly.
"""

import requests
import json
import time

# Test configuration with different vehicle type combinations
test_configs = [
    {
        "name": "All vehicle types",
        "config": {
            "sessionId": f"test_{int(time.time())}_all",
            "timestamp": "2025-09-02T13:45:00.000Z",
            "config": {
                "sumo_begin": 0,
                "sumo_end": 1800,
                "sumo_step_length": 1.0,
                "sumo_time_to_teleport": 300,
                "sumo_traffic_intensity": 1.0,
                "enabledVehicles": ["passenger", "bus", "truck", "motorcycle"],
                "vehicleTypes": {
                    "passenger": {"enabled": True, "name": "Passenger Cars"},
                    "bus": {"enabled": True, "name": "Buses"},
                    "truck": {"enabled": True, "name": "Trucks"},
                    "motorcycle": {"enabled": True, "name": "Motorcycles"}
                },
                "original_config": {
                    "beginTime": 0,
                    "endTime": 1800,
                    "stepLength": 1.0,
                    "timeToTeleport": 300,
                    "trafficIntensity": 1.0
                }
            }
        }
    },
    {
        "name": "Passenger only",
        "config": {
            "sessionId": f"test_{int(time.time())}_passenger",
            "timestamp": "2025-09-02T13:45:00.000Z",
            "config": {
                "sumo_begin": 0,
                "sumo_end": 1800,
                "sumo_step_length": 1.0,
                "sumo_time_to_teleport": 300,
                "sumo_traffic_intensity": 1.5,
                "enabledVehicles": ["passenger"],
                "vehicleTypes": {
                    "passenger": {"enabled": True, "name": "Passenger Cars"},
                    "bus": {"enabled": False, "name": "Buses"},
                    "truck": {"enabled": False, "name": "Trucks"},
                    "motorcycle": {"enabled": False, "name": "Motorcycles"}
                },
                "original_config": {
                    "beginTime": 0,
                    "endTime": 1800,
                    "stepLength": 1.0,
                    "timeToTeleport": 300,
                    "trafficIntensity": 1.5
                }
            }
        }
    },
    {
        "name": "No vehicles (error case)",
        "config": {
            "sessionId": f"test_{int(time.time())}_none",
            "timestamp": "2025-09-02T13:45:00.000Z", 
            "config": {
                "sumo_begin": 0,
                "sumo_end": 1800,
                "sumo_step_length": 1.0,
                "sumo_time_to_teleport": 300,
                "sumo_traffic_intensity": 1.0,
                "enabledVehicles": [],
                "vehicleTypes": {
                    "passenger": {"enabled": False, "name": "Passenger Cars"},
                    "bus": {"enabled": False, "name": "Buses"},
                    "truck": {"enabled": False, "name": "Trucks"},
                    "motorcycle": {"enabled": False, "name": "Motorcycles"}
                },
                "original_config": {
                    "beginTime": 0,
                    "endTime": 1800,
                    "stepLength": 1.0,
                    "timeToTeleport": 300,
                    "trafficIntensity": 1.0
                }
            }
        }
    }
]

def test_configuration(base_url="http://localhost:5000"):
    """Test the configuration endpoint with various vehicle type combinations."""
    
    print("Testing Vehicle Type Configuration")
    print("=" * 50)
    
    for test_case in test_configs:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Send configuration to backend
            response = requests.post(
                f"{base_url}/api/simulation/save-config",
                json=test_case['config'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Success: {result.get('success', False)}")
                print(f"✓ Message: {result.get('message', 'N/A')}")
                
                # Show enabled vehicles
                enabled = test_case['config']['config']['enabledVehicles']
                print(f"✓ Enabled vehicles: {enabled if enabled else 'None'}")
                
            else:
                print(f"✗ Status: {response.status_code}")
                print(f"✗ Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed: {e}")
        
        time.sleep(1)  # Brief pause between tests

def test_network_endpoint(base_url="http://localhost:5000"):
    """Test the networks endpoint to see available networks."""
    
    print("\n\nTesting Available Networks")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/networks/available")
        
        if response.status_code == 200:
            networks = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Found {len(networks)} networks:")
            
            for network in networks:
                if isinstance(network, dict):
                    print(f"  - {network.get('id', 'N/A')}: {network.get('name', 'N/A')}")
                    if 'vehicleTypes' in network:
                        print(f"    Vehicle types: {network['vehicleTypes']}")
                else:
                    print(f"  - {network}")
                    
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"✗ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    # Test if backend is running
    try:
        response = requests.get("http://localhost:5000/api/status")
        if response.status_code == 200:
            print("Backend is running ✓")
            test_configuration()
            test_network_endpoint()
        else:
            print("Backend not responding properly")
    except requests.exceptions.RequestException:
        print("Backend is not running. Please start with: python backend/app.py")
