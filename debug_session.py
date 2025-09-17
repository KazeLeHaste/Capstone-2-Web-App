#!/usr/bin/env python3
"""
Debug script to check the actual return structure
"""

from backend.simulation_manager import SimulationManager
import uuid
import json

def debug_session_setup():
    sm = SimulationManager()
    
    # Get network
    networks_result = sm.get_available_networks()
    network = networks_result['networks'][0]
    
    # Create session
    session_id = f"debug_{uuid.uuid4().hex[:8]}"
    test_config = {
        'vehicles': 10,
        'simulationTime': 300,
        'enabledVehicles': ['passenger'],
        'sumo_begin': 0,
        'sumo_end': 300
    }
    
    result = sm.setup_session_network(session_id, network['id'], network['path'], test_config)
    
    print("Session setup result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    debug_session_setup()