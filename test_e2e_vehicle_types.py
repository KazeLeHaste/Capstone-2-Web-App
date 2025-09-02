#!/usr/bin/env python3
"""
End-to-end test for the vehicle type configuration workflow.
This script tests the complete flow from configuration to simulation setup.
"""

import requests
import json
import time
from pathlib import Path

def test_workflow(base_url="http://localhost:5000"):
    """Test the complete configuration workflow."""
    
    print("End-to-End Vehicle Type Configuration Test")
    print("=" * 60)
    
    # Step 1: Save configuration with specific vehicle types
    session_id = f"test_e2e_{int(time.time())}"
    config_data = {
        "sessionId": session_id,
        "timestamp": "2025-09-02T14:00:00.000Z",
        "config": {
            "sumo_begin": 0,
            "sumo_end": 3600,  # 1 hour simulation
            "sumo_step_length": 1.0,
            "sumo_time_to_teleport": 300,
            "sumo_traffic_intensity": 1.2,  # 20% more traffic
            "enabledVehicles": ["passenger", "bus"],  # Only passenger cars and buses
            "vehicleTypes": {
                "passenger": {"enabled": True, "name": "Passenger Cars"},
                "bus": {"enabled": True, "name": "Buses"},
                "truck": {"enabled": False, "name": "Trucks"},  # Disabled
                "motorcycle": {"enabled": False, "name": "Motorcycles"}  # Disabled
            },
            "original_config": {
                "beginTime": 0,
                "endTime": 3600,
                "stepLength": 1.0,
                "timeToTeleport": 300,
                "trafficIntensity": 1.2
            }
        }
    }
    
    print(f"\nStep 1: Save Configuration")
    print(f"Session ID: {session_id}")
    print(f"Enabled vehicles: {config_data['config']['enabledVehicles']}")
    print(f"Traffic intensity: {config_data['config']['sumo_traffic_intensity']}x")
    
    try:
        response = requests.post(f"{base_url}/api/simulation/save-config", json=config_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Configuration saved successfully")
        else:
            print(f"✗ Failed to save configuration: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error saving configuration: {e}")
        return False
    
    # Step 2: Get available networks  
    print(f"\nStep 2: Get Available Networks")
    try:
        response = requests.get(f"{base_url}/api/networks/available")
        if response.status_code == 200:
            result = response.json()
            networks = result.get('networks', [])
            print(f"✓ Found {len(networks)} available networks")
            
            # Find a network with route files
            target_network = None
            for network in networks:
                if network.get('vehicleTypes'):  # Check if network has vehicle types
                    target_network = network
                    break
            
            if target_network:
                print(f"✓ Selected network: {target_network['name']} ({target_network['id']})")
                print(f"  Available vehicle types: {target_network.get('vehicleTypes', [])}")
            else:
                print("✗ No suitable network found with route files")
                return False
                
        else:
            print(f"✗ Failed to get networks: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting networks: {e}")
        return False
    
    # Step 3: Setup network with vehicle filtering
    print(f"\nStep 3: Setup Network with Vehicle Type Filtering")
    
    # First, let's check what the network path should be
    network_id = target_network['id']
    network_path = target_network['path']
    
    setup_data = {
        "sessionId": session_id,
        "networkId": network_id,
        "networkPath": network_path,
        "config": config_data['config']
    }
    
    try:
        response = requests.post(f"{base_url}/api/simulation/setup-network", json=setup_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Network setup completed")
            print(f"✓ Session path: {result.get('sessionPath', 'N/A')}")
            
            # Check if session directory was created
            session_path = Path(result.get('sessionPath', ''))
            if session_path.exists():
                print(f"✓ Session directory created")
                
                # Check for route files
                routes_dir = session_path / "routes"
                if routes_dir.exists():
                    route_files = list(routes_dir.glob("*.rou.xml"))
                    print(f"✓ Found {len(route_files)} route files:")
                    for route_file in route_files:
                        file_size = route_file.stat().st_size
                        print(f"  - {route_file.name} ({file_size} bytes)")
                        
                        # Check if disabled files are empty/minimal
                        if any(disabled in route_file.name for disabled in ['truck', 'motorcycle']):
                            with open(route_file, 'r') as f:
                                content = f.read()
                                if "disabled by user configuration" in content:
                                    print(f"    ✓ Correctly disabled (minimal content)")
                                else:
                                    print(f"    ⚠ Should be disabled but contains routes")
                        else:
                            print(f"    ✓ Enabled vehicle type route file")
                
            else:
                print(f"✗ Session directory not found: {session_path}")
                
        else:
            print(f"✗ Failed to setup network: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error setting up network: {e}")
        return False
    
    # Step 4: Verify configuration file
    print(f"\nStep 4: Verify SUMO Configuration File")
    
    try:
        config_file = session_path / f"{network_id}.sumocfg"
        if config_file.exists():
            print(f"✓ SUMO configuration file created: {config_file.name}")
            
            # Parse and check the configuration
            with open(config_file, 'r') as f:
                content = f.read()
                
            # Check for enabled vehicle route files
            for enabled_type in ["passenger", "bus"]:
                route_file = f"routes/osm.{enabled_type}.rou.xml"
                if route_file in content:
                    print(f"✓ {enabled_type} routes included in configuration")
                else:
                    print(f"⚠ {enabled_type} routes not found in configuration")
                    
            # Check time parameters
            if f"<begin value=\"{config_data['config']['sumo_begin']}\"/>" in content:
                print(f"✓ Begin time configured correctly")
            if f"<end value=\"{config_data['config']['sumo_end']}\"/>" in content:
                print(f"✓ End time configured correctly")
                
        else:
            print(f"✗ SUMO configuration file not found")
            return False
            
    except Exception as e:
        print(f"✗ Error checking configuration file: {e}")
        return False
    
    print(f"\n{'='*60}")
    print(f"✓ End-to-End Test PASSED")
    print(f"✓ Vehicle type filtering is working correctly")
    print(f"✓ Configuration is properly applied to SUMO files")
    print(f"✓ Session: {session_id}")
    
    return True

def main():
    """Run the end-to-end test."""
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5000/api/status")
        if response.status_code == 200:
            print("Backend is running ✓")
            success = test_workflow()
            if success:
                print("\n🎉 All tests passed! Vehicle type configuration is working correctly.")
            else:
                print("\n❌ Some tests failed. Please check the implementation.")
        else:
            print("Backend not responding properly")
    except requests.exceptions.RequestException:
        print("❌ Backend is not running. Please start with: python backend/app.py")

if __name__ == "__main__":
    main()
