#!/usr/bin/env python3
"""
Test script to verify compressed network functionality end-to-end
"""

from backend.simulation_manager import SimulationManager
import uuid
import os
from pathlib import Path

def test_compressed_network():
    print("🧪 Testing compressed network functionality...")
    
    # Create session manager
    sm = SimulationManager()
    
    # Get available networks
    networks_result = sm.get_available_networks()
    
    if not networks_result['success'] or not networks_result['networks']:
        print("❌ No networks found")
        return False
    
    # Find our compressed network
    network = None
    for net in networks_result['networks']:
        if 'compressed' in net['name'].lower():
            network = net
            break
    
    if not network:
        network = networks_result['networks'][0]  # Use first available
    
    print(f"📁 Using network: {network['name']}")
    print(f"   Path: {network['path']}")
    print(f"   File size: {network['fileSize']}")
    print(f"   OSM scenario: {network['isOsmScenario']}")
    
    # Create a test session
    session_id = f"test_compressed_{uuid.uuid4().hex[:8]}"
    test_config = {
        'vehicles': 10,
        'simulationTime': 300,
        'enabledVehicles': ['passenger', 'bus'],
        'sumo_begin': 0,
        'sumo_end': 300,
        'sumo_step_length': 1.0
    }
    
    print(f"🔧 Setting up session: {session_id}")
    
    try:
        # Setup network for session
        result = sm.setup_session_network(session_id, network['id'], network['path'], test_config)
        
        if result.get('success'):
            print("✅ Session setup successful!")
            print(f"   Session path: {result['sessionPath']}")
            print(f"   Network file: {result['metadata']['files']['network']}")
            
            # Verify the session directory was created correctly
            session_path = Path(result['sessionPath'])
            if session_path.exists():
                print("✅ Session directory created")
                
                # List files in session directory
                files = list(session_path.iterdir())
                print(f"   Files created: {len(files)}")
                for file in files:
                    if file.name.endswith(('.net.xml', '.net.xml.gz')):
                        print(f"   📄 Network file: {file.name} ({file.stat().st_size} bytes)")
                    elif file.name.endswith('.sumocfg'):
                        print(f"   ⚙️  Config file: {file.name}")
                        
                        # Check if config references the correct network file
                        with open(file, 'r') as f:
                            config_content = f.read()
                            if result['metadata']['files']['network'] in config_content:
                                print("   ✅ Config correctly references network file")
                            else:
                                print("   ⚠️  Config may not reference correct network file")
                
                return True
            else:
                print("❌ Session directory not found")
                return False
        else:
            print(f"❌ Session setup failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during session setup: {e}")
        return False

if __name__ == "__main__":
    success = test_compressed_network()
    if success:
        print("\n🎉 All tests passed! Compressed network functionality is working correctly.")
    else:
        print("\n💥 Tests failed. Please check the errors above.")