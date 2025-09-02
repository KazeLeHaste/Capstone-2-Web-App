#!/usr/bin/env python3
"""
Test the complete workflow with a fresh session
"""

import requests
import json
import time

def test_complete_workflow():
    """Test saving config, preparing network, and launching simulation"""
    
    base_url = "http://localhost:5000/api"
    session_id = f"test_complete_{int(time.time())}"
    
    print(f"Testing complete workflow with session: {session_id}")
    
    # Step 1: Save configuration
    config_data = {
        "sessionId": session_id,
        "timestamp": "2025-09-02T15:30:00.000Z",
        "config": {
            "sumo_begin": 0,
            "sumo_end": 300,  # 5 minutes
            "sumo_step_length": 1,
            "sumo_time_to_teleport": 300,
            "sumo_traffic_intensity": 1,
            "enabledVehicles": ["passenger", "bus"],  # Enable two types
            "vehicleTypes": {
                "passenger": {"enabled": True, "name": "Passenger Cars"},
                "bus": {"enabled": True, "name": "Buses"},
                "truck": {"enabled": False, "name": "Trucks"},
                "motorcycle": {"enabled": False, "name": "Motorcycles"}
            }
        }
    }
    
    print("Step 1: Saving configuration...")
    response = requests.post(f"{base_url}/simulation/save-config", json=config_data)
    if response.status_code != 200:
        print(f"❌ Failed to save config: {response.status_code} - {response.text}")
        return False
    print("✅ Configuration saved")
    
    # Step 2: Prepare network
    print("Step 2: Preparing network...")
    network_data = {
        "sessionId": session_id,
        "networkId": "st_dominic_realistic",
        "config": config_data['config']
    }
    
    response = requests.post(f"{base_url}/simulation/prepare-network", json=network_data)
    if response.status_code != 200:
        print(f"❌ Failed to prepare network: {response.status_code} - {response.text}")
        return False
    print("✅ Network prepared")
    
    # Step 3: Launch simulation  
    print("Step 3: Launching simulation...")
    launch_data = {
        "sessionId": session_id,
        "enableGui": True,
        "config": config_data['config']
    }
    
    response = requests.post(f"{base_url}/simulation/launch", json=launch_data)
    if response.status_code != 200:
        print(f"❌ Failed to launch simulation: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Simulation launch failed: {result.get('message')}")
        return False
    
    print("✅ Simulation launched successfully!")
    print(f"Process ID: {result.get('processId')}")
    print(f"Message: {result.get('message')}")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🎉 Complete workflow test PASSED!")
    else:
        print("\n❌ Complete workflow test FAILED!")
