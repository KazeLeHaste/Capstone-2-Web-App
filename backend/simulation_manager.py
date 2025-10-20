"""
Simulation Management Module - Passive Data Collection Implementation

Handles the configuration-first simulation workflow including:
- Session configuration storage
- Network copying and modification
- SUMO simulation launching with PASSIVE live data streaming
- File management for session isolation

PASSIVE DATA COLLECTION: This module uses passive TraCI data collection that
preserves user control over simulation timing and delay settings. It reads
simulation data without stepping, allowing SUMO GUI delay controls to work
as expected.

Author: Traffic Simulator Team
Date: August 2025
"""

import os
import json
import shutil
import subprocess
import tempfile
import uuid
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

# TraCI functionality has been removed to prevent configuration conflicts with SUMO GUI
# The system now operates in pure GUI mode for better user control

def find_network_file(directory: Path, network_id: str) -> Optional[Path]:
    """
    Find the correct network file (compressed or uncompressed) in a directory
    
    Args:
        directory: Directory to search in
        network_id: Network identifier (without extension)
        
    Returns:
        Path to the network file (with correct extension) or None if not found
    """
    # Check for compressed version first (preferred for OSM scenarios)
    compressed_path = directory / f"{network_id}.net.xml.gz"
    if compressed_path.exists():
        return compressed_path
    
    # Check for uncompressed version
    uncompressed_path = directory / f"{network_id}.net.xml"
    if uncompressed_path.exists():
        return uncompressed_path
    
    return None

def get_network_filename(network_id: str, is_compressed: bool = False) -> str:
    """
    Get the correct network filename based on compression status
    
    Args:
        network_id: Network identifier
        is_compressed: Whether the network file should be compressed
        
    Returns:
        Complete filename with correct extension
    """
    return f"{network_id}.net.xml.gz" if is_compressed else f"{network_id}.net.xml"

def glob_network_files(directory: Path) -> List[Path]:
    """
    Find all network files (both compressed and uncompressed) in a directory
    
    Args:
        directory: Directory to search in
        
    Returns:
        List of network file paths
    """
    network_files = []
    network_files.extend(directory.glob("*.net.xml"))
    network_files.extend(directory.glob("*.net.xml.gz"))
    return network_files

class SimulationManager:
    def __init__(self, base_networks_dir: str = "networks", websocket_handler=None, db_service=None):
        """
        Initialize the simulation manager
        
        Args:
            base_networks_dir: Directory containing original network files
            websocket_handler: WebSocket handler for live data broadcasting
            db_service: Database service for persistent storage
        """
        # Get the backend directory path (where this script is located)
        backend_dir = Path(__file__).parent
        
        # Ensure paths are relative to the backend directory
        self.base_networks_dir = backend_dir / base_networks_dir
        self.sessions_dir = backend_dir / "sessions"
        self.active_processes = {}
        self.websocket_handler = websocket_handler
        self.db_service = db_service
        
        # Start periodic process monitoring
        self._start_process_monitor()
        
        # Ensure directories exist
        self.base_networks_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        
    def save_session_config(self, session_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save session configuration to persistent storage (database and file backup)
        
        Args:
            session_id: Unique session identifier
            config_data: Configuration parameters
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Create session directory for file-based operations
            session_config_dir = self.sessions_dir / session_id
            session_config_dir.mkdir(exist_ok=True)
            
            # Process configuration data before saving
            processed_config = config_data.copy()
            
            # Extract the actual config if nested
            config_to_process = processed_config.get('config', processed_config)
            
            # Use traffic_scale directly from frontend (no conversion needed)
            if 'traffic_scale' in config_to_process:
                traffic_scale = config_to_process['traffic_scale']
                config_to_process['sumo_traffic_scale'] = traffic_scale
                print(f"DEBUG: Using traffic_scale {traffic_scale} directly as sumo_traffic_scale")
            
            # Legacy support for old terminology (backward compatibility)
            elif 'trafficIntensity' in config_to_process:
                config_to_process['sumo_traffic_scale'] = config_to_process['trafficIntensity']
                print(f"DEBUG: Mapped legacy trafficIntensity {config_to_process['trafficIntensity']} to sumo_traffic_scale")
            elif 'vehicles_per_minute' in config_to_process:
                # Convert legacy vehicles_per_minute to traffic scale
                baseline_vehicles_per_minute = 10.0
                vehicles_per_minute = config_to_process['vehicles_per_minute']
                traffic_scale = vehicles_per_minute / baseline_vehicles_per_minute
                config_to_process['sumo_traffic_scale'] = traffic_scale
                print(f"DEBUG: Converted legacy vehicles_per_minute {vehicles_per_minute} to sumo_traffic_scale {traffic_scale} (baseline: {baseline_vehicles_per_minute})")
            else:
                # Default traffic scale if not provided
                config_to_process['sumo_traffic_scale'] = 1.0
                print(f"DEBUG: Using default sumo_traffic_scale 1.0")
            
            # Update the processed config with the modified config
            if 'config' in processed_config:
                processed_config['config'] = config_to_process
            
            # Save to database if available
            if self.db_service:
                # Create session in database
                self.db_service.create_session(
                    session_id=session_id,
                    session_path=str(session_config_dir)
                )
                
                # Save configuration to database
                success = self.db_service.save_configuration(session_id, processed_config)
                if not success:
                    print(f"Warning: Failed to save configuration to database for session {session_id}")
            
            # Also save to file as backup (maintain backward compatibility)
            config_file = session_config_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(processed_config, f, indent=2)
            
            return {
                "success": True,
                "message": "Configuration saved successfully",
                "config_path": str(config_file),
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to save configuration: {str(e)}"
            }
    
    def get_available_networks(self) -> Dict[str, Any]:
        """
        Get list of available SUMO networks including OSM scenarios
        
        Returns:
            Dictionary containing available networks
        """
        try:
            networks = []
            
            # Scan for both compressed and uncompressed network files
            network_patterns = ["**/*.net.xml", "**/*.net.xml.gz"]
            for pattern in network_patterns:
                for network_file in self.base_networks_dir.glob(pattern):
                    try:
                        # Parse network file to get basic info (handle compression)
                        if network_file.suffix == '.gz':
                            import gzip
                            with gzip.open(network_file, 'rt', encoding='utf-8') as f:
                                content = f.read()
                            root = ET.fromstring(content)
                        else:
                            tree = ET.parse(network_file)
                            root = tree.getroot()
                        
                        # Count edges and junctions
                        edges = len([e for e in root.findall(".//edge") if not e.get('function')])
                        junctions = len(root.findall('.//junction[@type!="internal"]'))
                        lanes = len(root.findall(".//lane"))
                        
                        # Get file info
                        stat = network_file.stat()
                        
                        # Check if this is an OSM scenario
                        network_dir = network_file.parent
                        metadata_file = network_dir / "metadata.json"
                        is_osm_scenario = False
                        vehicle_types = []
                        osm_metadata = {}
                        
                        if metadata_file.exists():
                            try:
                                with open(metadata_file, 'r') as f:
                                    osm_metadata = json.load(f)
                                    is_osm_scenario = osm_metadata.get('is_osm_scenario', False)
                                    vehicle_types = osm_metadata.get('vehicle_types', [])
                            except Exception:
                                pass
                        
                        # Check for OSM route files (legacy detection)
                        if not is_osm_scenario:
                            osm_routes = self._find_osm_route_files(network_file.stem)
                            has_osm_routes = len(osm_routes) > 0
                            if has_osm_routes:
                                vehicle_types = self._extract_vehicle_types_from_routes(osm_routes)
                        else:
                            has_osm_routes = True
                        
                        # Build description
                        description = f"SUMO network with {edges} edges and {junctions} junctions"
                        if is_osm_scenario:
                            description = f"OSM scenario: {description}"
                        
                        # Generate clean network ID by removing all network file extensions
                        clean_id = network_file.name.replace('.net.xml.gz', '').replace('.net.xml', '')
                        
                        network_info = {
                            "id": clean_id,
                            "name": clean_id.replace("_", " ").title(),
                            "path": str(network_file),
                            "description": description,
                            "edges": edges,
                            "junctions": junctions,
                            "lanes": lanes,
                            "fileSize": f"{stat.st_size / 1024:.1f} KB",
                            "lastModified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                            "isOsmScenario": is_osm_scenario,
                            "hasRealisticTraffic": is_osm_scenario,
                            "vehicleTypes": vehicle_types,
                            "routeSource": "OSM Web Wizard" if has_osm_routes else "Generated",
                            "metadata": osm_metadata
                        }
                        
                        networks.append(network_info)
                        
                    except Exception as e:
                        print(f"Error parsing network file {network_file}: {e}")
                        continue
            
            return {
                "success": True,
                "networks": networks,
                "count": len(networks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load networks: {str(e)}",
                "networks": []
            }
    
    def _extract_vehicle_types_from_routes(self, route_files: List[Path]) -> List[str]:
        """
        Extract vehicle types from route file names
        
        Args:
            route_files: List of route file paths
            
        Returns:
            List of vehicle types found
        """
        vehicle_types = []
        vehicle_patterns = ['passenger', 'bus', 'truck', 'motorcycle']
        
        for route_file in route_files:
            for vehicle_type in vehicle_patterns:
                if vehicle_type in route_file.name.lower():
                    if vehicle_type not in vehicle_types:
                        vehicle_types.append(vehicle_type)
        
        return vehicle_types
    
    def setup_session_network(self, session_id: str, network_id: str, 
                            network_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy network to session folder and apply configurations, with OSM scenario support
        
        Args:
            session_id: Session identifier
            network_id: Network identifier
            network_path: Path to original network file or "generated" for programmatic creation
            config: Configuration to apply
            
        Returns:
            Result dictionary with session path
        """
        try:
            session_dir = self.sessions_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Check if we need to generate network programmatically or copy existing
            if network_path == "generated":
                # Generate network based on config (always uncompressed for generated networks)
                network_dest = session_dir / f"{network_id}.net.xml"
                self._generate_network_programmatically(network_dest, config)
                is_osm_scenario = False
            else:
                # Copy existing network files to session directory
                network_source = Path(network_path)
                
                # Determine correct destination path based on source compression
                if network_source.suffix == '.gz':
                    network_dest = session_dir / f"{network_id}.net.xml.gz"
                else:
                    network_dest = session_dir / f"{network_id}.net.xml"
                network_source_dir = network_source.parent
                
                # Check if this is an OSM scenario
                metadata_file = network_source_dir / "metadata.json"
                is_osm_scenario = False
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            is_osm_scenario = metadata.get('is_osm_scenario', False)
                    except Exception:
                        pass
                
                if is_osm_scenario:
                    # Handle OSM scenario copying
                    self._copy_osm_scenario_to_session(network_source_dir, session_dir, network_id, config)
                else:
                    # Copy traditional network
                    shutil.copy2(network_source, network_dest)
                    # Apply configurations to the copied network
                    self._apply_network_modifications(network_dest, config)
            
            # Generate additional SUMO files (if not OSM scenario)
            if not is_osm_scenario:
                self._generate_route_file(session_dir, network_id, config)
                self._generate_sumo_config(session_dir, network_id, config)
            
            # Create session metadata
            session_metadata = {
                "session_id": session_id,
                "network_id": network_id,
                "network_path": str(network_dest),
                "is_osm_scenario": is_osm_scenario,
                "config_applied": True,
                "created_at": datetime.now().isoformat(),
                "files": {
                    "network": network_dest.name,
                    "routes": f"{network_id}.rou.xml" if not is_osm_scenario else "routes/",
                    "config": f"{network_id}.sumocfg",
                    "additional": f"{network_id}.add.xml"
                }
            }
            
            metadata_file = session_dir / "session_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(session_metadata, f, indent=2)
            
            # Update database with session and network information
            if self.db_service:
                # Update session with network information
                self.db_service.update_session_status(
                    session_id, 
                    'network_configured',
                    network_id=network_id,
                    network_name=network_id,  # Can be improved to get actual network name
                    session_path=str(session_dir)
                )
                
                # Save/update network metadata
                network_data = {
                    'id': network_id,
                    'name': network_id,  # Can be improved
                    'path': str(network_dest),
                    'is_osm_scenario': is_osm_scenario
                }
                self.db_service.save_network(network_data)
                self.db_service.update_network_last_used(network_id)
            
            return {
                "success": True,
                "message": "Network setup completed",
                "sessionPath": str(session_dir),
                "metadata": session_metadata,
                "isOsmScenario": is_osm_scenario
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to setup network: {str(e)}"
            }
    
    def _copy_osm_scenario_to_session(self, source_dir: Path, session_dir: Path, 
                                    network_id: str, config: Dict[str, Any]):
        """
        Copy OSM scenario files to session directory and apply configuration
        
        Args:
            source_dir: Source OSM scenario directory
            session_dir: Target session directory
            network_id: Network identifier for file naming
            config: Configuration to apply
        """
        try:
            # Copy main network file (preserve compression)
            network_files = glob_network_files(source_dir)
            if network_files:
                network_source = network_files[0]
                # Preserve the original file extension (compressed or uncompressed)
                if network_source.suffix == '.gz':
                    network_dest = session_dir / f"{network_id}.net.xml.gz"
                else:
                    network_dest = session_dir / f"{network_id}.net.xml"
                shutil.copy2(network_source, network_dest)
            
            # Copy routes directory with vehicle filtering FIRST
            routes_source_dir = source_dir / "routes"
            if routes_source_dir.exists():
                routes_dest_dir = session_dir / "routes"
                routes_dest_dir.mkdir(exist_ok=True)
                
                # Apply vehicle type filtering
                enabled_vehicles = config.get('enabledVehicles', ['passenger', 'bus', 'truck', 'motorcycle'])
                
                # Safeguard: ensure at least one vehicle type is enabled
                if not enabled_vehicles:
                    print("WARNING: No vehicle types enabled, defaulting to passenger cars")
                    enabled_vehicles = ['passenger']
                
                print(f"Enabled vehicle types: {enabled_vehicles}")
                self._copy_and_filter_routes(routes_source_dir, routes_dest_dir, enabled_vehicles, config, is_osm_scenario=True)
            
            # Copy SUMO config file AFTER route files are in place
            config_files = list(source_dir.glob("*.sumocfg"))
            if config_files:
                config_source = config_files[0]
                config_dest = session_dir / f"{network_id}.sumocfg"
                self._process_osm_config_file(config_source, config_dest, network_id, config)
            
            # Copy additional files (views, edge data, etc.)
            additional_patterns = ['*.osm_view.xml', '*.view.xml', '*.add.xml', '*output_add.xml', 'edgeData*', 'stats*', 'tripinfos*']
            for pattern in additional_patterns:
                for source_file in source_dir.glob(pattern):
                    if source_file.is_file():
                        # Don't rename these files - keep original names since config expects them
                        dest_file = session_dir / source_file.name
                        shutil.copy2(source_file, dest_file)
            
            # Generate or modify additional file for traffic light configuration
            self._process_osm_additional_file(session_dir, network_id, config)
        
        except Exception as e:
            print(f"Error copying OSM scenario: {e}")
            raise
    
    def _process_osm_config_file(self, source_config: Path, dest_config: Path, 
                               network_id: str, config: Dict[str, Any]):
        """
        Process OSM SUMO config file with updated paths and settings
        
        Args:
            source_config: Source configuration file
            dest_config: Destination configuration file
            network_id: Network identifier
            config: User configuration
        """
        try:
            tree = ET.parse(source_config)
            root = tree.getroot()
            
            # Update network file reference (handle both compressed and uncompressed)
            net_input = root.find('.//net-file')
            if net_input is not None:
                # Find the actual copied network file (compressed or uncompressed)
                network_files = glob_network_files(dest_config.parent)
                if network_files:
                    # Use the first (and should be only) network file found
                    actual_network_filename = network_files[0].name
                    net_input.set('value', actual_network_filename)
                    print(f"Set network file reference to: {actual_network_filename}")
                else:
                    # Fallback to uncompressed format
                    net_input.set('value', f"{network_id}.net.xml")
            
            # Update route files based on enabled vehicles - prioritize enhanced.rou.xml, then .trips.xml for realistic patterns
            enabled_vehicles = config.get('enabledVehicles', ['passenger', 'bus', 'truck', 'motorcycle'])
            route_files = []
            
            # Check for enhanced route file first (best option with our improvements)
            enhanced_route_file = "routes/osm.enhanced.rou.xml"
            enhanced_route_path = dest_config.parent / enhanced_route_file
            
            if enhanced_route_path.exists():
                route_files.append(enhanced_route_file)
                print(f"🌟 Including enhanced route file in config: {enhanced_route_file}")
            else:
                # Fall back to individual vehicle type files
                for vehicle_type in enabled_vehicles:
                    # Check for trips file first (better realism), then route file as fallback
                    trips_file = f"routes/osm.{vehicle_type}.trips.xml"
                    route_file = f"routes/osm.{vehicle_type}.rou.xml"
                    
                    trips_path = dest_config.parent / trips_file
                    route_path = dest_config.parent / route_file
                    
                    if trips_path.exists():
                        route_files.append(trips_file)
                        print(f"Including trips file in config: {trips_file}")
                    elif route_path.exists():
                        route_files.append(route_file)
                        print(f"Including route file in config: {route_file}")
                    else:
                        print(f"No route or trips file found for {vehicle_type}, skipping")
            
            route_input = root.find('.//route-files')
            if route_input is not None:
                if route_files:
                    route_input.set('value', ','.join(route_files))
                    print(f"Updated route files in config: {route_files}")
                else:
                    print("WARNING: No route files found for enabled vehicles!")
                    # Remove the route-files element entirely since no routes exist
                    parent = root.find('.//input')
                    if parent is not None and route_input is not None:
                        parent.remove(route_input)
            
            # Update simulation time settings - map from frontend config
            begin_time = config.get('sumo_begin', config.get('beginTime', 0))
            end_time = config.get('sumo_end', config.get('endTime', 3600))
            step_length = config.get('sumo_step_length', config.get('stepLength', 1.0))
            
            print(f"Time settings: begin={begin_time}, end={end_time}, step-length={step_length}")
            
            # Find or create time section
            time_section = root.find('.//time')
            if time_section is None:
                # Create time section if it doesn't exist
                time_section = ET.SubElement(root, 'time')
            
            # Update or create time elements
            begin_elem = time_section.find('begin')
            if begin_elem is None:
                begin_elem = ET.SubElement(time_section, 'begin')
            begin_elem.set('value', str(begin_time))
            
            end_elem = time_section.find('end')
            if end_elem is None:
                end_elem = ET.SubElement(time_section, 'end')
            end_elem.set('value', str(end_time))
            
            step_elem = time_section.find('step-length')
            if step_elem is None:
                step_elem = ET.SubElement(time_section, 'step-length')
            step_elem.set('value', str(step_length))
            
            print(f"Updated OSM config: begin={begin_time}s, end={end_time}s, step-length={step_length}s")
            
            # Save updated config
            tree.write(dest_config, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"Warning: Could not process OSM config file: {e}")
            # Fallback: just copy the file
            shutil.copy2(source_config, dest_config)

    def _process_osm_additional_file(self, session_dir: Path, network_id: str, config: Dict[str, Any]):
        """
        Generate or modify additional file for OSM scenarios to include traffic light configuration
        
        Args:
            session_dir: Session directory containing OSM scenario files
            network_id: Network identifier
            config: Configuration parameters including traffic control settings
        """
        try:
            # Look for existing additional files
            additional_files = list(session_dir.glob("*.add.xml")) + list(session_dir.glob("*output.add.xml"))
            
            traffic_control_config = config.get('trafficControl')
            if not traffic_control_config:
                print("DEBUG: No traffic control configuration found")
                return
            
            # Generate traffic light configurations
            network_file = find_network_file(session_dir, network_id)
            if not network_file or not network_file.exists():
                print(f"DEBUG: Network file not found for network_id: {network_id}")
                return
            
            tl_configs = self._generate_traffic_light_configs(network_file, traffic_control_config)
            if not tl_configs:
                print("DEBUG: No traffic light configurations generated")
                return
            
            # Create or modify additional file
            if additional_files:
                # Modify existing additional file
                additional_file = additional_files[0]
                self._inject_traffic_lights_into_additional_file(additional_file, tl_configs)
            else:
                # Create new additional file
                additional_file = session_dir / "traffic_lights.add.xml"
                self._create_traffic_light_additional_file(additional_file, tl_configs)
                
                # Update SUMO config to include the new additional file
                self._update_osm_config_with_additional_file(session_dir, network_id, "traffic_lights.add.xml")
            
        except Exception as e:
            print(f"ERROR: Failed to process OSM additional file: {e}")

    def _inject_traffic_lights_into_additional_file(self, additional_file: Path, tl_configs: str):
        """
        Inject traffic light configurations into existing additional file
        
        Args:
            additional_file: Path to existing additional file
            tl_configs: Traffic light XML configurations to inject
        """
        try:
            tree = ET.parse(additional_file)
            root = tree.getroot()
            
            # Create a temporary element to parse the traffic light XML
            temp_xml = f"<temp>{tl_configs}</temp>"
            temp_tree = ET.fromstring(temp_xml)
            
            # Append all traffic light elements to the root
            for element in temp_tree:
                root.append(element)
            
            # Write back to file
            tree.write(additional_file, encoding='UTF-8', xml_declaration=True)
            print(f"DEBUG: Injected traffic light configurations into {additional_file}")
            
        except ET.ParseError as e:
            print(f"ERROR: Failed to parse additional file {additional_file}: {e}")
        except Exception as e:
            print(f"ERROR: Failed to inject traffic lights into additional file: {e}")

    def _create_traffic_light_additional_file(self, additional_file: Path, tl_configs: str):
        """
        Create new additional file with traffic light configurations
        
        Args:
            additional_file: Path to new additional file
            tl_configs: Traffic light XML configurations
        """
        additional_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- Traffic Light Configurations -->
    {tl_configs}

</additional>'''
        
        with open(additional_file, 'w') as f:
            f.write(additional_content)
        
        print(f"DEBUG: Created traffic light additional file: {additional_file}")

    def _update_osm_config_with_additional_file(self, session_dir: Path, network_id: str, additional_filename: str):
        """
        Update OSM SUMO configuration to include new additional file
        
        Args:
            session_dir: Session directory
            network_id: Network identifier
            additional_filename: Name of additional file to include
        """
        try:
            config_file = session_dir / f"{network_id}.sumocfg"
            if not config_file.exists():
                print(f"WARNING: SUMO config file not found: {config_file}")
                return
            
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Find or create input section
            input_section = root.find('.//input')
            if input_section is None:
                input_section = ET.SubElement(root, 'input')
            
            # Add additional files reference
            additional_elem = input_section.find('additional-files')
            if additional_elem is None:
                additional_elem = ET.SubElement(input_section, 'additional-files')
                additional_elem.set('value', additional_filename)
            else:
                # Append to existing additional files
                current_value = additional_elem.get('value', '')
                if current_value:
                    additional_elem.set('value', f"{current_value},{additional_filename}")
                else:
                    additional_elem.set('value', additional_filename)
            
            # Write back to config
            tree.write(config_file, encoding='UTF-8', xml_declaration=True)
            print(f"DEBUG: Updated SUMO config to include {additional_filename}")
            
        except Exception as e:
            print(f"ERROR: Failed to update OSM config with additional file: {e}")
    
    def _copy_and_filter_routes(self, source_dir: Path, dest_dir: Path, 
                              enabled_vehicles: List[str], config: Dict[str, Any], is_osm_scenario: bool = None):
        """
        Copy route files and apply vehicle type filtering, preserving OSM Web Wizard route variety.
        Prioritizes .trips.xml files for realistic traffic patterns.
        
        Args:
            source_dir: Source routes directory
            dest_dir: Destination routes directory
            enabled_vehicles: List of enabled vehicle types
            config: Configuration parameters
            
        Note:
            This method now prioritizes .trips.xml files over .rou.xml files to maintain
            the original OSM Web Wizard timing patterns and realistic vehicle behavior.
        """
        try:
            # Check if this is an OSM scenario (has pre-generated varied routes)
            if is_osm_scenario is None:
                # Fall back to metadata file detection if not explicitly provided
                session_dir = dest_dir.parent
                metadata_file = session_dir / "session_metadata.json"  # Fixed: correct filename
                is_osm_scenario = False
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            is_osm_scenario = metadata.get('is_osm_scenario', False)
                    except:
                        pass
            
            # For OSM scenarios, preserve the original route variety instead of generating new routes
            if is_osm_scenario:
                print("🌟 Preserving OSM Web Wizard route variety...")
                self._preserve_osm_route_variety(source_dir, dest_dir, enabled_vehicles, config)
                return
            else:
                print("DEBUG: Not treated as OSM scenario - using fallback route generation")
            
            # For non-OSM scenarios, check if we should generate diverse routes
            generate_diverse = config.get('generate_diverse_routes', True)  # Default to True for better analytics
            
            if generate_diverse and 'passenger' in enabled_vehicles:
                print("🎯 Generating diverse routes for better traffic analytics...")
                
                # Find network file for route generation
                network_files = glob_network_files(session_dir)
                
                if network_files:
                    network_file = network_files[0]
                    # Extract network_id properly (handle .net.xml.gz extension)
                    network_id = network_file.name.replace('.net.xml.gz', '').replace('.net.xml', '')
                    
                    # Generate diverse routes for passenger vehicles
                    self._generate_diverse_osm_routes(session_dir, network_id, config, enabled_vehicles)
                    return
                else:
                    print("⚠️  Network file not found, falling back to copying existing routes")
            
            # Fallback: Copy existing routes (original behavior)
            traffic_density = config.get('trafficDensity', 1.0)
            
            # Copy and filter route files - only copy enabled vehicle types
            for route_file in source_dir.glob("*.rou.xml"):
                # Determine vehicle type from filename
                vehicle_type = None
                for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                    if vtype in route_file.name.lower():
                        vehicle_type = vtype
                        break
                
                if vehicle_type and vehicle_type in enabled_vehicles:
                    dest_file = dest_dir / route_file.name
                    if traffic_density != 1.0:
                        # Apply traffic density scaling
                        self._scale_route_file(route_file, dest_file, traffic_density)
                    else:
                        # Just copy the file
                        shutil.copy2(route_file, dest_file)
                    print(f"Copied route file for enabled vehicle type: {vehicle_type}")
                else:
                    # Skip disabled vehicle types - don't create empty files
                    if vehicle_type:
                        print(f"Skipped route file for disabled vehicle type: {vehicle_type}")
            
            # Copy trip files as well - only for enabled vehicles (support compressed and uncompressed)
            trip_files = list(source_dir.glob("*.trips.xml")) + list(source_dir.glob("*.trips.xml.gz"))
            for trip_file in trip_files:
                vehicle_type = None
                for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                    if vtype in trip_file.name.lower():
                        vehicle_type = vtype
                        break
                
                if vehicle_type and vehicle_type in enabled_vehicles:
                    if trip_file.name.endswith('.gz'):
                        # Decompress .gz trip files
                        import gzip
                        dest_file = dest_dir / trip_file.name.replace('.gz', '')
                        try:
                            with gzip.open(trip_file, 'rt', encoding='utf-8') as f_in:
                                with open(dest_file, 'w', encoding='utf-8') as f_out:
                                    f_out.write(f_in.read())
                            print(f"Decompressed and copied trip file for enabled vehicle type: {vehicle_type}")
                        except Exception as e:
                            print(f"Failed to decompress {trip_file}: {e}, copying as-is")
                            dest_file = dest_dir / trip_file.name
                            shutil.copy2(trip_file, dest_file)
                    else:
                        dest_file = dest_dir / trip_file.name
                        shutil.copy2(trip_file, dest_file)
                        print(f"Copied trip file for enabled vehicle type: {vehicle_type}")
        
        except Exception as e:
            print(f"Error filtering routes: {e}")
            # Fallback: copy all files
            for file in source_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest_dir / file.name)
    
    def _generate_diverse_osm_routes(self, session_dir: Path, network_id: str, config: Dict[str, Any], enabled_vehicles: List[str]):
        """
        Generate diverse routes for OSM scenarios instead of using static routes
        
        Args:
            session_dir: Session directory containing network file
            network_id: Network identifier
            config: Configuration parameters
            enabled_vehicles: List of enabled vehicle types
        """
        try:
            network_file = find_network_file(session_dir, network_id)
            if not network_file:
                raise FileNotFoundError(f"Network file not found for network_id: {network_id}")
            routes_dir = session_dir / "routes"
            routes_dir.mkdir(exist_ok=True)
            
            # Calculate vehicle count from config
            vehicle_count = config.get('vehicles', 20)
            traffic_scale = config.get('sumo_traffic_scale', 1.0)
            simulation_time = config.get('simulationTime', 300)
            
            # Scale vehicle count based on simulation time and traffic scale
            adjusted_count = max(int(vehicle_count * traffic_scale * (simulation_time / 300)), 5)
            
            print(f"🚗 Generating {adjusted_count} diverse vehicles for {simulation_time}s simulation")
            
            # Generate diverse routes for each enabled vehicle type
            for vehicle_type in enabled_vehicles:
                route_file = routes_dir / f"osm.{vehicle_type}.rou.xml"
                
                try:
                    # Use enhanced randomTrips.py for this vehicle type
                    import subprocess
                    import os
                    
                    sumo_home = os.environ.get('SUMO_HOME', 'C:\\Program Files (x86)\\Eclipse\\Sumo')
                    randomtrips_script = os.path.join(sumo_home, 'tools', 'randomTrips.py')
                    
                    if not os.path.exists(randomtrips_script):
                        print(f"⚠️  randomTrips.py not found, falling back to simple generation for {vehicle_type}")
                        self._create_simple_osm_route_file(route_file, vehicle_type, adjusted_count)
                        continue
                    
                    # Enhanced parameters for realistic traffic
                    # Convert paths to absolute strings to avoid subprocess path issues
                    network_file_str = str(network_file.resolve())
                    route_file_str = str(route_file.resolve())
                    
                    cmd = [
                        "python", randomtrips_script,
                        "-n", network_file_str,
                        "-o", route_file_str,
                        "--route-file", route_file_str,
                        "--period", str(max(simulation_time / adjusted_count, 1.0)),  # Distribute over simulation time
                        "--fringe-factor", "2.0",  # Reduce border concentration
                        "--intermediate", "1",  # Add waypoints for longer routes
                        "--min-distance", "200",  # Minimum trip distance
                        "--max-distance", "2000",  # Maximum trip distance
                        "--speed-exponent", "1.5",  # Weight by road importance
                        "--lanes",  # Consider lane count
                        "--random-factor", "0.3",  # Add randomness
                        "--fringe-start-attributes", f'departSpeed="max" type="veh_{vehicle_type}"',
                        "--trip-attributes", f'departLane="best" type="veh_{vehicle_type}"',
                        "--validate",  # Ensure routes are valid
                        "--begin", "0",
                        "--end", str(simulation_time),
                        "--seed", str(hash(network_id + vehicle_type) % 1000)  # Reproducible but different per type
                    ]
                    
                    # Add vehicle class parameter if supported
                    if vehicle_type != 'passenger':
                        cmd.extend(["--vehicle-class", vehicle_type])
                    
                    print(f"🔧 Generating diverse routes for {vehicle_type}...")
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=session_dir, timeout=30)
                    
                    if result.returncode == 0:
                        print(f"✅ Generated diverse {vehicle_type} routes: {route_file.name}")
                        
                        # Add vehicle type definition to the route file
                        self._add_vehicle_type_to_route_file(route_file, vehicle_type)
                    else:
                        print(f"⚠️  randomTrips failed for {vehicle_type}: {result.stderr}")
                        print(f"   Falling back to simple generation...")
                        self._create_simple_osm_route_file(route_file, vehicle_type, adjusted_count)
                        
                except Exception as e:
                    print(f"⚠️  Error generating diverse routes for {vehicle_type}: {e}")
                    print(f"   Creating simple fallback routes...")
                    self._create_simple_osm_route_file(route_file, vehicle_type, adjusted_count)
            
            print("🎯 Diverse route generation completed!")
            
        except Exception as e:
            print(f"❌ Error in diverse OSM route generation: {e}")
            raise
    
    def _create_simple_osm_route_file(self, route_file: Path, vehicle_type: str, vehicle_count: int):
        """Create a simple route file for OSM scenarios when randomTrips fails"""
        
        # Get network edges from the network file
        network_dir = route_file.parent.parent
        network_id = network_dir.name.split('_')[0]
        network_file = find_network_file(network_dir, network_id)
        
        if not network_file:
            # Fallback: find any network file in the directory
            network_files = glob_network_files(network_dir)
            if network_files:
                network_file = network_files[0]
        
        edge_ids = self._extract_edge_ids(network_file) if network_file.exists() else []
        
        if not edge_ids:
            print(f"No edges found for {vehicle_type}, creating minimal route file")
            edge_ids = ['dummy_edge']
        
        # Create diverse routes using available edges
        route_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <vType id="veh_{vehicle_type}" vClass="{vehicle_type}" color="yellow"/>
'''
        
        # Create routes with some variety
        used_edges = edge_ids[:min(len(edge_ids), 20)]  # Use up to 20 different edges
        
        for i in range(vehicle_count):
            if len(used_edges) >= 2:
                # Create routes between different edges
                from_edge = used_edges[i % len(used_edges)]
                to_edge = used_edges[(i + len(used_edges)//2) % len(used_edges)]
                
                depart_time = (i * 300) / vehicle_count  # Distribute over 5 minutes
                
                route_content += f'''    <vehicle id="{vehicle_type}_{i}" type="veh_{vehicle_type}" depart="{depart_time:.1f}" departLane="best" departSpeed="max">
        <route edges="{from_edge} {to_edge}"/>
    </vehicle>
'''
        
        route_content += '</routes>'
        
        with open(route_file, 'w', encoding='utf-8') as f:
            f.write(route_content)
        
        print(f"✅ Created simple diverse routes for {vehicle_type}")
    
    def _add_vehicle_type_to_route_file(self, route_file: Path, vehicle_type: str):
        """Add vehicle type definition to route file if missing"""
        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if vehicle type already exists
            if f'veh_{vehicle_type}' in content:
                return  # Already has vehicle type
            
            # Add vehicle type definition
            vtype_colors = {
                'passenger': 'yellow',
                'bus': 'blue', 
                'truck': 'red',
                'motorcycle': 'green'
            }
            
            color = vtype_colors.get(vehicle_type, 'gray')
            vtype_def = f'    <vType id="veh_{vehicle_type}" vClass="{vehicle_type}" color="{color}"/>\n'
            
            # Insert after the opening routes tag
            content = content.replace('<routes xmlns:xsi', f'{vtype_def}<routes xmlns:xsi')
            
            with open(route_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Warning: Could not add vehicle type to {route_file}: {e}")
    
    def _scale_route_file(self, source_file: Path, dest_file: Path, scale_factor: float):
        """
        Scale traffic density in route file by modifying departure times
        
        Args:
            source_file: Source route file
            dest_file: Destination route file
            scale_factor: Traffic density scaling factor
        """
        try:
            tree = ET.parse(source_file)
            root = tree.getroot()
            
            # Scale vehicle departures
            for vehicle in root.findall('.//vehicle'):
                depart = vehicle.get('depart')
                if depart and depart != 'triggered':
                    try:
                        depart_time = float(depart)
                        # Scale departure time (reduce frequency if scale < 1.0)
                        scaled_time = depart_time / scale_factor
                        vehicle.set('depart', f"{scaled_time:.2f}")
                    except ValueError:
                        pass  # Skip non-numeric departures
            
            # Save scaled file
            tree.write(dest_file, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"Error scaling route file: {e}")
            # Fallback: just copy the file
            shutil.copy2(source_file, dest_file)
    
    def _create_disabled_route_file(self, dest_file: Path, source_file: Path):
        """
        Create a minimal route file for disabled vehicle types
        
        Args:
            dest_file: Destination file path
            source_file: Source file for reference
        """
        try:
            # Create minimal XML with comments
            content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Vehicle type disabled by user configuration -->
<!-- Original file: {source_file.name} -->
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <!-- No routes - vehicle type disabled -->
</routes>
'''
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        except Exception as e:
            print(f"Error creating disabled route file: {e}")
    
    def _preserve_osm_route_variety(self, source_dir: Path, dest_dir: Path, 
                                   enabled_vehicles: List[str], config: Dict[str, Any]):
        """
        Preserve the original route variety from OSM Web Wizard scenarios while applying filtering
        
        Args:
            source_dir: Source routes directory
            dest_dir: Destination routes directory  
            enabled_vehicles: List of enabled vehicle types
            config: Configuration parameters
        """
        try:
            traffic_density = config.get('trafficDensity', 1.0)
            vehicle_count_override = config.get('vehicles')
            
            print(f"📊 Processing OSM routes for {len(enabled_vehicles)} enabled vehicle types...")
            
            # PRIORITY 1: Check for enhanced route file first (best option with our improvements)
            enhanced_route_file = source_dir / "osm.enhanced.rou.xml"
            if enhanced_route_file.exists():
                print("🌟 Found enhanced route file - using improved routes with better distribution!")
                dest_file = dest_dir / "osm.enhanced.rou.xml"
                
                if traffic_density != 1.0:
                    self._scale_route_file(enhanced_route_file, dest_file, traffic_density)
                else:
                    shutil.copy2(enhanced_route_file, dest_file)
                
                print(f"✅ Copied enhanced route file with all vehicle types: {dest_file.name}")
                return  # We're done - enhanced route file contains everything
            else:
                print("DEBUG: Enhanced route file not found, falling back to trip files")
            
            # FALLBACK: Process trip files first for enabled vehicle types (better realism) - support compressed files
            copied_types = set()
            trip_files = list(source_dir.glob("*.trips.xml")) + list(source_dir.glob("*.trips.xml.gz"))
            for trip_file in trip_files:
                # Determine vehicle type from filename
                vehicle_type = None
                for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                    if vtype in trip_file.name.lower():
                        vehicle_type = vtype
                        break
                
                if vehicle_type and vehicle_type in enabled_vehicles:
                    # Handle compressed trip files - decompress during copy
                    if trip_file.name.endswith('.gz'):
                        import gzip
                        dest_file = dest_dir / trip_file.name.replace('.gz', '')
                        try:
                            with gzip.open(trip_file, 'rt', encoding='utf-8') as f_in:
                                if traffic_density != 1.0:
                                    # Create temporary uncompressed file for scaling
                                    temp_file = dest_file.with_suffix('.temp.xml')
                                    temp_file.write_text(f_in.read(), encoding='utf-8')
                                    self._scale_route_file(temp_file, dest_file, traffic_density)
                                    temp_file.unlink()
                                else:
                                    with open(dest_file, 'w', encoding='utf-8') as f_out:
                                        f_out.write(f_in.read())
                            print(f"✅ Decompressed and preserved {vehicle_type} trip file (realistic patterns): {dest_file.name}")
                            
                            # Enhance trip file with colors and attributes
                            try:
                                tree = ET.parse(dest_file)
                                root = tree.getroot()
                                self._enhance_osm_vehicle_definitions(root, vehicle_type)
                                tree.write(dest_file, encoding='utf-8', xml_declaration=True)
                            except Exception as e:
                                print(f"  ⚠️  Could not enhance {vehicle_type} trip file: {e}")
                                
                        except Exception as e:
                            print(f"Failed to decompress {trip_file}: {e}, copying as-is")
                            dest_file = dest_dir / trip_file.name
                            shutil.copy2(trip_file, dest_file)
                    else:
                        dest_file = dest_dir / trip_file.name
                        # For trip files, preserve them directly for realistic patterns
                        if traffic_density != 1.0:
                            self._scale_route_file(trip_file, dest_file, traffic_density)
                        else:
                            shutil.copy2(trip_file, dest_file)
                        print(f"✅ Preserved {vehicle_type} trip file (realistic patterns): {dest_file.name}")
                    
                    # Enhance trip file with colors and attributes
                    try:
                        tree = ET.parse(dest_file)
                        root = tree.getroot()
                        self._enhance_osm_vehicle_definitions(root, vehicle_type)
                        tree.write(dest_file, encoding='utf-8', xml_declaration=True)
                    except Exception as e:
                        print(f"  ⚠️  Could not enhance {vehicle_type} trip file: {e}")
                    
                    copied_types.add(vehicle_type)
                elif vehicle_type:
                    print(f"⏭️  Skipped disabled vehicle type: {vehicle_type}")
            
            # Process route files as fallback for types not covered by trip files
            for route_file in source_dir.glob("*.rou.xml"):
                # Determine vehicle type from filename
                vehicle_type = None
                for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                    if vtype in route_file.name.lower():
                        vehicle_type = vtype
                        break
                
                if vehicle_type and vehicle_type in enabled_vehicles and vehicle_type not in copied_types:
                    dest_file = dest_dir / route_file.name
                    
                    # Preserve original route variety with intelligent filtering
                    self._filter_and_enhance_osm_routes(route_file, dest_file, vehicle_type, 
                                                       traffic_density, vehicle_count_override)
                    
                    print(f"✅ Preserved {vehicle_type} route variety: {route_file.name}")
                elif vehicle_type:
                    print(f"⏭️  Skipped disabled vehicle type: {vehicle_type}")
                        
        except Exception as e:
            print(f"❌ Error preserving OSM route variety: {e}")
            # Fallback to basic copying
            self._copy_routes_basic(source_dir, dest_dir, enabled_vehicles, config)
    
    def _filter_and_enhance_osm_routes(self, source_file: Path, dest_file: Path, 
                                      vehicle_type: str, traffic_density: float, 
                                      vehicle_count_override: Optional[int]):
        """
        Filter OSM routes while preserving variety and applying enhancements
        
        Args:
            source_file: Source route file
            dest_file: Destination route file
            vehicle_type: Vehicle type being processed
            traffic_density: Traffic scaling factor
            vehicle_count_override: Optional vehicle count override
        """
        try:
            tree = ET.parse(source_file)
            root = tree.getroot()
            
            # Collect all vehicles and analyze variety
            vehicles = root.findall('.//vehicle')
            original_count = len(vehicles)
            
            if original_count == 0:
                print(f"⚠️  No vehicles found in {source_file.name}")
                shutil.copy2(source_file, dest_file)
                return
            
            # Apply vehicle count filtering if specified
            target_count = original_count
            if vehicle_count_override and vehicle_count_override > 0:
                target_count = min(vehicle_count_override, original_count)
            
            # Apply traffic density scaling
            if traffic_density != 1.0:
                target_count = max(1, int(target_count * traffic_density))
            
            # Select vehicles to preserve variety
            if target_count < original_count:
                # Intelligently sample vehicles to preserve variety
                selected_vehicles = self._select_diverse_vehicles(vehicles, target_count)
                
                # Remove unselected vehicles
                for vehicle in vehicles:
                    if vehicle not in selected_vehicles:
                        root.remove(vehicle)
                        
                print(f"📉 Filtered {vehicle_type}: {original_count} → {len(selected_vehicles)} vehicles")
            else:
                print(f"📊 Preserved all {original_count} {vehicle_type} vehicles")
            
            # Enhance vehicle definitions for better simulation
            self._enhance_osm_vehicle_definitions(root, vehicle_type)
            
            # Apply traffic density to departure times if needed
            if traffic_density != 1.0:
                self._scale_departure_times(root, traffic_density)
            
            # Save the processed file
            tree.write(dest_file, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"❌ Error filtering OSM routes for {vehicle_type}: {e}")
            # Fallback: just copy the original file
            shutil.copy2(source_file, dest_file)
    
    def _select_diverse_vehicles(self, vehicles: List[ET.Element], target_count: int) -> List[ET.Element]:
        """
        Intelligently select a subset of vehicles that preserves route diversity
        
        Args:
            vehicles: List of vehicle elements
            target_count: Target number of vehicles to select
            
        Returns:
            List of selected vehicle elements that maintain diversity
        """
        if target_count >= len(vehicles):
            return vehicles
        
        # Analyze route diversity
        route_patterns = {}
        
        for vehicle in vehicles:
            route_elem = vehicle.find('route')
            if route_elem is not None:
                edges = route_elem.get('edges', '')
                # Create a pattern from start/end edges
                edge_list = edges.split()
                if len(edge_list) >= 2:
                    pattern = f"{edge_list[0]}->{edge_list[-1]}"
                else:
                    pattern = edges
                
                if pattern not in route_patterns:
                    route_patterns[pattern] = []
                route_patterns[pattern].append(vehicle)
        
        # Select vehicles to maintain pattern diversity
        selected = []
        patterns = list(route_patterns.keys())
        
        # First, select one vehicle from each unique route pattern
        for pattern in patterns:
            if len(selected) < target_count:
                selected.append(route_patterns[pattern][0])
        
        # Fill remaining slots by cycling through patterns
        pattern_index = 0
        vehicle_indices = {pattern: 1 for pattern in patterns}  # Start from second vehicle
        
        while len(selected) < target_count:
            pattern = patterns[pattern_index % len(patterns)]
            vehicles_in_pattern = route_patterns[pattern]
            vehicle_index = vehicle_indices[pattern]
            
            if vehicle_index < len(vehicles_in_pattern):
                selected.append(vehicles_in_pattern[vehicle_index])
                vehicle_indices[pattern] += 1
            
            pattern_index += 1
            
            # Prevent infinite loop
            if pattern_index > target_count * len(patterns):
                break
        
        print(f"🎯 Selected {len(selected)} vehicles from {len(patterns)} route patterns")
        return selected[:target_count]
    
    def _enhance_osm_vehicle_definitions(self, root: ET.Element, vehicle_type: str):
        """
        Enhance OSM vehicle definitions with better parameters for simulation
        
        Args:
            root: Root element of the routes XML
            vehicle_type: Type of vehicles being enhanced
        """
        try:
            # Define color mapping for vehicle types
            color_map = {
                'passenger': 'yellow',
                'bus': 'blue', 
                'truck': 'orange',
                'motorcycle': 'red'
            }
            
            # Find ALL vType elements that match this vehicle type (handle multiple ID patterns)
            # Possible patterns: veh_{type}, {type}_{type}, {prefix}_{type}, etc.
            all_vtypes = root.findall('.//vType')
            vtype_elem = None
            
            for vtype in all_vtypes:
                vtype_id = vtype.get('id', '')
                vtype_class = vtype.get('vClass', '')
                
                # Match by vClass or if the vehicle_type is in the ID
                if vtype_class == vehicle_type or vehicle_type in vtype_id.lower():
                    vtype_elem = vtype
                    # Add or update color attribute if missing or default
                    current_color = vtype.get('color', '').lower()
                    if not current_color or current_color in ['yellow', 'gray', '1,1,0', '']:
                        vtype.set('color', color_map.get(vehicle_type, 'gray'))
                        print(f"  🎨 Added color '{color_map.get(vehicle_type)}' to vType '{vtype_id}'")
                    break
            
            # If no vType found, create one with standard naming
            if vtype_elem is None:
                vtype_id = f"veh_{vehicle_type}"
                vtype_elem = ET.Element('vType')
                vtype_elem.set('id', vtype_id)
                vtype_elem.set('vClass', vehicle_type)
                vtype_elem.set('color', color_map.get(vehicle_type, 'gray'))
                
                # Insert at the beginning
                root.insert(0, vtype_elem)
                print(f"  ✨ Created new vType '{vtype_id}' with color '{color_map.get(vehicle_type)}'")
            
            # Enhance individual vehicles and trips
            for vehicle in root.findall('.//vehicle'):
                # Add optimized departure attributes if missing
                if not vehicle.get('departLane'):
                    vehicle.set('departLane', 'best')
                if not vehicle.get('departSpeed'):
                    vehicle.set('departSpeed', 'max')
            
            # Also enhance trip elements
            for trip in root.findall('.//trip'):
                # Add optimized departure attributes if missing
                if not trip.get('departLane'):
                    trip.set('departLane', 'best')
                if not trip.get('departSpeed'):
                    trip.set('departSpeed', 'max')
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not enhance vehicle definitions: {e}")
    
    def _scale_departure_times(self, root: ET.Element, scale_factor: float):
        """
        Scale departure times while preserving relative timing patterns
        
        Args:
            root: Root element of routes XML
            scale_factor: Scaling factor for traffic density
        """
        try:
            vehicles = root.findall('.//vehicle')
            if not vehicles:
                return
            
            # Extract and scale departure times
            departure_times = []
            for vehicle in vehicles:
                depart = vehicle.get('depart')
                if depart and depart != 'triggered':
                    try:
                        departure_times.append((vehicle, float(depart)))
                    except ValueError:
                        pass
            
            if not departure_times:
                return
            
            # Sort by departure time
            departure_times.sort(key=lambda x: x[1])
            
            # Scale while preserving relative spacing
            for i, (vehicle, original_time) in enumerate(departure_times):
                if scale_factor < 1.0:
                    # Reduce density by spacing out departures more
                    scaled_time = original_time / scale_factor
                else:
                    # Increase density by compacting departures
                    scaled_time = original_time / scale_factor
                
                vehicle.set('depart', f"{scaled_time:.2f}")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not scale departure times: {e}")
    
    def _copy_routes_basic(self, source_dir: Path, dest_dir: Path, 
                          enabled_vehicles: List[str], config: Dict[str, Any]):
        """
        Basic route copying fallback method
        
        Args:
            source_dir: Source routes directory
            dest_dir: Destination routes directory
            enabled_vehicles: List of enabled vehicle types
            config: Configuration parameters
        """
        traffic_density = config.get('trafficDensity', 1.0)
        copied_types = set()
        
        # Copy trip files first - prioritize for realistic patterns (support compressed files)
        trip_files = list(source_dir.glob("*.trips.xml")) + list(source_dir.glob("*.trips.xml.gz"))
        for trip_file in trip_files:
            # Determine vehicle type from filename
            vehicle_type = None
            for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                if vtype in trip_file.name.lower():
                    vehicle_type = vtype
                    break
            
            if vehicle_type and vehicle_type in enabled_vehicles:
                # Handle compressed trip files - decompress during copy
                if trip_file.name.endswith('.gz'):
                    import gzip
                    dest_file = dest_dir / trip_file.name.replace('.gz', '')
                    try:
                        with gzip.open(trip_file, 'rt', encoding='utf-8') as f_in:
                            if traffic_density != 1.0:
                                # Create temporary uncompressed file for scaling
                                temp_file = dest_file.with_suffix('.temp.xml')
                                temp_file.write_text(f_in.read(), encoding='utf-8')
                                self._scale_route_file(temp_file, dest_file, traffic_density)
                                temp_file.unlink()
                            else:
                                with open(dest_file, 'w', encoding='utf-8') as f_out:
                                    f_out.write(f_in.read())
                        print(f"Decompressed and copied trip file for enabled vehicle type: {vehicle_type}")
                    except Exception as e:
                        print(f"Failed to decompress {trip_file}: {e}, copying as-is")
                        dest_file = dest_dir / trip_file.name
                        shutil.copy2(trip_file, dest_file)
                else:
                    dest_file = dest_dir / trip_file.name
                    if traffic_density != 1.0:
                        # Apply traffic density scaling
                        self._scale_route_file(trip_file, dest_file, traffic_density)
                    else:
                        # Just copy the file
                        shutil.copy2(trip_file, dest_file)
                    print(f"Copied trip file for enabled vehicle type: {vehicle_type}")
                
                copied_types.add(vehicle_type)
        
        # Copy route files as fallback - only for types not covered by trip files
        for route_file in source_dir.glob("*.rou.xml"):
            # Determine vehicle type from filename
            vehicle_type = None
            for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                if vtype in route_file.name.lower():
                    vehicle_type = vtype
                    break
            
            if vehicle_type and vehicle_type in enabled_vehicles and vehicle_type not in copied_types:
                dest_file = dest_dir / route_file.name
                if traffic_density != 1.0:
                    # Apply traffic density scaling
                    self._scale_route_file(route_file, dest_file, traffic_density)
                else:
                    # Just copy the file
                    shutil.copy2(route_file, dest_file)
                print(f"Copied route file for enabled vehicle type: {vehicle_type}")
    
    def _apply_network_modifications(self, network_file: Path, config: Dict[str, Any]):
        """
        Apply configuration modifications to network file
        
        Args:
            network_file: Path to network file
            config: Configuration containing modifications
        """
        try:
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            # Apply speed limit changes
            speed_limits = config.get('speedLimits', [])
            for speed_limit in speed_limits:
                edge_id = speed_limit.get('edgeId')
                new_speed = speed_limit.get('speedLimit')
                
                if edge_id and new_speed:
                    # Find the edge and update speed
                    edge_elem = root.find(f".//edge[@id='{edge_id}']")
                    if edge_elem is not None:
                        # Update all lanes in the edge
                        for lane in edge_elem.findall(".//lane"):
                            lane.set('speed', str(new_speed / 3.6))  # Convert km/h to m/s
            
            # Save modified network
            tree.write(network_file, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"Error applying network modifications: {e}")
    
    def _generate_network_programmatically(self, network_file: Path, config: Dict[str, Any]):
        """
        Generate SUMO network file programmatically based on configuration
        
        Args:
            network_file: Path to output network file
            config: Configuration parameters
        """
        network_type = config.get('networkType', 'simple_grid')
        
        if network_type == 'simple_grid':
            self._generate_simple_grid_network(network_file, config)
        else:
            # Default to simple grid if unknown type
            self._generate_simple_grid_network(network_file, config)
    
    def _generate_simple_grid_network(self, network_file: Path, config: Dict[str, Any]):
        """
        Generate a simple grid network
        
        Args:
            network_file: Path to output network file
            config: Configuration parameters
        """
        grid_size = config.get('gridSize', 3)
        edge_length = 200.0  # meters
        
        # Create SUMO network XML content
        network_content = '''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.16" junctionCornerDetail="5" limitTurnSpeed="5.50" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">

    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,{max_x:.2f},{max_y:.2f}" origBoundary="-10000000000.00,-10000000000.00,10000000000.00,10000000000.00" projParameter="!"/>

'''.format(max_x=grid_size * edge_length, max_y=grid_size * edge_length)

        # Generate nodes (intersections)
        for i in range(grid_size + 1):
            for j in range(grid_size + 1):
                x = i * edge_length
                y = j * edge_length
                node_id = f"n_{i}_{j}"
                network_content += f'    <junction id="{node_id}" type="priority" x="{x:.2f}" y="{y:.2f}" incLanes="" intLanes="" shape="{x-2:.2f},{y-2:.2f} {x+2:.2f},{y-2:.2f} {x+2:.2f},{y+2:.2f} {x-2:.2f},{y+2:.2f}"/>\n'

        # Generate edges (roads)
        edge_id = 0
        
        # Horizontal edges
        for i in range(grid_size + 1):
            for j in range(grid_size):
                from_node = f"n_{i}_{j}"
                to_node = f"n_{i}_{j+1}"
                network_content += f'''    <edge id="e_{edge_id}" from="{from_node}" to="{to_node}" priority="1">
        <lane id="e_{edge_id}_0" index="0" speed="13.89" length="{edge_length:.2f}" shape="{i*edge_length:.2f},{j*edge_length + 2:.2f} {i*edge_length:.2f},{(j+1)*edge_length - 2:.2f}"/>
    </edge>
'''
                edge_id += 1
                
        # Vertical edges  
        for i in range(grid_size):
            for j in range(grid_size + 1):
                from_node = f"n_{i}_{j}"
                to_node = f"n_{i+1}_{j}"
                network_content += f'''    <edge id="e_{edge_id}" from="{from_node}" to="{to_node}" priority="1">
        <lane id="e_{edge_id}_0" index="0" speed="13.89" length="{edge_length:.2f}" shape="{i*edge_length + 2:.2f},{j*edge_length:.2f} {(i+1)*edge_length - 2:.2f},{j*edge_length:.2f}"/>
    </edge>
'''
                edge_id += 1

        network_content += '\n</net>'
        
        # Write the network file
        with open(network_file, 'w') as f:
            f.write(network_content)
    
    def _generate_route_file(self, session_dir: Path, network_id: str, config: Dict[str, Any]):
        """
        Generate route file based on configuration, preferring OSM-generated routes
        
        Args:
            session_dir: Session directory
            network_id: Network identifier
            config: Configuration parameters
        """
        route_file = session_dir / f"{network_id}.rou.xml"
        network_file = find_network_file(session_dir, network_id)
        if not network_file:
            raise FileNotFoundError(f"Network file not found for network_id: {network_id}")
        
        # First, check if we have OSM-generated route files for this network
        osm_routes = self._find_osm_route_files(network_id)
        
        if osm_routes:
            print(f"Found {len(osm_routes)} OSM route files for {network_id}")
            self._use_osm_route_files(session_dir, network_id, osm_routes, config)
            return
        
        print(f"No OSM routes found for {network_id}, generating custom routes...")
        
        # Fallback to custom route generation
        vehicle_count = config.get('vehicles', 10)
        
        # Extract real edge IDs from the network file
        edge_ids = self._extract_edge_ids(network_file)
        
        if not edge_ids:
            print(f"Warning: No edges found in network file {network_file}")
            # Create a minimal fallback route file
            self._create_minimal_route_file(route_file, vehicle_count)
            return
        
        print(f"Found {len(edge_ids)} edges in network")
        
        # Try to create better routes using SUMO's route generation
        try:
            self._generate_sumo_routes(session_dir, network_id, edge_ids, vehicle_count)
        except Exception as e:
            print(f"Failed to generate SUMO routes: {e}")
            # Fallback to simple routes
            self._create_simple_route_file(route_file, edge_ids, vehicle_count)
    
    def _find_osm_route_files(self, network_id: str) -> List[Path]:
        """
        Find OSM-generated route files for a given network
        
        Args:
            network_id: Network identifier
            
        Returns:
            List of available OSM route files
        """
        # Look for route files within the network directory
        network_dir = self.base_networks_dir / network_id
        routes_dir = network_dir / "routes"
        osm_routes = []
        
        # Check both network directory and routes subdirectory
        search_dirs = [network_dir, routes_dir] if routes_dir.exists() else [network_dir]
        
        for search_dir in search_dirs:
            # Look for various OSM route file patterns
            patterns = [
                "*.rou.xml",
                "osm.*.rou.xml", 
                "*passenger*.rou*",
                "*bus*.rou*",
                "*truck*.rou*"
            ]
            
            for pattern in patterns:
                osm_routes.extend(search_dir.glob(pattern))
        
        return list(set(osm_routes))  # Remove duplicates
    
    def _use_osm_route_files(self, session_dir: Path, network_id: str, osm_routes: List[Path], config: Dict[str, Any]):
        """
        Use OSM-generated route files, combining them if multiple exist
        
        Args:
            session_dir: Session directory
            network_id: Network identifier
            osm_routes: List of OSM route files
            config: Configuration parameters
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        target_route_file = session_dir / f"{network_id}.rou.xml"
        
        if len(osm_routes) == 1:
            # Single route file - copy directly
            import shutil
            shutil.copy2(osm_routes[0], target_route_file)
            print(f"Copied OSM route file: {osm_routes[0].name}")
            
        else:
            # Multiple route files - combine them
            print(f"Combining {len(osm_routes)} OSM route files...")
            self._combine_osm_route_files(osm_routes, target_route_file, config)
    
    def _combine_osm_route_files(self, osm_routes: List[Path], target_file: Path, config: Dict[str, Any]):
        """
        Combine multiple OSM route files into one
        
        Args:
            osm_routes: List of OSM route files to combine
            target_file: Target combined route file
            config: Configuration parameters
        """
        import xml.etree.ElementTree as ET
        
        # Create new routes XML structure
        root = ET.Element("routes")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")
        
        vehicle_types = set()
        routes = []
        vehicles = []
        flows = []
        
        vehicle_scale = config.get('vehicleScale', 1.0)  # Scale factor for number of vehicles
        
        # Parse each route file
        for route_file in osm_routes:
            try:
                tree = ET.parse(route_file)
                file_root = tree.getroot()
                
                # Extract vehicle types
                for vtype in file_root.findall(".//vType"):
                    vtype_id = vtype.get('id')
                    if vtype_id and vtype_id not in vehicle_types:
                        root.append(vtype)
                        vehicle_types.add(vtype_id)
                
                # Extract routes
                for route in file_root.findall(".//route"):
                    root.append(route)
                
                # Extract vehicles and flows with scaling
                for vehicle in file_root.findall(".//vehicle"):
                    # Scale vehicle timing based on config
                    depart = vehicle.get('depart')
                    if depart and depart.replace('.', '').isdigit():
                        scaled_depart = float(depart) / vehicle_scale
                        vehicle.set('depart', str(scaled_depart))
                    root.append(vehicle)
                
                for flow in file_root.findall(".//flow"):
                    # Scale flow rates
                    if 'vehsPerHour' in flow.attrib:
                        orig_rate = float(flow.get('vehsPerHour'))
                        scaled_rate = orig_rate * vehicle_scale
                        flow.set('vehsPerHour', str(scaled_rate))
                    root.append(flow)
                
                print(f"Added content from: {route_file.name}")
                
            except Exception as e:
                print(f"Error parsing OSM route file {route_file}: {e}")
                continue
        
        # Write combined file
        tree = ET.ElementTree(root)
        tree.write(target_file, encoding='utf-8', xml_declaration=True)
        print(f"Combined OSM routes written to: {target_file.name}")
    
    def _create_minimal_route_file(self, route_file: Path, vehicle_count: int):
        """Create a minimal route file when no edges are found"""
        route_content = '''<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <!-- No vehicles - network has no valid edges -->
</routes>'''
        
        with open(route_file, 'w') as f:
            f.write(route_content)
    
    def _generate_sumo_routes(self, session_dir: Path, network_id: str, edge_ids: List[str], vehicle_count: int):
        """
        Use SUMO's enhanced randomTrips.py to generate diverse, realistic routes
        """
        import subprocess
        import os
        
        network_file = find_network_file(session_dir, network_id)
        if not network_file:
            raise FileNotFoundError(f"Network file not found for network_id: {network_id}")
        route_file = session_dir / f"{network_id}.rou.xml"
        
        try:
            # Find SUMO tools directory
            sumo_home = os.environ.get('SUMO_HOME', 'C:\\Program Files (x86)\\Eclipse\\Sumo')
            randomtrips_script = os.path.join(sumo_home, 'tools', 'randomTrips.py')
            
            # Enhanced randomTrips.py with parameters for realistic diversity
            randomtrips_cmd = [
                "python", randomtrips_script,
                "-n", str(network_file),
                "-o", str(route_file),
                "--route-file", str(route_file),  # Generate routes directly
                "--period", "3.0",  # Average 3 seconds between vehicles
                "--fringe-factor", "2.0",  # Reduce border concentration
                "--intermediate", "1",  # Add waypoints for longer routes
                "--min-distance", "300",  # Minimum trip distance (meters)
                "--max-distance", "3000",  # Maximum trip distance  
                "--speed-exponent", "1.5",  # Weight by road speed/importance
                "--lanes",  # Consider lane count
                "--random-factor", "0.3",  # Add 30% randomness to selection
                "--fringe-start-attributes", 'departSpeed="max"',
                "--trip-attributes", 'departLane="best"',
                "--validate",  # Ensure routes are valid
                "--begin", "0",
                "--end", str(vehicle_count * 3),  # Scale time period
                "--seed", "42"  # Reproducible but diverse
            ]
            
            print(f"Generating diverse routes with command: {' '.join(randomtrips_cmd)}")
            result = subprocess.run(randomtrips_cmd, capture_output=True, text=True, cwd=session_dir)
            
            if result.returncode == 0:
                print(f"Successfully generated diverse routes using enhanced randomTrips.py")
                print(f"Route generation output: {result.stdout}")
                return
            else:
                print(f"Enhanced randomTrips.py failed: {result.stderr}")
                print(f"Falling back to simple route generation...")
                # Fallback to original simple method
                self._create_simple_route_file(route_file, edge_ids, vehicle_count)
                
        except Exception as e:
            print(f"Error in enhanced route generation: {e}")
            # Fallback to simple route generation
            self._create_simple_route_file(route_file, edge_ids, vehicle_count)
    
    def _create_simple_route_file(self, route_file: Path, edge_ids: List[str], vehicle_count: int):
        """
        Create simple route file with single-edge routes as fallback
        """
        # Use longer edges and filter out very short ones
        filtered_edges = [e for e in edge_ids if not e.startswith(':') and '#' not in e][:10]
        
        if not filtered_edges:
            filtered_edges = edge_ids[:10]
        
        route_content = '''<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    
    <!-- Vehicle Types -->
    <vType id="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" maxSpeed="55.56" color="yellow"/>
    
    <!-- Routes -->'''
        
        # Create routes with the available edges
        for i, edge_id in enumerate(filtered_edges):
            route_content += f'''
    <route id="route{i}" edges="{edge_id}"/>'''
        
        route_content += '''
    
    <!-- Vehicle Flows -->'''
        
        # Generate vehicles with reduced frequency to avoid congestion
        for i in range(min(vehicle_count, len(filtered_edges))):
            route_id = f"route{i}"
            depart_time = i * 10  # 10 second intervals
            route_content += f'''
    <vehicle id="veh_{i}" type="passenger" route="{route_id}" depart="{depart_time}" color="1,1,0"/>'''
        
        route_content += '''

</routes>'''
        
        with open(route_file, 'w') as f:
            f.write(route_content)
    
    def _extract_edge_ids(self, network_file: Path) -> List[str]:
        """
        Extract edge IDs from SUMO network file
        
        Args:
            network_file: Path to network file
            
        Returns:
            List of edge IDs (excluding internal edges)
        """
        edge_ids = []
        
        try:
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            # Find all edge elements, excluding internal edges (those starting with ':')
            for edge in root.findall(".//edge"):
                edge_id = edge.get('id')
                if edge_id and not edge_id.startswith(':'):
                    edge_ids.append(edge_id)
                    
        except Exception as e:
            print(f"Error parsing network file {network_file}: {e}")
            
        return edge_ids
    
    def _generate_valid_routes(self, edge_ids: List[str], max_routes: int = 5) -> List[List[str]]:
        """
        Generate valid routes from available edge IDs
        
        Args:
            edge_ids: List of available edge IDs
            max_routes: Maximum number of routes to generate
            
        Returns:
            List of routes (each route is a list of edge IDs)
        """
        routes = []
        
        if len(edge_ids) < 2:
            # If we have very few edges, create simple single-edge routes
            for edge_id in edge_ids[:max_routes]:
                routes.append([edge_id])
        else:
            # Create simple single-edge routes for better compatibility
            # This is safer than trying to create multi-edge routes without knowing the topology
            import random
            random.seed(42)  # For reproducible results
            
            # Select diverse edges for routes
            selected_edges = edge_ids[:max_routes] if len(edge_ids) >= max_routes else edge_ids
            
            for edge_id in selected_edges:
                routes.append([edge_id])
            
            # Fill remaining slots if needed
            while len(routes) < max_routes and len(edge_ids) > len(routes):
                remaining_edges = [e for e in edge_ids if [e] not in routes]
                if remaining_edges:
                    routes.append([random.choice(remaining_edges)])
                else:
                    break
        
        # Ensure we have at least one route
        if not routes:
            routes.append([edge_ids[0]] if edge_ids else ["edge0"])
            
        return routes
    
    def _generate_sumo_config(self, session_dir: Path, network_id: str, config: Dict[str, Any]):
        """
        Generate SUMO configuration file with simplified essential parameters
        
        Args:
            session_dir: Session directory
            network_id: Network identifier
            config: Configuration parameters with simplified structure
        """
        config_file = session_dir / f"{network_id}.sumocfg"
        additional_file = session_dir / f"{network_id}.add.xml"
        gui_settings_file = session_dir / "gui-settings.xml"
        
        # Determine the actual network filename (compressed or uncompressed)
        network_file = find_network_file(session_dir, network_id)
        if not network_file:
            # Fallback to uncompressed if not found
            network_filename = f"{network_id}.net.xml"
        else:
            network_filename = network_file.name
        
        # Generate additional file for road closures and other modifications
        self._generate_additional_file(additional_file, config)
        
        # Generate GUI settings file
        self._generate_gui_settings_file(gui_settings_file)
        
        # Extract simplified SUMO parameters from config
        # These come from the frontend as sumo_begin, sumo_end, etc.
        begin_time = config.get('sumo_begin', 0)  # From --begin parameter
        end_time = config.get('sumo_end', 1800)   # From --end parameter
        step_length = config.get('sumo_step_length', 1.0)  # From --step-length parameter
        time_to_teleport = config.get('sumo_time_to_teleport', 300)  # From --time-to-teleport parameter
        traffic_scale = config.get('sumo_traffic_scale', config.get('traffic_scale', config.get('sumo_traffic_intensity', 1.0)))  # Traffic scale multiplier
        
        # Fallback to original config structure for backward compatibility
        if 'original_config' in config:
            original = config['original_config']
            begin_time = original.get('beginTime', begin_time)
            end_time = original.get('endTime', end_time)
            step_length = original.get('stepLength', step_length)
            time_to_teleport = original.get('timeToTeleport', time_to_teleport)
        
        # Auto-calculate duration if not provided or if it's too short
        route_file = session_dir / f"{network_id}.rou.xml"
        auto_duration = self._calculate_simulation_duration(route_file)
        
        # Use the larger of provided end_time or auto-calculated duration
        if end_time <= begin_time or end_time < 300:  # Minimum 5 minutes
            simulation_end_time = max(auto_duration, begin_time + 1800)  # At least 30 minutes
        else:
            simulation_end_time = max(end_time, auto_duration)
        
        # SUMO configuration template with essential parameters only
        # This follows SUMO documentation structure exactly
        sumo_config = f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

    <input>
        <net-file value="{network_filename}"/>
        <route-files value="{network_id}.rou.xml"/>
        <additional-files value="{network_id}.add.xml"/>
    </input>

    <time>
        <begin value="{begin_time}"/>
        <end value="{simulation_end_time}"/>
        <step-length value="{step_length}"/>
    </time>

    <processing>
        <time-to-teleport value="{time_to_teleport}"/>
        <lateral-resolution value="0.8"/>
    </processing>

    <routing>
        <device.rerouting.adaptation-steps value="18"/>
        <device.rerouting.adaptation-interval value="10"/>
    </routing>

    <output>
        <summary-output value="{network_id}_summary.xml"/>
        <tripinfo-output value="{network_id}_tripinfo.xml"/>
        <emission-output value="{network_id}_emissions.xml"/>
        <edgedata-output value="{network_id}_edgedata.xml"/>
    </output>

    <report>
        <verbose value="true"/>
        <duration-log.statistics value="true"/>
    </report>

    <gui_only>
        <gui-settings-file value="gui-settings.xml"/>
    </gui_only>

</configuration>'''
        
        with open(config_file, 'w') as f:
            f.write(sumo_config)
            
        # Log the configuration for debugging
        print(f"DEBUG: Generated SUMO config with:")
        print(f"  Begin time: {begin_time}s")
        print(f"  End time: {simulation_end_time}s")
        print(f"  Duration: {simulation_end_time - begin_time}s")
        print(f"  Step length: {step_length}s")
        print(f"  Time to teleport: {time_to_teleport}s")
        print(f"  Lateral resolution: 0.8m (sublane model enabled for smooth lane changing)")
        print(f"  Traffic scale: {traffic_scale}x")
        if traffic_scale != 1.0:
            print(f"  Traffic scaling: enabled via --scale parameter")
    
    def _calculate_simulation_duration(self, route_file: Path) -> int:
        """
        Calculate appropriate simulation duration based on vehicle departure times
        
        Args:
            route_file: Path to route file
            
        Returns:
            Simulation duration in seconds
        """
        try:
            if not route_file.exists():
                return 3600  # Default 1 hour
            
            max_depart_time = 0.0
            
            # Parse route file to find maximum departure time
            tree = ET.parse(route_file)
            root = tree.getroot()
            
            for vehicle in root.findall('.//vehicle'):
                depart_str = vehicle.get('depart', '0')
                try:
                    depart_time = float(depart_str)
                    max_depart_time = max(max_depart_time, depart_time)
                except (ValueError, TypeError):
                    continue
            
            # Add buffer time for vehicles to complete their journeys
            # Use 30 minutes buffer or 20% of simulation time, whichever is larger
            buffer_time = max(1800, max_depart_time * 0.2)
            total_duration = int(max_depart_time + buffer_time)
            
            # Ensure minimum duration of 5 minutes
            return max(300, total_duration)
            
        except Exception as e:
            print(f"Error calculating simulation duration: {e}")
            return 3600  # Default 1 hour if error occurs
    
    def _generate_additional_file(self, additional_file: Path, config: Dict[str, Any]):
        """
        Generate additional file for road closures, traffic lights, and other modifications
        
        Args:
            additional_file: Path to additional file
            config: Configuration parameters (simplified structure)
        """
        additional_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- Additional file for simulation configuration -->
    <!-- Traffic intensity is controlled via SUMO's --scale parameter -->
    
    <!-- Traffic Light Logic Configuration -->
    <!-- Generated based on configuration settings -->
    
    <!-- Detectors for Live Data Collection and Adaptive Traffic Lights -->
    <!-- Basic detectors can be added here in future versions -->
    
</additional>'''
        
        # Generate traffic light configurations if specified
        traffic_control_config = config.get('trafficControl')
        if traffic_control_config:
            network_file = find_network_file(additional_file.parent, additional_file.stem)
            if network_file and network_file.exists():
                tl_configs = self._generate_traffic_light_configs(network_file, traffic_control_config)
                if tl_configs:
                    additional_content = additional_content.replace(
                        '<!-- Generated based on configuration settings -->',
                        tl_configs
                    )
        
        # Check if we have the original config with advanced features (backward compatibility)
        if 'original_config' in config:
            original = config['original_config']
            road_closures = original.get('roadClosures', [])
            
            if road_closures:
                additional_content = additional_content.replace(
                    '<!-- Basic detectors can be added here in future versions -->',
                    '''<!-- Road Closures from advanced configuration -->'''
                )
                
                for closure in road_closures:
                    edge_id = closure.get('edgeId')
                    start_time = closure.get('startTime', 0)
                    end_time = closure.get('endTime', 1800)
                    
                    if edge_id:
                        # Add closingRerouter for this edge
                        closure_xml = f'''
    <closingRerouter id="closure_{edge_id}" edges="{edge_id}" file="closure_{edge_id}.xml">
        <interval begin="{start_time}" end="{end_time}"/>
    </closingRerouter>'''
                        additional_content = additional_content.replace(
                            '<!-- Basic detectors can be added here in future versions -->',
                            closure_xml + '\n    <!-- Basic detectors can be added here in future versions -->'
                        )
        
        with open(additional_file, 'w') as f:
            f.write(additional_content)

    def _generate_traffic_light_configs(self, network_file: Path, traffic_control_config: Dict[str, Any]) -> str:
        """
        Generate traffic light logic configurations based on network topology
        
        Args:
            network_file: Path to the network file
            traffic_control_config: Traffic control configuration from frontend
            
        Returns:
            XML string containing traffic light logic definitions
        """
        try:
            # Parse network file to extract actual traffic light signal information
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            # Extract traffic light information from connections
            tl_signals = self._extract_traffic_light_signals(root)
            
            if not tl_signals:
                print("DEBUG: No traffic light signals found in network")
                return ""
            
            print(f"DEBUG: Found {len(tl_signals)} traffic light signals: {list(tl_signals.keys())}")
            
            # Generate traffic light logic based on control method
            method = traffic_control_config.get('method', 'fixed')
            
            tl_xml_parts = []
            tl_xml_parts.append("<!-- Traffic Light Logic Configurations -->")
            
            if method == 'fixed':
                # Generate fixed timer traffic lights
                tl_xml_parts.extend(self._generate_fixed_timer_tls(tl_signals, traffic_control_config))
            elif method == 'adaptive':
                # Generate adaptive traffic lights with detectors
                tl_xml_parts.extend(self._generate_adaptive_tls(tl_signals, traffic_control_config))
            
            # Only return traffic light XML if there are new configurations to add
            if not tl_xml_parts or len(tl_xml_parts) <= 1:  # Only the comment line
                print("DEBUG: No additional traffic light configurations needed")
                return ""
            
            return "\n    ".join(tl_xml_parts)
            
        except ET.ParseError as e:
            print(f"ERROR: Failed to parse network file {network_file}: {e}")
            return ""
        except Exception as e:
            print(f"ERROR: Failed to generate traffic light configs: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return ""

    def _extract_traffic_light_signals(self, root):
        """
        Extract traffic light signal information from network XML
        
        Args:
            root: XML root element of network file
            
        Returns:
            Dictionary mapping tl_id -> {'num_links': int, 'connections': list, 'existing_logic': bool}
        """
        tl_signals = {}
        
        # First, check for existing traffic light logic definitions in the network
        existing_tl_logic = {}
        for tl_logic in root.findall('tlLogic'):
            tl_id = tl_logic.get('id')
            program_id = tl_logic.get('programID', '0')
            if tl_id:
                existing_tl_logic[tl_id] = program_id
        
        print(f"DEBUG: Found existing traffic light logic: {list(existing_tl_logic.keys())}")
        
        # Find all connections with tl attribute
        for connection in root.findall('connection'):
            tl_id = connection.get('tl')
            if tl_id:
                link_index_str = connection.get('linkIndex')
                if link_index_str is not None:
                    link_index = int(link_index_str)
                    
                    if tl_id not in tl_signals:
                        tl_signals[tl_id] = {
                            'max_link_index': -1, 
                            'connections': [], 
                            'existing_logic': tl_id in existing_tl_logic
                        }
                    
                    tl_signals[tl_id]['max_link_index'] = max(tl_signals[tl_id]['max_link_index'], link_index)
                    tl_signals[tl_id]['connections'].append({
                        'from': connection.get('from'),
                        'to': connection.get('to'),
                        'link_index': link_index,
                        'dir': connection.get('dir', 's')  # direction: s=straight, l=left, r=right, t=turn
                    })
        
        # Calculate number of links for each signal
        for tl_id in tl_signals:
            tl_signals[tl_id]['num_links'] = tl_signals[tl_id]['max_link_index'] + 1
            
        print(f"DEBUG: Extracted traffic light signals: {[(tl_id, info['num_links'], info['existing_logic']) for tl_id, info in tl_signals.items()]}")
        
        return tl_signals

    def _generate_fixed_timer_tls(self, tl_signals: dict, traffic_control_config: Dict[str, Any]) -> list:
        """
        Generate fixed timer traffic light logic
        
        Args:
            tl_signals: Dictionary mapping tl_id -> {'num_links': int, 'connections': list}
            traffic_control_config: Traffic control configuration
            
        Returns:
            List of XML strings for fixed timer traffic light logic
        """
        fixed_config = traffic_control_config.get('fixedTimer', {})
        green_phase = fixed_config.get('greenPhase', 30)
        yellow_phase = fixed_config.get('yellowPhase', 3)
        red_phase = fixed_config.get('redPhase', 30)
        all_red_phase = fixed_config.get('allRedPhase', 2)
        
        tl_xml_parts = []
        
        for tl_id, signal_info in tl_signals.items():
            # Skip if traffic light logic already exists in the network file
            if signal_info.get('existing_logic', False):
                print(f"DEBUG: Skipping {tl_id} - logic already exists in network file")
                continue
                
            num_links = signal_info['num_links']
            connections = signal_info['connections']
            
            # Generate state strings based on actual number of links
            # Create a simple 2-phase system: main direction green, then cross direction green
            state_main_green = self._generate_state_string(connections, num_links, 'main_green')
            state_main_yellow = self._generate_state_string(connections, num_links, 'main_yellow')
            state_cross_green = self._generate_state_string(connections, num_links, 'cross_green')
            state_cross_yellow = self._generate_state_string(connections, num_links, 'cross_yellow')
            state_all_red = 'r' * num_links
            
            tl_logic = f'''<tlLogic id="{tl_id}" type="static" programID="0" offset="0">
        <!-- Green phase for main direction -->
        <phase duration="{green_phase}" state="{state_main_green}"/>
        <!-- Yellow phase for main direction -->
        <phase duration="{yellow_phase}" state="{state_main_yellow}"/>
        <!-- All-red safety phase -->
        <phase duration="{all_red_phase}" state="{state_all_red}"/>
        <!-- Green phase for cross direction -->
        <phase duration="{red_phase}" state="{state_cross_green}"/>
        <!-- Yellow phase for cross direction -->
        <phase duration="{yellow_phase}" state="{state_cross_yellow}"/>
        <!-- All-red safety phase -->
        <phase duration="{all_red_phase}" state="{state_all_red}"/>
    </tlLogic>'''
            
            tl_xml_parts.append(tl_logic)
        
        if not tl_xml_parts:
            print("DEBUG: No new traffic light configurations generated - all signals already have logic in network file")
        else:
            print(f"DEBUG: Generated {len(tl_xml_parts)} fixed timer traffic light configurations")
        
        return tl_xml_parts

    def _generate_adaptive_tls(self, tl_signals: dict, traffic_control_config: Dict[str, Any]) -> list:
        """
        Generate adaptive (actuated) traffic light logic with detectors
        
        Args:
            tl_signals: Dictionary mapping tl_id -> {'num_links': int, 'connections': list, 'existing_logic': bool}
            traffic_control_config: Traffic control configuration
            
        Returns:
            List of XML strings for adaptive traffic light logic and detectors
        """
        adaptive_config = traffic_control_config.get('adaptive', {})
        min_green = adaptive_config.get('minGreenTime', 5)
        max_green = adaptive_config.get('maxGreenTime', 60)
        sensitivity = adaptive_config.get('detectorSensitivity', 1.0)
        jam_threshold = adaptive_config.get('jamThreshold', 30)
        
        tl_xml_parts = []
        detector_xml_parts = []
        
        for tl_id, signal_info in tl_signals.items():
            # Skip if traffic light logic already exists in the network file
            if signal_info.get('existing_logic', False):
                print(f"DEBUG: Skipping {tl_id} - logic already exists in network file")
                continue
                
            num_links = signal_info['num_links']
            connections = signal_info['connections']
            
            # Generate state strings based on actual number of links
            state_main_green = self._generate_state_string(connections, num_links, 'main_green')
            state_main_yellow = self._generate_state_string(connections, num_links, 'main_yellow')
            state_cross_green = self._generate_state_string(connections, num_links, 'cross_green')
            state_cross_yellow = self._generate_state_string(connections, num_links, 'cross_yellow')
            state_all_red = 'r' * num_links
            
            # Generate actuated traffic light logic
            tl_logic = f'''<tlLogic id="{tl_id}" type="actuated" programID="0" offset="0">
        <!-- Green phase for main direction (detector-controlled) -->
        <phase duration="{min_green}" minDur="{min_green}" maxDur="{max_green}" state="{state_main_green}"/>
        <!-- Yellow phase for main direction -->
        <phase duration="3" state="{state_main_yellow}"/>
        <!-- All-red safety phase -->
        <phase duration="2" state="{state_all_red}"/>
        <!-- Green phase for cross direction (detector-controlled) -->
        <phase duration="{min_green}" minDur="{min_green}" maxDur="{max_green}" state="{state_cross_green}"/>
        <!-- Yellow phase for cross direction -->
        <phase duration="3" state="{state_cross_yellow}"/>
        <!-- All-red safety phase -->
        <phase duration="2" state="{state_all_red}"/>
        <!-- Adaptive parameters -->
        <param key="detector-gap" value="{3.0 / sensitivity}"/>
        <param key="max-gap" value="{5.0 / sensitivity}"/>
        <param key="jam-threshold" value="{jam_threshold}"/>
    </tlLogic>'''
            
            tl_xml_parts.append(tl_logic)
            
            # Generate lane area detectors for incoming edges
            unique_from_edges = set()
            for conn in connections:
                from_edge = conn['from']
                if from_edge and not from_edge.startswith(':'):  # Skip internal edges
                    unique_from_edges.add(from_edge)
            
            if unique_from_edges:
                detector_xml = f'<!-- Detectors for adaptive traffic light {tl_id} -->'
                for i, from_edge in enumerate(sorted(unique_from_edges)):
                    # Generate detector for first lane of each incoming edge
                    detector_xml += f'\n    <laneAreaDetector id="det_{tl_id}_{i}" lane="{from_edge}_0" pos="10" length="50" file="NUL" freq="60"/>'
                detector_xml_parts.append(detector_xml)
        
        # Combine traffic light logic and detectors
        all_parts = tl_xml_parts + detector_xml_parts
        
        if not tl_xml_parts:
            print("DEBUG: No new traffic light configurations generated - all signals already have logic in network file")
        else:
            print(f"DEBUG: Generated {len(tl_xml_parts)} adaptive traffic light configurations with detectors")
        
        return all_parts

    def _generate_state_string(self, connections, num_links, phase_type):
        """
        Generate traffic light state string based on connection directions
        
        Args:
            connections: List of connection dictionaries with 'dir' and 'link_index'
            num_links: Total number of links in the signal
            phase_type: 'main_green', 'main_yellow', 'cross_green', 'cross_yellow'
            
        Returns:
            State string for the traffic light phase
        """
        # Initialize all links as red
        state = ['r'] * num_links
        
        # Define which movements get which signal based on direction
        # This is a simplified model - in reality, signal timing depends on intersection geometry
        
        for conn in connections:
            link_index = conn['link_index']
            direction = conn.get('dir', 's')
            
            if phase_type == 'main_green':
                # Main phase: straight and right turn movements (north-south corridor)
                if direction in ['s', 'S']:  # Straight through
                    state[link_index] = 'G'  # Green
                elif direction in ['r', 'R']:  # Right turn
                    state[link_index] = 'g'  # Green (lowercase for uncontrolled)
                    
            elif phase_type == 'main_yellow':
                # Yellow phase for main direction
                if direction in ['s', 'S']:
                    state[link_index] = 'y'  # Yellow
                elif direction in ['r', 'R']:
                    state[link_index] = 'y'
                    
            elif phase_type == 'cross_green':
                # Cross phase: east-west movements and left turns
                if direction in ['s', 'S']:  # Actually cross-street straight
                    # For cross phase, what was "straight" for other directions becomes green
                    # This is a simplified heuristic - we'd need better geometry analysis
                    pass  # Keep red for now, will be handled by connection analysis
                elif direction in ['l', 'L']:  # Left turns
                    state[link_index] = 'G'  # Green
                elif direction in ['t']:  # U-turns
                    state[link_index] = 'g'  # Green (typically lower priority)
                    
            elif phase_type == 'cross_yellow':
                # Yellow phase for cross direction
                if direction in ['l', 'L', 't']:
                    state[link_index] = 'y'  # Yellow
        
        # Heuristic: if no movements were assigned green in cross phase, 
        # alternate some straight movements
        if phase_type == 'cross_green' and 'G' not in state and 'g' not in state:
            # Give green to some straight movements that weren't in main phase
            for conn in connections:
                link_index = conn['link_index']
                if conn.get('dir') == 's' and state[link_index] == 'r':
                    # This heuristic assumes alternating directions for straight movements
                    if link_index % 2 == 1:  # Odd indices get green in cross phase
                        state[link_index] = 'G'
                        if len([s for s in state if s == 'G']) >= 3:  # Limit to avoid conflicts
                            break
        
        return ''.join(state)
    
    def _generate_gui_settings_file(self, gui_settings_file: Path):
        """
        Generate GUI settings file for SUMO GUI
        
        Args:
            gui_settings_file: Path to GUI settings file
        """
        gui_settings_content = '''<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/guiConfiguration.xsd">

    <gui>
        <viewport zoom="225.0" x="300.0" y="300.0" angle="0.0"/>
    </gui>

    <delay value="200"/>
    
    <background backgroundColor="white"/>

    <edges>
        <edge id="" color="black" width="3.0"/>
    </edges>

    <vehicles>
        <vehicle color="red" shape="passenger"/>
    </vehicles>
    
    <junctions>
        <junction color="darkGray"/>
    </junctions>

</configuration>'''
        
        with open(gui_settings_file, 'w') as f:
            f.write(gui_settings_content)
    
    def launch_simulation(self, session_id: str, session_path: str, config: Dict[str, Any],
                         enable_gui: bool = True, enable_live_data: bool = True) -> Dict[str, Any]:
        """
        Launch SUMO simulation
        
        Args:
            session_id: Session identifier
            session_path: Path to session directory
            config: Configuration parameters
            enable_gui: Whether to launch SUMO GUI
            enable_live_data: Whether to enable live data streaming
            
        Returns:
            Result dictionary with process information
        """
        try:
            session_dir = Path(session_path)
            
            # Find the configuration file
            config_files = list(session_dir.glob("*.sumocfg"))
            if not config_files:
                return {
                    "success": False,
                    "message": "No SUMO configuration file found in session directory"
                }
            
            config_file = config_files[0]
            
            # Extract network_id from config file name (remove .sumocfg extension)
            network_id = config_file.stem if config_file.suffix == '.sumocfg' else config_file.name.replace('.sumocfg', '')
            
            # Prepare SUMO command
            sumo_path = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin"
            if enable_gui:
                sumo_cmd = [os.path.join(sumo_path, "sumo-gui.exe")]
            else:
                sumo_cmd = [os.path.join(sumo_path, "sumo.exe")]
            
            sumo_cmd.extend([
                "-c", config_file.name,  # Use just the filename since we set cwd=session_dir
                "--time-to-teleport", "300",  # Prevent vehicles from getting stuck
                "--no-warnings",  # Reduce console spam
                "--lateral-resolution", "0.8"  # Enable sublane model for smooth lane changing
            ])
            
            # Add step-length parameter from user configuration
            step_length = config.get('sumo_step_length', 1.0)  # Default to 1.0 for normal time progression
            sumo_cmd.extend(["--step-length", str(step_length)])
            print(f"DEBUG: Using step-length: {step_length}s")
            print(f"DEBUG: Sublane model enabled with lateral-resolution: 0.8m")
            
            # Extract end time from config and add --end parameter for automatic termination
            # This ensures SUMO will automatically terminate when the simulation time is reached
            duration_seconds = None
            
            # Try different ways to get the duration from config
            if 'sumo_end' in config and 'sumo_begin' in config and config.get('sumo_end') is not None and config.get('sumo_begin') is not None:
                # Frontend sends sumo_begin and sumo_end
                begin_time = config.get('sumo_begin', 0)
                end_time = config.get('sumo_end', 60)
                duration_seconds = end_time - begin_time
                print(f"DEBUG: Using sumo_end-sumo_begin: {end_time} - {begin_time} = {duration_seconds} seconds")
                
                # Update the SUMO configuration file with correct timing
                self._update_sumo_config_timing(session_dir, network_id, begin_time, end_time)
                
            elif 'duration' in config and config.get('duration') is not None:
                # Direct duration field
                duration_seconds = config.get('duration')
                begin_time = 0
                end_time = duration_seconds
                print(f"DEBUG: Using direct duration: {duration_seconds} seconds")
                
                # Update the SUMO configuration file with correct timing
                self._update_sumo_config_timing(session_dir, network_id, begin_time, end_time)
                
            elif 'endTime' in config and config.get('endTime') is not None:
                # Frontend sends endTime - beginTime as duration
                begin_time = config.get('beginTime', 0)
                end_time = config.get('endTime', 60)
                duration_seconds = end_time - begin_time
                print(f"DEBUG: Using endTime-beginTime: {end_time} - {begin_time} = {duration_seconds} seconds")
                
                # Update the SUMO configuration file with correct timing
                self._update_sumo_config_timing(session_dir, network_id, begin_time, end_time)
                
            else:
                # Default fallback
                duration_seconds = 60  # 1 minute default to match frontend default
                begin_time = 0
                end_time = 60
                print(f"DEBUG: Using default duration: {duration_seconds} seconds")
                
                # Update the SUMO configuration file with correct timing
                self._update_sumo_config_timing(session_dir, network_id, begin_time, end_time)

            # Note: We no longer add --end parameter to command line since we update the config file directly
            
            # Add traffic scale if specified
            traffic_scale = config.get('sumo_traffic_scale', config.get('traffic_scale', config.get('sumo_traffic_intensity', 1.0)))  # Legacy fallback
            if traffic_scale != 1.0:
                sumo_cmd.extend(["--scale", str(traffic_scale)])
                print(f"DEBUG: Adding traffic scaling: --scale {traffic_scale}")
            else:
                print(f"DEBUG: No traffic scaling (scale = 1.0)")
            
            # Add gaming mode settings for GUI (automatic start and better UX)
            if enable_gui:
                # Use GUI settings file for proper input handling
                gui_settings_path = os.path.join(os.path.dirname(__file__), "gui_settings.xml")
                sumo_cmd.extend([
                    "--gui-settings-file", gui_settings_path,  # Use custom GUI settings
                    "--game",        # Enable gaming mode
                    "--game.mode", "tls",  # Traffic Light Signal gaming mode
                    "--window-size", "1200,800",  # Set consistent window size
                ])
                
                # Add user-specified delay from configuration
                gui_delay = config.get('sumo_gui_delay', 0)  # Get delay from frontend config
                sumo_cmd.extend(["--delay", str(gui_delay)])
                print(f"DEBUG: Using user-specified GUI delay: {gui_delay}ms")
                
                # Gaming mode: Interactive traffic light control and enhanced user experience
                print(f"DEBUG: Using GUI settings file: {gui_settings_path}")
            else:
                sumo_cmd.extend(["--quit-on-end"])
            
            # SOLUTION: For GUI mode, don't use TraCI at all to preserve full user control
            # This gives complete simulation control to the SUMO GUI interface
            if enable_live_data and not enable_gui:
                # Only add remote port for headless mode (no GUI)
                sumo_cmd.extend([
                    "--remote-port", "8813",
                    "--start"  # Start simulation immediately for headless mode
                ])
                print("DEBUG: Headless mode with TraCI control")
            elif enable_gui:
                # GUI-ONLY MODE: No TraCI, pure GUI control for immediate simulation start
                sumo_cmd.extend([
                    "--start"  # Start simulation immediately in GUI mode
                ])
                print("DEBUG: Pure GUI mode - no TraCI, immediate simulation start with --start flag")
                print("DEBUG: SUMO GUI has full control, simulation will start automatically")
                enable_live_data = False  # Critical: No data streaming threads, no TraCI
            
            # Launch SUMO process
            print(f"DEBUG: Executing SUMO command: {' '.join(sumo_cmd)}")
            print(f"DEBUG: Working directory: {session_dir}")
            
            process = subprocess.Popen(
                sumo_cmd,
                cwd=session_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Check if process started successfully
            import time
            time.sleep(0.5)  # Give process a moment to start
            if process.poll() is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                error_msg = f"SUMO failed to start. Exit code: {process.returncode}"
                if stderr:
                    error_msg += f"\nSTDERR: {stderr}"
                if stdout:
                    error_msg += f"\nSTDOUT: {stdout}"
                print(f"DEBUG: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
            else:
                print(f"DEBUG: SUMO process started successfully with PID: {process.pid}")
            
            # Store process information
            process_info = {
                "processId": process.pid,
                "sessionId": session_id,
                "sessionPath": session_path,
                "command": " ".join(sumo_cmd),
                "port": 8813 if enable_live_data else None,
                "startTime": datetime.now().isoformat()
            }
            
            self.active_processes[session_id] = {
                "process": process,
                "info": process_info,
                "paused": False  # Initialize as not paused
            }
            
            # Live data collection has been disabled to prevent TraCI configuration conflicts
            # The system now operates in pure GUI mode for better user control
            print("Live data collection disabled - using pure GUI mode")
            
            return {
                "success": True,
                "message": "SUMO simulation launched successfully",
                "process": process_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to launch simulation: {str(e)}"
            }
    
    def get_simulation_stats(self, process_id: int) -> Dict[str, Any]:
        """
        Get live simulation statistics from actual SUMO simulation
        
        Args:
            process_id: Process ID of running simulation
            
        Returns:
            Dictionary containing real simulation statistics
        """
        try:
            # Find session by process ID
            session_data = None
            session_id = None
            for sid, data in self.active_processes.items():
                if data["info"]["processId"] == process_id:
                    session_data = data
                    session_id = sid
                    break
            
            if not session_data:
                return {
                    "success": False,
                    "message": "Simulation process not found"
                }
            
            # Check if process is still running
            process = session_data["process"]
            if process.poll() is not None:
                return {
                    "success": False,
                    "message": "Simulation process has ended"
                }
            
            # Try to get real statistics from SUMO
            real_stats = self._get_real_sumo_stats(session_id, process_id)
            
            if real_stats:
                return {
                    "success": True,
                    "stats": real_stats
                }
            else:
                # Fallback to basic elapsed time if TraCI is not available
                process_start_time = session_data["info"].get("startTime")
                if process_start_time:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(process_start_time.replace('Z', '+00:00') if 'Z' in process_start_time else process_start_time)
                    elapsed_seconds = int((datetime.now() - start_dt).total_seconds())
                else:
                    elapsed_seconds = 0
                
                return {
                    "success": True,
                    "stats": {
                        "simulationTime": elapsed_seconds,
                        "totalVehicles": 0,
                        "runningVehicles": 0,
                        "waitingVehicles": 0,
                        "averageSpeed": 0.0,
                        "averageWaitingTime": 0.0,
                        "throughput": 0,
                        "message": "Live data unavailable - TraCI not connected"
                    }
                }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get simulation stats: {str(e)}"
            }
    
    def _get_real_sumo_stats(self, session_id: str, process_id: int) -> Dict[str, Any]:
        """
        Attempt to get real statistics from SUMO via TraCI or output files
        
        Args:
            session_id: Session identifier
            process_id: Process ID
            
        Returns:
            Dictionary with real stats or None if unavailable
        """
        try:
            # Method 1: Try to read SUMO output files if they exist
            session_dir = self.sessions_dir / session_id
            
            # Look for SUMO summary output files
            summary_files = list(session_dir.glob("*summary*.xml"))
            tripinfo_files = list(session_dir.glob("*tripinfo*.xml"))
            
            if summary_files or tripinfo_files:
                return self._parse_sumo_output_files(session_dir)
            
            # Method 2: Try TraCI connection (if port is available)
            # This would require the simulation to be running with TraCI enabled
            # For now, we'll focus on file-based statistics
            
            return None
            
        except Exception as e:
            print(f"Error getting real SUMO stats: {e}")
            return None
    
    def _parse_sumo_output_files(self, session_dir: Path) -> Dict[str, Any]:
        """
        Parse SUMO output files to extract real statistics
        
        Args:
            session_dir: Session directory path
            
        Returns:
            Dictionary with parsed statistics
        """
        import xml.etree.ElementTree as ET
        from datetime import datetime
        
        stats = {
            "simulationTime": 0,
            "totalVehicles": 0,
            "runningVehicles": 0,
            "waitingVehicles": 0,
            "averageSpeed": 0.0,
            "averageWaitingTime": 0.0,
            "throughput": 0
        }
        
        try:
            # Parse summary files for vehicle counts and speeds
            summary_files = list(session_dir.glob("*summary*.xml"))
            for summary_file in summary_files:
                try:
                    tree = ET.parse(summary_file)
                    root = tree.getroot()
                    
                    # Get all time step data
                    timesteps = root.findall(".//step")
                    if timesteps:
                        latest_step = timesteps[-1]
                        
                        # Basic counts from latest step
                        stats["simulationTime"] = float(latest_step.get("time", 0))
                        stats["runningVehicles"] = int(latest_step.get("running", 0))
                        stats["waitingVehicles"] = int(latest_step.get("waiting", 0))
                        stats["totalVehicles"] = int(latest_step.get("loaded", 0))
                        stats["averageWaitingTime"] = round(float(latest_step.get("meanWaitingTime", 0)), 1)
                        
                        # For average speed, find the most recent step with valid data
                        # (SUMO uses -1.00 when no vehicles are running)
                        valid_speed = 0.0
                        for step in reversed(timesteps):
                            mean_speed = float(step.get("meanSpeed", -1))
                            if mean_speed >= 0:  # Valid speed data
                                valid_speed = mean_speed
                                break
                        
                        # Convert from m/s to km/h
                        stats["averageSpeed"] = round(valid_speed * 3.6, 1)
                        
                except Exception as e:
                    print(f"Error parsing summary file {summary_file}: {e}")
                    continue
            
            # Calculate throughput (vehicles per hour)
            if stats["simulationTime"] > 0:
                vehicles_per_second = stats["totalVehicles"] / stats["simulationTime"]
                stats["throughput"] = int(vehicles_per_second * 3600)
            
            return stats
            
        except Exception as e:
            print(f"Error parsing SUMO output files: {e}")
            return None
    
    def stop_simulation(self, process_id: int) -> Dict[str, Any]:
        """
        Stop running simulation
        
        Args:
            process_id: Process ID of simulation to stop
            
        Returns:
            Result dictionary
        """
        try:
            # Find and terminate the process
            for session_id, data in self.active_processes.items():
                if data["info"]["processId"] == process_id:
                    process = data["process"]
                    session_path = data["info"]["sessionPath"]
                    
                    # Check if the process is still running
                    if process.poll() is not None:
                        # Process has already terminated, just clean up
                        print(f"Process {process_id} has already terminated, cleaning up session {session_id}")
                        
                        # Parse and save session statistics
                        try:
                            session_stats = self._parse_sumo_output_files(Path(session_path))
                            if session_stats:
                                stats_file = Path(session_path) / "session_statistics.json"
                                with open(stats_file, 'w') as f:
                                    json.dump({
                                        'session_id': session_id,
                                        'completed_at': datetime.now().isoformat(),
                                        'completion_reason': 'Process ended (detected)',
                                        'statistics': session_stats,
                                        'can_analyze': True
                                    }, f, indent=2)
                                print(f"Session statistics saved to {stats_file}")
                        except Exception as e:
                            print(f"Error parsing session statistics for {session_id}: {e}")
                        
                        # Remove from active processes
                        del self.active_processes[session_id]
                        
                        # Broadcast simulation completion
                        if self.websocket_handler:
                            self.websocket_handler.broadcast_simulation_status('completed', 'Simulation completed (detected)', {
                                'session_id': session_id,
                                'reason': 'Process ended (detected)',
                                'process_id': process_id
                            })
                            
                            completion_data = {
                                'session_id': session_id,
                                'reason': 'Process ended (detected)',
                                'completed_at': datetime.now().isoformat(),
                                'can_analyze': True
                            }
                            self.websocket_handler.broadcast_message('session_completed', completion_data)
                        
                        return {
                            "success": True,
                            "message": "Simulation was already completed, cleaned up successfully",
                            "session_id": session_id
                        }
                    
                    # Process is still running, terminate it
                    process.terminate()
                    
                    # Wait for process to finish
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    
                    # Parse and save session statistics for manual stops too
                    print(f"Parsing simulation output for manually stopped session {session_id}")
                    try:
                        session_stats = self._parse_sumo_output_files(Path(session_path))
                        if session_stats:
                            # Save session statistics to a JSON file
                            stats_file = Path(session_path) / "session_statistics.json"
                            with open(stats_file, 'w') as f:
                                json.dump({
                                    'session_id': session_id,
                                    'completed_at': datetime.now().isoformat(),
                                    'completion_reason': 'Manually stopped',
                                    'statistics': session_stats,
                                    'can_analyze': True
                                }, f, indent=2)
                            print(f"Session statistics saved to {stats_file}")
                    except Exception as e:
                        print(f"Error parsing session statistics for {session_id}: {e}")
                    
                    # Remove from active processes
                    del self.active_processes[session_id]
                    
                    # Broadcast simulation stopped via WebSocket
                    if self.websocket_handler:
                        self.websocket_handler.broadcast_simulation_status('stopped', 'Simulation manually stopped', {
                            'session_id': session_id,
                            'reason': 'Manually stopped',
                            'process_id': process_id
                        })
                        
                        # Send session completed event
                        completion_data = {
                            'session_id': session_id,
                            'reason': 'Manually stopped',
                            'completed_at': datetime.now().isoformat(),
                            'can_analyze': True
                        }
                        self.websocket_handler.broadcast_message('session_completed', completion_data)
                    
                    return {
                        "success": True,
                        "message": "Simulation stopped successfully",
                        "session_id": session_id
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop simulation: {str(e)}"
            }
    
    # Pause/Resume functionality removed - use SUMO GUI controls directly
    # This prevents configuration conflicts with TraCI
    


    # Zoom controls removed - use SUMO GUI controls directly
    # Zoom is now hardcoded to 225 in the GUI settings file



    # Center view functionality removed - no longer using TraCI

    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """
        Clean up session files and processes
        
        Args:
            session_id: Session identifier
            
        Returns:
            Result dictionary
        """
        try:
            # Stop any running processes for this session
            if session_id in self.active_processes:
                process_id = self.active_processes[session_id]["info"]["processId"]
                self.stop_simulation(process_id)
            
            # Remove session directory
            session_dir = self.sessions_dir / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
            
            return {
                "success": True,
                "message": "Session cleaned up successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to cleanup session: {str(e)}"
            }
    
    def _start_data_collection_thread(self, session_id: str, port: int, config: Dict[str, Any]):
        """
        TraCI data collection has been disabled - method kept for compatibility
        
        Args:
            session_id: Session identifier  
            port: TraCI port number
            config: Session configuration containing stepLength and other settings
        """
        # TraCI data collection disabled - simulation now runs in pure GUI mode
        print(f"Data collection disabled for session {session_id} - using pure GUI mode")
        return


    def _handle_simulation_completion(self, session_id: str, reason: str):
        """
        Handle proper simulation completion and cleanup
        
        Args:
            session_id: Session identifier
            reason: Reason for completion (e.g., "Duration reached", "All vehicles completed")
        """
        try:
            import time  # Import here for sleep functionality
            print(f"Handling simulation completion for session {session_id}: {reason}")
            
            # Stop the SUMO process if it's still running
            if session_id in self.active_processes:
                process_data = self.active_processes[session_id]
                process = process_data["process"]
                process_id = process_data["info"]["processId"]
                session_path = process_data["info"]["sessionPath"]
                
                # Terminate the process gracefully
                if process.poll() is None:  # Process is still running
                    print(f"Gracefully stopping SUMO process {process_id} for session {session_id}")
                    
                    # Give SUMO time to finish writing files
                    time.sleep(2)
                    
                    # Send SIGTERM first (graceful shutdown)
                    process.terminate()
                    
                    # Wait longer for process to finish writing files
                    try:
                        process.wait(timeout=15)  # Increased timeout
                        print(f"SUMO process {process_id} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        print(f"SUMO process {process_id} didn't terminate gracefully within 15s, force killing")
                        process.kill()
                        # Even after killing, give a moment for file system to sync
                        time.sleep(1)
                
                # Parse and save session statistics 
                print(f"Parsing simulation output for session {session_id}")
                try:
                    session_stats = self._parse_sumo_output_files(Path(session_path))
                    current_time = datetime.now().isoformat()
                    
                    if session_stats:
                        # Save session statistics to a JSON file (backward compatibility)
                        stats_file = Path(session_path) / "session_statistics.json"
                        with open(stats_file, 'w') as f:
                            json.dump({
                                'session_id': session_id,
                                'completed_at': current_time,
                                'completion_reason': reason,
                                'statistics': session_stats,
                                'can_analyze': True
                            }, f, indent=2)
                        print(f"Session statistics saved to {stats_file}")
                        
                        # Save analytics to database if available
                        if self.db_service:
                            try:
                                # Convert session_stats to KPI format
                                kpis_data = {
                                    'total_vehicles_loaded': session_stats.get('totalVehicles', 0),
                                    'total_vehicles_completed': session_stats.get('totalVehicles', 0),
                                    'avg_travel_time': session_stats.get('averageTravelTime', 0),
                                    'avg_waiting_time': session_stats.get('averageWaitingTime', 0),
                                    'avg_speed': session_stats.get('averageSpeed', 0) / 3.6 if session_stats.get('averageSpeed', 0) > 0 else 0,  # Convert km/h to m/s
                                    'throughput': session_stats.get('throughput', 0),
                                    'simulation_duration': session_stats.get('simulationTime', 0),
                                    'notes': f"Completed: {reason}"
                                }
                                
                                success = self.db_service.save_kpis(session_id, kpis_data)
                                if success:
                                    print(f"Session analytics saved to database for session {session_id}")
                                else:
                                    print(f"Warning: Failed to save analytics to database for session {session_id}")
                            except Exception as db_error:
                                print(f"Error saving analytics to database: {db_error}")
                        
                        # Also save session metadata for the analytics API (backward compatibility)
                        metadata_file = Path(session_path) / "session_metadata.json"
                        
                        # Try to load existing config to get network info
                        config_file = Path(session_path) / "config.json"
                        network_id = "unknown"
                        if config_file.exists():
                            try:
                                with open(config_file, 'r') as f:
                                    config_data = json.load(f)
                                    # Extract network info from config or session path
                                    network_id = config_data.get('network_id', 'unknown')
                                    if network_id == 'unknown':
                                        # Try to infer from SUMO files in the directory
                                        sumo_files = list(Path(session_path).glob('*.sumocfg'))
                                        if sumo_files:
                                            network_id = sumo_files[0].stem
                            except Exception as e:
                                print(f"Could not load config for network ID: {e}")
                        
                        metadata = {
                            'session_id': session_id,
                            'created_at': current_time,
                            'completed_at': current_time,
                            'completion_reason': reason,
                            'network_id': network_id,
                            'can_analyze': True,
                            'has_statistics': True,
                            'status': 'completed'
                        }
                        
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        print(f"Session metadata saved to {metadata_file}")
                    else:
                        print(f"Warning: No statistics could be parsed for session {session_id}")
                        
                        # Still save metadata even without statistics
                        metadata_file = Path(session_path) / "session_metadata.json"
                        metadata = {
                            'session_id': session_id,
                            'created_at': current_time,
                            'completed_at': current_time,
                            'completion_reason': reason,
                            'network_id': 'unknown',
                            'can_analyze': False,
                            'has_statistics': False,
                            'status': 'completed_no_data'
                        }
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        print(f"Session metadata (no stats) saved to {metadata_file}")
                        
                except Exception as e:
                    print(f"Error parsing session statistics for {session_id}: {e}")
                    
                    # Save basic metadata even if statistics parsing failed
                    try:
                        metadata_file = Path(session_path) / "session_metadata.json"
                        metadata = {
                            'session_id': session_id,
                            'created_at': datetime.now().isoformat(),
                            'completed_at': datetime.now().isoformat(),
                            'completion_reason': f"{reason} (with errors)",
                            'network_id': 'unknown',
                            'can_analyze': False,
                            'has_statistics': False,
                            'status': 'completed_with_errors',
                            'error': str(e)
                        }
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        print(f"Basic session metadata saved despite errors")
                    except Exception as meta_error:
                        print(f"Failed to save even basic metadata: {meta_error}")
                
                # Remove from active processes
                del self.active_processes[session_id]
                print(f"Removed session {session_id} from active processes")
                
                # Broadcast simulation completion via WebSocket
                if self.websocket_handler:
                    self.websocket_handler.broadcast_simulation_status('completed', f"Simulation completed: {reason}", {
                        'session_id': session_id,
                        'reason': reason,
                        'process_id': process_id
                    })
                    
                    # Also send session completed event for UI updates
                    completion_data = {
                        'session_id': session_id,
                        'reason': reason,
                        'completed_at': datetime.now().isoformat(),
                        'can_analyze': True  # Session is now ready for analysis
                    }
                    self.websocket_handler.broadcast_message('session_completed', completion_data)
                
                print(f"Simulation completion handled successfully for session {session_id}")
                
        except Exception as e:
            print(f"Error handling simulation completion for session {session_id}: {e}")

    def _start_process_monitor(self):
        """
        Start a background thread to periodically check for ended simulations
        """
        def monitor_processes():
            while True:
                try:
                    # Check every 10 seconds
                    import time
                    time.sleep(10)
                    
                    # Check for dead processes
                    orphaned_sessions = []
                    for session_id, data in self.active_processes.copy().items():
                        process = data["process"]
                        if process.poll() is not None:  # Process has ended
                            print(f"Detected ended simulation process for session {session_id}")
                            orphaned_sessions.append(session_id)
                    
                    # Clean up orphaned sessions
                    for session_id in orphaned_sessions:
                        try:
                            data = self.active_processes[session_id]
                            process_id = data["info"]["processId"]
                            session_path = data["info"]["sessionPath"]
                            
                            # Parse and save session statistics
                            try:
                                session_stats = self._parse_sumo_output_files(Path(session_path))
                                if session_stats:
                                    stats_file = Path(session_path) / "session_statistics.json"
                                    with open(stats_file, 'w') as f:
                                        json.dump({
                                            'session_id': session_id,
                                            'completed_at': datetime.now().isoformat(),
                                            'completion_reason': 'Natural completion (detected)',
                                            'statistics': session_stats,
                                            'can_analyze': True
                                        }, f, indent=2)
                                    print(f"Session statistics saved to {stats_file}")
                            except Exception as e:
                                print(f"Error parsing session statistics for {session_id}: {e}")
                            
                            # Remove from active processes
                            del self.active_processes[session_id]
                            
                            # Broadcast completion
                            if self.websocket_handler:
                                self.websocket_handler.broadcast_simulation_status('completed', 'Simulation completed', {
                                    'session_id': session_id,
                                    'reason': 'Natural completion (detected)',
                                    'process_id': process_id
                                })
                                
                                completion_data = {
                                    'session_id': session_id,
                                    'reason': 'Natural completion (detected)',
                                    'completed_at': datetime.now().isoformat(),
                                    'can_analyze': True
                                }
                                self.websocket_handler.broadcast_message('session_completed', completion_data)
                            
                            print(f"Cleaned up orphaned session {session_id}")
                            
                        except Exception as e:
                            print(f"Error cleaning up orphaned session {session_id}: {e}")
                            
                except Exception as e:
                    print(f"Error in process monitor: {e}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
        monitor_thread.start()
        print("Process monitor thread started")

    def _update_sumo_config_timing(self, session_dir: Path, network_id: str, begin_time: int, end_time: int) -> None:
        """
        Update the SUMO configuration file with correct begin and end times
        
        Args:
            session_dir: Path to session directory
            network_id: Network identifier
            begin_time: Simulation begin time in seconds
            end_time: Simulation end time in seconds
        """
        config_file = session_dir / f"{network_id}.sumocfg"
        
        if not config_file.exists():
            print(f"WARNING: SUMO config file not found: {config_file}")
            return
            
        try:
            # Parse the existing configuration file
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Find or create the time element
            time_elem = root.find('time')
            if time_elem is None:
                time_elem = ET.SubElement(root, 'time')
            
            # Update begin time
            begin_elem = time_elem.find('begin')
            if begin_elem is None:
                begin_elem = ET.SubElement(time_elem, 'begin')
            begin_elem.set('value', str(begin_time))
            
            # Update end time
            end_elem = time_elem.find('end')
            if end_elem is None:
                end_elem = ET.SubElement(time_elem, 'end')
            end_elem.set('value', str(end_time))
            
            # Write the updated configuration back to the file
            tree.write(config_file, encoding='UTF-8', xml_declaration=True)
            
            print(f"DEBUG: Updated SUMO config timing - begin: {begin_time}s, end: {end_time}s")
            
        except ET.ParseError as e:
            print(f"ERROR: Failed to parse SUMO config file {config_file}: {e}")
        except Exception as e:
            print(f"ERROR: Failed to update SUMO config timing: {e}")
