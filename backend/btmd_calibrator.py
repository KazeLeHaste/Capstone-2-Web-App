"""
BTMD Traffic Data Calibration Script

This script calibrates SUMO traffic simulation networks to match real-world traffic data
collected by the Bacoor Traffic Management Department (BTMD).

Features:
- Converts BTMD vehicle count data into SUMO flow definitions
- Adjusts vehicle type proportions to match observed traffic mix
- Implements temporal distribution (peak/off-peak patterns)
- Generates calibrated route files using <flow> elements
- Standardizes configuration across all networks

Root Causes Addressed:
- Root Cause #1: Under-populated route files
- Root Cause #2: Temporal distribution mismatch  
- Root Cause #3: Vehicle type proportion mismatch
- Root Cause #7: Configuration standardization

Author: Traffic Simulator Team
Date: December 2025
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import gzip

# BTMD Traffic Data - Vehicle counts and proportions per intersection
# Data represents 16-hour observation period (6 AM - 10 PM)
BTMD_TRAFFIC_DATA = {
    "SM Bacoor Area": {
        "name": "Aguinaldo Highway and Tirona highway Intersection (SM Bacoor Area)",
        "observation_hours": 16,  # 6:01 AM - 10:00 PM
        "total_vehicles_per_day": 42148,
        "avg_vehicles_per_hour": 2634,
        "peak_hour_volume": 2823,  # 6:01-7:00 AM
        "vehicle_mix": {
            "passenger": 0.452,  # Private vehicles: 19,061 / 42,148
            "motorcycle": 0.319,  # Motorcycles: 13,452 / 42,148
            "truck": 0.101,      # Trucks (combined): 4,277 / 42,148
            "jeepney": 0.055,    # Jeepneys: 2,336 / 42,148
            "bus": 0.022,        # Buses: 907 / 42,148
            "taxi": 0.041        # Taxis/UV: 1,725 / 42,148 (mapped to passenger)
        },
        "hourly_patterns": {  # Relative to average
            "6-7": 1.07,   # 2,823 / 2,634
            "7-8": 1.07,   # 2,821 / 2,634
            "8-9": 1.05,   # 2,756 / 2,634
            "9-10": 1.03,  # 2,713 / 2,634
            "10-11": 1.03, # 2,703 / 2,634
            "11-12": 1.03, # 2,708 / 2,634
            "12-13": 1.02, # 2,685 / 2,634
            "13-14": 1.02, # 2,692 / 2,634
            "14-15": 1.02, # 2,681 / 2,634
            "15-16": 1.01, # 2,670 / 2,634
            "16-17": 0.98, # 2,581 / 2,634
            "17-18": 0.96, # 2,528 / 2,634
            "18-19": 0.96, # 2,527 / 2,634
            "19-20": 0.94, # 2,468 / 2,634
            "20-21": 0.92, # 2,419 / 2,634
            "21-22": 0.90  # 2,373 / 2,634
        }
    },
    "SM Molino Area": {
        "name": "Daang Hari Road and Molino Road Intersection (SM Molino Area)",
        "observation_hours": 16,
        "total_vehicles_per_day": 30650,
        "avg_vehicles_per_hour": 1916,
        "peak_hour_volume": 2085,
        "vehicle_mix": {
            "passenger": 0.581,  # 17,805 / 30,650
            "motorcycle": 0.322, # 9,878 / 30,650
            "truck": 0.056,      # 1,720 / 30,650
            "jeepney": 0.000,    # No jeepney data
            "bus": 0.004,        # 109 / 30,650
            "taxi": 0.020        # 610 / 30,650 (mapped to passenger)
        },
        "hourly_patterns": {
            "6-7": 1.09, "7-8": 1.02, "8-9": 1.00, "9-10": 1.03,
            "10-11": 1.02, "11-12": 1.00, "12-13": 1.00, "13-14": 1.02,
            "14-15": 1.02, "15-16": 1.05, "16-17": 0.97, "17-18": 0.99,
            "18-19": 0.97, "19-20": 0.94, "20-21": 0.94, "21-22": 0.91
        }
    },
    "Jollibee Molino Area": {
        "name": "Bacoor Blvd. and Molino Road Intersection (Jollibee Molino Area)",
        "observation_hours": 16,
        "total_vehicles_per_day": 22072,
        "avg_vehicles_per_hour": 1380,
        "peak_hour_volume": 1485,
        "vehicle_mix": {
            "passenger": 0.527,  # 11,627 / 22,072
            "motorcycle": 0.320, # 7,068 / 22,072
            "truck": 0.024,      # 535 / 22,072
            "jeepney": 0.095,    # 2,106 / 22,072
            "bus": 0.000,        # No bus data
            "taxi": 0.033        # 736 / 22,072
        },
        "hourly_patterns": {
            "6-7": 1.08, "7-8": 1.06, "8-9": 1.05, "9-10": 1.04,
            "10-11": 1.02, "11-12": 0.99, "12-13": 0.99, "13-14": 0.98,
            "14-15": 0.98, "15-16": 0.97, "16-17": 0.97, "17-18": 0.98,
            "18-19": 0.99, "19-20": 0.97, "20-21": 0.98, "21-22": 0.95
        }
    },
    "St Dominic Area": {
        "name": "Bacoor Blvd. and Aguinaldo Highway Intersection (St. Dominic Area)",
        "observation_hours": 16,
        "total_vehicles_per_day": 13981,
        "avg_vehicles_per_hour": 874,
        "peak_hour_volume": 974,
        "vehicle_mix": {
            "passenger": 0.344,  # 4,816 / 13,981
            "motorcycle": 0.335, # 4,678 / 13,981
            "truck": 0.181,      # 2,528 / 13,981
            "jeepney": 0.072,    # 1,004 / 13,981
            "bus": 0.013,        # 180 / 13,981
            "taxi": 0.034        # 482 / 13,981
        },
        "hourly_patterns": {
            "6-7": 1.03, "7-8": 1.00, "8-9": 1.00, "9-10": 1.11,
            "10-11": 1.11, "11-12": 1.10, "12-13": 1.08, "13-14": 1.08,
            "14-15": 1.09, "15-16": 1.07, "16-17": 0.92, "17-18": 0.91,
            "18-19": 0.90, "19-20": 0.89, "20-21": 0.87, "21-22": 0.82
        }
    },
    "Bayanan Area": {
        "name": "Bacoor Blvd. and Bayanan Road Intersection (Bayanan Area)",
        "observation_hours": 16,
        "total_vehicles_per_day": 9901,
        "avg_vehicles_per_hour": 619,
        "peak_hour_volume": 763,
        "vehicle_mix": {
            "passenger": 0.444,  # 4,392 / 9,901 (includes tricycles as special vehicle)
            "motorcycle": 0.200, # 1,985 / 9,901
            "truck": 0.033,      # 330 / 9,901
            "jeepney": 0.294,    # 2,915 / 9,901 (includes multicabs)
            "bus": 0.000,        # No bus data
            "taxi": 0.028        # Estimated from multicab
        },
        "hourly_patterns": {
            "6-7": 1.23, "7-8": 1.16, "8-9": 1.16, "9-10": 1.10,
            "10-11": 0.90, "11-12": 1.03, "12-13": 1.04, "13-14": 1.06,
            "14-15": 1.05, "15-16": 1.02, "16-17": 1.02, "17-18": 1.02,
            "18-19": 0.88, "19-20": 0.82, "20-21": 0.77, "21-22": 0.71
        }
    }
}


class BTMDCalibrator:
    """
    Calibrates SUMO networks to match BTMD real-world traffic data.
    For intersections without BTMD data, applies averaged traffic patterns.
    """
    
    def __init__(self, networks_dir: str = "networks"):
        """
        Initialize the BTMD calibrator
        
        Args:
            networks_dir: Directory containing SUMO network files
        """
        self.networks_dir = Path(networks_dir)
        self.networks_dir.mkdir(exist_ok=True)
        
        # Calculate average traffic data from networks with BTMD data
        self.average_traffic_data = self._calculate_average_traffic_data()
    
    def _calculate_average_traffic_data(self) -> Dict[str, Any]:
        """
        Calculate average traffic patterns from all intersections with BTMD data.
        This will be used for intersections without specific BTMD data.
        
        Returns:
            Dictionary with averaged traffic patterns
        """
        networks_with_data = BTMD_TRAFFIC_DATA.keys()
        
        # Calculate averages
        total_avg_vph = sum(d["avg_vehicles_per_hour"] for d in BTMD_TRAFFIC_DATA.values())
        total_peak_vph = sum(d["peak_hour_volume"] for d in BTMD_TRAFFIC_DATA.values())
        count = len(BTMD_TRAFFIC_DATA)
        
        # Average vehicle mix across all intersections
        vehicle_mix_sum = {
            "passenger": 0.0,
            "motorcycle": 0.0,
            "truck": 0.0,
            "jeepney": 0.0,
            "bus": 0.0,
            "taxi": 0.0
        }
        
        for data in BTMD_TRAFFIC_DATA.values():
            for vtype, proportion in data["vehicle_mix"].items():
                vehicle_mix_sum[vtype] += proportion
        
        avg_vehicle_mix = {k: v / count for k, v in vehicle_mix_sum.items()}
        
        # Average hourly patterns
        hourly_patterns_sum = {}
        for data in BTMD_TRAFFIC_DATA.values():
            for hour, multiplier in data["hourly_patterns"].items():
                if hour not in hourly_patterns_sum:
                    hourly_patterns_sum[hour] = 0.0
                hourly_patterns_sum[hour] += multiplier
        
        avg_hourly_patterns = {k: v / count for k, v in hourly_patterns_sum.items()}
        
        return {
            "name": "Average BTMD Intersection (Calculated)",
            "observation_hours": 16,
            "total_vehicles_per_day": int(total_avg_vph * 16),
            "avg_vehicles_per_hour": int(total_avg_vph / count),
            "peak_hour_volume": int(total_peak_vph / count),
            "vehicle_mix": avg_vehicle_mix,
            "hourly_patterns": avg_hourly_patterns,
            "is_averaged": True,
            "source_intersections": list(networks_with_data)
        }
    
    def calibrate_network(self, network_name: str, 
                         simulation_hours: float = 2.0,
                         time_of_day: str = "morning_peak",
                         use_temporal_patterns: bool = True,
                         traffic_intensity: float = 1.0) -> Dict[str, Any]:
        """
        Calibrate a network to match BTMD data with traffic intensity scaling.
        For networks without BTMD data, uses averaged traffic patterns.
        
        Args:
            network_name: Name of the network to calibrate
            simulation_hours: Duration of simulation in hours
            time_of_day: Time period ("morning_peak", "midday", "evening", "night")
            use_temporal_patterns: Whether to apply hourly variation patterns
            traffic_intensity: Traffic intensity (1.0 = normal, 10.0 = rush hour peak)
            
        Returns:
            Calibration result dictionary
        """
        # Check if BTMD data exists for this network
        if network_name in BTMD_TRAFFIC_DATA:
            btmd_data = BTMD_TRAFFIC_DATA[network_name]
            using_average = False
        else:
            # Use averaged traffic data for networks without specific BTMD data
            btmd_data = self.average_traffic_data
            using_average = True
            print(f"⚠️  No specific BTMD data for '{network_name}'")
            print(f"📊 Using averaged traffic data from {len(self.average_traffic_data['source_intersections'])} intersections:")
            for source in self.average_traffic_data['source_intersections']:
                print(f"   - {source}")
        
        network_path = self.networks_dir / network_name
        
        if not network_path.exists():
            return {
                "success": False,
                "error": f"Network directory not found: {network_path}"
            }
        
        try:
            # Calculate base target using traffic intensity
            # intensity 1.0 = average traffic, intensity 10.0 = peak traffic
            avg_veh_per_hour = btmd_data["avg_vehicles_per_hour"]
            peak_veh_per_hour = btmd_data["peak_hour_volume"]
            
            # Linear interpolation between average and peak based on intensity
            # intensity 1.0 -> avg, intensity 10.0 -> peak
            intensity_factor = min(max(traffic_intensity, 1.0), 10.0)  # Clamp to 1-10
            target_veh_per_hour = int(avg_veh_per_hour + 
                                     (peak_veh_per_hour - avg_veh_per_hour) * 
                                     (intensity_factor - 1.0) / 9.0)
            
            # Apply temporal pattern if requested (additional multiplier)
            if use_temporal_patterns:
                pattern_key = self._get_pattern_key(time_of_day)
                if pattern_key in btmd_data["hourly_patterns"]:
                    multiplier = btmd_data["hourly_patterns"][pattern_key]
                    target_veh_per_hour = int(target_veh_per_hour * multiplier)
            
            total_vehicles = int(target_veh_per_hour * simulation_hours)
            
            # Get vehicle type proportions
            vehicle_mix = btmd_data["vehicle_mix"]
            
            # Calculate vehicles per type
            vehicles_per_type = {}
            for vtype, proportion in vehicle_mix.items():
                # Map taxi to passenger (SUMO doesn't distinguish)
                if vtype == "taxi":
                    vehicles_per_type["passenger"] = vehicles_per_type.get("passenger", 0) + int(total_vehicles * proportion)
                else:
                    vehicles_per_type[vtype] = int(total_vehicles * proportion)
            
            # Generate calibrated flow files
            self._generate_calibrated_flows(
                network_path=network_path,
                vehicles_per_type=vehicles_per_type,
                simulation_hours=simulation_hours,
                network_name=network_name
            )
            
            # Update network configuration
            self._update_network_config(
                network_path=network_path,
                network_name=network_name
            )
            
            # Generate calibration report
            report = {
                "success": True,
                "network": network_name,
                "btmd_data": btmd_data["name"],
                "using_averaged_data": using_average,
                "simulation_hours": simulation_hours,
                "time_of_day": time_of_day,
                "traffic_intensity": traffic_intensity,
                "target_total_vehicles": total_vehicles,
                "target_vehicles_per_hour": target_veh_per_hour,
                "btmd_avg_per_hour": btmd_data["avg_vehicles_per_hour"],
                "btmd_peak_per_hour": btmd_data["peak_hour_volume"],
                "vehicle_breakdown": vehicles_per_type,
                "calibrated_files": [
                    str(network_path / "routes" / "osm.passenger.flows.xml"),
                    str(network_path / "routes" / "osm.motorcycle.flows.xml"),
                    str(network_path / "routes" / "osm.truck.flows.xml"),
                    str(network_path / "routes" / "osm.jeepney.flows.xml"),
                    str(network_path / "routes" / "osm.bus.flows.xml")
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            if using_average:
                report["source_intersections"] = btmd_data["source_intersections"]
            
            # Save calibration report
            report_path = network_path / "calibration_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            data_source = "AVERAGED DATA" if using_average else "BTMD DATA"
            print(f"\n[SUCCESS] Successfully calibrated {network_name} (using {data_source})")
            print(f"   Intensity: {traffic_intensity}x (1x={btmd_data['avg_vehicles_per_hour']} veh/hr, 10x={btmd_data['peak_hour_volume']} veh/hr)")
            print(f"   Target: {total_vehicles} vehicles ({target_veh_per_hour} veh/hr)")
            print(f"   Mix: Passenger={vehicles_per_type.get('passenger', 0)}, "
                  f"Motorcycle={vehicles_per_type.get('motorcycle', 0)}, "
                  f"Truck={vehicles_per_type.get('truck', 0)}, "
                  f"Jeepney={vehicles_per_type.get('jeepney', 0)}, "
                  f"Bus={vehicles_per_type.get('bus', 0)}")
            
            return report
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Calibration failed: {str(e)}"
            }
    
    def _get_pattern_key(self, time_of_day: str) -> str:
        """
        Map time_of_day to hourly pattern key
        
        Args:
            time_of_day: Time period name
            
        Returns:
            Pattern key for hourly_patterns dictionary
        """
        time_mappings = {
            "morning_peak": "6-7",
            "morning": "8-9",
            "midday": "12-13",
            "afternoon": "15-16",
            "evening_peak": "17-18",
            "evening": "19-20",
            "night": "21-22"
        }
        return time_mappings.get(time_of_day, "6-7")
    
    def _generate_calibrated_flows(self, network_path: Path, 
                                   vehicles_per_type: Dict[str, int],
                                   simulation_hours: float,
                                   network_name: str):
        """
        Generate calibrated SUMO flow files using <flow> elements
        
        Args:
            network_path: Path to network directory
            vehicles_per_type: Number of vehicles per type
            simulation_hours: Simulation duration in hours
            network_name: Name of the network
        """
        routes_dir = network_path / "routes"
        routes_dir.mkdir(exist_ok=True)
        
        # Generate flow file for each vehicle type
        vehicle_types = ["passenger", "motorcycle", "truck", "jeepney", "bus"]
        
        for vtype in vehicle_types:
            num_vehicles = vehicles_per_type.get(vtype, 0)
            
            if num_vehicles == 0:
                print(f"   Skipping {vtype}: 0 vehicles")
                continue
            
            # Calculate vehicles per hour for flow definition
            veh_per_hour = num_vehicles / simulation_hours
            
            # Try to extract edges from existing OSM trip files first (most accurate)
            osm_edges = self._extract_edges_from_osm_trips(network_path, vtype)
            
            if osm_edges['origins'] and osm_edges['destinations']:
                print(f"   Using OSM-validated edges: {len(osm_edges['origins'])} origins, {len(osm_edges['destinations'])} destinations")
                # Generate trip file with OSM-validated edges, then run duarouter
                self._create_trip_file_with_od_pairs(
                    routes_dir=routes_dir,
                    vehicle_type=vtype,
                    veh_per_hour=veh_per_hour,
                    simulation_duration=int(simulation_hours * 3600),
                    origin_edges=osm_edges['origins'],
                    destination_edges=osm_edges['destinations']
                )
            else:
                # Fallback to heuristic fringe edge detection
                print(f"   No OSM trip file found, using fringe edge heuristics")
                edges = self._extract_network_edges(network_path, network_name)
                
                if not edges:
                    raise ValueError(f"No edges found in network {network_name}")
                
                fringe_edges = [e for e in edges if self._is_fringe_edge(e)]
                
                if not fringe_edges:
                    print(f"   Warning: No fringe edges identified, using all edges")
                    fringe_edges = edges
                
                # Generate trip file with heuristic edges (same origins/destinations)
                self._create_trip_file_with_od_pairs(
                    routes_dir=routes_dir,
                    vehicle_type=vtype,
                    veh_per_hour=veh_per_hour,
                    simulation_duration=int(simulation_hours * 3600),
                    origin_edges=fringe_edges,
                    destination_edges=fringe_edges
                )
            
            print(f"   Generated {vtype} flows: {num_vehicles} vehicles ({veh_per_hour:.1f} veh/hr)")
    
    def _extract_network_edges(self, network_path: Path, network_name: str) -> List[str]:
        """
        Extract edge IDs from network file
        
        Args:
            network_path: Path to network directory
            network_name: Name of the network
            
        Returns:
            List of edge IDs
        """
        network_file = network_path / f"{network_name}.net.xml.gz"
        
        if not network_file.exists():
            network_file = network_path / f"{network_name}.net.xml"
        
        if not network_file.exists():
            raise FileNotFoundError(f"Network file not found: {network_file}")
        
        try:
            if network_file.suffix == '.gz':
                with gzip.open(network_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
                root = ET.fromstring(content)
            else:
                tree = ET.parse(network_file)
                root = tree.getroot()
            
            # Extract regular edges (not internal)
            edges = []
            for edge in root.findall('.//edge'):
                edge_id = edge.get('id')
                function = edge.get('function', '')
                
                # Skip internal edges
                if function != 'internal' and not edge_id.startswith(':'):
                    edges.append(edge_id)
            
            return edges
            
        except Exception as e:
            print(f"Error extracting edges: {e}")
            return []
    
    def _extract_edges_from_osm_trips(self, network_path: Path, vehicle_type: str) -> Dict[str, List[str]]:
        """
        Extract actual origin and destination edges from existing OSM trip files
        
        This provides the most accurate edge selection since OSM Web Wizard already
        validated these edges for proper routing.
        
        Args:
            network_path: Path to network directory
            vehicle_type: Vehicle type to extract edges for
            
        Returns:
            Dictionary with 'origins' and 'destinations' lists of edge IDs
        """
        trip_file = network_path / "routes" / f"osm.{vehicle_type}.trips.xml"
        
        if not trip_file.exists():
            return {'origins': [], 'destinations': []}
        
        try:
            tree = ET.parse(trip_file)
            root = tree.getroot()
            
            origins = set()
            destinations = set()
            
            for trip in root.findall('.//trip'):
                from_edge = trip.get('from')
                to_edge = trip.get('to')
                
                if from_edge:
                    origins.add(from_edge)
                if to_edge:
                    destinations.add(to_edge)
            
            return {
                'origins': list(origins),
                'destinations': list(destinations)
            }
            
        except Exception as e:
            print(f"   Warning: Could not extract edges from {trip_file}: {e}")
            return {'origins': [], 'destinations': []}
    
    def _is_fringe_edge(self, edge_id: str) -> bool:
        """
        Heuristic to identify fringe edges (edges at network boundary)
        
        In SUMO networks from OSM, fringe edges typically:
        - Have longer IDs (represent major roads entering/exiting the area)
        - Are not internal edges (no ':' prefix)
        
        Args:
            edge_id: Edge identifier
            
        Returns:
            True if edge is likely a fringe edge
        """
        # Internal edges have ':' prefix
        if edge_id.startswith(':'):
            return False
        
        # For OSM networks, numeric edge IDs with length > 8 are often fringe edges
        if edge_id.lstrip('-').isdigit() and len(edge_id) > 8:
            return True
        
        # Edges with '#' are split edges, often fringe
        if '#' in edge_id:
            return True
        
        return False
    
    def _create_trip_file_with_od_pairs(self, routes_dir: Path, vehicle_type: str,
                         veh_per_hour: float, simulation_duration: int,
                         origin_edges: List[str], destination_edges: List[str]):
        """
        Create a SUMO trip file using <trip> elements with staggered depart times.
        These will be converted to routes with pre-computed paths using duarouter.
        
        This method mimics OSM's approach: individual trips with explicit depart times.
        
        Args:
            routes_dir: Directory to save trip files
            vehicle_type: Vehicle type (passenger, motorcycle, etc.)
            veh_per_hour: Vehicles per hour
            simulation_duration: Total simulation duration in seconds
            origin_edges: List of edge IDs where vehicles spawn (origins)
            destination_edges: List of edge IDs where vehicles should route to (destinations)
        """
        # Use naming convention: .trips.xml for input, will generate .rou.xml after duarouter
        trip_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
        
        # Create XML structure
        root = ET.Element('routes')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation', 'http://sumo.dlr.de/xsd/routes_file.xsd')
        
        # Add comment
        comment = ET.Comment(f' Generated by BTMD Calibrator - {datetime.now().isoformat()} ')
        root.append(comment)
        
        # Define vehicle type
        vtype_elem = ET.SubElement(root, 'vType')
        vtype_elem.set('id', f'calibrated_{vehicle_type}')
        vtype_elem.set('vClass', self._map_vehicle_class(vehicle_type))
        
        # Add vehicle type specific attributes
        if vehicle_type == "jeepney":
            vtype_elem.set('length', '6.0')
            vtype_elem.set('width', '2.0')
            vtype_elem.set('color', 'orange')
        elif vehicle_type == "bus":
            vtype_elem.set('length', '12.0')
            vtype_elem.set('width', '2.5')
            vtype_elem.set('personCapacity', '50')
        elif vehicle_type == "truck":
            vtype_elem.set('length', '7.5')
            vtype_elem.set('width', '2.4')
        elif vehicle_type == "motorcycle":
            vtype_elem.set('length', '2.2')
            vtype_elem.set('width', '0.8')
        
        # Need at least one origin and one destination
        if not origin_edges or not destination_edges:
            print(f"ERROR: Cannot create trips without origin or destination edges for {vehicle_type}")
            return
        
        # Calculate total number of vehicles needed based on veh_per_hour and duration
        total_vehicles = int((veh_per_hour * simulation_duration) / 3600)
        
        if total_vehicles == 0:
            print(f"WARNING: veh_per_hour {veh_per_hour} too low for duration {simulation_duration}s")
            total_vehicles = max(1, int(veh_per_hour))  # At least 1 vehicle
        
        # Calculate time interval between vehicle departures (in seconds)
        if total_vehicles > 1:
            time_interval = simulation_duration / total_vehicles
        else:
            time_interval = 0
        
        # Generate individual trips with staggered depart times
        import random
        random.seed(42)  # Reproducible results
        
        for i in range(total_vehicles):
            # Calculate depart time (evenly distributed across simulation)
            depart_time = i * time_interval
            
            # Select random origin and destination
            from_edge = random.choice(origin_edges)
            to_edge = random.choice([d for d in destination_edges if d != from_edge] or destination_edges)
            
            # Create trip element
            trip_elem = ET.SubElement(root, 'trip')
            trip_elem.set('id', f'{vehicle_type}_{i}')
            trip_elem.set('type', f'calibrated_{vehicle_type}')
            trip_elem.set('depart', f'{depart_time:.2f}')
            trip_elem.set('from', from_edge)
            trip_elem.set('to', to_edge)
            trip_elem.set('departLane', 'best')
            trip_elem.set('departSpeed', 'max')
        
        # Write trip file
        tree = ET.ElementTree(root)
        ET.indent(tree, space='    ')
        tree.write(trip_file, encoding='utf-8', xml_declaration=True)
        
        print(f"Generated {total_vehicles} trips for {vehicle_type} in {trip_file.name}")
        
        # Now use duarouter to convert trips to routes with pre-computed paths
        self._run_duarouter(routes_dir, vehicle_type)
    
    def _run_duarouter(self, routes_dir: Path, vehicle_type: str):
        """
        Run SUMO's duarouter to convert trip file to route file with pre-computed paths.
        This eliminates runtime routing failures.
        
        Args:
            routes_dir: Directory containing trip file and network
            vehicle_type: Vehicle type (passenger, motorcycle, etc.)
        """
        import subprocess
        
        trip_file = routes_dir / f"osm.{vehicle_type}.trips.xml"
        route_file = routes_dir / f"osm.{vehicle_type}.rou.xml"  # Output from duarouter
        
        # Find the network file - it's named after the area
        network_dir = routes_dir.parent
        net_files = list(network_dir.glob("*.net.xml.gz"))
        
        if not net_files:
            print(f"ERROR: No .net.xml.gz file found in {network_dir}")
            return
        
        net_file = net_files[0]  # Use the first (and usually only) network file
        
        if not trip_file.exists():
            print(f"ERROR: Trip file not found: {trip_file}")
            return
        
        if not net_file.exists():
            print(f"ERROR: Network file not found: {net_file}")
            return
        
        # Build duarouter command with absolute paths
        duarouter_cmd = [
            'duarouter',
            '-n', str(net_file.absolute()),
            '-r', str(trip_file.absolute()),
            '-o', str(route_file.absolute()),
            '--ignore-errors', 'true',  # Continue if some routes fail
            '--repair', 'true',  # Try to repair invalid routes
            '--remove-loops', 'true',  # Clean up routes
            '--no-step-log', 'true',  # Suppress verbose output
            '--no-warnings', 'false',  # Show warnings so we know if routes fail
        ]
        
        print(f"Running duarouter for {vehicle_type}...")
        try:
            result = subprocess.run(
                duarouter_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully generated routes: {route_file.name}")
                if result.stdout:
                    print(f"  {result.stdout.strip()}")
            else:
                print(f"✗ duarouter failed with return code {result.returncode}")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
                if result.stdout:
                    print(f"  Output: {result.stdout}")
        
        except FileNotFoundError:
            print("ERROR: duarouter not found. Make sure SUMO is installed and in PATH")
        except Exception as e:
            print(f"ERROR running duarouter: {e}")
    
    def _map_vehicle_class(self, vehicle_type: str) -> str:
        """
        Map vehicle type to SUMO vClass
        
        Args:
            vehicle_type: Vehicle type identifier
            
        Returns:
            SUMO vClass string
        """
        mapping = {
            "passenger": "passenger",
            "motorcycle": "motorcycle",
            "truck": "truck",
            "jeepney": "bus",  # Jeepneys are similar to buses in SUMO
            "bus": "bus",
            "taxi": "taxi"
        }
        return mapping.get(vehicle_type, "passenger")
    
    def _update_network_config(self, network_path: Path, network_name: str):
        """
        Update SUMO configuration file to use calibrated route files.
        Only includes route files that actually exist.
        
        Args:
            network_path: Path to network directory
            network_name: Name of the network
        """
        config_file = network_path / f"{network_name}.sumocfg"
        
        if not config_file.exists():
            print(f"Warning: Config file not found: {config_file}")
            return
        
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Find or create route-files element
            route_files_elem = root.find('.//route-files')
            
            if route_files_elem is None:
                # Create input section if it doesn't exist
                input_elem = root.find('.//input')
                if input_elem is None:
                    input_elem = ET.SubElement(root, 'input')
                route_files_elem = ET.SubElement(input_elem, 'route-files')
            
            # Check which route files actually exist
            routes_dir = network_path / "routes"
            possible_routes = [
                "routes/osm.passenger.rou.xml",
                "routes/osm.motorcycle.rou.xml",
                "routes/osm.truck.rou.xml",
                "routes/osm.jeepney.rou.xml",
                "routes/osm.bus.rou.xml"
            ]
            
            # Only include files that exist
            existing_routes = [
                route for route in possible_routes
                if (network_path / route).exists()
            ]
            
            if not existing_routes:
                print("Warning: No route files found!")
                return
            
            route_files_elem.set('value', ','.join(existing_routes))
            
            # Save updated config
            ET.indent(tree, space='    ')
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            
            print(f"   Updated configuration file: {config_file}")
            
        except Exception as e:
            print(f"Warning: Failed to update config file: {e}")
    
    def calibrate_all_networks(self, simulation_hours: float = 2.0,
                               time_of_day: str = "morning_peak",
                               traffic_intensity: float = 1.0) -> Dict[str, Any]:
        """
        Calibrate all networks with BTMD data
        
        Args:
            simulation_hours: Duration of simulation in hours
            time_of_day: Time period for simulation
            traffic_intensity: Traffic intensity (1.0 = normal, 10.0 = rush hour)
            
        Returns:
            Summary of calibration results
        """
        results = {
            "success": True,
            "calibrated_networks": [],
            "failed_networks": [],
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("BTMD TRAFFIC DATA CALIBRATION")
        print("="*60)
        print(f"Simulation Duration: {simulation_hours} hours")
        print(f"Time of Day: {time_of_day}")
        print(f"Traffic Intensity: {traffic_intensity}x")
        print(f"Target Accuracy: 90% match with BTMD data")
        print("="*60 + "\n")
        
        for network_name in BTMD_TRAFFIC_DATA.keys():
            print(f"\nCalibrating: {network_name}")
            print("-" * 60)
            
            result = self.calibrate_network(
                network_name=network_name,
                simulation_hours=simulation_hours,
                time_of_day=time_of_day,
                traffic_intensity=traffic_intensity
            )
            
            if result["success"]:
                results["calibrated_networks"].append(result)
            else:
                results["failed_networks"].append({
                    "network": network_name,
                    "error": result.get("error", "Unknown error")
                })
                results["success"] = False
        
        # Save overall summary
        summary_file = self.networks_dir / "calibration_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*60)
        print("CALIBRATION COMPLETE")
        print("="*60)
        print(f"Successfully calibrated: {len(results['calibrated_networks'])} networks")
        print(f"Failed: {len(results['failed_networks'])} networks")
        print(f"Summary saved to: {summary_file}")
        print("="*60 + "\n")
        
        return results
    
    def print_average_data_summary(self):
        """
        Print a summary of the averaged traffic data used for networks without BTMD data.
        """
        avg = self.average_traffic_data
        
        print("\n" + "="*70)
        print("AVERAGED BTMD TRAFFIC DATA")
        print("="*70)
        print(f"\nCalculated from {len(avg['source_intersections'])} intersections:")
        for source in avg['source_intersections']:
            btmd = BTMD_TRAFFIC_DATA[source]
            print(f"  • {source}: {btmd['avg_vehicles_per_hour']} veh/hr avg, "
                  f"{btmd['peak_hour_volume']} veh/hr peak")
        
        print(f"\nAveraged Traffic Volume:")
        print(f"  Average vehicles/hour: {avg['avg_vehicles_per_hour']} veh/hr")
        print(f"  Peak vehicles/hour: {avg['peak_hour_volume']} veh/hr")
        print(f"  Total vehicles/day: {avg['total_vehicles_per_day']} vehicles (16 hours)")
        
        print(f"\nAveraged Vehicle Mix:")
        for vtype, proportion in avg['vehicle_mix'].items():
            print(f"  {vtype.capitalize()}: {proportion:.1%}")
        
        print(f"\nThis data is automatically applied to networks without specific BTMD data.")
        print("="*70 + "\n")


def main():
    """
    Command-line interface for BTMD calibration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calibrate SUMO networks to BTMD traffic data')
    parser.add_argument('--network', type=str, help='Specific network to calibrate (optional)')
    parser.add_argument('--hours', type=float, default=2.0, help='Simulation duration in hours (default: 2.0)')
    parser.add_argument('--time', type=str, default='morning_peak', 
                       choices=['morning_peak', 'morning', 'midday', 'afternoon', 'evening_peak', 'evening', 'night'],
                       help='Time of day (default: morning_peak)')
    parser.add_argument('--intensity', type=float, default=1.0,
                       help='Traffic intensity: 1.0=normal/average, 10.0=rush hour/peak (default: 1.0)')
    parser.add_argument('--networks-dir', type=str, default='networks', help='Networks directory (default: networks)')
    parser.add_argument('--list', action='store_true', help='List available networks with BTMD data')
    parser.add_argument('--show-average', action='store_true', help='Show averaged traffic data summary')
    
    args = parser.parse_args()
    
    calibrator = BTMDCalibrator(networks_dir=args.networks_dir)
    
    if args.show_average:
        calibrator.print_average_data_summary()
        return
    
    if args.list:
        print("\nAvailable networks with BTMD data:")
        print("="*60)
        for network, data in BTMD_TRAFFIC_DATA.items():
            print(f"\n{network}")
            print(f"  Location: {data['name']}")
            print(f"  Daily vehicles: {data['total_vehicles_per_day']:,}")
            print(f"  Avg per hour: {data['avg_vehicles_per_hour']:,}")
            print(f"  Peak hour: {data['peak_hour_volume']:,}")
        print("\n")
        return
    
    if args.network:
        # Calibrate specific network
        result = calibrator.calibrate_network(
            network_name=args.network,
            simulation_hours=args.hours,
            time_of_day=args.time,
            traffic_intensity=args.intensity
        )
        
        if not result["success"]:
            print(f"\nError: {result['error']}")
            return 1
    else:
        # Calibrate all networks
        results = calibrator.calibrate_all_networks(
            simulation_hours=args.hours,
            time_of_day=args.time,
            traffic_intensity=args.intensity
        )
        
        if not results["success"]:
            print("\nSome networks failed to calibrate. Check the summary for details.")
            return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
