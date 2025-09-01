"""
Simulation Management Module

Handles the configuration-first simulation workflow including:
- Session configuration storage
- Network copying and modification
- SUMO simulation launching with live data streaming
- File management for session isolation

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

# Import SUMO libraries for TraCI communication
try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    print("Warning: TraCI not available. Live data collection will be disabled.")
    TRACI_AVAILABLE = False

class SimulationManager:
    def __init__(self, base_networks_dir: str = "networks", websocket_handler=None):
        """
        Initialize the simulation manager
        
        Args:
            base_networks_dir: Directory containing original network files
            websocket_handler: WebSocket handler for live data broadcasting
        """
        # Get the backend directory path (where this script is located)
        backend_dir = Path(__file__).parent
        
        # Ensure paths are relative to the backend directory
        self.base_networks_dir = backend_dir / base_networks_dir
        self.sessions_dir = backend_dir / "sessions"
        self.active_processes = {}
        self.websocket_handler = websocket_handler
        
        # Ensure directories exist
        self.base_networks_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        
    def save_session_config(self, session_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save session configuration to persistent storage
        
        Args:
            session_id: Unique session identifier
            config_data: Configuration parameters
            
        Returns:
            Result dictionary with success status
        """
        try:
            session_config_dir = self.sessions_dir / session_id
            session_config_dir.mkdir(exist_ok=True)
            
            config_file = session_config_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return {
                "success": True,
                "message": "Configuration saved successfully",
                "config_path": str(config_file)
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
            
            # Scan for .net.xml files in the networks directory
            for network_file in self.base_networks_dir.glob("**/*.net.xml"):
                try:
                    # Parse network file to get basic info
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
                    
                    network_info = {
                        "id": network_file.stem,
                        "name": network_file.stem.replace("_", " ").title(),
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
            # Map frontend configuration to backend configuration
            if 'trafficIntensity' in config:
                config['sumo_traffic_intensity'] = config['trafficIntensity']
                print(f"DEBUG: Mapped trafficIntensity {config['trafficIntensity']} to sumo_traffic_intensity")
            
            session_dir = self.sessions_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            network_dest = session_dir / f"{network_id}.net.xml"
            
            # Check if we need to generate network programmatically or copy existing
            if network_path == "generated":
                # Generate network based on config
                self._generate_network_programmatically(network_dest, config)
                is_osm_scenario = False
            else:
                # Copy existing network files to session directory
                network_source = Path(network_path)
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
                    "network": f"{network_id}.net.xml",
                    "routes": f"{network_id}.rou.xml" if not is_osm_scenario else "routes/",
                    "config": f"{network_id}.sumocfg",
                    "additional": f"{network_id}.add.xml"
                }
            }
            
            metadata_file = session_dir / "session_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(session_metadata, f, indent=2)
            
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
            # Copy main network file
            network_files = list(source_dir.glob("*.net.xml"))
            if network_files:
                network_source = network_files[0]
                network_dest = session_dir / f"{network_id}.net.xml"
                shutil.copy2(network_source, network_dest)
            
            # Copy SUMO config file
            config_files = list(source_dir.glob("*.sumocfg"))
            if config_files:
                config_source = config_files[0]
                config_dest = session_dir / f"{network_id}.sumocfg"
                self._process_osm_config_file(config_source, config_dest, network_id, config)
            
            # Copy routes directory with vehicle filtering
            routes_source_dir = source_dir / "routes"
            if routes_source_dir.exists():
                routes_dest_dir = session_dir / "routes"
                routes_dest_dir.mkdir(exist_ok=True)
                
                # Apply vehicle type filtering
                enabled_vehicles = config.get('enabledVehicles', ['passenger', 'bus', 'truck', 'motorcycle'])
                self._copy_and_filter_routes(routes_source_dir, routes_dest_dir, enabled_vehicles, config)
            
            # Copy additional files (views, edge data, etc.)
            additional_patterns = ['*.osm_view.xml', '*.view.xml', '*.add.xml', '*output_add.xml', 'edgeData*', 'stats*', 'tripinfos*']
            for pattern in additional_patterns:
                for source_file in source_dir.glob(pattern):
                    if source_file.is_file():
                        # Don't rename these files - keep original names since config expects them
                        dest_file = session_dir / source_file.name
                        shutil.copy2(source_file, dest_file)
        
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
            
            # Update network file reference
            net_input = root.find('.//net-file')
            if net_input is not None:
                net_input.set('value', f"{network_id}.net.xml")
            
            # Update route files based on enabled vehicles
            enabled_vehicles = config.get('enabledVehicles', ['passenger', 'bus', 'truck', 'motorcycle'])
            route_files = []
            for vehicle_type in enabled_vehicles:
                route_file = f"routes/osm.{vehicle_type}.rou.xml"
                if (dest_config.parent / route_file).exists():
                    route_files.append(route_file)
            
            route_input = root.find('.//route-files')
            if route_input is not None and route_files:
                route_input.set('value', ','.join(route_files))
                print(f"Updated route files: {route_files}")
            
            # Update simulation time settings
            duration = config.get('duration', 3600)
            step_length = config.get('stepLength', 1.0)
            
            # Find or create time section
            time_section = root.find('.//time')
            if time_section is None:
                # Create time section if it doesn't exist
                time_section = ET.SubElement(root, 'time')
            
            # Update or create time elements
            begin_elem = time_section.find('begin')
            if begin_elem is None:
                begin_elem = ET.SubElement(time_section, 'begin')
            begin_elem.set('value', '0')
            
            end_elem = time_section.find('end')
            if end_elem is None:
                end_elem = ET.SubElement(time_section, 'end')
            end_elem.set('value', str(duration))
            
            step_elem = time_section.find('step-length')
            if step_elem is None:
                step_elem = ET.SubElement(time_section, 'step-length')
            step_elem.set('value', str(step_length))
            
            print(f"Updated OSM config: duration={duration}s, step-length={step_length}s")
            
            # Save updated config
            tree.write(dest_config, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"Warning: Could not process OSM config file: {e}")
            # Fallback: just copy the file
            shutil.copy2(source_config, dest_config)
    
    def _copy_and_filter_routes(self, source_dir: Path, dest_dir: Path, 
                              enabled_vehicles: List[str], config: Dict[str, Any]):
        """
        Copy route files and apply vehicle type filtering
        
        Args:
            source_dir: Source routes directory
            dest_dir: Destination routes directory
            enabled_vehicles: List of enabled vehicle types
            config: Configuration parameters
        """
        try:
            traffic_density = config.get('trafficDensity', 1.0)
            
            # Copy and filter route files
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
                elif vehicle_type:
                    # Create empty/commented route file for disabled vehicles
                    dest_file = dest_dir / route_file.name
                    self._create_disabled_route_file(dest_file, route_file)
            
            # Copy trip files as well
            for trip_file in source_dir.glob("*.trips.xml"):
                vehicle_type = None
                for vtype in ['passenger', 'bus', 'truck', 'motorcycle']:
                    if vtype in trip_file.name.lower():
                        vehicle_type = vtype
                        break
                
                if vehicle_type and vehicle_type in enabled_vehicles:
                    dest_file = dest_dir / trip_file.name
                    shutil.copy2(trip_file, dest_file)
        
        except Exception as e:
            print(f"Error filtering routes: {e}")
            # Fallback: copy all files
            for file in source_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest_dir / file.name)
    
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
        network_file = session_dir / f"{network_id}.net.xml"
        
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
        Use SUMO's built-in tools to generate realistic routes
        """
        import subprocess
        import tempfile
        
        network_file = session_dir / f"{network_id}.net.xml"
        route_file = session_dir / f"{network_id}.rou.xml"
        
        # Create trips file first
        trips_file = session_dir / f"{network_id}.trips.xml"
        
        # Generate random trips using SUMO's randomTrips.py
        try:
            # Use a subset of edges as origins/destinations
            selected_edges = edge_ids[:min(20, len(edge_ids))]
            
            trips_content = '''<?xml version="1.0" encoding="UTF-8"?>
<trips xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/trips_file.xsd">
'''
            
            # Create simple trips between different edges
            for i in range(vehicle_count):
                if len(selected_edges) >= 2:
                    from_edge = selected_edges[i % len(selected_edges)]
                    to_edge = selected_edges[(i + 1) % len(selected_edges)]
                    depart_time = i * 5  # 5 second intervals
                    
                    trips_content += f'    <trip id="trip_{i}" depart="{depart_time}" from="{from_edge}" to="{to_edge}"/>\n'
            
            trips_content += '</trips>'
            
            with open(trips_file, 'w') as f:
                f.write(trips_content)
            
            # Convert trips to routes using duarouter
            duarouter_cmd = [
                "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\duarouter.exe",
                "-n", str(network_file),
                "-t", str(trips_file),
                "-o", str(route_file),
                "--ignore-errors"
            ]
            
            result = subprocess.run(duarouter_cmd, capture_output=True, text=True, cwd=session_dir)
            
            if result.returncode == 0:
                print("Successfully generated routes using duarouter")
                return
            else:
                print(f"duarouter failed: {result.stderr}")
                raise Exception("duarouter failed")
                
        except Exception as e:
            print(f"Error in SUMO route generation: {e}")
            raise
    
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
        traffic_intensity = config.get('sumo_traffic_intensity', 1.0)  # Traffic intensity multiplier
        
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
        <net-file value="{network_id}.net.xml"/>
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
        print(f"  Traffic intensity: {traffic_intensity}x")
        if traffic_intensity != 1.0:
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
        Generate additional file for road closures and other modifications
        
        Args:
            additional_file: Path to additional file
            config: Configuration parameters (simplified structure)
        """
        additional_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- Simple additional file for essential simulation configuration -->
    <!-- Traffic intensity is now controlled via SUMO's --scale parameter -->
    
    <!-- Detectors for Live Data Collection -->
    <!-- Basic detectors can be added here in future versions -->
    
</additional>'''
        
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
    
    def _generate_gui_settings_file(self, gui_settings_file: Path):
        """
        Generate GUI settings file for SUMO GUI
        
        Args:
            gui_settings_file: Path to GUI settings file
        """
        gui_settings_content = '''<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/guiConfiguration.xsd">

    <gui>
        <viewport zoom="50.0" x="300.0" y="300.0" angle="0.0"/>
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
            
            # Prepare SUMO command
            sumo_path = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin"
            if enable_gui:
                sumo_cmd = [os.path.join(sumo_path, "sumo-gui.exe")]
            else:
                sumo_cmd = [os.path.join(sumo_path, "sumo.exe")]
            
            sumo_cmd.extend([
                "-c", config_file.name,  # Use just the filename since we set cwd=session_dir
                "--time-to-teleport", "300",  # Prevent vehicles from getting stuck
                "--no-warnings"  # Reduce console spam
            ])
            
            # Add traffic intensity scaling if specified
            traffic_intensity = config.get('sumo_traffic_intensity', 1.0)
            if traffic_intensity != 1.0:
                sumo_cmd.extend(["--scale", str(traffic_intensity)])
                print(f"DEBUG: Adding traffic scaling: --scale {traffic_intensity}")
            else:
                print(f"DEBUG: No traffic scaling (intensity = 1.0)")
            
            # Add gaming mode settings for GUI (automatic start and better UX)
            if enable_gui:
                # Use GUI settings file for proper input handling
                gui_settings_path = os.path.join(os.path.dirname(__file__), "gui_settings.xml")
                sumo_cmd.extend([
                    "--gui-settings-file", gui_settings_path,  # Use custom GUI settings
                    "--start",       # Start simulation automatically
                    "--game",        # Enable gaming mode
                    "--game.mode", "tls",  # Traffic Light Signal gaming mode
                    "--window-size", "1200,800",  # Set consistent window size
                    "--delay", "50"  # Override delay for more responsive gaming
                ])
                # Gaming mode: Interactive traffic light control and enhanced user experience
                print(f"DEBUG: Using GUI settings file: {gui_settings_path}")
            else:
                sumo_cmd.extend(["--quit-on-end"])
            
            # Enable TraCI when live data is requested, regardless of GUI mode
            if enable_live_data:
                # Enable TraCI for live data collection
                sumo_cmd.extend([
                    "--remote-port", "8813"
                ])
                # Add --start flag only if GUI is disabled (GUI mode already adds it above)
                if not enable_gui:
                    sumo_cmd.extend(["--start"])  # Start simulation immediately for headless mode
            
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
                "command": " ".join(sumo_cmd),
                "port": 8813 if enable_live_data else None,
                "startTime": datetime.now().isoformat()
            }
            
            self.active_processes[session_id] = {
                "process": process,
                "info": process_info,
                "paused": False  # Initialize as not paused
            }
            
            # Start data collection thread if live data is enabled
            if enable_live_data and TRACI_AVAILABLE and self.websocket_handler:
                print(f"Starting data collection thread for session {session_id}")
                def start_data_collection():
                    print(f"Data collection thread starting, waiting 3 seconds for SUMO startup...")
                    time.sleep(3)  # Wait for SUMO to start up
                    self._start_data_collection_thread(session_id, 8813, config)
                
                threading.Thread(target=start_data_collection, daemon=True).start()
            else:
                if not enable_live_data:
                    print("Live data collection disabled")
                elif not TRACI_AVAILABLE:
                    print("TraCI not available")
                elif not self.websocket_handler:
                    print("WebSocket handler not available")
            
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
                    process.terminate()
                    
                    # Wait for process to finish
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    
                    # Remove from active processes
                    del self.active_processes[session_id]
                    
                    return {
                        "success": True,
                        "message": "Simulation stopped successfully"
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
    
    def pause_simulation(self, process_id: int) -> Dict[str, Any]:
        """
        Pause running simulation via TraCI
        
        Args:
            process_id: Process identifier
            
        Returns:
            Result dictionary with success status
        """
        print(f"DEBUG: SimulationManager.pause_simulation called with process_id: {process_id}")
        try:
            # Find the session with this process ID
            session_id = None
            for sid, session_data in self.active_processes.items():
                if session_data["info"]["processId"] == process_id:
                    session_id = sid
                    break
            
            print(f"DEBUG: Found session_id: {session_id}")
            print(f"DEBUG: Active processes: {list(self.active_processes.keys())}")
            
            if session_id and TRACI_AVAILABLE:
                # Pause the simulation by stopping the simulation step loop
                # We'll set a flag to pause the simulation loop
                if session_id in self.active_processes:
                    self.active_processes[session_id]["paused"] = True
                    print(f"DEBUG: Set paused flag to True for session {session_id}")
                    
                    return {
                        "success": True,
                        "message": "Simulation paused successfully",
                        "processId": process_id
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found or TraCI not available"
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in pause_simulation: {e}")
            return {
                "success": False,
                "message": f"Failed to pause simulation: {str(e)}"
            }
    
    def resume_simulation(self, process_id: int) -> Dict[str, Any]:
        """
        Resume paused simulation via TraCI
        
        Args:
            process_id: Process identifier
            
        Returns:
            Result dictionary with success status
        """
        print(f"DEBUG: SimulationManager.resume_simulation called with process_id: {process_id}")
        try:
            # Find the session with this process ID
            session_id = None
            for sid, session_data in self.active_processes.items():
                if session_data["info"]["processId"] == process_id:
                    session_id = sid
                    break
            
            print(f"DEBUG: Found session_id: {session_id}")
            
            if session_id and TRACI_AVAILABLE:
                # Resume the simulation by clearing the pause flag
                if session_id in self.active_processes:
                    self.active_processes[session_id]["paused"] = False
                    print(f"DEBUG: Set paused flag to False for session {session_id}")
                    
                    return {
                        "success": True,
                        "message": "Simulation resumed successfully",
                        "processId": process_id
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found or TraCI not available"
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in resume_simulation: {e}")
            return {
                "success": False,
                "message": f"Failed to resume simulation: {str(e)}"
            }

    def get_zoom_level(self, process_id: int) -> Dict[str, Any]:
        """
        Get current zoom level from SUMO GUI via TraCI
        
        Args:
            process_id: Process identifier
            
        Returns:
            Result dictionary with current zoom level
        """
        try:
            # Find the session with this process ID
            session_id = None
            for sid, session_data in self.active_processes.items():
                if session_data["info"]["processId"] == process_id:
                    session_id = sid
                    break
            
            if session_id and TRACI_AVAILABLE:
                try:
                    # Get zoom level from first view (View #0)
                    zoom_level = traci.gui.getZoom("View #0")
                    return {
                        "success": True,
                        "zoomLevel": round(zoom_level, 2),
                        "processId": process_id
                    }
                except Exception as traci_e:
                    print(f"DEBUG: TraCI zoom retrieval error: {traci_e}")
                    return {
                        "success": False,
                        "message": f"Failed to get zoom level: {str(traci_e)}"
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found or TraCI not available"
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in get_zoom_level: {e}")
            return {
                "success": False,
                "message": f"Failed to get zoom level: {str(e)}"
            }

    def set_zoom_level(self, process_id: int, zoom_level: float) -> Dict[str, Any]:
        """
        Set zoom level in SUMO GUI via TraCI
        
        Args:
            process_id: Process identifier
            zoom_level: New zoom level (percentage, e.g., 100.0 for 100%)
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Find the session with this process ID
            session_id = None
            for sid, session_data in self.active_processes.items():
                if session_data["info"]["processId"] == process_id:
                    session_id = sid
                    break
            
            if session_id and TRACI_AVAILABLE:
                try:
                    # Set zoom level for first view (View #0)
                    traci.gui.setZoom("View #0", zoom_level)
                    return {
                        "success": True,
                        "zoomLevel": zoom_level,
                        "processId": process_id
                    }
                except Exception as traci_e:
                    print(f"DEBUG: TraCI zoom setting error: {traci_e}")
                    return {
                        "success": False,
                        "message": f"Failed to set zoom level: {str(traci_e)}"
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found or TraCI not available"
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in set_zoom_level: {e}")
            return {
                "success": False,
                "message": f"Failed to set zoom level: {str(e)}"
            }

    def center_view(self, process_id: int) -> Dict[str, Any]:
        """
        Center the view to show the entire network
        
        Args:
            process_id: Process identifier
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Find the session with this process ID
            session_id = None
            for sid, session_data in self.active_processes.items():
                if session_data["info"]["processId"] == process_id:
                    session_id = sid
                    break
            
            if session_id and TRACI_AVAILABLE:
                try:
                    # Get network boundary and set view to show the entire network
                    boundary = traci.gui.getBoundary("View #0")
                    traci.gui.setBoundary("View #0", boundary[0], boundary[1], boundary[2], boundary[3])
                    
                    # Also get the new zoom level to return it
                    zoom_level = traci.gui.getZoom("View #0")
                    
                    return {
                        "success": True,
                        "message": "View centered successfully",
                        "zoomLevel": round(zoom_level, 2),
                        "processId": process_id
                    }
                except Exception as traci_e:
                    print(f"DEBUG: TraCI center view error: {traci_e}")
                    return {
                        "success": False,
                        "message": f"Failed to center view: {str(traci_e)}"
                    }
            
            return {
                "success": False,
                "message": "Simulation process not found or TraCI not available"
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in center_view: {e}")
            return {
                "success": False,
                "message": f"Failed to center view: {str(e)}"
            }

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
        Start a background thread to collect live data from SUMO via TraCI
        
        Args:
            session_id: Session identifier
            port: TraCI port number
            config: Session configuration containing stepLength and other settings
        """
        def collect_data():
            try:
                # Extract configuration settings
                step_length = config.get('stepLength', 1.0)  # Default to 1 second
                duration = config.get('duration', 3600)  # Default to 1 hour
                
                print(f"Starting data collection for session {session_id}")
                print(f"Step length: {step_length}s, Duration: {duration}s")
                
                # Connect to SUMO TraCI
                print(f"Connecting to SUMO TraCI on port {port} for session {session_id}")
                
                # Try to connect with multiple attempts
                max_attempts = 10
                connected = False
                for attempt in range(max_attempts):
                    try:
                        traci.init(port)
                        print(f"Successfully connected to TraCI on port {port}")
                        connected = True
                        break
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(f"TraCI connection attempt {attempt + 1} failed, retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            print(f"Failed to connect to TraCI after {max_attempts} attempts: {e}")
                            return
                
                if not connected:
                    return
                
                # Ensure simulation starts automatically
                print(f"Starting simulation automatically for session {session_id}")
                
                # Start simulation if it's not already running
                # This ensures SUMO GUI starts immediately instead of staying paused
                try:
                    # Check if simulation needs to be started
                    current_time = traci.simulation.getTime()
                    print(f"Initial simulation time: {current_time}")
                    
                    # Force simulation to start if it's at time 0 and paused
                    if current_time == 0:
                        print("Simulation at time 0, ensuring it starts...")
                        # Step once to initialize
                        traci.simulationStep()
                        current_time = traci.simulation.getTime()
                        print(f"After initial step, simulation time: {current_time}")
                    
                except Exception as e:
                    print(f"Error during simulation initialization: {e}")
                
                # Initialize simulation time tracking
                last_sim_time = 0
                start_time = time.time()
                step_count = 0
                
                while session_id in self.active_processes:
                    try:
                        # Check if process is still running
                        process_data = self.active_processes[session_id]
                        if process_data["process"].poll() is not None:
                            print(f"SUMO process ended for session {session_id}")
                            break
                        
                        # Check if simulation is paused
                        if process_data.get("paused", False):
                            print(f"DEBUG: Simulation paused for session {session_id}, waiting...")
                            time.sleep(0.5)  # Check every half second if still paused
                            continue
                        
                        # Step the simulation forward (this starts/continues the simulation)
                        traci.simulationStep()
                        
                        # Get current simulation time after stepping
                        sim_time = traci.simulation.getTime()
                        
                        # Check if simulation time is progressing
                        if sim_time == last_sim_time and sim_time > 0:
                            print(f"Warning: Simulation time not advancing for session {session_id} at time {sim_time}")
                        
                        last_sim_time = sim_time
                        
                        # Check if simulation has reached configured duration
                        if sim_time >= duration:
                            print(f"Simulation reached configured duration ({duration}s) for session {session_id}")
                            break
                        
                        # Check if simulation is running
                        min_expected_vehicles = traci.simulation.getMinExpectedNumber()
                        if min_expected_vehicles == 0 and sim_time > 60:  # Allow some time for vehicles to spawn
                            print(f"No more vehicles expected, simulation ending for session {session_id}")
                            break
                        
                        # Log progress based on step length
                        if int(sim_time) % (step_length * 30) == 0 and int(sim_time) > 0:
                            print(f"Simulation time: {sim_time}s for session {session_id}")
                        
                        # Get vehicle data
                        vehicle_ids = traci.vehicle.getIDList()
                        total_vehicles = len(vehicle_ids)
                        
                        # Calculate average speed
                        total_speed = 0
                        if total_vehicles > 0:
                            for veh_id in vehicle_ids:
                                try:
                                    speed = traci.vehicle.getSpeed(veh_id)
                                    total_speed += speed
                                except:
                                    pass
                            avg_speed = total_speed / total_vehicles
                        else:
                            avg_speed = 0
                        
                        # Get throughput (vehicles per hour)
                        # This is a simplified calculation
                        throughput = total_vehicles * 3600 / max(sim_time, 1)
                        
                        # Prepare live statistics data
                        live_data = {
                            'simulation_time': int(sim_time),
                            'active_vehicles': total_vehicles,
                            'avg_speed': round(avg_speed * 3.6, 1),  # Convert m/s to km/h
                            'throughput': round(throughput, 0),
                            'timestamp': time.time(),
                            'session_id': session_id
                        }
                        
                        # Add zoom level to live data (try to get it, but don't fail if it doesn't work)
                        try:
                            zoom_level = traci.gui.getZoom("View #0")
                            live_data['zoom_level'] = round(zoom_level, 2)
                        except Exception:
                            # Zoom might not be available in headless mode
                            pass
                        
                        # Debug: Print data every few steps
                        step_count += 1
                        if step_count % 5 == 0:  # Print every 5 steps
                            print(f"Step {step_count}: sim_time={sim_time}s, vehicles={total_vehicles}, avg_speed={avg_speed:.1f}m/s")
                        
                        # Broadcast data via WebSocket
                        if self.websocket_handler:
                            self.websocket_handler.broadcast_simulation_data(live_data)
                        else:
                            print("Warning: No WebSocket handler available for broadcasting")
                        
                        # Sleep for the configured step length
                        time.sleep(step_length)  # Use user-configured step length
                        
                    except Exception as e:
                        print(f"Error collecting data for session {session_id}: {e}")
                        time.sleep(step_length)  # Use step length even for error recovery
                
                print(f"Data collection ended for session {session_id}")
                print(f"Final simulation time: {traci.simulation.getTime()}s")
                
            except Exception as e:
                print(f"Failed to connect to TraCI for session {session_id}: {e}")
            finally:
                try:
                    traci.close()
                    print(f"TraCI connection closed for session {session_id}")
                except:
                    pass
        
        # Start the data collection thread
        data_thread = threading.Thread(target=collect_data, daemon=True)
        data_thread.start()
