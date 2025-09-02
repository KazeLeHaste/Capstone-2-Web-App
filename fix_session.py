#!/usr/bin/env python3
"""
Quick fix script to test SUMO with all vehicles enabled
"""

import json
import shutil
from pathlib import Path

def fix_latest_session():
    """Enable all vehicle types in the latest session and copy original route files"""
    sessions_dir = Path("backend/sessions")
    
    # Find the most recent session
    session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
    session_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_session = session_dirs[0]
    
    print(f"Fixing session: {latest_session.name}")
    
    # Update configuration to enable all vehicles
    config_file = latest_session / "config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Enable all vehicle types
        config['config']['enabledVehicles'] = ['passenger', 'bus', 'truck', 'motorcycle']
        for vtype in config['config']['vehicleTypes']:
            config['config']['vehicleTypes'][vtype]['enabled'] = True
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("Updated config to enable all vehicle types")
    
    # Copy original route files from the network source
    network_source = Path("backend/networks/st_dominic_realistic")
    routes_source = network_source / "routes"
    routes_dest = latest_session / "routes"
    
    if routes_source.exists():
        for route_file in routes_source.glob("*.rou.xml"):
            dest_file = routes_dest / route_file.name
            shutil.copy2(route_file, dest_file)
            print(f"Restored {route_file.name}")
    
    print("Session fixed! Try launching the simulation again.")

if __name__ == "__main__":
    fix_latest_session()
