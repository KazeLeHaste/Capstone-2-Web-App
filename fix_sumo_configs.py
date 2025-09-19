#!/usr/bin/env python3
"""
Fix SUMO configuration files to include summary-output for analytics
This script adds missing summary-output elements to all SUMO config files
"""

import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

def fix_sumo_config(config_path: Path):
    """
    Add summary-output to a SUMO configuration file if missing
    
    Args:
        config_path: Path to the .sumocfg file
    """
    try:
        # Parse the XML
        tree = ET.parse(config_path)
        root = tree.getroot()
        
        # Find or create output section
        output_section = root.find('.//output')
        if output_section is None:
            output_section = ET.SubElement(root, 'output')
        
        # Determine the network name from config filename or parent directory
        network_name = config_path.stem
        if network_name == 'osm':
            # For OSM configs, use parent directory name
            network_name = config_path.parent.name
        
        changes_made = False
        
        # Check if summary-output already exists
        summary_output = output_section.find('summary-output')
        if summary_output is None:
            # Add summary-output element
            summary_output = ET.SubElement(output_section, 'summary-output')
            summary_output.set('value', f'{network_name}_summary.xml')
            changes_made = True
            print(f"  + Added summary-output")
        
        # Check if emission-output exists
        emission_output = output_section.find('emission-output')
        if emission_output is None:
            # Add emission-output element
            emission_output = ET.SubElement(output_section, 'emission-output')
            emission_output.set('value', f'{network_name}_emissions.xml')
            changes_made = True
            print(f"  + Added emission-output")
        
        # Check if edgedata-output exists
        edgedata_output = output_section.find('edgedata-output')
        if edgedata_output is None:
            # Add edgedata-output element
            edgedata_output = ET.SubElement(output_section, 'edgedata-output')
            edgedata_output.set('value', f'{network_name}_edgedata.xml')
            changes_made = True
            print(f"  + Added edgedata-output")
        
        if changes_made:
            # Save the updated config
            tree.write(config_path, encoding='utf-8', xml_declaration=True)
            print(f"✅ Updated: {config_path}")
            return True
        else:
            print(f"⚠️  No changes needed in: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {config_path}: {e}")
        return False

def main():
    """Fix all SUMO configuration files in the project"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Find all .sumocfg files
    config_paths = []
    
    # Search in backend/networks
    networks_dir = project_root / 'backend' / 'networks'
    if networks_dir.exists():
        config_paths.extend(networks_dir.rglob('*.sumocfg'))
    
    # Search in osm_scenarios
    osm_scenarios_dir = project_root / 'osm_scenarios'
    if osm_scenarios_dir.exists():
        config_paths.extend(osm_scenarios_dir.rglob('*.sumocfg'))
    
    if not config_paths:
        print("No SUMO configuration files found!")
        return
    
    print(f"Found {len(config_paths)} SUMO configuration files")
    print("=" * 60)
    
    fixed_count = 0
    for config_path in config_paths:
        if fix_sumo_config(config_path):
            fixed_count += 1
    
    print("=" * 60)
    print(f"Fixed {fixed_count} out of {len(config_paths)} configuration files")
    
    if fixed_count > 0:
        print("\n✅ Summary output has been enabled for analytics!")
        print("   Time series charts should now display data after running simulations.")
    else:
        print("\n⚠️  No configuration files needed updates.")

if __name__ == '__main__':
    main()