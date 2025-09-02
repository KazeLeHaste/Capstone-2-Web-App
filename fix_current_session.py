#!/usr/bin/env python3
"""
Fix the current running session configuration
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

def fix_current_session():
    """Fix the SUMO configuration for the current running session"""
    
    sessions_dir = Path("backend/sessions")
    
    # Find the most recent session
    session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
    session_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_session = session_dirs[0]
    
    print(f"Fixing session: {latest_session.name}")
    
    # Fix SUMO configuration
    sumo_configs = list(latest_session.glob("*.sumocfg"))
    if not sumo_configs:
        print("❌ No SUMO config found")
        return
    
    config_file = sumo_configs[0]
    print(f"Fixing config file: {config_file.name}")
    
    try:
        # Load and fix the XML
        tree = ET.parse(config_file)
        root = tree.getroot()
        
        # Check which route files actually exist
        routes_dir = latest_session / "routes"
        existing_routes = []
        if routes_dir.exists():
            for route_file in routes_dir.glob("*.rou.xml"):
                existing_routes.append(f"routes/{route_file.name}")
        
        print(f"Existing route files: {existing_routes}")
        
        # Update route-files element to only reference existing files
        route_input = root.find('.//route-files')
        if route_input is not None:
            if existing_routes:
                route_input.set('value', ','.join(existing_routes))
                print(f"✅ Updated route-files to: {existing_routes}")
            else:
                print("❌ No existing route files found")
                return
        
        # Fix network file path if it's wrong
        net_input = root.find('.//net-file')
        if net_input is not None:
            current_net_path = net_input.get('value')
            print(f"Current network path: {current_net_path}")
            
            # Check if the referenced file exists
            net_file_path = latest_session / current_net_path
            if not net_file_path.exists():
                # Try to find the correct network file
                net_files = list(latest_session.glob("*.net.xml"))
                if net_files:
                    correct_net_file = net_files[0].name
                    net_input.set('value', correct_net_file)
                    print(f"✅ Fixed network path to: {correct_net_file}")
                else:
                    print("❌ No network file found")
        
        # Ensure time section has step-length
        time_section = root.find('.//time')
        if time_section is not None:
            step_elem = time_section.find('step-length')
            if step_elem is None:
                step_elem = ET.SubElement(time_section, 'step-length')
                step_elem.set('value', '1.0')
                print("✅ Added missing step-length")
        
        # Save the fixed config
        tree.write(config_file, encoding='utf-8', xml_declaration=True)
        print("✅ SUMO config fixed!")
        
        # Verify the fix worked
        print("\n--- Fixed SUMO Config ---")
        with open(config_file, 'r') as f:
            content = f.read()
        
        print("Route files section:")
        for line in content.split('\n'):
            if 'route-files' in line:
                print(f"  {line.strip()}")
        
        print("Network file section:")
        for line in content.split('\n'):
            if 'net-file' in line:
                print(f"  {line.strip()}")
                
        print("Time section:")
        for line in content.split('\n'):
            if '<time>' in line or 'begin' in line or 'end' in line or 'step-length' in line:
                print(f"  {line.strip()}")
        
    except Exception as e:
        print(f"❌ Error fixing config: {e}")

if __name__ == "__main__":
    fix_current_session()
