"""
Traffic Analytics Engine

Processes SUMO simulation output files to extract KPIs and generate
analytics data for the post-simulation dashboard.

Author: Traffic Simulator Team
Date: September 2025
"""

import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import statistics
from dataclasses import dataclass, asdict

@dataclass
class TrafficKPIs:
    """Data class for traffic simulation KPIs"""
    # Basic vehicle statistics
    total_vehicles_loaded: int = 0
    total_vehicles_completed: int = 0
    total_vehicles_running: int = 0
    total_vehicles_waiting: int = 0
    
    # Time-based metrics
    avg_travel_time: float = 0.0
    max_travel_time: float = 0.0
    avg_waiting_time: float = 0.0
    max_waiting_time: float = 0.0
    avg_time_loss: float = 0.0
    simulation_duration: float = 0.0
    
    # Speed metrics
    avg_speed: float = 0.0
    avg_relative_speed: float = 0.0
    
    # Route metrics
    avg_route_length: float = 0.0
    total_distance_traveled: float = 0.0
    
    # Congestion metrics
    avg_density: float = 0.0
    max_density: float = 0.0
    congestion_index: float = 0.0
    
    # Efficiency metrics
    throughput: float = 0.0  # vehicles per hour
    
    # Additional info
    notes: str = ""
    flow_rate: float = 0.0   # vehicles per second
    
    # Safety metrics
    total_teleports: int = 0
    total_collisions: int = 0
    safety_score: float = 0.0  # Composite safety score (0-100, higher is safer)
    avg_deceleration_events: float = 0.0
    emergency_stops: int = 0
    
    # Environmental metrics (if emissions data available)
    total_co2: float = 0.0
    total_co: float = 0.0
    total_nox: float = 0.0
    total_fuel_consumption: float = 0.0
    
    # Network metrics (if edgedata available)
    avg_edge_density: float = 0.0
    max_edge_density: float = 0.0
    avg_edge_occupancy: float = 0.0
    max_edge_occupancy: float = 0.0
    bottleneck_edges: int = 0
    avg_network_speed: float = 0.0

@dataclass 
class TimeSeriesData:
    """Time series data point"""
    time: float
    running_vehicles: int
    halting_vehicles: int
    mean_speed: float
    mean_waiting_time: float
    teleports: int
    collisions: int

@dataclass
class RecommendationRule:
    """Rule for generating recommendations"""
    rule_id: str
    condition: str
    threshold: float
    message: str
    priority: str  # "high", "medium", "low"
    category: str  # "congestion", "safety", "efficiency", "environmental"

class TrafficAnalyticsEngine:
    """Main analytics engine for processing SUMO outputs"""
    
    def __init__(self, db_service=None):
        """Initialize the analytics engine"""
        self.db_service = db_service
        self.recommendation_rules = self._initialize_recommendation_rules()
    
    def _initialize_recommendation_rules(self) -> List[RecommendationRule]:
        """Initialize built-in recommendation rules"""
        return [
            # Congestion rules
            RecommendationRule(
                rule_id="high_avg_waiting_time",
                condition="avg_waiting_time",
                threshold=60.0,  # seconds
                message="High average waiting time detected ({value:.1f}s). Consider reducing traffic inflow or optimizing signal timing.",
                priority="high",
                category="congestion"
            ),
            RecommendationRule(
                rule_id="low_throughput",
                condition="throughput",
                threshold=500,  # vehicles/hour
                message="Low throughput detected ({value:.0f} vehicles/hour). Network may be underutilized or experiencing bottlenecks.",
                priority="medium",
                category="efficiency"
            ),
            RecommendationRule(
                rule_id="high_time_loss",
                condition="avg_time_loss",
                threshold=120.0,  # seconds
                message="High time loss detected ({value:.1f}s per trip). Consider alternative routing or infrastructure improvements.",
                priority="high",
                category="efficiency"
            ),
            RecommendationRule(
                rule_id="low_avg_speed",
                condition="avg_speed",
                threshold=5.0,  # m/s (18 km/h)
                message="Low average speed detected ({value:.1f} m/s). Severe congestion may be present.",
                priority="high",
                category="congestion"
            ),
            RecommendationRule(
                rule_id="high_teleports",
                condition="total_teleports",
                threshold=10,  # count
                message="High number of teleports detected ({value:.0f}). Check for gridlocks or insufficient infrastructure capacity.",
                priority="high",
                category="safety"
            ),
            RecommendationRule(
                rule_id="high_collisions",
                condition="total_collisions",
                threshold=5,  # count
                message="Collisions detected ({value:.0f}). Review intersection safety and vehicle behavior parameters.",
                priority="high",
                category="safety"
            ),
            RecommendationRule(
                rule_id="high_co2_emissions",
                condition="total_co2",
                threshold=1000,  # grams (converted from mg)
                message="High CO2 emissions detected ({value:.1f}g). Consider promoting public transport or electric vehicles.",
                priority="medium",
                category="environmental"
            ),
            RecommendationRule(
                rule_id="high_nox_emissions",
                condition="total_nox",
                threshold=50,  # grams
                message="High NOx emissions detected ({value:.1f}g). Consider diesel vehicle restrictions or emission standards.",
                priority="medium",
                category="environmental"
            ),
            RecommendationRule(
                rule_id="high_fuel_consumption",
                condition="total_fuel_consumption",
                threshold=500,  # grams
                message="High fuel consumption detected ({value:.1f}g). Optimize traffic flow to reduce stop-and-go driving.",
                priority="medium",
                category="environmental"
            ),
            # Network analysis rules
            RecommendationRule(
                rule_id="high_edge_density",
                condition="avg_edge_density",
                threshold=30,  # veh/km
                message="High average edge density detected ({value:.1f} veh/km). Network capacity may be strained.",
                priority="medium",
                category="congestion"
            ),
            RecommendationRule(
                rule_id="high_occupancy",
                condition="avg_edge_occupancy",
                threshold=70,  # percentage
                message="High average edge occupancy detected ({value:.1f}%). Consider capacity improvements.",
                priority="high",
                category="congestion"
            ),
            RecommendationRule(
                rule_id="bottleneck_detected",
                condition="bottleneck_edges",
                threshold=5,  # count
                message="Multiple bottleneck edges detected ({value:.0f}). Focus on critical infrastructure improvements.",
                priority="high",
                category="efficiency"
            ),
            # Safety-specific rules
            RecommendationRule(
                rule_id="low_safety_score",
                condition="safety_score",
                threshold=70,  # score out of 100
                message="Low safety score detected ({value:.1f}/100). Review traffic management and safety measures.",
                priority="high",
                category="safety"
            ),
            RecommendationRule(
                rule_id="high_deceleration_events",
                condition="avg_deceleration_events",
                threshold=0.3,  # ratio
                message="High frequency of deceleration events ({value:.2f} per trip). Consider traffic flow improvements.",
                priority="medium",
                category="safety"
            ),
            RecommendationRule(
                rule_id="emergency_stops_detected",
                condition="emergency_stops",
                threshold=5,  # count
                message="Emergency stops detected ({value:.0f}). Review intersection design and signal timing.",
                priority="high",
                category="safety"
            ),
            # Positive recommendations
            RecommendationRule(
                rule_id="good_flow",
                condition="flow_rate",
                threshold=0.5,  # vehicles/second
                message="Good traffic flow achieved ({value:.2f} vehicles/s). Current configuration appears optimal.",
                priority="low",
                category="efficiency"
            )
        ]
    
    def analyze_session(self, session_path: str, session_id: str = None, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Analyze a complete simulation session
        
        Args:
            session_path: Path to session directory containing SUMO output files
            session_id: Session ID (for database storage)
            force_reprocess: Force reprocessing even if analytics already exist
            
        Returns:
            Dictionary containing complete analytics results
        """
        try:
            session_path = Path(session_path)
            
            # Extract session_id from path if not provided
            if not session_id:
                session_id = session_path.name

            # Quick check if analytics already exist (unless forcing reprocess)
            if not force_reprocess:
                try:
                    existing_kpis = self.db_service.get_kpis(session_id)
                    if existing_kpis:
                        print(f"Using cached analytics for session {session_id}")
                        return self._build_cached_analytics_response(session_id)
                except Exception:
                    # If there's an error checking existing data, proceed with full analysis
                    pass
            
            print(f"Processing analytics for session {session_id}...")
            
            # Locate output files
            tripinfo_file = self._find_file(session_path, "*.tripinfos.xml")
            stats_file = self._find_file(session_path, "*.stats.xml")
            summary_file = self._find_file(session_path, "*summary.xml")
            emissions_file = self._find_file(session_path, "*emissions.xml")
            edgedata_file = self._find_file(session_path, "*edgedata.xml")
            
            # Parse files
            kpis = self._extract_kpis(tripinfo_file, stats_file, summary_file, emissions_file, edgedata_file)
            time_series = self._extract_time_series(summary_file)
            trip_data = self._extract_trip_data(tripinfo_file)
            network_data = self._extract_network_data(edgedata_file)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(kpis)
            
            # Calculate additional analytics
            vehicle_type_breakdown = self._analyze_vehicle_types(trip_data)
            route_analysis = self._analyze_routes(trip_data)
            temporal_patterns = self._analyze_temporal_patterns(time_series)
            network_analysis = self._analyze_network_performance(network_data)
            
            # Save to database if available
            if self.db_service and session_id:
                try:
                    # Save KPIs
                    kpis_dict = asdict(kpis)
                    self.db_service.save_kpis(session_id, kpis_dict)
                    
                    # Save time series data
                    time_series_dicts = [asdict(ts) for ts in time_series]
                    # Convert time_step to time for database compatibility
                    for ts_dict in time_series_dicts:
                        ts_dict['time_step'] = ts_dict.pop('time', 0)
                    self.db_service.save_time_series(session_id, time_series_dicts)
                    
                    # Save trip data
                    self.db_service.save_trips(session_id, trip_data)
                    
                    # Save recommendations
                    rec_dicts = []
                    for rec in recommendations:
                        rec_dict = {
                            'rule_id': rec.get('rule_id', ''),
                            'priority': rec.get('priority', 'medium'),
                            'category': rec.get('category', 'general'),
                            'message': rec.get('message', ''),
                            'kpi_name': rec.get('kpi', ''),
                            'actual_value': rec.get('actual_value', 0),
                            'threshold_value': rec.get('threshold', 0)
                        }
                        rec_dicts.append(rec_dict)
                    self.db_service.save_recommendations(session_id, rec_dicts)
                    
                    # Save vehicle emissions data (if available) - with reduced processing for speed
                    if emissions_file and emissions_file.exists():
                        # Use smaller sample size for faster processing
                        emissions_data = self._extract_emissions_data(emissions_file, max_vehicles=250)
                        if emissions_data:
                            self.db_service.save_vehicle_emissions(session_id, emissions_data)
                    
                    # Save edge data (if available)
                    if edgedata_file and edgedata_file.exists():
                        edge_data = self._extract_edge_data(edgedata_file)
                        if edge_data:
                            self.db_service.save_edge_data(session_id, edge_data)
                    
                    # Save safety metrics
                    safety_metrics = self._extract_safety_metrics(trip_data, network_data, time_series)
                    if safety_metrics:
                        self.db_service.save_safety_metrics(session_id, safety_metrics)
                    
                    # Save route analysis
                    if route_analysis:
                        self.db_service.save_route_analysis(session_id, route_analysis)
                    
                    # Save temporal patterns
                    if temporal_patterns:
                        self.db_service.save_temporal_patterns(session_id, temporal_patterns)
                    
                    print(f"Analytics data saved to database for session {session_id}")
                except Exception as db_error:
                    print(f"Warning: Failed to save analytics to database: {db_error}")
            
            return {
                "session_path": str(session_path),
                "session_id": session_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "kpis": asdict(kpis),
                "time_series": [asdict(ts) for ts in time_series],
                "recommendations": recommendations,
                "vehicle_type_breakdown": vehicle_type_breakdown,
                "route_analysis": route_analysis,
                "temporal_patterns": temporal_patterns,
                "network_analysis": network_analysis,
                "trip_data_sample": trip_data[:10] if len(trip_data) > 10 else trip_data  # Sample for frontend
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "session_path": str(session_path),
                "session_id": session_id,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _find_file(self, session_path: Path, pattern: str) -> Optional[Path]:
        """Find file matching pattern in session directory"""
        files = list(session_path.glob(pattern))
        return files[0] if files else None
    
    def _extract_kpis(self, tripinfo_file: Optional[Path], 
                     stats_file: Optional[Path], 
                     summary_file: Optional[Path],
                     emissions_file: Optional[Path],
                     edgedata_file: Optional[Path]) -> TrafficKPIs:
        """Extract KPIs from SUMO output files"""
        kpis = TrafficKPIs()
        
        # Extract from tripinfo.xml
        if tripinfo_file and tripinfo_file.exists():
            kpis = self._process_tripinfo_file(tripinfo_file, kpis)
        
        # Extract from stats.xml (if available)
        if stats_file and stats_file.exists():
            kpis = self._process_stats_file(stats_file, kpis)
        
        # Extract from summary.xml (if available)
        if summary_file and summary_file.exists():
            kpis = self._process_summary_file(summary_file, kpis)
        
        # Extract from emissions.xml (if available)
        if emissions_file and emissions_file.exists():
            kpis = self._process_emissions_file(emissions_file, kpis)
        
        # Extract from edgedata.xml (if available)
        if edgedata_file and edgedata_file.exists():
            kpis = self._process_edgedata_file(edgedata_file, kpis)
        
        # Calculate derived metrics
        kpis = self._calculate_derived_metrics(kpis)
        
        # Calculate safety metrics from trip and simulation data
        kpis = self._enhance_safety_metrics(kpis, tripinfo_file)
        
        # If no completed trips, try to extract basic simulation info
        if kpis.total_vehicles_completed == 0:
            kpis = self._extract_basic_simulation_info(tripinfo_file, kpis)
        
        return kpis
    
    def _process_tripinfo_file(self, tripinfo_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Process tripinfo.xml file for vehicle trip data"""
        try:
            # Try to repair the file if it's incomplete
            self._repair_xml_file_if_needed(tripinfo_file)
            
            tree = ET.parse(tripinfo_file)
            root = tree.getroot()
            
            travel_times = []
            waiting_times = []
            time_losses = []
            route_lengths = []
            speeds = []
            
            total_co2 = 0.0
            total_co = 0.0
            total_nox = 0.0
            total_fuel = 0.0
            
            for tripinfo in root.findall('tripinfo'):
                # Basic trip metrics
                duration = float(tripinfo.get('duration', 0))
                waiting_time = float(tripinfo.get('waitingTime', 0))
                time_loss = float(tripinfo.get('timeLoss', 0))
                route_length = float(tripinfo.get('routeLength', 0))
                
                travel_times.append(duration)
                waiting_times.append(waiting_time)
                time_losses.append(time_loss)
                route_lengths.append(route_length)
                
                # Calculate average speed
                if duration > 0:
                    avg_speed = route_length / duration
                    speeds.append(avg_speed)
                
                # Check for emissions data
                emissions = tripinfo.find('emissions')
                if emissions is not None:
                    total_co2 += float(emissions.get('CO2_abs', 0))
                    total_co += float(emissions.get('CO_abs', 0))
                    total_nox += float(emissions.get('NOx_abs', 0))
                    total_fuel += float(emissions.get('fuel_abs', 0))
            
            # Calculate aggregated metrics
            if travel_times:
                kpis.total_vehicles_completed = len(travel_times)
                kpis.avg_travel_time = statistics.mean(travel_times)
                kpis.max_travel_time = max(travel_times)
            
            if waiting_times:
                kpis.avg_waiting_time = statistics.mean(waiting_times)
                kpis.max_waiting_time = max(waiting_times)
            
            if time_losses:
                kpis.avg_time_loss = statistics.mean(time_losses)
            
            if route_lengths:
                kpis.avg_route_length = statistics.mean(route_lengths)
                kpis.total_distance_traveled = sum(route_lengths)
            
            if speeds:
                kpis.avg_speed = statistics.mean(speeds)
            
            # Environmental metrics
            kpis.total_co2 = total_co2
            kpis.total_co = total_co
            kpis.total_nox = total_nox
            kpis.total_fuel_consumption = total_fuel
            
        except Exception as e:
            print(f"Error processing tripinfo file: {e}")
        
        return kpis
    
    def _process_stats_file(self, stats_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Process stats.xml file for overall statistics"""
        try:
            # Try to repair the file if it's incomplete
            self._repair_xml_file_if_needed(stats_file)
            
            tree = ET.parse(stats_file)
            root = tree.getroot()
            
            # Extract vehicle statistics
            vehicle_trip_stats = root.find('.//vehicleTripStatistics')
            if vehicle_trip_stats is not None:
                kpis.total_vehicles_loaded = int(vehicle_trip_stats.get('count', 0))
                
                # Override with more accurate stats data if available
                if 'duration' in vehicle_trip_stats.attrib:
                    kpis.avg_travel_time = float(vehicle_trip_stats.get('duration'))
                if 'routeLength' in vehicle_trip_stats.attrib:
                    kpis.avg_route_length = float(vehicle_trip_stats.get('routeLength'))
                if 'speed' in vehicle_trip_stats.attrib:
                    kpis.avg_speed = float(vehicle_trip_stats.get('speed'))
                if 'waitingTime' in vehicle_trip_stats.attrib:
                    kpis.avg_waiting_time = float(vehicle_trip_stats.get('waitingTime'))
                if 'timeLoss' in vehicle_trip_stats.attrib:
                    kpis.avg_time_loss = float(vehicle_trip_stats.get('timeLoss'))
            
            # Extract safety statistics
            safety_stats = root.find('.//safety')
            if safety_stats is not None:
                kpis.total_collisions = int(safety_stats.get('collisions', 0))
            
        except Exception as e:
            print(f"Error processing stats file: {e}")
        
        return kpis
    
    def _process_summary_file(self, summary_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Process summary.xml file for timestep data"""
        try:
            tree = ET.parse(summary_file)
            root = tree.getroot()
            
            total_teleports = 0
            
            # Process each time step
            for step in root.findall('step'):
                teleports = int(step.get('teleports', 0))
                total_teleports += teleports
            
            kpis.total_teleports = total_teleports
            
        except Exception as e:
            print(f"Error processing summary file: {e}")
        
        return kpis
    
    def _process_emissions_file(self, emissions_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Process emissions.xml file for environmental metrics"""
        try:
            tree = ET.parse(emissions_file)
            root = tree.getroot()
            
            total_co2 = 0.0
            total_co = 0.0
            total_nox = 0.0
            total_fuel = 0.0
            total_pmx = 0.0
            total_hc = 0.0
            vehicle_count = 0
            
            # Process each timestep
            for timestep in root.findall('timestep'):
                # Process each vehicle in the timestep
                for vehicle in timestep.findall('vehicle'):
                    # Extract emissions data (values are in mg/s)
                    co2 = float(vehicle.get('CO2', 0))
                    co = float(vehicle.get('CO', 0))
                    nox = float(vehicle.get('NOx', 0))
                    fuel = float(vehicle.get('fuel', 0))
                    pmx = float(vehicle.get('PMx', 0))
                    hc = float(vehicle.get('HC', 0))
                    
                    # Accumulate totals
                    total_co2 += co2
                    total_co += co
                    total_nox += nox
                    total_fuel += fuel
                    total_pmx += pmx
                    total_hc += hc
                    vehicle_count += 1
            
            # Convert from mg/s to total mg (multiply by simulation duration if needed)
            # For now, store the raw accumulated values
            kpis.total_co2 = total_co2 / 1000.0  # Convert mg to grams
            kpis.total_co = total_co / 1000.0    # Convert mg to grams  
            kpis.total_nox = total_nox / 1000.0  # Convert mg to grams
            kpis.total_fuel_consumption = total_fuel / 1000.0  # Convert mg to grams
            
            # Store additional emissions in notes for future use
            additional_emissions = {
                'total_pmx_g': total_pmx / 1000.0,
                'total_hc_g': total_hc / 1000.0,
                'vehicle_timesteps': vehicle_count
            }
            
            # Add to notes if not already present
            if kpis.notes:
                kpis.notes += f"; Emissions: {additional_emissions}"
            else:
                kpis.notes = f"Emissions: {additional_emissions}"
            
            print(f"Processed emissions data: CO2={kpis.total_co2:.2f}g, NOx={kpis.total_nox:.2f}g, Fuel={kpis.total_fuel_consumption:.2f}g")
            
        except Exception as e:
            print(f"Error processing emissions file: {e}")
        
        return kpis
    
    def _process_edgedata_file(self, edgedata_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Process edgedata.xml file for network metrics"""
        try:
            tree = ET.parse(edgedata_file)
            root = tree.getroot()
            
            densities = []
            occupancies = []
            speeds = []
            bottleneck_count = 0
            
            # Process each interval (usually just one for the whole simulation)
            for interval in root.findall('interval'):
                # Process each edge in the interval
                for edge in interval.findall('edge'):
                    density = float(edge.get('density', 0))
                    occupancy = float(edge.get('occupancy', 0))
                    speed = float(edge.get('speed', 0))
                    sampled_seconds = float(edge.get('sampledSeconds', 0))
                    
                    # Only include edges that had traffic
                    if sampled_seconds > 0:
                        densities.append(density)
                        occupancies.append(occupancy)
                        speeds.append(speed)
                        
                        # Consider edge a bottleneck if occupancy > 80% or density > 40 veh/km
                        if occupancy > 80 or density > 40:
                            bottleneck_count += 1
            
            # Calculate network-level metrics
            if densities:
                kpis.avg_edge_density = statistics.mean(densities)
                kpis.max_edge_density = max(densities)
                kpis.avg_edge_occupancy = statistics.mean(occupancies)
                kpis.max_edge_occupancy = max(occupancies)
                kpis.avg_network_speed = statistics.mean(speeds)
                kpis.bottleneck_edges = bottleneck_count
                
                print(f"Processed network data: {len(densities)} edges, {bottleneck_count} bottlenecks, avg density={kpis.avg_edge_density:.2f} veh/km")
            
        except Exception as e:
            print(f"Error processing edgedata file: {e}")
        
        return kpis
    
    def _extract_network_data(self, edgedata_file: Optional[Path]) -> List[Dict[str, Any]]:
        """Extract detailed network data for analysis"""
        network_data = []
        
        if not edgedata_file or not edgedata_file.exists():
            return network_data
        
        try:
            tree = ET.parse(edgedata_file)
            root = tree.getroot()
            
            # Process each interval
            for interval in root.findall('interval'):
                interval_data = {
                    'begin': float(interval.get('begin', 0)),
                    'end': float(interval.get('end', 0)),
                    'edges': []
                }
                
                # Process each edge in the interval
                for edge in interval.findall('edge'):
                    edge_data = {
                        'id': edge.get('id'),
                        'density': float(edge.get('density', 0)),
                        'occupancy': float(edge.get('occupancy', 0)),
                        'speed': float(edge.get('speed', 0)),
                        'traveltime': float(edge.get('traveltime', 0)),
                        'waitingTime': float(edge.get('waitingTime', 0)),
                        'sampledSeconds': float(edge.get('sampledSeconds', 0)),
                        'departed': int(edge.get('departed', 0)),
                        'arrived': int(edge.get('arrived', 0)),
                        'entered': int(edge.get('entered', 0)),
                        'left': int(edge.get('left', 0))
                    }
                    
                    # Calculate utilization metrics
                    if edge_data['sampledSeconds'] > 0:
                        edge_data['utilization'] = min(100, edge_data['occupancy'])
                        edge_data['efficiency'] = edge_data['speed'] / max(1, edge_data['traveltime']) if edge_data['traveltime'] > 0 else 0
                        edge_data['is_bottleneck'] = edge_data['occupancy'] > 80 or edge_data['density'] > 40
                    else:
                        edge_data['utilization'] = 0
                        edge_data['efficiency'] = 0
                        edge_data['is_bottleneck'] = False
                    
                    interval_data['edges'].append(edge_data)
                
                network_data.append(interval_data)
                
        except Exception as e:
            print(f"Error extracting network data: {e}")
        
        return network_data
    
    def _extract_basic_simulation_info(self, tripinfo_file: Optional[Path], kpis: TrafficKPIs) -> TrafficKPIs:
        """
        Extract basic simulation information from configuration when no trips completed.
        This helps provide some analytics even for very short simulations.
        """
        try:
            if not tripinfo_file or not tripinfo_file.exists():
                return kpis
                
            # Parse the XML to get simulation configuration
            tree = ET.parse(tripinfo_file)
            root = tree.getroot()
            
            # Look for SUMO configuration in the XML comments/header
            config_text = str(tree)
            
            # Extract simulation duration from config
            if '<end value="' in config_text:
                start_idx = config_text.find('<end value="') + 12
                end_idx = config_text.find('"', start_idx)
                if end_idx > start_idx:
                    try:
                        sim_duration = float(config_text[start_idx:end_idx])
                        kpis.simulation_duration = sim_duration
                    except:
                        pass
            
            # Extract scale factor if available
            if '<scale value="' in config_text:
                start_idx = config_text.find('<scale value="') + 14
                end_idx = config_text.find('"', start_idx)
                if end_idx > start_idx:
                    try:
                        scale_factor = float(config_text[start_idx:end_idx])
                        # Estimate vehicles based on scale factor (rough approximation)
                        kpis.total_vehicles_loaded = int(scale_factor * 10)  # Very rough estimate
                    except:
                        pass
            
            # If we have a session directory, check route files for better vehicle count estimation
            session_path = tripinfo_file.parent
            routes_dir = session_path / "routes"
            if routes_dir.exists():
                vehicle_count = 0
                for route_file in routes_dir.glob("*.xml"):
                    try:
                        route_tree = ET.parse(route_file)
                        route_root = route_tree.getroot()
                        # Count vehicle definitions
                        vehicles = route_root.findall('.//vehicle')
                        vehicle_count += len(vehicles)
                    except:
                        continue
                
                if vehicle_count > 0:
                    kpis.total_vehicles_loaded = vehicle_count
                    # For short simulations, assume vehicles were running but didn't complete
                    kpis.total_vehicles_running = vehicle_count
                    
                    # Provide a message indicating this is partial data
                    kpis.notes = f"Simulation too short ({getattr(kpis, 'simulation_duration', 'unknown')}s) for vehicles to complete trips. Stats based on loaded vehicles."
            
        except Exception as e:
            print(f"Error extracting basic simulation info: {e}")
        
        return kpis
    
    def _repair_xml_file_if_needed(self, xml_file: Path):
        """
        Repair XML files that weren't properly closed by SUMO
        """
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if tripinfos file is incomplete
            if xml_file.name.endswith('tripinfos.xml'):
                if '<tripinfos' in content and not content.strip().endswith('</tripinfos>'):
                    print(f"Repairing incomplete tripinfos file: {xml_file}")
                    # Add closing tag
                    if not content.strip().endswith('>'):
                        content += '>'
                    content += '\n</tripinfos>'
                    
                    # Write back the repaired content
                    with open(xml_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            # Check if stats file is incomplete  
            elif xml_file.name.endswith('stats.xml'):
                if content.strip() and not content.strip().endswith('>'):
                    print(f"Repairing incomplete stats file: {xml_file}")
                    # For stats file, we might need to add proper structure
                    if '<statistics>' not in content:
                        content += '\n<statistics>\n</statistics>'
                    
                    with open(xml_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
        except Exception as e:
            print(f"Error repairing XML file {xml_file}: {e}")
    
    def _calculate_derived_metrics(self, kpis: TrafficKPIs) -> TrafficKPIs:
        """Calculate derived metrics from basic KPIs"""
        # Throughput (vehicles per hour)
        if kpis.avg_travel_time > 0:
            kpis.throughput = 3600 / kpis.avg_travel_time * kpis.total_vehicles_completed
        
        # Flow rate (vehicles per second)  
        kpis.flow_rate = kpis.throughput / 3600 if kpis.throughput > 0 else 0
        
        # Congestion index (ratio of actual to free-flow speed)
        # Assuming free-flow speed is around 13.89 m/s (50 km/h)
        if kpis.avg_speed > 0:
            free_flow_speed = 13.89  # m/s
            kpis.congestion_index = kpis.avg_speed / free_flow_speed
        
        return kpis
    
    def _extract_time_series(self, summary_file: Optional[Path]) -> List[TimeSeriesData]:
        """Extract time series data from summary file"""
        time_series = []
        
        if not summary_file or not summary_file.exists():
            return time_series
        
        try:
            tree = ET.parse(summary_file)
            root = tree.getroot()
            
            for step in root.findall('step'):
                ts_data = TimeSeriesData(
                    time=float(step.get('time', 0)),
                    running_vehicles=int(step.get('running', 0)),
                    halting_vehicles=int(step.get('halting', 0)),
                    mean_speed=float(step.get('meanSpeed', 0)),
                    mean_waiting_time=float(step.get('meanWaitingTime', 0)),
                    teleports=int(step.get('teleports', 0)),
                    collisions=int(step.get('collisions', 0))
                )
                time_series.append(ts_data)
        
        except Exception as e:
            print(f"Error extracting time series: {e}")
        
        return time_series
    
    def _extract_trip_data(self, tripinfo_file: Optional[Path]) -> List[Dict[str, Any]]:
        """Extract individual trip data"""
        trips = []
        
        if not tripinfo_file or not tripinfo_file.exists():
            return trips
        
        try:
            tree = ET.parse(tripinfo_file)
            root = tree.getroot()
            
            for tripinfo in root.findall('tripinfo'):
                trip = {
                    'id': tripinfo.get('id'),
                    'depart': float(tripinfo.get('depart', 0)),
                    'arrival': float(tripinfo.get('arrival', 0)),
                    'duration': float(tripinfo.get('duration', 0)),
                    'routeLength': float(tripinfo.get('routeLength', 0)),
                    'waitingTime': float(tripinfo.get('waitingTime', 0)),
                    'timeLoss': float(tripinfo.get('timeLoss', 0)),
                    'vType': tripinfo.get('vtype', 'unknown'),
                    'departSpeed': float(tripinfo.get('departSpeed', 0)),
                    'arrivalSpeed': float(tripinfo.get('arrivalSpeed', 0))
                }
                
                # Calculate average speed
                if trip['duration'] > 0:
                    trip['avgSpeed'] = trip['routeLength'] / trip['duration']
                else:
                    trip['avgSpeed'] = 0
                
                trips.append(trip)
        
        except Exception as e:
            print(f"Error extracting trip data: {e}")
        
        return trips
    
    def _generate_recommendations(self, kpis: TrafficKPIs) -> List[Dict[str, Any]]:
        """Generate recommendations based on KPIs and rules"""
        recommendations = []
        
        for rule in self.recommendation_rules:
            try:
                kpi_value = getattr(kpis, rule.condition, 0)
                
                # Check condition based on rule type
                condition_met = False
                if rule.condition in ['avg_waiting_time', 'avg_time_loss', 'total_teleports', 'total_collisions', 
                                    'total_co2', 'total_nox', 'total_fuel_consumption', 'avg_edge_density', 
                                    'avg_edge_occupancy', 'bottleneck_edges', 'avg_deceleration_events', 'emergency_stops']:
                    # Higher is worse
                    condition_met = kpi_value > rule.threshold
                elif rule.condition in ['throughput', 'flow_rate', 'avg_speed', 'avg_network_speed', 'safety_score']:
                    # Lower is worse (except for positive rules)
                    if rule.rule_id == 'good_flow':
                        condition_met = kpi_value >= rule.threshold
                    else:
                        condition_met = kpi_value < rule.threshold
                
                if condition_met:
                    recommendation = {
                        'id': rule.rule_id,
                        'message': rule.message.format(value=kpi_value),
                        'priority': rule.priority,
                        'category': rule.category,
                        'kpi': rule.condition,
                        'threshold': rule.threshold,
                        'actual_value': kpi_value
                    }
                    recommendations.append(recommendation)
            
            except Exception as e:
                print(f"Error evaluating rule {rule.rule_id}: {e}")
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return recommendations
    
    def _analyze_vehicle_types(self, trip_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze vehicle type breakdown"""
        type_stats = {}
        
        for trip in trip_data:
            vtype = trip.get('vType', 'unknown')
            
            if vtype not in type_stats:
                type_stats[vtype] = {
                    'count': 0,
                    'total_distance': 0,
                    'total_time': 0,
                    'total_waiting_time': 0
                }
            
            type_stats[vtype]['count'] += 1
            type_stats[vtype]['total_distance'] += trip.get('routeLength', 0)
            type_stats[vtype]['total_time'] += trip.get('duration', 0)
            type_stats[vtype]['total_waiting_time'] += trip.get('waitingTime', 0)
        
        # Calculate averages
        for vtype, stats in type_stats.items():
            if stats['count'] > 0:
                stats['avg_distance'] = stats['total_distance'] / stats['count']
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['avg_waiting_time'] = stats['total_waiting_time'] / stats['count']
                stats['avg_speed'] = stats['total_distance'] / stats['total_time'] if stats['total_time'] > 0 else 0
        
        return type_stats
    
    def _analyze_routes(self, trip_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze route patterns and statistics"""
        if not trip_data:
            return {}
        
        route_lengths = [trip['routeLength'] for trip in trip_data]
        durations = [trip['duration'] for trip in trip_data]
        speeds = [trip.get('avgSpeed', 0) for trip in trip_data]
        
        return {
            'route_length_distribution': {
                'min': min(route_lengths) if route_lengths else 0,
                'max': max(route_lengths) if route_lengths else 0,
                'median': statistics.median(route_lengths) if route_lengths else 0,
                'std_dev': statistics.stdev(route_lengths) if len(route_lengths) > 1 else 0
            },
            'duration_distribution': {
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0,
                'median': statistics.median(durations) if durations else 0,
                'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0
            },
            'speed_distribution': {
                'min': min(speeds) if speeds else 0,
                'max': max(speeds) if speeds else 0,
                'median': statistics.median(speeds) if speeds else 0,
                'std_dev': statistics.stdev(speeds) if len(speeds) > 1 else 0
            }
        }
    
    def _analyze_temporal_patterns(self, time_series: List[TimeSeriesData]) -> Dict[str, Any]:
        """Analyze temporal patterns in the simulation"""
        if not time_series:
            return {}
        
        # Find peak times
        max_running = max((ts.running_vehicles for ts in time_series), default=0)
        peak_times = [ts.time for ts in time_series if ts.running_vehicles >= max_running * 0.9]
        
        # Find congested periods (high halting vehicles)
        total_vehicles_by_time = [(ts.time, ts.running_vehicles + ts.halting_vehicles) for ts in time_series]
        if total_vehicles_by_time:
            avg_total = statistics.mean([total for _, total in total_vehicles_by_time])
            congested_periods = [time for time, total in total_vehicles_by_time if total > avg_total * 1.2]
        else:
            congested_periods = []
        
        return {
            'peak_traffic_times': peak_times[:5],  # Top 5 peak times
            'max_concurrent_vehicles': max_running,
            'congested_periods': congested_periods[:10],  # Top 10 congested periods
            'simulation_duration': max((ts.time for ts in time_series), default=0),
            'avg_speed_over_time': [{'time': ts.time, 'speed': ts.mean_speed} for ts in time_series[-20:]]  # Last 20 data points
        }

    def compare_sessions(self, session_paths: List[str]) -> Dict[str, Any]:
        """
        Compare multiple simulation sessions with caching
        
        Args:
            session_paths: List of session directory paths
            
        Returns:
            Comparison analysis results
        """
        # Generate cache key for this comparison
        session_ids = [Path(path).name for path in session_paths]
        cache_key = f"comparison_{'_'.join(sorted(session_ids))}"
        
        # Check if comparison is cached
        cached_result = self._get_comparison_cache(cache_key)
        if cached_result:
            print(f"Using cached comparison for sessions: {session_ids}")
            return cached_result
        
        print(f"Computing comparison for sessions: {session_ids}")
        comparisons = {}
        session_data = {}
        
        # Analyze each session (this uses individual session caching)
        for session_path in session_paths:
            session_id = Path(session_path).name
            analysis = self.analyze_session(session_path)  # This already has caching
            session_data[session_id] = analysis
        
        # Compare KPIs
        kpi_comparison = self._compare_kpis(session_data)
        
        # Compare recommendations  
        recommendation_comparison = self._compare_recommendations(session_data)
        
        result = {
            "comparison_timestamp": datetime.now().isoformat(),
            "sessions": list(session_data.keys()),
            "session_data": session_data,
            "kpi_comparison": kpi_comparison,
            "recommendation_comparison": recommendation_comparison,
            "best_performing_session": self._find_best_session(session_data)
        }
        
        # Cache the result
        self._cache_comparison(cache_key, result)
        
        return result
    
    def _compare_kpis(self, session_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare KPIs across sessions"""
        comparison = {}
        
        # Get all KPI keys from the first valid session
        kpi_keys = []
        for session_id, data in session_data.items():
            if "kpis" in data and isinstance(data["kpis"], dict):
                kpi_keys = list(data["kpis"].keys())
                break
        
        # Compare each KPI
        for kpi in kpi_keys:
            values = {}
            for session_id, data in session_data.items():
                if "kpis" in data and kpi in data["kpis"]:
                    values[session_id] = data["kpis"][kpi]
            
            if values:
                comparison[kpi] = {
                    "values": values,
                    "best_session": min(values.keys(), key=lambda k: abs(values[k])) if kpi in ['avg_waiting_time', 'avg_time_loss'] else max(values.keys(), key=lambda k: values[k]),
                    "worst_session": max(values.keys(), key=lambda k: abs(values[k])) if kpi in ['avg_waiting_time', 'avg_time_loss'] else min(values.keys(), key=lambda k: values[k])
                }
        
        return comparison
    
    def _compare_recommendations(self, session_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare recommendations across sessions"""
        all_recommendations = {}
        
        for session_id, data in session_data.items():
            if "recommendations" in data:
                all_recommendations[session_id] = data["recommendations"]
        
        # Count recommendation categories
        category_counts = {}
        priority_counts = {}
        
        for session_id, recommendations in all_recommendations.items():
            category_counts[session_id] = {}
            priority_counts[session_id] = {}
            
            for rec in recommendations:
                category = rec.get("category", "unknown")
                priority = rec.get("priority", "unknown")
                
                category_counts[session_id][category] = category_counts[session_id].get(category, 0) + 1
                priority_counts[session_id][priority] = priority_counts[session_id].get(priority, 0) + 1
        
        return {
            "all_recommendations": all_recommendations,
            "category_breakdown": category_counts,
            "priority_breakdown": priority_counts
        }
    
    def _find_best_session(self, session_data: Dict[str, Dict]) -> Optional[str]:
        """Find the best performing session based on key metrics"""
        scores = {}
        
        for session_id, data in session_data.items():
            if "kpis" not in data or "error" in data:
                continue
            
            kpis = data["kpis"]
            
            # Calculate composite score (higher is better)
            score = 0
            
            # Positive factors
            score += kpis.get("avg_speed", 0) * 10  # Higher speed is better
            score += kpis.get("throughput", 0) * 0.01  # Higher throughput is better
            score += kpis.get("flow_rate", 0) * 100  # Higher flow is better
            
            # Negative factors
            score -= kpis.get("avg_waiting_time", 0) * 0.1  # Lower waiting time is better
            score -= kpis.get("avg_time_loss", 0) * 0.1  # Lower time loss is better
            score -= kpis.get("total_teleports", 0) * 5  # Fewer teleports is better
            score -= kpis.get("total_collisions", 0) * 20  # Fewer collisions is better
            
            scores[session_id] = score
        
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return None
    
    def _analyze_network_performance(self, network_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network performance from edge data"""
        if not network_data:
            return {
                "total_edges": 0,
                "bottleneck_edges": [],
                "utilization_distribution": {},
                "speed_distribution": {},
                "congested_areas": []
            }
        
        try:
            all_edges = []
            bottlenecks = []
            congested_areas = []
            
            # Collect data from all intervals
            for interval_data in network_data:
                for edge_data in interval_data.get('edges', []):
                    all_edges.append(edge_data)
                    
                    # Identify bottlenecks
                    if edge_data.get('is_bottleneck', False):
                        bottlenecks.append({
                            'edge_id': edge_data['id'],
                            'density': edge_data['density'],
                            'occupancy': edge_data['occupancy'],
                            'speed': edge_data['speed'],
                            'waiting_time': edge_data['waitingTime']
                        })
                    
                    # Identify congested areas (high waiting time)
                    if edge_data['waitingTime'] > 30:  # More than 30 seconds waiting
                        congested_areas.append({
                            'edge_id': edge_data['id'],
                            'waiting_time': edge_data['waitingTime'],
                            'occupancy': edge_data['occupancy'],
                            'speed': edge_data['speed']
                        })
            
            # Calculate utilization distribution
            utilization_ranges = {'0-20%': 0, '21-40%': 0, '41-60%': 0, '61-80%': 0, '81-100%': 0}
            speed_ranges = {'0-5 km/h': 0, '6-20 km/h': 0, '21-40 km/h': 0, '41-60 km/h': 0, '60+ km/h': 0}
            
            active_edges = [edge for edge in all_edges if edge['sampledSeconds'] > 0]
            
            for edge in active_edges:
                # Utilization distribution
                util = edge['utilization']
                if util <= 20:
                    utilization_ranges['0-20%'] += 1
                elif util <= 40:
                    utilization_ranges['21-40%'] += 1
                elif util <= 60:
                    utilization_ranges['41-60%'] += 1
                elif util <= 80:
                    utilization_ranges['61-80%'] += 1
                else:
                    utilization_ranges['81-100%'] += 1
                
                # Speed distribution (convert m/s to km/h)
                speed_kmh = edge['speed'] * 3.6
                if speed_kmh <= 5:
                    speed_ranges['0-5 km/h'] += 1
                elif speed_kmh <= 20:
                    speed_ranges['6-20 km/h'] += 1
                elif speed_kmh <= 40:
                    speed_ranges['21-40 km/h'] += 1
                elif speed_kmh <= 60:
                    speed_ranges['41-60 km/h'] += 1
                else:
                    speed_ranges['60+ km/h'] += 1
            
            # Sort bottlenecks and congested areas by severity
            bottlenecks.sort(key=lambda x: x['occupancy'], reverse=True)
            congested_areas.sort(key=lambda x: x['waiting_time'], reverse=True)
            
            return {
                "total_edges": len(all_edges),
                "active_edges": len(active_edges),
                "bottleneck_edges": bottlenecks[:10],  # Top 10 bottlenecks
                "utilization_distribution": utilization_ranges,
                "speed_distribution": speed_ranges,
                "congested_areas": congested_areas[:10],  # Top 10 congested areas
                "network_efficiency": len(active_edges) / max(1, len(all_edges)) * 100 if all_edges else 0
            }
            
        except Exception as e:
            print(f"Error analyzing network performance: {e}")
            return {
                "total_edges": 0,
                "bottleneck_edges": [],
                "utilization_distribution": {},
                "speed_distribution": {},
                "congested_areas": [],
                "error": str(e)
            }
    
    def _enhance_safety_metrics(self, kpis: TrafficKPIs, tripinfo_file: Optional[Path]) -> TrafficKPIs:
        """Calculate enhanced safety metrics from available data"""
        try:
            # Calculate safety score based on existing metrics
            safety_score = 100.0  # Start with perfect score
            
            # Penalize for collisions (most severe)
            if kpis.total_collisions > 0:
                collision_penalty = min(50, kpis.total_collisions * 10)
                safety_score -= collision_penalty
            
            # Penalize for teleports (safety incidents)
            if kpis.total_teleports > 0:
                teleport_penalty = min(30, kpis.total_teleports * 2)
                safety_score -= teleport_penalty
            
            # Penalize for high waiting times (potential for aggressive behavior)
            if kpis.avg_waiting_time > 60:  # More than 1 minute
                waiting_penalty = min(10, (kpis.avg_waiting_time - 60) / 60 * 5)
                safety_score -= waiting_penalty
            
            # Penalize for low speeds (potential congestion leading to safety issues)
            if kpis.avg_speed < 2.0:  # Less than 7.2 km/h
                speed_penalty = min(10, (2.0 - kpis.avg_speed) * 5)
                safety_score -= speed_penalty
            
            # Penalize for high time loss (frustration leading to risky behavior)
            if kpis.avg_time_loss > 120:  # More than 2 minutes
                time_loss_penalty = min(10, (kpis.avg_time_loss - 120) / 120 * 5)
                safety_score -= time_loss_penalty
            
            kpis.safety_score = max(0, safety_score)
            
            # Analyze trip data for detailed safety metrics
            if tripinfo_file and tripinfo_file.exists():
                kpis = self._analyze_trip_safety_patterns(tripinfo_file, kpis)
            
            print(f"Calculated safety score: {kpis.safety_score:.1f}/100")
            
        except Exception as e:
            print(f"Error enhancing safety metrics: {e}")
        
        return kpis
    
    def _analyze_trip_safety_patterns(self, tripinfo_file: Path, kpis: TrafficKPIs) -> TrafficKPIs:
        """Analyze trip data for safety-related patterns"""
        try:
            tree = ET.parse(tripinfo_file)
            root = tree.getroot()
            
            deceleration_events = 0
            emergency_stops = 0
            total_trips = 0
            
            for tripinfo in root.findall('tripinfo'):
                total_trips += 1
                
                # Analyze trip characteristics for safety indicators
                duration = float(tripinfo.get('duration', 0))
                route_length = float(tripinfo.get('routeLength', 0))
                waiting_time = float(tripinfo.get('waitingTime', 0))
                time_loss = float(tripinfo.get('timeLoss', 0))
                depart_delay = float(tripinfo.get('departDelay', 0))
                
                # Estimate deceleration events from time loss and waiting time
                # High time loss relative to trip duration suggests frequent stops/slowdowns
                if duration > 0:
                    time_loss_ratio = time_loss / duration
                    if time_loss_ratio > 0.3:  # More than 30% of trip was lost time
                        deceleration_events += 1
                
                # Estimate emergency stops from high waiting time relative to duration
                if duration > 0 and waiting_time > 0:
                    waiting_ratio = waiting_time / duration
                    if waiting_ratio > 0.2:  # More than 20% of trip was waiting
                        emergency_stops += 1
            
            # Update KPIs with safety metrics
            if total_trips > 0:
                kpis.avg_emergency_stops = emergency_stops / total_trips
                kpis.high_deceleration_events = deceleration_events
                kpis.lane_change_frequency = 0.0  # Would need lane change data
            
            return kpis
            
        except Exception as e:
            print(f"Error analyzing trip safety patterns: {e}")
            return kpis
    
    def _extract_emissions_data(self, emissions_file: Path, max_vehicles: int = 250) -> List[Dict[str, Any]]:
        """Extract vehicle emissions data for database storage with sampling for large files"""
        emissions_data = []
        try:
            # Check file size first
            file_size = emissions_file.stat().st_size
            large_file_threshold = 100 * 1024 * 1024  # 100MB
            
            if file_size > large_file_threshold:
                print(f"Large emissions file detected ({file_size / (1024*1024):.1f} MB). Using streaming approach...")
                return self._extract_emissions_data_streaming(emissions_file, max_vehicles)
            
            # For smaller files, use the normal approach
            import xml.etree.ElementTree as ET
            tree = ET.parse(emissions_file)
            root = tree.getroot()
            
            for vehicle in root.findall('.//vehicle'):
                vehicle_data = {
                    'vehicle_id': vehicle.get('id', ''),
                    'vehicle_type': vehicle.get('type', 'default'),
                    'co2_emissions': float(vehicle.get('CO2', 0)),
                    'co_emissions': float(vehicle.get('CO', 0)),
                    'hc_emissions': float(vehicle.get('HC', 0)),
                    'nox_emissions': float(vehicle.get('NOx', 0)),
                    'pmx_emissions': float(vehicle.get('PMx', 0)),
                    'fuel_consumption': float(vehicle.get('fuel', 0)),
                    'energy_consumption': float(vehicle.get('electricity', 0)),
                    # These might need to be calculated from other sources
                    'distance_traveled': 0.0,
                    'travel_time': 0.0
                }
                emissions_data.append(vehicle_data)
                
        except Exception as e:
            print(f"Error extracting emissions data: {e}")
            
        return emissions_data
    
    def _extract_emissions_data_streaming(self, emissions_file: Path, max_vehicles: int = 250) -> List[Dict[str, Any]]:
        """Extract emissions data using streaming for large files"""
        emissions_data = []
        vehicle_count = 0
        sample_interval = 1  # Start by sampling every vehicle
        
        try:
            import xml.etree.ElementTree as ET
            
            # Calculate sampling interval based on file size
            file_size = emissions_file.stat().st_size
            estimated_vehicles = file_size // 1000  # Rough estimate
            if estimated_vehicles > max_vehicles:
                sample_interval = estimated_vehicles // max_vehicles
                print(f"Sampling every {sample_interval}th vehicle from large emissions file")
            
            # Use iterparse for memory-efficient processing
            context = ET.iterparse(emissions_file, events=('start', 'end'))
            context = iter(context)
            
            event, root = next(context)
            
            for event, elem in context:
                if event == 'end' and elem.tag == 'vehicle':
                    vehicle_count += 1
                    
                    # Sample vehicles based on interval
                    if vehicle_count % sample_interval == 0:
                        vehicle_data = {
                            'vehicle_id': elem.get('id', ''),
                            'vehicle_type': elem.get('type', 'default'),
                            'co2_emissions': float(elem.get('CO2', 0)),
                            'co_emissions': float(elem.get('CO', 0)),
                            'hc_emissions': float(elem.get('HC', 0)),
                            'nox_emissions': float(elem.get('NOx', 0)),
                            'pmx_emissions': float(elem.get('PMx', 0)),
                            'fuel_consumption': float(elem.get('fuel', 0)),
                            'energy_consumption': float(elem.get('electricity', 0)),
                            'distance_traveled': 0.0,
                            'travel_time': 0.0
                        }
                        emissions_data.append(vehicle_data)
                        
                        # Stop when we have enough samples
                        if len(emissions_data) >= max_vehicles:
                            break
                    
                    # Clear the element to free memory
                    elem.clear()
                    root.clear()
            
            print(f"Extracted {len(emissions_data)} vehicle emissions records from {vehicle_count} total vehicles")
            
        except Exception as e:
            print(f"Error in streaming emissions extraction: {e}")
            
        return emissions_data
    
    def _extract_edge_data(self, edgedata_file: Path) -> List[Dict[str, Any]]:
        """Extract edge performance data for database storage"""
        edge_data = []
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(edgedata_file)
            root = tree.getroot()
            
            for interval in root.findall('.//interval'):
                interval_begin = float(interval.get('begin', 0))
                interval_end = float(interval.get('end', 0))
                
                for edge in interval.findall('.//edge'):
                    edge_record = {
                        'edge_id': edge.get('id', ''),
                        'time_interval_begin': interval_begin,
                        'time_interval_end': interval_end,
                        'entered_vehicles': int(edge.get('entered', 0)),
                        'left_vehicles': int(edge.get('left', 0)),
                        'vehicle_sum': int(edge.get('vehSum', 0)),
                        'occupancy': float(edge.get('occupancy', 0)),
                        'mean_speed': float(edge.get('meanSpeed', 0)),
                        'density': float(edge.get('density', 0)),
                        'travel_time': float(edge.get('traveltime', 0)),
                        'waiting_time': float(edge.get('waitingTime', 0)),
                        # Safety metrics (if available from edge attributes)
                        'emergency_stops': 0,  # Would need additional SUMO output
                        'high_decel_events': 0  # Would need additional SUMO output
                    }
                    edge_data.append(edge_record)
                    
        except Exception as e:
            print(f"Error extracting edge data: {e}")
            
        return edge_data
    
    def _extract_safety_metrics(self, trip_data: List[Dict], network_data: Dict, time_series: List) -> Dict[str, Any]:
        """Extract safety metrics for database storage"""
        try:
            # Calculate trip-based safety metrics
            total_emergency_stops = 0
            total_high_decel_events = 0
            total_lane_changes = 0
            total_deceleration = 0.0
            max_deceleration = 0.0
            
            # Process trip data for safety indicators
            for trip in trip_data:
                # Estimate emergency stops and high deceleration events
                # These would ideally come from detailed SUMO output
                duration = trip.get('duration', 0)
                waiting_time = trip.get('waiting_time', 0)
                time_loss = trip.get('time_loss', 0)
                
                if duration > 0:
                    # Estimate emergency stops from high waiting time ratio
                    waiting_ratio = waiting_time / duration
                    if waiting_ratio > 0.2:
                        total_emergency_stops += 1
                    
                    # Estimate high deceleration events from time loss ratio
                    time_loss_ratio = time_loss / duration
                    if time_loss_ratio > 0.3:
                        total_high_decel_events += 1
                        
                    # Estimate deceleration from time patterns
                    estimated_decel = time_loss_ratio * 2.0  # rough estimate
                    total_deceleration += estimated_decel
                    max_deceleration = max(max_deceleration, estimated_decel)
            
            # Calculate averages
            num_trips = len(trip_data) if trip_data else 1
            avg_deceleration = total_deceleration / num_trips
            
            # Identify critical periods (high collision/teleport times)
            critical_periods = []
            if time_series:
                for i, ts in enumerate(time_series):
                    if hasattr(ts, 'collisions') and ts.collisions > 0:
                        critical_periods.append({
                            'time': getattr(ts, 'time', i),
                            'collisions': ts.collisions,
                            'type': 'collision_peak'
                        })
                    if hasattr(ts, 'teleports') and ts.teleports > 2:
                        critical_periods.append({
                            'time': getattr(ts, 'time', i),
                            'teleports': ts.teleports,
                            'type': 'teleport_peak'
                        })
            
            # Identify high risk edges from network data
            high_risk_edges = []
            if network_data and 'edge_performance' in network_data:
                for edge_id, data in network_data['edge_performance'].items():
                    occupancy = data.get('avg_occupancy', 0)
                    waiting_time = data.get('avg_waiting_time', 0)
                    if occupancy > 0.8 or waiting_time > 30:  # High risk thresholds
                        high_risk_edges.append(edge_id)
            
            # Calculate composite safety scores
            collision_density = sum(getattr(ts, 'collisions', 0) for ts in time_series) / max(len(time_series), 1)
            teleport_density = sum(getattr(ts, 'teleports', 0) for ts in time_series) / max(len(time_series), 1)
            
            # Composite safety score (0-100, higher is safer)
            collision_factor = max(0, 100 - collision_density * 10)
            teleport_factor = max(0, 100 - teleport_density * 5)
            decel_factor = max(0, 100 - avg_deceleration * 20)
            composite_safety_score = (collision_factor + teleport_factor + decel_factor) / 3
            
            return {
                'total_emergency_stops': total_emergency_stops,
                'total_high_decel_events': total_high_decel_events,
                'total_lane_changes': total_lane_changes,
                'avg_deceleration': avg_deceleration,
                'max_deceleration': max_deceleration,
                'critical_periods': critical_periods,
                'peak_collision_times': [p for p in critical_periods if p.get('type') == 'collision_peak'],
                'high_risk_edges': high_risk_edges,
                'intersection_hotspots': [],  # Would need intersection analysis
                'collision_risk_score': collision_factor,
                'congestion_safety_impact': teleport_factor,
                'speed_variance_risk': decel_factor,
                'collision_density': collision_density,
                'teleport_density': teleport_density,
                'composite_safety_score': composite_safety_score,
                'avg_emergency_stops': total_emergency_stops / max(num_trips, 1),
                'high_deceleration_events': total_high_decel_events,
                'lane_change_frequency': total_lane_changes / max(num_trips, 1),
                'intersection_conflicts': 0,  # Would need intersection data
                'critical_gap_violations': 0  # Would need gap analysis
            }
            
        except Exception as e:
            print(f"Error extracting safety metrics: {e}")
            return {}

    def _build_cached_analytics_response(self, session_id: str) -> Dict[str, Any]:
        """Build analytics response from cached database data for faster loading"""
        try:
            # Get cached data from database
            kpis = self.db_service.get_kpis(session_id)
            recommendations = self.db_service.get_recommendations(session_id)
            time_series = self.db_service.get_time_series(session_id)
            
            # Build the response in the expected format
            analytics_dict = {
                'kpis': kpis.__dict__ if hasattr(kpis, '__dict__') else kpis,
                'recommendations': [rec.__dict__ if hasattr(rec, '__dict__') else rec for rec in recommendations] if recommendations else [],
                'time_series': [ts.__dict__ if hasattr(ts, '__dict__') else ts for ts in time_series] if time_series else [],
                'analysis_timestamp': datetime.now().isoformat(),
                'emissions_data': [],  # Could be populated if needed
                'safety_data': {},
                'network_analysis': {},
                'route_analysis': {},
                'temporal_patterns': {},
                'performance_metrics': {}
            }
            
            return analytics_dict
            
        except Exception as e:
            print(f"Error building cached analytics response: {e}")
            # Fall back to empty response structure
            return {
                'kpis': {},
                'recommendations': [],
                'time_series': [],
                'analysis_timestamp': datetime.now().isoformat(),
                'emissions_data': [],
                'safety_data': {},
                'network_analysis': {},
                'route_analysis': {},
                'temporal_patterns': {},
                'performance_metrics': {}
            }

    def _get_comparison_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached comparison result"""
        try:
            cache_file = Path("cache") / f"{cache_key}.json"
            if cache_file.exists():
                # Check if cache is less than 1 hour old
                if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() < 3600:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
        except Exception as e:
            print(f"Error reading comparison cache: {e}")
        return None
    
    def _cache_comparison(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache comparison result"""
        try:
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Error caching comparison: {e}")

