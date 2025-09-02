#!/usr/bin/env python3
"""
Traffic Light Demo Script

This script demonstrates the traffic light functionality by creating
a sample simulation session and showing the generated files.

Usage:
    python demo_traffic_lights.py

Author: Traffic Simulator Team
Date: September 2025
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from simulation_manager import SimulationManager

def demo_traffic_lights():
    """Demonstrate traffic light configuration with a real network"""
    print("🚦 Traffic Light Configuration Demo\n")
    
    # Initialize simulation manager
    sim_manager = SimulationManager()
    
    # Get available networks
    networks_result = sim_manager.get_available_networks()
    
    if not networks_result['success'] or not networks_result['networks']:
        print("❌ No networks available for demonstration")
        return
    
    # Use the first available network
    network = networks_result['networks'][0]
    print(f"🌐 Using network: {network['name']} ({network['id']})")
    print(f"   - Junctions: {network['junctions']}")
    print(f"   - Edges: {network['edges']}")
    print(f"   - OSM Scenario: {network.get('isOsmScenario', False)}")
    print()
    
    # Demo both traffic control methods
    configs = [
        {
            'name': 'Fixed Timer Configuration',
            'config': {
                'sessionId': 'demo_fixed_timer',
                'timestamp': '2025-09-03T12:00:00Z',
                'config': {
                    'sumo_begin': 0,
                    'sumo_end': 1800,
                    'sumo_step_length': 1.0,
                    'sumo_time_to_teleport': 300,
                    'sumo_traffic_intensity': 1.0,
                    'enabledVehicles': ['passenger', 'bus'],
                    'trafficControl': {
                        'method': 'fixed',
                        'globalMode': True,
                        'fixedTimer': {
                            'greenPhase': 35,
                            'yellowPhase': 4,
                            'redPhase': 35,
                            'allRedPhase': 2
                        }
                    }
                }
            }
        },
        {
            'name': 'Adaptive Configuration',
            'config': {
                'sessionId': 'demo_adaptive',
                'timestamp': '2025-09-03T12:00:00Z',
                'config': {
                    'sumo_begin': 0,
                    'sumo_end': 1800,
                    'sumo_step_length': 1.0,
                    'sumo_time_to_teleport': 300,
                    'sumo_traffic_intensity': 1.5,  # Higher traffic for adaptive demo
                    'enabledVehicles': ['passenger', 'bus', 'truck'],
                    'trafficControl': {
                        'method': 'adaptive',
                        'globalMode': True,
                        'adaptive': {
                            'minGreenTime': 8,
                            'maxGreenTime': 45,
                            'detectorSensitivity': 1.2,
                            'jamThreshold': 25
                        }
                    }
                }
            }
        }
    ]
    
    for demo_config in configs:
        print(f"📋 {demo_config['name']}")
        print("-" * 50)
        
        config = demo_config['config']
        session_id = config['sessionId']
        
        # Save configuration
        save_result = sim_manager.save_session_config(session_id, config)
        if not save_result['success']:
            print(f"❌ Failed to save configuration: {save_result.get('message')}")
            continue
        
        # Setup network
        setup_result = sim_manager.setup_session_network(
            session_id,
            network['id'],
            network['path'],
            config['config']
        )
        
        if not setup_result['success']:
            print(f"❌ Failed to setup network: {setup_result.get('message')}")
            continue
        
        print(f"✅ Session created successfully: {session_id}")
        
        # Check generated files
        session_dir = sim_manager.sessions_dir / session_id
        files_to_check = [
            f"{network['id']}.net.xml",
            f"{network['id']}.add.xml",
            f"{network['id']}.sumocfg",
            "session_metadata.json"
        ]
        
        print("\n📁 Generated Files:")
        for file_name in files_to_check:
            file_path = session_dir / file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"   ✅ {file_name} ({file_size} bytes)")
            else:
                print(f"   ❌ {file_name} (not found)")
        
        # Show traffic light configuration in additional file
        additional_file = session_dir / f"{network['id']}.add.xml"
        if additional_file.exists():
            try:
                with open(additional_file, 'r') as f:
                    content = f.read()
                
                print("\n🚦 Traffic Light Configuration Preview:")
                if 'tlLogic' in content:
                    # Extract just the tlLogic section for display
                    lines = content.split('\n')
                    tl_lines = []
                    in_tl_logic = False
                    for line in lines:
                        if '<tlLogic' in line:
                            in_tl_logic = True
                        if in_tl_logic:
                            tl_lines.append(line)
                        if '</tlLogic>' in line:
                            in_tl_logic = False
                            break
                    
                    if tl_lines:
                        preview = '\n'.join(tl_lines[:10])  # Show first 10 lines
                        print(f"   {preview}")
                        if len(tl_lines) > 10:
                            print("   ... (truncated)")
                    
                    # Show detector info for adaptive
                    if 'laneAreaDetector' in content:
                        detector_count = content.count('laneAreaDetector')
                        print(f"   📡 {detector_count} lane area detectors configured")
                    
                else:
                    print("   ⚠️  No traffic light logic found in additional file")
                    
            except Exception as e:
                print(f"   ❌ Error reading additional file: {e}")
        
        print(f"\n📍 Session Location: {session_dir}")
        print("=" * 80)
        print()

def main():
    """Run the traffic light demonstration"""
    try:
        demo_traffic_lights()
        print("🎉 Traffic Light Demo completed successfully!")
        print("\nTo test these configurations:")
        print("1. Open the web application at http://localhost:3000")
        print("2. Go to Configuration → Select traffic control method")
        print("3. Go to Network Selection → Choose a network")
        print("4. Launch Simulation → Observe traffic light behavior in SUMO GUI")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
