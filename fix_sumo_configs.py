#!/usr/bin/env python3
"""
Fix SUMO configuration files for imported OSM scenarios.
Corrects the additional-files reference to match actual file names.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

def fix_sumo_configs(networks_dir="backend/networks"):
    """
    Fix SUMO config files to reference correct additional file names
    """
    networks_path = Path(networks_dir)
    
    if not networks_path.exists():
        print(f"❌ Networks directory not found: {networks_dir}")
        return False
    
    print("🔧 Fixing SUMO configuration files...")
    
    fixed_count = 0
    
    for network_dir in networks_path.iterdir():
        if network_dir.is_dir():
            # Find SUMO config file
            sumocfg_files = list(network_dir.glob("*.sumocfg"))
            if not sumocfg_files:
                continue
                
            sumocfg_file = sumocfg_files[0]
            print(f"\n📁 Processing {network_dir.name}...")
            print(f"   Config: {sumocfg_file.name}")
            
            try:
                # Parse the SUMO config
                tree = ET.parse(sumocfg_file)
                root = tree.getroot()
                
                # Find the additional-files element
                additional_files = root.find('.//additional-files')
                if additional_files is not None:
                    current_value = additional_files.get('value', '')
                    print(f"   Current: {current_value}")
                    
                    # Fix the filename (remove extra dot)
                    if '.output.add.xml' in current_value:
                        fixed_value = current_value.replace('.output.add.xml', '.output_add.xml')
                        additional_files.set('value', fixed_value)
                        print(f"   Fixed to: {fixed_value}")
                        
                        # Write back the fixed config
                        tree.write(sumocfg_file, encoding='utf-8', xml_declaration=True)
                        print(f"   ✅ Fixed {sumocfg_file.name}")
                        fixed_count += 1
                    else:
                        print(f"   ✅ Already correct")
                else:
                    print(f"   ⚠️  No additional-files element found")
            
            except Exception as e:
                print(f"   ❌ Error processing {sumocfg_file}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} SUMO configuration files!")
    return fixed_count > 0

def verify_additional_files(networks_dir="backend/networks"):
    """
    Verify that additional files exist and match config references
    """
    networks_path = Path(networks_dir)
    
    print(f"\n🔍 Verifying additional files...")
    
    for network_dir in networks_path.iterdir():
        if network_dir.is_dir():
            sumocfg_files = list(network_dir.glob("*.sumocfg"))
            if not sumocfg_files:
                continue
                
            sumocfg_file = sumocfg_files[0]
            
            try:
                tree = ET.parse(sumocfg_file)
                root = tree.getroot()
                
                additional_files = root.find('.//additional-files')
                if additional_files is not None:
                    referenced_file = additional_files.get('value', '')
                    file_path = network_dir / referenced_file
                    
                    print(f"\n📁 {network_dir.name}")
                    print(f"   References: {referenced_file}")
                    
                    if file_path.exists():
                        print(f"   ✅ File exists ({file_path.stat().st_size:,} bytes)")
                    else:
                        print(f"   ❌ File missing: {file_path}")
                        
                        # Look for similar files
                        similar_files = list(network_dir.glob("*.output*.xml"))
                        if similar_files:
                            print(f"   📝 Available files: {[f.name for f in similar_files]}")
                    
            except Exception as e:
                print(f"   ❌ Error checking {network_dir.name}: {e}")

if __name__ == "__main__":
    print("🚗 SUMO Config Fixer for OSM Networks")
    print("Fixing additional-files references in SUMO configurations...\n")
    
    # Fix the config files
    success = fix_sumo_configs()
    
    # Verify the fixes
    verify_additional_files()
    
    if success:
        print("\n✅ All SUMO configuration files have been fixed!")
        print("Your OSM scenarios should now launch correctly in the web application.")
    else:
        print("\n⚠️  No fixes were needed or errors occurred.")
