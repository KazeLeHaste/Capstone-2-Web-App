#!/usr/bin/env python3
"""
Debug what network ID is being used
"""

from backend.simulation_manager import SimulationManager

def debug_network_id():
    sm = SimulationManager()
    
    # Get network
    networks_result = sm.get_available_networks()
    network = networks_result['networks'][0]
    
    print(f"Network ID: '{network['id']}'")
    print(f"Network name: '{network['name']}'")
    print(f"Network path: '{network['path']}'")
    
    # Parse the network ID properly
    from pathlib import Path
    path = Path(network['path'])
    
    print(f"Path name: '{path.name}'")
    print(f"Path stem: '{path.stem}'")
    print(f"Path suffix: '{path.suffix}'")
    
    # Remove all extensions properly
    clean_id = path.name.replace('.net.xml.gz', '').replace('.net.xml', '')
    print(f"Clean ID: '{clean_id}'")

if __name__ == "__main__":
    debug_network_id()