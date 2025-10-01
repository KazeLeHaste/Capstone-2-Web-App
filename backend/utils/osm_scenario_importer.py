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