"""
OSM Scenario Importer

Processes OSM Web Wizard generated scenarios and imports them into the traffic simulator
web application. Preserves realistic traffic patterns by prioritizing original trip files.

Features:
- Import complete OSM scenarios with all vehicle types
- Preserve original OSM Web Wizard timing, spawning, and route patterns
- Prioritize .trips.xml files over .rou.xml for better realism
- Create network packages compatible with web app
- Support vehicle type filtering and configuration
- Optional route diversity enhancement (may affect realism)

Key Changes (Solution 1 - Preserve Original Files):
- Copy original trip files (.trips.xml) first to maintain realistic vehicle behavior
- Enhanced routes (.rou.xml) are only used as fallback for backward compatibility
- Route diversity enhancement is optional and warns about potential realism impact

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
import subprocess
import random
import tempfile

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
            'additional': ['osm.view.xml', 'osm.view', 'edgeData.xml', 'edgeData', 'stats.xml', 'stats', 'tripinfos.xml', 'tripinfos', 'output.add.xml', 'output.add'],
            'polygons': ['osm.poly.xml.gz', 'osm.poly.xml', 'osm.poly.add.xml', 'poly.add.xml', 'polygons.add.xml', 'osm.buildings.xml', 'buildings.xml']
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
    
    def import_scenario(self, scenario_name: str, target_name: str = None, enhance_diversity: bool = False) -> Dict[str, Any]:
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
            self._copy_osm_files(scenario_path, target_path, scenario_info, enhance_diversity)
            
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
    
    def _copy_osm_files(self, source_path: Path, target_path: Path, scenario_info: Dict[str, Any], enhance_diversity: bool = False):
        """
        Copy and rename OSM files to target directory, preserving original trip files for realism
        
        Args:
            source_path: Source OSM scenario directory
            target_path: Target network directory
            scenario_info: Scenario metadata
            enhance_diversity: If True, applies route enhancement (may reduce realism)
            
        Note:
            This method prioritizes .trips.xml files over .rou.xml files to preserve
            the original OSM Web Wizard timing patterns and realistic vehicle behavior.
        """
        network_name = target_path.name
        
        # Copy main network file (preserve compression for SUMO behavioral accuracy)
        source_network = Path(scenario_info['network_file'])
        
        if source_network.suffix == '.gz':
            # Preserve compressed format - critical for exact SUMO simulation behavior
            target_network = target_path / f"{network_name}.net.xml.gz"
            shutil.copy2(source_network, target_network)
        else:
            # Copy uncompressed network file
            target_network = target_path / f"{network_name}.net.xml"
            shutil.copy2(source_network, target_network)
        
        # Copy config file
        source_config = Path(scenario_info['config_file'])
        target_config = target_path / f"{network_name}.sumocfg"
        self._process_config_file(source_config, target_config, network_name, enhance_diversity, scenario_info['vehicle_types'])
        
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
        
        # Copy polygon files if they exist (for visual enhancement)
        polygon_found = False
        for poly_pattern in self.osm_files['polygons']:
            source_file = source_path / poly_pattern
            if source_file.exists():
                target_file = target_path / f"{network_name}.poly.add.xml"
                
                if source_file.suffix == '.gz':
                    # Decompress .gz polygon file
                    try:
                        with gzip.open(source_file, 'rt', encoding='utf-8') as f_in:
                            with open(target_file, 'w', encoding='utf-8') as f_out:
                                f_out.write(f_in.read())
                        print(f"Decompressed and copied polygon file: {poly_pattern} -> {target_file.name}")
                    except Exception as e:
                        print(f"Failed to decompress polygon file {poly_pattern}: {e}")
                        # Fall back to copying as-is
                        shutil.copy2(source_file, target_file)
                        print(f"Copied polygon file (as-is): {poly_pattern} -> {target_file.name}")
                else:
                    shutil.copy2(source_file, target_file)
                    print(f"Copied polygon file: {poly_pattern} -> {target_file.name}")
                
                polygon_found = True
                break  # Use first polygon file found
        
        if not polygon_found:
            print(f"No polygon files found in {source_path.name} - visual elements will be limited")
        
        # Create routes directory and copy route/trip files
        routes_dir = target_path / 'routes'
        routes_dir.mkdir(exist_ok=True)
        
        # Copy route files by vehicle type (preserve original OSM files - prefer .trips for realistic patterns)
        for vehicle_type in scenario_info['vehicle_types']:
            # First try trip files (original OSM Web Wizard format with realistic timing)
            copied = False
            if vehicle_type in self.osm_files['trips']:
                for pattern in self.osm_files['trips'][vehicle_type]:
                    source_file = source_path / pattern
                    if source_file.exists():
                        target_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
                        shutil.copy2(source_file, target_file)
                        copied = True
                        print(f"Copied original trip file for {vehicle_type}: {pattern}")
                        break
            
            # If no trip file, try route files as fallback
            if not copied and vehicle_type in self.osm_files['routes']:
                for pattern in self.osm_files['routes'][vehicle_type]:
                    source_file = source_path / pattern
                    if source_file.exists():
                        target_file = routes_dir / f"osm.{vehicle_type}.rou.xml"
                        shutil.copy2(source_file, target_file)
                        copied = True
                        print(f"Copied route file for {vehicle_type}: {pattern}")
                        break
            
            if not copied:
                print(f"Warning: No route or trip file found for {vehicle_type}")
        
        # Preserve original OSM Web Wizard route patterns by default for realistic traffic
        if enhance_diversity:
            print("⚠️  Route diversity enhancement requested...")
            print("Note: Enhancement may alter realistic OSM Web Wizard traffic patterns")
            try:
                self._enhance_route_diversity(target_path, scenario_info)
                print("Route diversity enhancement completed successfully")
                
                # Update config file to reference enhanced routes
                target_config = target_path / f"{network_name}.sumocfg"
                self._update_config_for_enhanced_routes(target_config, scenario_info['vehicle_types'])
                
            except Exception as e:
                print(f"Warning: Route diversity enhancement failed: {e}")
                print("Continuing with original routes for realistic traffic patterns...")
        else:
            print("✅ Preserving original OSM Web Wizard routes for realistic traffic patterns")
            print("   (Original files maintain proper timing, spawning, and vehicle behavior)")
    
    def _process_config_file(self, source_config: Path, target_config: Path, network_name: str, enhance_diversity: bool = False, vehicle_types: List[str] = None):
        """
        Process and update SUMO configuration file with new paths, prioritizing trip files
        
        Args:
            source_config: Source configuration file
            target_config: Target configuration file
            network_name: Network name for path updates
            enhance_diversity: If True, references enhanced route files
            vehicle_types: List of vehicle types to include
            
        Note:
            This method prioritizes .trips.xml files over .rou.xml files in the SUMO
            configuration to maintain realistic traffic patterns from OSM Web Wizard.
        """
        try:
            tree = ET.parse(source_config)
            root = tree.getroot()
            
            # Update network file path (preserve compression format for SUMO accuracy)
            net_input = root.find('.//net-file')
            if net_input is not None:
                # Determine if source uses compressed network
                source_network_path = Path(source_config.parent) / net_input.get('value', '')
                if source_network_path.suffix == '.gz' or source_network_path.name.endswith('.net.xml.gz'):
                    net_input.set('value', f"{network_name}.net.xml.gz")
                else:
                    net_input.set('value', f"{network_name}.net.xml")
            
            # Update route file paths to point to routes directory
            route_input = root.find('.//route-files')
            if route_input is not None:
                route_files = []
                
                # Use vehicle_types parameter if provided, otherwise default to common types
                types_to_check = vehicle_types if vehicle_types else ['passenger', 'bus', 'truck', 'motorcycle']
                
                # If diversity enhancement is enabled, use merged enhanced route file
                if enhance_diversity:
                    enhanced_merged_file = "routes/osm.enhanced.rou.xml"
                    if (target_config.parent / enhanced_merged_file).exists():
                        route_files.append(enhanced_merged_file)
                    else:
                        # Fallback to individual enhanced files
                        for vehicle_type in types_to_check:
                            enhanced_rou_file = f"routes/osm.{vehicle_type}.enhanced.rou.xml"
                            if (target_config.parent / enhanced_rou_file).exists():
                                route_files.append(enhanced_rou_file)
                else:
                    # Use original files when diversity enhancement is disabled - prefer .trips.xml for realistic patterns
                    for vehicle_type in types_to_check:
                        trips_file = f"routes/osm.{vehicle_type}.trips.xml"
                        rou_file = f"routes/osm.{vehicle_type}.rou.xml"
                        
                        # Prioritize trips files for better realism, fallback to rou files
                        if (target_config.parent / trips_file).exists():
                            route_files.append(trips_file)
                        elif (target_config.parent / rou_file).exists():
                            route_files.append(rou_file)
                
                if route_files:
                    route_input.set('value', ','.join(route_files))
            
            # Ensure output section exists and add missing outputs for analytics
            output_section = root.find('.//output')
            if output_section is None:
                # Create output section if it doesn't exist
                output_section = ET.SubElement(root, 'output')
            
            # Add summary-output if missing (critical for time series analytics)
            summary_output = output_section.find('summary-output')
            if summary_output is None:
                summary_output = ET.SubElement(output_section, 'summary-output')
                summary_output.set('value', f'{network_name}_summary.xml')
                print(f"Added summary-output to config: {network_name}_summary.xml")
            
            # Ensure tripinfo-output exists for trip analytics
            tripinfo_output = output_section.find('tripinfo-output')
            if tripinfo_output is None:
                tripinfo_output = ET.SubElement(output_section, 'tripinfo-output')
                tripinfo_output.set('value', f'{network_name}_tripinfo.xml')
                print(f"Added tripinfo-output to config: {network_name}_tripinfo.xml")
            
            # Add emission-output for environmental analytics
            emission_output = output_section.find('emission-output')
            if emission_output is None:
                emission_output = ET.SubElement(output_section, 'emission-output')
                emission_output.set('value', f'{network_name}_emissions.xml')
                print(f"Added emission-output to config: {network_name}_emissions.xml")
            
            # Add edgedata-output for network analysis
            edgedata_output = output_section.find('edgedata-output')
            if edgedata_output is None:
                edgedata_output = ET.SubElement(output_section, 'edgedata-output')
                edgedata_output.set('value', f'{network_name}_edgedata.xml')
                print(f"Added edgedata-output to config: {network_name}_edgedata.xml")
            
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
                            # Keep original file extension (.trips.xml or .rou.xml) and add routes/ prefix
                            if not file.startswith('routes/'):
                                file = f'routes/{file}'
                            new_files.append(file)
                    route_files_elem.set('value', ','.join(new_files))
                
                # Fix additional files path and polygon references
                additional_files_elem = input_elem.find('additional-files')
                if additional_files_elem is not None:
                    old_value = additional_files_elem.get('value', '')
                    new_files = []
                    
                    for file in old_value.split(','):
                        file = file.strip()
                        if file:
                            # Update file references with scenario name prefix
                            if 'poly.xml' in file:
                                file = f'{scenario_name}.poly.add.xml'
                            elif file == 'output.add.xml':
                                file = f'{scenario_name}.output_add.xml'
                            elif not file.startswith(scenario_name):
                                file = f'{scenario_name}.{file}'
                            new_files.append(file)
                    
                    # Check if polygon file exists and ensure it's in the list
                    poly_file = config_file.parent / f"{scenario_name}.poly.add.xml"
                    poly_filename = f"{scenario_name}.poly.add.xml"
                    
                    if poly_file.exists() and poly_filename not in new_files:
                        new_files.insert(0, poly_filename)  # Add polygon file first
                        print(f"Added polygon file to SUMO configuration: {poly_filename}")
                    
                    additional_files_elem.set('value', ','.join(new_files))
                else:
                    # Create additional-files element if polygon exists
                    poly_file = config_file.parent / f"{scenario_name}.poly.add.xml"
                    if poly_file.exists():
                        additional_files_elem = ET.SubElement(input_elem, 'additional-files')
                        additional_files_elem.set('value', f'{scenario_name}.poly.add.xml')
                        print(f"Created additional-files section with polygon: {scenario_name}.poly.add.xml")
            
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
                        # Convert dots to underscores to match file naming convention
                        fixed_filename = old_value.replace('.xml', '').replace('.', '_') + '.xml'
                        gui_settings_elem.set('value', f'{scenario_name}.{fixed_filename}')
            
            # Write the fixed config file
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            print(f"Fixed SUMO configuration file paths")
            return True
            
        except Exception as e:
            print(f"Error fixing SUMO config paths: {e}")
            return False

    def _enhance_route_diversity(self, target_path: Path, scenario_info: Dict[str, Any]):
        """
        Enhance route diversity by generating additional diverse trips for each vehicle type
        using SUMO's randomTrips.py with vehicle-type-specific parameters.
        
        Args:
            target_path: Target network directory
            scenario_info: Scenario information dictionary
        """
        import subprocess
        import random
        
        network_file = target_path / f"{target_path.name}.net.xml"
        network_file_gz = target_path / f"{target_path.name}.net.xml.gz"
        routes_dir = target_path / 'routes'
        
        # Check if network file exists (compressed or uncompressed)
        temp_network_file = None
        if network_file.exists():
            # Use existing uncompressed file
            actual_network_file = network_file
        elif network_file_gz.exists():
            # Decompress temporarily for enhancement
            try:
                temp_network_file = network_file
                with gzip.open(network_file_gz, 'rt', encoding='utf-8') as f_in:
                    with open(temp_network_file, 'w', encoding='utf-8') as f_out:
                        f_out.write(f_in.read())
                actual_network_file = temp_network_file
                print(f"Temporarily decompressed network file for enhancement")
            except Exception as e:
                print(f"Failed to decompress network file: {e}")
                return
        else:
            print(f"Network file not found: {network_file} or {network_file_gz}")
            return
        
        print(f"Enhancing route diversity for network: {actual_network_file}")
        
        try:
            # Vehicle-type-specific parameters with enhanced randomization
            vehicle_params = {
                'passenger': {
                    'insertion_density': 12.0,
                    'min_distance': 200.0,  # Reduced for more variety
                    'fringe_factor': 1.5,   # Reduced for more inner road usage
                    'random_factor': 1.4,   # Increased randomness
                    'lanes_weight': True,
                    'length_weight': True,
                    'speed_exponent': 0.1
                },
                'bus': {
                    'insertion_density': 4.0,
                    'min_distance': 400.0,  # Reduced for more local routes
                    'fringe_factor': 2.0,   # Reduced for variety
                    'random_factor': 1.3,
                    'lanes_weight': False,
                    'length_weight': True,
                    'speed_exponent': 0.2
                },
                'truck': {
                    'insertion_density': 6.0,  # Reduced density for more realism
                    'min_distance': 500.0,
                    'fringe_factor': 2.5,   # Trucks still prefer main roads but with variety
                    'random_factor': 1.25,
                    'lanes_weight': True,
                    'length_weight': True,
                    'speed_exponent': 0.15
                },
                'motorcycle': {
                    'insertion_density': 8.0,
                    'min_distance': 150.0,  # Motorcycles can take very short routes
                    'fringe_factor': 1.0,   # Maximum flexibility
                    'random_factor': 1.5,   # Maximum randomness
                    'lanes_weight': False,
                    'length_weight': False,
                    'speed_exponent': 0.0
                }
            }
            
            # Process each vehicle type
            for vehicle_type in scenario_info['vehicle_types']:
                print(f"  Processing {vehicle_type} routes...")
                
                # Get original trip file
                original_trips_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
                
                if not original_trips_file.exists():
                    print(f"    No trip file found for {vehicle_type}, skipping")
                    continue
                
                try:
                    # Analyze original file to determine parameters
                    original_stats = self._analyze_route_file(original_trips_file)
                    print(f"    Original stats: {original_stats['vehicle_count']} vehicles, {original_stats['time_span']:.0f}s span")
                    
                    # Get vehicle-specific parameters
                    params = vehicle_params.get(vehicle_type, vehicle_params['passenger'])
                    
                    # Generate enhanced diverse trips
                    enhanced_trips = self._generate_realistic_diverse_trips(
                        actual_network_file,
                        vehicle_type,
                        original_stats,
                        params
                    )
                    
                    if enhanced_trips:
                        # Merge enhanced trips with original trips
                        enhanced_file = self._merge_trip_files(
                            original_trips_file,
                            enhanced_trips,
                            vehicle_type
                        )
                        
                        if enhanced_file:
                            # Replace original with enhanced version (keep uncompressed like original OSM files)
                            enhanced_file_path = routes_dir / f"osm.{vehicle_type}.trips.xml"
                            shutil.move(enhanced_file, enhanced_file_path)
                            print(f"    ✅ Enhanced {vehicle_type} trips (kept uncompressed as per OSM standard)")
                        
                        
                except Exception as e:
                    print(f"    ❌ Failed to enhance {vehicle_type} routes: {e}")
                    continue
            
            # Create a single merged route file with all vehicle types to avoid ID conflicts
            print("Creating final merged route file...")
            self._create_merged_enhanced_routes(routes_dir, scenario_info['vehicle_types'], actual_network_file)
        
        finally:
            # Clean up temporary network file if created
            if temp_network_file and temp_network_file.exists():
                try:
                    temp_network_file.unlink()
                    print(f"Cleaned up temporary network file")
                except:
                    pass
    
    def _analyze_route_file(self, route_file: Path) -> Dict[str, Any]:
        """
        Analyze existing route/trip file to extract statistics
        
        Args:
            route_file: Path to route or trip file
            
        Returns:
            Dictionary with file statistics
        """
        try:
            tree = ET.parse(route_file)
            root = tree.getroot()
            
            # Count vehicles/trips
            vehicles = root.findall('.//vehicle') + root.findall('.//trip')
            vehicle_count = len(vehicles)
            
            # Extract timing information
            depart_times = []
            for vehicle in vehicles:
                depart = vehicle.get('depart', '0')
                try:
                    depart_times.append(float(depart))
                except:
                    pass
            
            # Calculate time span
            time_span = max(depart_times) - min(depart_times) if depart_times else 3600
            
            return {
                'vehicle_count': vehicle_count,
                'time_span': time_span,
                'avg_period': time_span / vehicle_count if vehicle_count > 0 else 30,
                'min_depart': min(depart_times) if depart_times else 0,
                'max_depart': max(depart_times) if depart_times else 3600
            }
            
        except Exception as e:
            print(f"    Warning: Could not analyze route file {route_file}: {e}")
            return {
                'vehicle_count': 100,
                'time_span': 3600,
                'avg_period': 36,
                'min_depart': 0,
                'max_depart': 3600
            }
    
    def _generate_enhanced_trips(self, network_file: Path, output_file: Path, 
                               vehicle_type: str, original_stats: Dict[str, Any],
                               params: Dict[str, Any]):
        """
        Generate enhanced trips using randomTrips.py with diversity parameters
        
        Args:
            network_file: Path to network file
            output_file: Output trips file
            vehicle_type: Vehicle type (passenger, bus, etc.)
            original_stats: Statistics from original file
            params: Enhancement parameters
        """
        import subprocess
        
        # Calculate parameters based on original stats
        num_trips = max(50, original_stats['vehicle_count'] // 2)  # Generate supplemental trips
        time_span = original_stats['time_span']
        period = time_span / num_trips if num_trips > 0 else 30
        
        # Build randomTrips.py command with enhanced diversity  
        sumo_tools_path = r"C:\Program Files (x86)\Eclipse\Sumo\tools"
        randomtrips_script = os.path.join(sumo_tools_path, "randomTrips.py")
        
        # Convert paths to absolute paths with forward slashes for SUMO compatibility
        network_file_abs = str(network_file.resolve()).replace('\\', '/')
        output_file_abs = str(output_file.resolve()).replace('\\', '/')
        
        # Ensure begin time is never 0 to prevent clustering at depart=0
        begin_time = max(1.0, original_stats['min_depart'])  # Start at least at 1 second
        end_time = original_stats['max_depart']
        
        cmd = [
            'python', randomtrips_script,
            "-n", network_file_abs,
            "-o", output_file_abs,
            "--vehicle-class", vehicle_type,
            "--edge-permission", vehicle_type,
            "-b", str(begin_time),
            "-e", str(end_time),
            "-p", str(period),
            "--fringe-factor", str(params['fringe_factor']),
            "--min-distance", str(params['min_distance']),
            "--random-factor", str(params['random_factor']),
            "--intermediate", str(params['intermediate_waypoints']),
            "--speed-exponent", str(params['speed_exponent']),
            "--random",
            "--validate"
        ]
        
        # Add optional flags
        if params['lanes_weight']:
            cmd.append("-L")
        if params['length_weight']:  
            cmd.append("-l")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(network_file.parent))
            if result.returncode == 0:
                print(f"    ✅ Generated enhanced trips: {output_file.name}")
            else:
                print(f"    ❌ randomTrips.py failed: {result.stderr}")
        except Exception as e:
            print(f"    ❌ Failed to run randomTrips.py: {e}")
    
    def _generate_diverse_routes(self, network_file: Path, trips_file: Path, 
                               routes_file: Path, vehicle_type: str):
        """
        Generate diverse routes using duarouter with alternative route options
        
        Args:
            network_file: Path to network file
            trips_file: Input trips file
            routes_file: Output routes file
            vehicle_type: Vehicle type
        """
        import subprocess
        
        # Build duarouter command with diversity options
        # Convert paths to absolute paths with forward slashes for SUMO compatibility
        network_file_abs = str(network_file.resolve()).replace('\\', '/')
        trips_file_abs = str(trips_file.resolve()).replace('\\', '/')
        routes_file_abs = str(routes_file.resolve()).replace('\\', '/')
        
        cmd = [
            'duarouter',
            '-n', network_file_abs,
            '-r', trips_file_abs,
            '-o', routes_file_abs,
            '--max-alternatives', '3',              # Generate route alternatives
            '--weights.random-factor', '1.2',      # Add routing randomness
            '--route-choice-method', 'gawron',     # Use Gawron route choice
            '--remove-loops',                      # Clean up routes
            '--ignore-errors'                      # Continue on errors
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(network_file.parent))
            if result.returncode == 0:
                print(f"    ✅ Generated diverse routes: {routes_file.name}")
            else:
                print(f"    ❌ duarouter failed: {result.stderr}")
        except Exception as e:
            print(f"    ❌ Failed to run duarouter: {e}")
    
    def _generate_realistic_diverse_trips(self, network_file: Path, vehicle_type: str, 
                                        original_stats: Dict[str, Any], params: Dict[str, Any]) -> Optional[List[ET.Element]]:
        """
        Generate realistic diverse trips with enhanced randomization for vehicle type, 
        spawn locations, destinations, and temporal distribution
        
        Args:
            network_file: Path to network file
            vehicle_type: Vehicle type (passenger, bus, etc.)
            original_stats: Statistics from original file
            params: Vehicle-type-specific parameters
            
        Returns:
            List of trip elements with enhanced randomization
        """
        import subprocess
        import tempfile
        import random
        
        # Create multiple temporary files for different randomization approaches
        temp_files = []
        all_trips = []
        
        try:
            # Generate multiple batches with different parameters for maximum variety
            batch_configs = self._create_randomization_batches(vehicle_type, original_stats, params)
            
            for i, batch_config in enumerate(batch_configs):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.trips_{i}.xml', delete=False) as temp_file:
                    temp_trips_file = Path(temp_file.name)
                    temp_files.append(temp_trips_file)
                    
                    # Generate batch with specific randomization parameters
                    batch_trips = self._generate_trip_batch(network_file, temp_trips_file, batch_config)
                    if batch_trips:
                        all_trips.extend(batch_trips)
            
            if all_trips:
                # Apply enhanced randomization to all trips
                randomized_trips = self._apply_enhanced_randomization(all_trips, vehicle_type, original_stats)
                return randomized_trips
                
        except Exception as e:
            print(f"    ❌ Failed to generate realistic diverse trips: {e}")
            return None
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except:
                    pass
                    
        return None
    
    def _create_randomization_batches(self, vehicle_type: str, original_stats: Dict[str, Any], 
                                    base_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create multiple randomization batch configurations for maximum diversity
        """
        # Base configuration
        num_trips_per_batch = max(15, original_stats['vehicle_count'] // 5)
        time_span = original_stats['time_span']
        
        # Create 4 different batches with varying parameters for maximum randomization
        batches = []
        
        # Batch 1: Inner city focus (lower fringe factor)
        batches.append({
            'vehicle_type': vehicle_type,
            'num_trips': num_trips_per_batch,
            'time_span': time_span,
            'fringe_factor': max(1.0, base_params['fringe_factor'] * 0.5),  # More inner roads
            'min_distance': base_params['min_distance'] * 0.7,
            'random_factor': base_params['random_factor'] * 1.3,
            'period_variance': 0.4,  # High temporal randomness
            'seed_offset': 42
        })
        
        # Batch 2: Mixed urban (medium fringe factor)  
        batches.append({
            'vehicle_type': vehicle_type,
            'num_trips': num_trips_per_batch,
            'time_span': time_span,
            'fringe_factor': base_params['fringe_factor'],
            'min_distance': base_params['min_distance'],
            'random_factor': base_params['random_factor'] * 1.1,
            'period_variance': 0.3,
            'seed_offset': 123
        })
        
        # Batch 3: Suburban/arterial focus (higher fringe factor)
        batches.append({
            'vehicle_type': vehicle_type,
            'num_trips': num_trips_per_batch,
            'time_span': time_span,
            'fringe_factor': base_params['fringe_factor'] * 1.5,
            'min_distance': base_params['min_distance'] * 1.3,
            'random_factor': base_params['random_factor'] * 0.9,
            'period_variance': 0.2,
            'seed_offset': 789
        })
        
        # Batch 4: Long distance trips (maximum variety)
        batches.append({
            'vehicle_type': vehicle_type,
            'num_trips': max(10, num_trips_per_batch // 2),  # Fewer but longer trips
            'time_span': time_span,
            'fringe_factor': base_params['fringe_factor'] * 2.0,
            'min_distance': base_params['min_distance'] * 2.0,  # Longer trips
            'random_factor': base_params['random_factor'] * 1.5,
            'period_variance': 0.5,
            'seed_offset': 456
        })
        
        return batches
    
    def _generate_trip_batch(self, network_file: Path, output_file: Path, 
                           batch_config: Dict[str, Any]) -> Optional[List[ET.Element]]:
        """
        Generate a single batch of trips with specific randomization parameters
        """
        import subprocess
        
        try:
            # Calculate randomized period
            base_period = batch_config['time_span'] / batch_config['num_trips'] if batch_config['num_trips'] > 0 else 30
            period_variance = batch_config.get('period_variance', 0.3)
            min_period = base_period * (1 - period_variance)
            max_period = base_period * (1 + period_variance)
            
            # Build randomTrips.py command with enhanced randomization
            sumo_tools_path = r"C:\Program Files (x86)\Eclipse\Sumo\tools"
            randomtrips_script = os.path.join(sumo_tools_path, "randomTrips.py")
            
            # Convert paths to absolute paths with forward slashes for SUMO compatibility
            network_file_abs = str(network_file.resolve()).replace('\\', '/')
            output_file_abs = str(output_file.resolve()).replace('\\', '/')
            
            # Use random period within variance range
            import random
            random.seed(batch_config['seed_offset'])
            actual_period = random.uniform(min_period, max_period)
            
            cmd = [
                'python', randomtrips_script,
                "-n", network_file_abs,
                "-o", output_file_abs,
                "--vehicle-class", batch_config['vehicle_type'],
                "--edge-permission", batch_config['vehicle_type'],
                "-p", str(actual_period),
                "--fringe-factor", str(batch_config['fringe_factor']),
                "--min-distance", str(batch_config['min_distance']),
                "--random-factor", str(batch_config['random_factor']),
                "--seed", str(batch_config['seed_offset']),  # Different seed for each batch
                "--random",
                "--validate"
            ]
            
            # Run randomTrips.py
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(network_file.parent))
            
            if result.returncode == 0 and output_file.exists():
                # Parse generated trips
                tree = ET.parse(output_file)
                root = tree.getroot()
                trips = root.findall('.//trip')
                print(f"    Generated {len(trips)} diverse trips for batch")
                return trips
            else:
                print(f"    ❌ randomTrips.py failed for batch: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"    ❌ Failed to generate diverse trips for batch: {e}")
            return None
    
    def _merge_trip_files(self, original_file: Path, enhanced_trips: List[ET.Element], 
                         vehicle_type: str) -> Optional[Path]:
        """
        Merge original trips with enhanced diverse trips
        
        Args:
            original_file: Original trip file
            enhanced_trips: List of enhanced trip elements
            vehicle_type: Vehicle type
            
        Returns:
            Path to merged file or None if failed
        """
        import tempfile
        
        try:
            # Parse original file
            original_tree = ET.parse(original_file)
            original_root = original_tree.getroot()
            
            # Get original trips
            original_trips = original_root.findall('.//trip')
            
            # Create new root with same structure
            merged_root = ET.Element('routes')
            merged_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            merged_root.set('xsi:noNamespaceSchemaLocation', 'http://sumo.dlr.de/xsd/routes_file.xsd')
            
            # Copy vType definitions and enhance them
            for vtype in original_root.findall('.//vType'):
                # Enhance vType with proper colors and shapes
                enhanced_vtype = self._enhance_vehicle_type_definition(vtype)
                merged_root.append(enhanced_vtype)
            
            # Add original trips (keep 80% for vehicle type diversity)
            import random
            random.seed(hash(vehicle_type))  # Consistent but different per vehicle type
            selected_original = random.sample(original_trips, min(len(original_trips), int(len(original_trips) * 0.8)))
            
            # Generate unique trip IDs using timestamp and vehicle type
            import time
            base_id = int(time.time() * 1000) % 1000000  # Use timestamp for uniqueness
            trip_id_counter = 0
            
            # Add selected original trips
            for trip in selected_original:
                new_trip = ET.Element('trip')
                for attr, value in trip.attrib.items():
                    if attr == 'id':
                        new_trip.set(attr, f"{vehicle_type}_{base_id}_{trip_id_counter}")
                        trip_id_counter += 1
                    else:
                        new_trip.set(attr, value)
                merged_root.append(new_trip)
            
            # Add enhanced trips with proper IDs and timing distribution
            for trip in enhanced_trips:
                new_trip = ET.Element('trip')
                for attr, value in trip.attrib.items():
                    if attr == 'id':
                        new_trip.set(attr, f"{vehicle_type}_{base_id}_enh_{trip_id_counter}")
                        trip_id_counter += 1
                    elif attr == 'type':
                        # Map to correct vType ID from original file
                        original_vtypes = [vt.get('id') for vt in original_root.findall('.//vType')]
                        # Look for matching vType (should be veh_passenger, bus_bus, etc.)
                        correct_type = None
                        for vtype_id in original_vtypes:
                            if vehicle_type in vtype_id.lower():
                                correct_type = vtype_id
                                break
                        new_trip.set(attr, correct_type if correct_type else f"veh_{vehicle_type}")
                    else:
                        new_trip.set(attr, value)
                merged_root.append(new_trip)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{vehicle_type}.trips.xml', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            # Write merged file
            merged_tree = ET.ElementTree(merged_root)
            merged_tree.write(temp_path, encoding='utf-8', xml_declaration=True)
            
            total_trips = len(selected_original) + len(enhanced_trips)
            print(f"    Merged {len(selected_original)} original + {len(enhanced_trips)} enhanced = {total_trips} total trips")
            
            return temp_path
            
        except Exception as e:
            print(f"    ❌ Failed to merge trip files for {vehicle_type}: {e}")
            return None
    
    def _analyze_trip_file_stats(self, trip_file: Path) -> Dict[str, Any]:
        """
        Analyze statistics from a trip file for diversity enhancement
        
        Args:
            trip_file: Path to trip file
            
        Returns:
            Dictionary with statistics
        """
        try:
            tree = ET.parse(trip_file)
            root = tree.getroot()
            
            trips = root.findall('.//trip')
            
            if not trips:
                return {
                    'vehicle_count': 0,
                    'min_depart': 0,
                    'max_depart': 3600,
                    'time_span': 3600
                }
            
            # Analyze departure times
            depart_times = []
            for trip in trips:
                depart = trip.get('depart', '0')
                try:
                    depart_times.append(float(depart))
                except (ValueError, TypeError):
                    depart_times.append(0)
            
            min_depart = min(depart_times) if depart_times else 0
            max_depart = max(depart_times) if depart_times else 3600
            
            return {
                'vehicle_count': len(trips),
                'min_depart': int(min_depart),
                'max_depart': int(max_depart),
                'time_span': int(max_depart - min_depart) if max_depart > min_depart else 3600
            }
            
        except Exception as e:
            print(f"    ❌ Failed to analyze trip file stats: {e}")
            return {
                'vehicle_count': 0,
                'min_depart': 0,
                'max_depart': 3600,
                'time_span': 3600
            }
    
    def _create_merged_enhanced_routes(self, routes_dir: Path, vehicle_types: List[str], network_file: Path):
        """
        Create a single merged route file from all enhanced trip files using duarouter
        with unique vehicle IDs across all vehicle types.
        
        Args:
            routes_dir: Routes directory
            vehicle_types: List of vehicle types
            network_file: Network file path
        """
        import subprocess
        import tempfile
        
        try:
            # Create a temporary merged trips file with unique IDs
            with tempfile.NamedTemporaryFile(mode='w', suffix='.trips.xml', delete=False) as temp_file:
                temp_trips_file = Path(temp_file.name)
            
            # Create merged root element
            merged_root = ET.Element('routes')
            merged_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            merged_root.set('xsi:noNamespaceSchemaLocation', 'http://sumo.dlr.de/xsd/routes_file.xsd')
            
            global_vehicle_id = 0
            
            # Collect all vehicle types and trips
            for vehicle_type in vehicle_types:
                trips_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
                
                if not trips_file.exists():
                    continue
                
                try:
                    # Parse vehicle type trips
                    tree = ET.parse(trips_file)
                    root = tree.getroot()
                    
                    # Copy vType definitions
                    for vtype in root.findall('.//vType'):
                        # Check if vType already exists
                        existing_vtypes = [vt.get('id') for vt in merged_root.findall('.//vType')]
                        if vtype.get('id') not in existing_vtypes:
                            merged_root.append(vtype)
                    
                    # Copy trips with unique global IDs and consistent type mapping
                    for trip in root.findall('.//trip'):
                        new_trip = ET.Element('trip')
                        
                        # Copy all attributes but assign unique ID and fix type mapping
                        for attr, value in trip.attrib.items():
                            if attr == 'id':
                                new_trip.set(attr, f"vehicle_{global_vehicle_id}")
                                global_vehicle_id += 1
                            elif attr == 'type':
                                # Ensure consistent type mapping - use the vType ID from this file
                                trip_vtypes = [vt.get('id') for vt in root.findall('.//vType')]
                                # Use the original type if it matches a vType, otherwise map to veh_vehicletype
                                if value in trip_vtypes:
                                    new_trip.set(attr, value)
                                else:
                                    # Find matching vType for this vehicle type
                                    correct_type = None
                                    for vtype_id in trip_vtypes:
                                        if vehicle_type in vtype_id.lower():
                                            correct_type = vtype_id
                                            break
                                    new_trip.set(attr, correct_type if correct_type else f"veh_{vehicle_type}")
                            else:
                                new_trip.set(attr, value)
                        
                        merged_root.append(new_trip)
                    
                    print(f"    Added {len(root.findall('.//trip'))} trips from {vehicle_type}")
                    
                except Exception as e:
                    print(f"    Warning: Could not process {vehicle_type} trips: {e}")
                    continue
            
            # Sort all trips by departure time before writing
            print(f"    Sorting {global_vehicle_id} trips by departure time...")
            trips = merged_root.findall('.//trip')
            
            # Sort trips by departure time
            def get_depart_time(trip):
                depart = trip.get('depart', '0')
                try:
                    return float(depart)
                except (ValueError, TypeError):
                    return 0.0
            
            trips.sort(key=get_depart_time)
            
            # CRITICAL FIX: Eliminate departure time clustering by redistributing vehicles with depart=0
            print("    🚨 Fixing departure time clustering (eliminating depart=0.00 vehicles)...")
            
            # Count vehicles with problematic departure times
            zero_depart_count = sum(1 for trip in trips if get_depart_time(trip) == 0.0)
            if zero_depart_count > 0:
                print(f"    Found {zero_depart_count} vehicles with depart=0.00 - redistributing...")
                
                # Calculate time range for redistribution
                non_zero_times = [get_depart_time(trip) for trip in trips if get_depart_time(trip) > 0]
                if non_zero_times:
                    min_time = min(non_zero_times)
                    max_time = max(non_zero_times)
                    time_span = max_time - min_time
                else:
                    # Fallback if all trips have depart=0
                    min_time = 10.0  # Start at 10 seconds
                    max_time = 3600.0  # End at 1 hour
                    time_span = max_time - min_time
                
                # Redistribute zero-departure vehicles across the time span
                import random
                for i, trip in enumerate(trips):
                    if get_depart_time(trip) == 0.0:
                        # Distribute evenly across time span with some randomness
                        base_time = min_time + (time_span * i / zero_depart_count)
                        jitter = random.uniform(-30, 30)  # ±30 seconds jitter
                        new_time = max(1.0, base_time + jitter)  # Ensure >= 1 second
                        trip.set('depart', f"{new_time:.2f}")
                        
                # Re-sort after redistribution
                trips.sort(key=get_depart_time)
                print(f"    ✅ Redistributed {zero_depart_count} vehicles - new range: {get_depart_time(trips[0]):.1f}s - {get_depart_time(trips[-1]):.1f}s")
            
            # Remove existing trips and add back in sorted order
            for trip in merged_root.findall('.//trip'):
                merged_root.remove(trip)
            
            for trip in trips:
                merged_root.append(trip)
            
            print(f"    Trips sorted by departure time (range: {get_depart_time(trips[0]):.1f}s - {get_depart_time(trips[-1]):.1f}s)")
            
            # Write merged trips file
            merged_tree = ET.ElementTree(merged_root)
            merged_tree.write(temp_trips_file, encoding='utf-8', xml_declaration=True)
            
            # Use duarouter to create final route file with proper routing
            final_routes_file = routes_dir / "osm.enhanced.rou.xml"
            
            # Build duarouter command
            sumo_tools_path = r"C:\Program Files (x86)\Eclipse\Sumo\tools"
            duarouter_path = os.path.join(sumo_tools_path, "duarouter.exe")
            
            if not os.path.exists(duarouter_path):
                duarouter_path = "duarouter"  # Fallback to system PATH
            
            # Convert paths to absolute paths with forward slashes for SUMO compatibility
            network_file_abs = str(network_file.resolve()).replace('\\', '/')
            temp_trips_file_abs = str(temp_trips_file.resolve()).replace('\\', '/')
            final_routes_file_abs = str(final_routes_file.resolve()).replace('\\', '/')
            
            cmd = [
                duarouter_path,
                "-n", network_file_abs,
                "-r", temp_trips_file_abs,
                "-o", final_routes_file_abs,
                "--max-alternatives", "3",
                "--remove-loops",
                "--weights.random-factor", "1.2",
                "--route-choice-method", "gawron",
                "--ignore-errors"
            ]
            
            print(f"    Running duarouter to generate final enhanced routes...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(routes_dir))
            
            if result.returncode == 0 and final_routes_file.exists():
                print(f"    ✅ Created merged enhanced route file with {global_vehicle_id} total vehicles")
                print(f"    Final route file: {final_routes_file.name}")
            else:
                print(f"    ❌ duarouter failed: {result.stderr}")
                print(f"    Falling back to using individual trip files...")
            
        except Exception as e:
            print(f"    ❌ Failed to create merged enhanced routes: {e}")
        finally:
            # Clean up temporary file
            if temp_trips_file.exists():
                temp_trips_file.unlink()
    
    def _update_config_for_enhanced_routes(self, config_file: Path, vehicle_types: List[str]):
        """
        Update SUMO config file to reference enhanced route files after they've been created
        
        Args:
            config_file: Path to SUMO config file
            vehicle_types: List of vehicle types
        """
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Update route file paths
            route_input = root.find('.//route-files')
            if route_input is not None:
                # Check if merged enhanced file exists
                routes_dir = config_file.parent / 'routes'
                merged_file = routes_dir / "osm.enhanced.rou.xml"
                
                if merged_file.exists():
                    # Use merged enhanced file
                    route_input.set('value', 'routes/osm.enhanced.rou.xml')
                    print("    Updated config to use merged enhanced route file")
                else:
                    # Fallback to individual enhanced files
                    route_files = []
                    for vehicle_type in vehicle_types:
                        enhanced_file = routes_dir / f"osm.{vehicle_type}.enhanced.rou.xml"
                        if enhanced_file.exists():
                            route_files.append(f"routes/osm.{vehicle_type}.enhanced.rou.xml")
                    
                    if route_files:
                        route_input.set('value', ','.join(route_files))
                        print(f"    Updated config to use {len(route_files)} individual enhanced route files")
            
            # Save updated config
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"    Warning: Could not update config for enhanced routes: {e}")

    def _apply_enhanced_randomization(self, trips: List[ET.Element], vehicle_type: str, 
                                    original_stats: Dict[str, Any]) -> List[ET.Element]:
        """
        Apply enhanced randomization to trip elements including:
        - Temporal randomization (departure time shuffling)
        - Vehicle color randomization  
        - Route attribute randomization
        - Vehicle shape settings
        """
        import random
        
        if not trips:
            return trips
            
        print(f"    Applying enhanced randomization to {len(trips)} {vehicle_type} trips...")
        
        # Extract departure times and shuffle them for temporal randomization
        departure_times = []
        for trip in trips:
            depart_time = float(trip.get('depart', 0))
            departure_times.append(depart_time)
        
        # Create shuffled departure times with some variance
        random.shuffle(departure_times)
        
        # Apply temporal jitter to prevent clustering
        jittered_times = []
        for base_time in departure_times:
            # Add random jitter of ±15 seconds to break up timing patterns
            jitter = random.uniform(-15.0, 15.0)
            jittered_time = max(0, base_time + jitter)
            jittered_times.append(jittered_time)
        
        # Sort to maintain chronological order but with randomized gaps
        jittered_times.sort()
        
        # Apply randomization to each trip
        color_schemes = self._get_vehicle_color_schemes(vehicle_type)
        
        for i, trip in enumerate(trips):
            # Apply randomized departure time
            if i < len(jittered_times):
                trip.set('depart', f"{jittered_times[i]:.2f}")
            
            # Set random color from appropriate scheme
            color = random.choice(color_schemes)
            trip.set('color', color)
            
            # Add enhanced vehicle attributes
            trip.set('departLane', 'best')
            trip.set('departSpeed', 'max')
            trip.set('departPos', 'random')
            
            # Note: guiShape should be on vType, not individual trips
            # We'll handle this in the vType definition instead
                
            # Add speed factor variation for more realistic behavior
            speed_factor = round(random.uniform(0.85, 1.15), 2)
            trip.set('speedFactor', str(speed_factor))
        
        print(f"    ✅ Applied enhanced randomization: colors, timing, and attributes")
        return trips
    
    def _get_vehicle_color_schemes(self, vehicle_type: str) -> List[str]:
        """
        Get realistic color schemes for different vehicle types
        """
        color_schemes = {
            'passenger': [
                '255,255,255',    # White
                '128,128,128',    # Gray  
                '0,0,0',          # Black
                '255,0,0',        # Red
                '0,0,255',        # Blue
                '255,255,0',      # Yellow
                '0,128,0',        # Green
                '128,0,128',      # Purple
                '255,165,0',      # Orange
                '192,192,192',    # Silver
                '139,69,19',      # Brown
                '0,255,255',      # Cyan
                '255,20,147',     # Deep Pink
                '50,205,50',      # Lime Green
                '255,69,0'        # Red Orange
            ],
            'bus': [
                '255,255,0',      # Yellow (school bus)
                '0,0,255',        # Blue
                '255,255,255',    # White
                '255,0,0',        # Red
                '0,128,0',        # Green
                '128,128,128',    # Gray
                '255,165,0'       # Orange
            ],
            'truck': [
                '255,255,255',    # White
                '128,128,128',    # Gray
                '0,0,0',          # Black
                '255,0,0',        # Red
                '0,0,255',        # Blue
                '255,255,0',      # Yellow
                '0,128,0'         # Green
            ],
            'motorcycle': [
                '255,0,0',        # Red
                '0,0,255',        # Blue
                '0,0,0',          # Black
                '255,255,255',    # White
                '255,255,0',      # Yellow
                '0,128,0',        # Green
                '255,165,0',      # Orange
                '128,0,128'       # Purple
            ]
        }
        
        return color_schemes.get(vehicle_type, color_schemes['passenger'])
    
    def _get_simple_shape_for_vehicle_type(self, vehicle_type: str) -> str:
        """
        Get simple shape for vehicle type as requested
        """
        shapes = {
            'passenger': 'passenger',
            'bus': 'bus', 
            'truck': 'truck',
            'motorcycle': 'motorcycle'
        }
        return shapes.get(vehicle_type, 'passenger')
    
    def _enhance_vehicle_type_definition(self, vtype_element: ET.Element) -> ET.Element:
        """
        Enhance a vType element with proper colors, shapes, and attributes
        """
        # Get vehicle class from the vType element
        vehicle_class = vtype_element.get('vClass', 'passenger')
        vtype_id = vtype_element.get('id', 'unknown')
        
        # Determine base vehicle type from ID or class
        base_type = 'passenger'
        for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
            if vtype in vtype_id.lower() or vtype in vehicle_class.lower():
                base_type = vtype
                break
        
        # Set simple shape
        shape = self._get_simple_shape_for_vehicle_type(base_type)
        vtype_element.set('guiShape', shape)
        
        # Set default color (vehicles will override this individually)
        default_colors = {
            'passenger': '128,128,128',  # Gray default
            'bus': '255,255,0',          # Yellow default
            'truck': '255,255,255',      # White default
            'motorcycle': '255,0,0'      # Red default
        }
        default_color = default_colors.get(base_type, '128,128,128')
        vtype_element.set('color', default_color)
        
        # Ensure realistic attributes for the vehicle type
        if base_type == 'passenger':
            if not vtype_element.get('maxSpeed'):
                vtype_element.set('maxSpeed', '55.56')  # 200 km/h
            if not vtype_element.get('accel'):
                vtype_element.set('accel', '2.6')
            if not vtype_element.get('decel'):
                vtype_element.set('decel', '4.5')
        elif base_type == 'bus':
            if not vtype_element.get('maxSpeed'):
                vtype_element.set('maxSpeed', '27.78')  # 100 km/h
            if not vtype_element.get('length'):
                vtype_element.set('length', '12.0')
        elif base_type == 'truck':
            if not vtype_element.get('maxSpeed'):
                vtype_element.set('maxSpeed', '25.0')   # 90 km/h
            if not vtype_element.get('length'):
                vtype_element.set('length', '10.0')
        elif base_type == 'motorcycle':
            if not vtype_element.get('maxSpeed'):
                vtype_element.set('maxSpeed', '50.0')   # 180 km/h
            if not vtype_element.get('length'):
                vtype_element.set('length', '2.5')
        
        return vtype_element
    
    def _compress_trip_file(self, trip_file: Path) -> Optional[Path]:
        """
        Compress a trip file using gzip as requested
        
        Args:
            trip_file: Path to uncompressed trip file
            
        Returns:
            Path to compressed file or None if failed
        """
        try:
            compressed_path = trip_file.with_suffix(trip_file.suffix + '.gz')
            
            with open(trip_file, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            print(f"    Compressed {trip_file.name} -> {compressed_path.name}")
            return compressed_path
            
        except Exception as e:
            print(f"    Warning: Failed to compress {trip_file.name}: {e}")
            return None

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
    parser.add_argument('--diversity', action='store_true', help='Enable route diversity enhancement during import')
    
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
        result = importer.import_scenario(args.import_scenario, args.name, enhance_diversity=args.diversity)
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
