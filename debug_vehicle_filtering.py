#!/usr/bin/env python3
"""
Debug script to check vehicle filtering issues
"""

import json
import os
from pathlib import Path

def check_session_config():
    """Check the latest session configuration"""
    sessions_dir = Path("backend/sessions")
    
    if not sessions_dir.exists():
        print("Sessions directory doesn't exist")
        return
    
    # Find the most recent session
    session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
    if not session_dirs:
        print("No session directories found")
        return
    
    # Sort by modification time
    session_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_session = session_dirs[0]
    
    print(f"Latest session: {latest_session.name}")
    
    # Check session configuration
    config_file = latest_session / "session_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Session config: {json.dumps(config, indent=2)}")
        
        # Check enabled vehicles
        enabled_vehicles = config.get('config', {}).get('enabledVehicles', [])
        print(f"Enabled vehicles: {enabled_vehicles}")
    else:
        print("No session config file found")
    
    # Check route files
    routes_dir = latest_session / "routes"
    if routes_dir.exists():
        route_files = list(routes_dir.glob("*.rou.xml"))
        print(f"Route files found: {[f.name for f in route_files]}")
        
        # Check content of route files
        for route_file in route_files:
            print(f"\n--- Content of {route_file.name} ---")
            with open(route_file, 'r') as f:
                content = f.read()
            print(content[:500] + ("..." if len(content) > 500 else ""))
    else:
        print("No routes directory found")
    
    # Check SUMO config file
    sumo_configs = list(latest_session.glob("*.sumocfg"))
    if sumo_configs:
        config_file = sumo_configs[0]
        print(f"\n--- SUMO Config: {config_file.name} ---")
        with open(config_file, 'r') as f:
            content = f.read()
        print(content)
    else:
        print("No SUMO config file found")

if __name__ == "__main__":
    check_session_config()
