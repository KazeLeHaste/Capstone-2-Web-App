"""
OSM Scenario Importer

Processes OSM Web Wizard generated scenarios and imports them into the traffic simulator
web application. Preserves realistic traffic patterns while allowing configuration overlay.

Features:
- Import complete OSM scenarios with all vehicle types
- Preserve realistic timing and route patterns
- Create network packages compatible with web app
- Support vehicle type filtering and configuration

Author: Traffic Simulator Team
Date: August 2025
"""

import os
import sys
import json
import shutil
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

class OSMScenarioImporter:
    """
    Handles importing OSM Web Wizard scenarios into the web application
    """
    
    def __init__(self, osm_scenarios_dir: str = "osm_scenarios", target_networks_dir: str = "../backend/networks"):
        """
        Initialize the OSM importer
        
        Args:
            osm_scenarios_dir: Directory containing OSM Web Wizard outputs
            target_networks_dir: Target networks directory for web app (backend/networks)
        """
        self.osm_scenarios_dir = Path(osm_scenarios_dir)
        self.target_networks_dir = Path(target_networks_dir)
        
        # Ensure directories exist
        self.osm_scenarios_dir.mkdir(exist_ok=True)
        self.target_networks_dir.mkdir(exist_ok=True)
        
        # OSM file patterns to look for
        self.osm_files = {
            'network': ['osm.net.xml', 'osm_bbox.net.xml', 'osm.net.xml.gz'],
            'config': ['osm.sumocfg', 'osm'],
            'netccfg': ['osm.netccfg'],
            'routes': {
                'passenger': ['osm.passenger.rou.xml', 'osm.passenger.rou'],
                'bus': ['osm.bus.rou.xml', 'osm.bus.rou'], 
                'truck': ['osm.truck.rou.xml', 'osm.truck.rou'],
                'motorcycle': ['osm.motorcycle.rou.xml', 'osm.motorcycle.rou']
            },
            'trips': {
                'passenger': ['osm.passenger.trips.xml', 'osm.passenger.trips'],
                'bus': ['osm.bus.trips.xml', 'osm.bus.trips'],
                'truck': ['osm.truck.trips.xml', 'osm.truck.trips'], 
                'motorcycle': ['osm.motorcycle.trips.xml', 'osm.motorcycle.trips']
            },
            'additional': ['osm.view.xml', 'osm.view', 'edgeData.xml', 'edgeData', 'stats.xml', 'stats', 'tripinfos.xml', 'tripinfos', 'output.add.xml', 'output.add']
        }
    
    def scan_osm_scenarios(self) -> List[Dict[str, Any]]:
        """
        Scan for available OSM scenarios in the osm_scenarios directory
        
        Returns:
            List of discovered OSM scenarios with metadata
        """
        scenarios = []
        
        for item in self.osm_scenarios_dir.iterdir():
            if item.is_dir():
                scenario_info = self._analyze_osm_scenario(item)
                if scenario_info:
                    scenarios.append(scenario_info)
        
        return scenarios
    
    def _analyze_osm_scenario(self, scenario_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze an OSM scenario directory to extract metadata
        
        Args:
            scenario_path: Path to OSM scenario directory
            
        Returns:
            Scenario metadata or None if not valid OSM scenario
        """
        try:
            # Check for required OSM files
            network_file = None
            config_file = None
            
            # Find network file
            for net_pattern in self.osm_files['network']:
                net_path = scenario_path / net_pattern
                if net_path.exists():
                    network_file = net_path
                    break
            
            # Find config file
            for cfg_pattern in self.osm_files['config']:
                cfg_path = scenario_path / cfg_pattern
                if cfg_path.exists():
                    config_file = cfg_path
                    break
            
            if not network_file or not config_file:
                return None
            
            # Parse network file for metadata
            network_info = self._parse_network_metadata(network_file)
            
            # Scan for available vehicle types
            vehicle_types = self._scan_vehicle_types(scenario_path)
            
            # Get scenario statistics
            stats = self._get_scenario_stats(scenario_path)
            
            return {
                'name': scenario_path.name,
                'path': str(scenario_path),
                'network_file': str(network_file),
                'config_file': str(config_file),
                'vehicle_types': vehicle_types,
                'network_info': network_info,
                'stats': stats,
                'is_osm_scenario': True,
                'import_date': None
            }
            
        except Exception as e:
            print(f"Error analyzing scenario {scenario_path.name}: {e}")
            return None
    
    def _parse_network_metadata(self, network_file: Path) -> Dict[str, Any]:
        """
        Parse network file to extract basic metadata
        
        Args:
            network_file: Path to .net.xml or .net.xml.gz file
            
        Returns:
            Network metadata dictionary
        """
        try:
            # Handle compressed files
            if network_file.suffix == '.gz':
                with gzip.open(network_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
                root = ET.fromstring(content)
            else:
                tree = ET.parse(network_file)
                root = tree.getroot()
            
            # Count network elements
            edges = len([e for e in root.findall('.//edge') if not e.get('function')])
            junctions = len(root.findall('.//junction[@type!="internal"]'))
            lanes = len(root.findall('.//lane'))
            
            # Get bounding box
            location = root.find('.//location')
            boundary = location.get('convBoundary', '0,0,0,0') if location is not None else '0,0,0,0'
            
            return {
                'edges': edges,
                'junctions': junctions,
                'lanes': lanes,
                'boundary': boundary,
                'file_size': network_file.stat().st_size
            }
            
        except Exception as e:
            print(f"Error parsing network metadata: {e}")
            return {'edges': 0, 'junctions': 0, 'lanes': 0, 'boundary': '0,0,0,0'}
    
    def _scan_vehicle_types(self, scenario_path: Path) -> List[str]:
        """
        Scan scenario for available vehicle types
        
        Args:
            scenario_path: Path to OSM scenario directory
            
        Returns:
            List of available vehicle types
        """
        vehicle_types = []
        
        # Check route files
        for vehicle_type, file_patterns in self.osm_files['routes'].items():
            for pattern in file_patterns:
                if (scenario_path / pattern).exists():
                    vehicle_types.append(vehicle_type)
                    break
        
        # If no route files, check trip files
        if not vehicle_types:
            for vehicle_type, file_patterns in self.osm_files['trips'].items():
                for pattern in file_patterns:
                    if (scenario_path / pattern).exists():
                        vehicle_types.append(vehicle_type)
                        break
        
        return vehicle_types
    
    def _get_scenario_stats(self, scenario_path: Path) -> Dict[str, Any]:
        """
        Get basic statistics about the scenario
        
        Args:
            scenario_path: Path to OSM scenario directory
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_files': len(list(scenario_path.iterdir())),
            'route_files': 0,
            'trip_files': 0,
            'total_size': 0
        }
        
        # Count file types and sizes
        for file in scenario_path.iterdir():
            if file.is_file():
                stats['total_size'] += file.stat().st_size
                if file.suffix == '.rou':
                    stats['route_files'] += 1
                elif file.name.endswith('.trips'):
                    stats['trip_files'] += 1
        
        return stats
    
    def import_scenario(self, scenario_name: str, target_name: str = None) -> Dict[str, Any]:
        """
        Import an OSM scenario into the web application networks directory
        
        Args:
            scenario_name: Name of the OSM scenario directory
            target_name: Optional custom name for imported network
            
        Returns:
            Import result dictionary
        """
        scenario_path = self.osm_scenarios_dir / scenario_name
        if not scenario_path.exists():
            return {
                'success': False,
                'error': f'Scenario "{scenario_name}" not found'
            }
        
        # Analyze scenario
        scenario_info = self._analyze_osm_scenario(scenario_path)
        if not scenario_info:
            return {
                'success': False,
                'error': f'Invalid OSM scenario: {scenario_name}'
            }
        
        # Determine target name
        if not target_name:
            target_name = f"osm_{scenario_name}"
        
        target_path = self.target_networks_dir / target_name
        
        try:
            # Create target directory
            target_path.mkdir(exist_ok=True)
            
            # Copy and process OSM files
            self._copy_osm_files(scenario_path, target_path, scenario_info)
            
            # Create metadata file
            self._create_network_metadata(target_path, scenario_info, target_name)
            
            return {
                'success': True,
                'message': f'Successfully imported OSM scenario "{scenario_name}" as "{target_name}"',
                'target_path': str(target_path),
                'vehicle_types': scenario_info['vehicle_types'],
                'network_info': scenario_info['network_info']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to import scenario: {str(e)}'
            }
    
    def _copy_osm_files(self, source_path: Path, target_path: Path, scenario_info: Dict[str, Any]):
        """
        Copy and rename OSM files to target directory
        
        Args:
            source_path: Source OSM scenario directory
            target_path: Target network directory
            scenario_info: Scenario metadata
        """
        network_name = target_path.name
        
        # Copy main network file (decompress if needed)
        source_network = Path(scenario_info['network_file'])
        target_network = target_path / f"{network_name}.net.xml"
        
        if source_network.suffix == '.gz':
            # Decompress .gz file
            with gzip.open(source_network, 'rt', encoding='utf-8') as f_in:
                with open(target_network, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
        else:
            shutil.copy2(source_network, target_network)
        
        # Copy config file
        source_config = Path(scenario_info['config_file'])
        target_config = target_path / f"{network_name}.sumocfg"
        self._process_config_file(source_config, target_config, network_name)
        
        # Copy additional files if they exist
        for add_pattern in self.osm_files['additional']:
            source_file = source_path / add_pattern
            if source_file.exists():
                target_file = target_path / f"{network_name}.{add_pattern.replace('.xml', '').replace('.', '_')}.xml"
                if source_file.suffix == '.gz':
                    # Decompress if needed
                    try:
                        with gzip.open(source_file, 'rt', encoding='utf-8') as f_in:
                            with open(target_file, 'w', encoding='utf-8') as f_out:
                                f_out.write(f_in.read())
                    except:
                        # If decompression fails, just copy
                        shutil.copy2(source_file, target_file)
                else:
                    shutil.copy2(source_file, target_file)
        
        # Create routes directory and copy route/trip files
        routes_dir = target_path / 'routes'
        routes_dir.mkdir(exist_ok=True)
        
        # Copy route files by vehicle type (prefer .rou, fallback to .trips)
        for vehicle_type in scenario_info['vehicle_types']:
            # First try route files
            copied = False
            if vehicle_type in self.osm_files['routes']:
                for pattern in self.osm_files['routes'][vehicle_type]:
                    source_file = source_path / pattern
                    if source_file.exists():
                        target_file = routes_dir / f"osm.{vehicle_type}.rou.xml"
                        shutil.copy2(source_file, target_file)
                        copied = True
                        break
            
            # If no route file, try trip files
            if not copied and vehicle_type in self.osm_files['trips']:
                for pattern in self.osm_files['trips'][vehicle_type]:
                    source_file = source_path / pattern
                    if source_file.exists():
                        target_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
                        shutil.copy2(source_file, target_file)
                        break
    
    def _process_config_file(self, source_config: Path, target_config: Path, network_name: str):
        """
        Process and update SUMO configuration file with new paths
        
        Args:
            source_config: Source configuration file
            target_config: Target configuration file
            network_name: Network name for path updates
        """
        try:
            tree = ET.parse(source_config)
            root = tree.getroot()
            
            # Update network file path (remove .gz if present)
            net_input = root.find('.//net-file')
            if net_input is not None:
                net_input.set('value', f"{network_name}.net.xml")
            
            # Update route file paths to point to routes directory
            route_input = root.find('.//route-files')
            if route_input is not None:
                route_files = []
                # Check for both .rou and .trips files
                for vehicle_type in ['passenger', 'bus', 'truck', 'motorcycle']:
                    rou_file = f"routes/osm.{vehicle_type}.rou.xml"
                    trips_file = f"routes/osm.{vehicle_type}.trips.xml"
                    
                    if (target_config.parent / rou_file).exists():
                        route_files.append(rou_file)
                    elif (target_config.parent / trips_file).exists():
                        route_files.append(trips_file)
                
                if route_files:
                    route_input.set('value', ','.join(route_files))
            
            # Save updated config
            tree.write(target_config, encoding='utf-8', xml_declaration=True)
            
            # Apply additional fixes for file paths
            self._fix_sumo_config_paths(target_config, network_name)
            
        except Exception as e:
            print(f"Warning: Could not process config file: {e}")
            # Fallback: just copy the file
            shutil.copy2(source_config, target_config)
            # Try to fix paths even with fallback
            try:
                self._fix_sumo_config_paths(target_config, network_name)
            except:
                pass
    
    def _create_network_metadata(self, target_path: Path, scenario_info: Dict[str, Any], network_name: str):
        """
        Create metadata file for the imported network
        
        Args:
            target_path: Target network directory
            scenario_info: Scenario information
            network_name: Network name
        """
        metadata = {
            'name': network_name,
            'type': 'osm_imported',
            'is_osm_scenario': True,
            'import_date': datetime.now().isoformat(),
            'original_scenario': scenario_info['name'],
            'vehicle_types': scenario_info['vehicle_types'],
            'network_info': scenario_info['network_info'],
            'stats': scenario_info['stats'],
            'description': f"Imported OSM scenario: {scenario_info['name']}",
            'supports_realistic_traffic': True,
            'configuration_overlay_supported': True
        }
        
        metadata_file = target_path / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _fix_sumo_config_paths(self, config_file: Path, scenario_name: str) -> bool:
        """
        Fix file paths in SUMO configuration file to match actual file names
        
        Args:
            config_file: Path to SUMO configuration file
            scenario_name: Name of the scenario
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse the config file
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Fix route files paths
            input_elem = root.find('.//input')
            if input_elem is not None:
                route_files_elem = input_elem.find('route-files')
                if route_files_elem is not None:
                    # Update route file paths to include routes/ subdirectory
                    old_value = route_files_elem.get('value', '')
                    # Replace .trips.xml with .rou.xml and add routes/ prefix
                    new_files = []
                    for file in old_value.split(','):
                        file = file.strip()
                        if file:
                            # Change .trips.xml to .rou.xml and add routes/ prefix
                            file = file.replace('.trips.xml', '.rou.xml')
                            if not file.startswith('routes/'):
                                file = f'routes/{file}'
                            new_files.append(file)
                    route_files_elem.set('value', ','.join(new_files))
                
                # Fix additional files path
                additional_files_elem = input_elem.find('additional-files')
                if additional_files_elem is not None:
                    old_value = additional_files_elem.get('value', '')
                    if old_value and not old_value.startswith(scenario_name):
                        additional_files_elem.set('value', f'{scenario_name}.{old_value}')
            
            # Fix output file paths
            output_elem = root.find('.//output')
            if output_elem is not None:
                for output_file_elem in output_elem:
                    old_value = output_file_elem.get('value', '')
                    if old_value and not old_value.startswith(scenario_name):
                        output_file_elem.set('value', f'{scenario_name}.{old_value}')
            
            # Fix GUI settings file path
            gui_elem = root.find('.//gui_only')
            if gui_elem is not None:
                gui_settings_elem = gui_elem.find('gui-settings-file')
                if gui_settings_elem is not None:
                    old_value = gui_settings_elem.get('value', '')
                    if old_value and not old_value.startswith(scenario_name):
                        gui_settings_elem.set('value', f'{scenario_name}.{old_value}')
            
            # Write the fixed config file
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            print(f"Fixed SUMO configuration file paths")
            return True
            
        except Exception as e:
            print(f"Error fixing SUMO config paths: {e}")
            return False

def main():
    """
    Command line interface for OSM scenario importer
    """
    parser = argparse.ArgumentParser(description='Import OSM Web Wizard scenarios')
    parser.add_argument('--list', action='store_true', help='List available OSM scenarios')
    parser.add_argument('--import', dest='import_scenario', help='Import specified scenario')
    parser.add_argument('--name', help='Custom name for imported network')
    parser.add_argument('--osm-dir', default='osm_scenarios', help='OSM scenarios directory')
    parser.add_argument('--target-dir', default='../backend/networks', help='Target networks directory')
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = OSMScenarioImporter(args.osm_dir, args.target_dir)
    
    if args.list:
        # List available scenarios
        scenarios = importer.scan_osm_scenarios()
        if not scenarios:
            print("No OSM scenarios found in", args.osm_dir)
            print("Place OSM Web Wizard output folders in this directory")
        else:
            print(f"Found {len(scenarios)} OSM scenarios:")
            for scenario in scenarios:
                print(f"\n📁 {scenario['name']}")
                print(f"   Edges: {scenario['network_info']['edges']}")
                print(f"   Junctions: {scenario['network_info']['junctions']}")
                print(f"   Vehicle types: {', '.join(scenario['vehicle_types'])}")
                print(f"   Files: {scenario['stats']['total_files']}")
    
    elif args.import_scenario:
        # Import specified scenario
        result = importer.import_scenario(args.import_scenario, args.name)
        if result['success']:
            print("✅", result['message'])
            print("   Target path:", result['target_path'])
            print("   Vehicle types:", ', '.join(result['vehicle_types']))
        else:
            print("❌ Import failed:", result['error'])
    
    else:
        # Show help
        parser.print_help()
        print("\nExample usage:")
        print("  python osm_scenario_importer.py --list")
        print("  python osm_scenario_importer.py --import my_scenario --name downtown_traffic")

if __name__ == "__main__":
    main()
