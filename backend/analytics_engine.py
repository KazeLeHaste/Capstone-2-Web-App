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
    
    # Environmental metrics (if emissions data available)
    total_co2: float = 0.0
    total_co: float = 0.0
    total_nox: float = 0.0
    total_fuel_consumption: float = 0.0

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
                rule_id="high_emissions",
                condition="total_co2",
                threshold=10000,  # mg
                message="High CO2 emissions detected ({value:.0f}mg). Consider promoting public transport or electric vehicles.",
                priority="medium",
                category="environmental"
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
    
    def analyze_session(self, session_path: str, session_id: str = None) -> Dict[str, Any]:
        """
        Analyze a complete simulation session
        
        Args:
            session_path: Path to session directory containing SUMO output files
            session_id: Session ID (for database storage)
            
        Returns:
            Dictionary containing complete analytics results
        """
        try:
            session_path = Path(session_path)
            
            # Extract session_id from path if not provided
            if not session_id:
                session_id = session_path.name
            
            # Locate output files
            tripinfo_file = self._find_file(session_path, "*.tripinfos.xml")
            stats_file = self._find_file(session_path, "*.stats.xml")
            summary_file = self._find_file(session_path, "*summary.xml")
            
            # Parse files
            kpis = self._extract_kpis(tripinfo_file, stats_file, summary_file)
            time_series = self._extract_time_series(summary_file)
            trip_data = self._extract_trip_data(tripinfo_file)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(kpis)
            
            # Calculate additional analytics
            vehicle_type_breakdown = self._analyze_vehicle_types(trip_data)
            route_analysis = self._analyze_routes(trip_data)
            temporal_patterns = self._analyze_temporal_patterns(time_series)
            
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
                     summary_file: Optional[Path]) -> TrafficKPIs:
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
        
        # Calculate derived metrics
        kpis = self._calculate_derived_metrics(kpis)
        
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
                if rule.condition in ['avg_waiting_time', 'avg_time_loss', 'total_teleports', 'total_collisions', 'total_co2']:
                    # Higher is worse
                    condition_met = kpi_value > rule.threshold
                elif rule.condition in ['throughput', 'flow_rate', 'avg_speed']:
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
        Compare multiple simulation sessions
        
        Args:
            session_paths: List of session directory paths
            
        Returns:
            Comparison analysis results
        """
        comparisons = {}
        session_data = {}
        
        # Analyze each session
        for session_path in session_paths:
            session_id = Path(session_path).name
            analysis = self.analyze_session(session_path)
            session_data[session_id] = analysis
        
        # Compare KPIs
        kpi_comparison = self._compare_kpis(session_data)
        
        # Compare recommendations
        recommendation_comparison = self._compare_recommendations(session_data)
        
        return {
            "comparison_timestamp": datetime.now().isoformat(),
            "sessions": list(session_data.keys()),
            "session_data": session_data,
            "kpi_comparison": kpi_comparison,
            "recommendation_comparison": recommendation_comparison,
            "best_performing_session": self._find_best_session(session_data)
        }
    
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
