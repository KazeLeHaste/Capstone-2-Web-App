"""
Database Service Layer

Provides database operations for session management, configuration storage,
and analytics data persistence.

Author: Traffic Simulator Team  
Date: September 2025
"""

from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import os

from .models import (
    Base, Session, Configuration, LiveData, KPI, Trip, TimeSeries, Recommendation, Network,
    VehicleEmissions, EdgeData, SafetyMetrics, RouteAnalysis, TemporalPatterns
)

class DatabaseService:
    """Database service for traffic simulator"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database service
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Default to backend directory
            backend_dir = Path(__file__).parent.parent
            db_path = backend_dir / "traffic_simulator.db"
        
        self.db_path = str(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        SessionLocal = sessionmaker(bind=self.engine)
        self.Session = scoped_session(SessionLocal)
    
    def get_session(self):
        """Get database session"""
        return self.Session()
    
    def close_session(self):
        """Close database session"""
        self.Session.remove()
    
    # ============================================================================
    # Session Management
    # ============================================================================
    
    def create_session(self, session_id: str, network_id: str = None, 
                      network_name: str = None, session_path: str = None,
                      traci_port: int = None, enable_gui: bool = True,
                      temp_directory: str = None) -> Session:
        """Create a new simulation session with enhanced multi-session support"""
        db_session = self.get_session()
        try:
            sim_session = Session(
                id=session_id,
                network_id=network_id,
                network_name=network_name,
                session_path=session_path,
                status='created',
                traci_port=traci_port,
                enable_gui=enable_gui,
                is_active=False,
                temp_directory=temp_directory
            )
            db_session.add(sim_session)
            db_session.commit()
            
            # Refresh to ensure all attributes are loaded
            db_session.refresh(sim_session)
            
            # Expunge the object from the session so it can be used after session closes
            db_session.expunge(sim_session)
            
            return sim_session
            
            return sim_session
        except IntegrityError:
            db_session.rollback()
            # Session already exists, return existing
            existing = db_session.query(Session).filter_by(id=session_id).first()
            if existing:
                db_session.expunge(existing)
            return existing
        finally:
            db_session.close()
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        db_session = self.get_session()
        try:
            sim_session = db_session.query(Session).filter_by(id=session_id).first()
            if sim_session:
                db_session.expunge(sim_session)
            return sim_session
        finally:
            db_session.close()
    
    def update_session_status(self, session_id: str, status: str, **kwargs) -> bool:
        """Update session status and other fields"""
        db_session = self.get_session()
        try:
            sim_session = db_session.query(Session).filter_by(id=session_id).first()
            if sim_session:
                sim_session.status = status
                sim_session.updated_at = datetime.utcnow()
                
                # Update additional fields
                for key, value in kwargs.items():
                    if hasattr(sim_session, key):
                        setattr(sim_session, key, value)
                
                db_session.commit()
                return True
            return False
        except Exception as e:
            db_session.rollback()
            print(f"Error updating session status: {e}")
            return False
        finally:
            db_session.close()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """Get recent sessions"""
        db_session = self.get_session()
        try:
            sessions = db_session.query(Session).order_by(Session.created_at.desc()).limit(limit).all()
            # Expunge all sessions so they can be used after session closes
            for session in sessions:
                db_session.expunge(session)
            return sessions
        finally:
            db_session.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and all related data"""
        db_session = self.get_session()
        try:
            # Delete in proper order to respect foreign key constraints
            db_session.query(Recommendation).filter_by(session_id=session_id).delete()
            db_session.query(TimeSeries).filter_by(session_id=session_id).delete()
            db_session.query(Trip).filter_by(session_id=session_id).delete()
            db_session.query(LiveData).filter_by(session_id=session_id).delete()
            db_session.query(KPI).filter_by(session_id=session_id).delete()
            db_session.query(Configuration).filter_by(session_id=session_id).delete()
            db_session.query(Session).filter_by(id=session_id).delete()
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error deleting session: {e}")
            return False
        finally:
            db_session.close()
    
    def get_active_sessions(self) -> List[Session]:
        """Get all currently active sessions"""
        db_session = self.get_session()
        try:
            sessions = db_session.query(Session).filter_by(is_active=True).all()
            # Expunge all sessions so they can be used after session closes
            for session in sessions:
                db_session.expunge(session)
            return sessions
        finally:
            db_session.close()
    
    def set_session_active(self, session_id: str, is_active: bool, 
                          process_id: int = None, launched_at: datetime = None) -> bool:
        """Set session active status and related fields"""
        db_session = self.get_session()
        try:
            sim_session = db_session.query(Session).filter_by(id=session_id).first()
            if sim_session:
                sim_session.is_active = is_active
                sim_session.updated_at = datetime.utcnow()
                
                if process_id is not None:
                    sim_session.process_id = process_id
                if launched_at is not None:
                    sim_session.launched_at = launched_at
                
                db_session.commit()
                return True
            return False
        except Exception as e:
            db_session.rollback()
            print(f"Error setting session active status: {e}")
            return False
        finally:
            db_session.close()
    
    def cleanup_inactive_sessions(self, timeout_hours: int = 1) -> int:
        """Clean up sessions that have been inactive for too long"""
        db_session = self.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)
            inactive_sessions = db_session.query(Session).filter(
                Session.updated_at < cutoff_time,
                Session.status.in_(['created', 'configured'])
            ).all()
            
            count = 0
            for session in inactive_sessions:
                # Only cleanup if not currently active
                if not session.is_active:
                    session.status = 'expired'
                    session.updated_at = datetime.utcnow()
                    count += 1
            
            db_session.commit()
            return count
        except Exception as e:
            db_session.rollback()
            print(f"Error cleaning up inactive sessions: {e}")
            return 0
        finally:
            db_session.close()
    
    # ============================================================================
    # Configuration Management
    # ============================================================================
    
    def save_configuration(self, session_id: str, config_data: Dict[str, Any]) -> bool:
        """Save session configuration"""
        db_session = self.get_session()
        try:
            # Check if configuration already exists
            existing_config = db_session.query(Configuration).filter_by(session_id=session_id).first()
            
            config = config_data.get('config', {})
            
            if existing_config:
                # Update existing configuration
                existing_config.sumo_begin = config.get('sumo_begin')
                existing_config.sumo_end = config.get('sumo_end')
                existing_config.sumo_step_length = config.get('sumo_step_length')
                existing_config.sumo_time_to_teleport = config.get('sumo_time_to_teleport')
                existing_config.sumo_traffic_intensity = config.get('sumo_traffic_intensity')
                existing_config.set_enabled_vehicles(config.get('enabledVehicles', []))
                existing_config.traffic_control_method = config.get('trafficControl', {}).get('method')
                existing_config.set_traffic_control_config(config.get('trafficControl', {}))
                existing_config.set_vehicle_types_config(config.get('vehicleTypes', {}))
                configuration = existing_config
            else:
                # Create new configuration
                configuration = Configuration(
                    session_id=session_id,
                    sumo_begin=config.get('sumo_begin'),
                    sumo_end=config.get('sumo_end'),
                    sumo_step_length=config.get('sumo_step_length'),
                    sumo_time_to_teleport=config.get('sumo_time_to_teleport'),
                    sumo_traffic_intensity=config.get('sumo_traffic_intensity'),
                    traffic_control_method=config.get('trafficControl', {}).get('method')
                )
                configuration.set_enabled_vehicles(config.get('enabledVehicles', []))
                configuration.set_traffic_control_config(config.get('trafficControl', {}))
                configuration.set_vehicle_types_config(config.get('vehicleTypes', {}))
                db_session.add(configuration)
            
            # Update session status
            self.update_session_status(session_id, 'configured')
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving configuration: {e}")
            return False
        finally:
            db_session.close()
    
    def get_configuration(self, session_id: str) -> Optional[Configuration]:
        """Get session configuration"""
        db_session = self.get_session()
        try:
            return db_session.query(Configuration).filter_by(session_id=session_id).first()
        finally:
            db_session.close()
    
    # ============================================================================
    # Live Data Management
    # ============================================================================
    
    def save_live_data(self, session_id: str, live_data: Dict[str, Any]) -> bool:
        """Save live simulation data"""
        db_session = self.get_session()
        try:
            data = LiveData(
                session_id=session_id,
                simulation_time=live_data.get('simulation_time'),
                active_vehicles=live_data.get('active_vehicles'),
                avg_speed=live_data.get('avg_speed'),
                throughput=live_data.get('throughput')
            )
            data.set_raw_data(live_data)
            
            db_session.add(data)
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving live data: {e}")
            return False
        finally:
            db_session.close()
    
    def get_live_data(self, session_id: str, limit: int = 100) -> List[LiveData]:
        """Get recent live data for session"""
        db_session = self.get_session()
        try:
            return db_session.query(LiveData).filter_by(session_id=session_id)\
                            .order_by(LiveData.timestamp.desc()).limit(limit).all()
        finally:
            db_session.close()
    
    # ============================================================================
    # Analytics Management
    # ============================================================================
    
    def save_kpis(self, session_id: str, kpis_data: Dict[str, Any]) -> bool:
        """Save KPIs for session"""
        db_session = self.get_session()
        try:
            # Check if KPIs already exist
            existing_kpis = db_session.query(KPI).filter_by(session_id=session_id).first()
            
            if existing_kpis:
                # Update existing KPIs
                for key, value in kpis_data.items():
                    if hasattr(existing_kpis, key):
                        setattr(existing_kpis, key, value)
                kpis = existing_kpis
            else:
                # Create new KPIs
                kpis = KPI(session_id=session_id, **kpis_data)
                db_session.add(kpis)
            
            # Update session to indicate it can be analyzed
            self.update_session_status(session_id, 'completed', can_analyze=True, completed_at=datetime.utcnow())
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving KPIs: {e}")
            return False
        finally:
            db_session.close()
    
    def get_kpis(self, session_id: str) -> Optional[KPI]:
        """Get KPIs for session"""
        db_session = self.get_session()
        try:
            return db_session.query(KPI).filter_by(session_id=session_id).first()
        finally:
            db_session.close()
    
    def save_trips(self, session_id: str, trips_data: List[Dict[str, Any]]) -> bool:
        """Save trip data for session"""
        db_session = self.get_session()
        try:
            # Delete existing trips for this session
            db_session.query(Trip).filter_by(session_id=session_id).delete()
            
            # Add new trips
            for trip_data in trips_data:
                trip = Trip(session_id=session_id, **trip_data)
                db_session.add(trip)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving trips: {e}")
            return False
        finally:
            db_session.close()
    
    def save_time_series(self, session_id: str, time_series_data: List[Dict[str, Any]]) -> bool:
        """Save time series data for session"""
        db_session = self.get_session()
        try:
            # Delete existing time series for this session
            db_session.query(TimeSeries).filter_by(session_id=session_id).delete()
            
            # Add new time series data
            for ts_data in time_series_data:
                ts = TimeSeries(session_id=session_id, **ts_data)
                db_session.add(ts)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving time series: {e}")
            return False
        finally:
            db_session.close()
    
    def save_recommendations(self, session_id: str, recommendations_data: List[Dict[str, Any]]) -> bool:
        """Save recommendations for session"""
        db_session = self.get_session()
        try:
            # Delete existing recommendations for this session
            db_session.query(Recommendation).filter_by(session_id=session_id).delete()
            
            # Add new recommendations
            for rec_data in recommendations_data:
                rec = Recommendation(session_id=session_id, **rec_data)
                db_session.add(rec)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving recommendations: {e}")
            return False
        finally:
            db_session.close()
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get complete analytics data for session"""
        db_session = self.get_session()
        try:
            session = db_session.query(Session).filter_by(id=session_id).first()
            if not session:
                return None
            
            kpis = db_session.query(KPI).filter_by(session_id=session_id).first()
            recommendations = db_session.query(Recommendation).filter_by(session_id=session_id).all()
            time_series = db_session.query(TimeSeries).filter_by(session_id=session_id).all()
            
            return {
                'session': session.to_dict(),
                'kpis': kpis.to_dict() if kpis else None,
                'recommendations': [rec.__dict__ for rec in recommendations] if recommendations else [],
                'time_series': [ts.__dict__ for ts in time_series] if time_series else [],
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
        finally:
            db_session.close()
    
    # ============================================================================
    # Network Management
    # ============================================================================
    
    def save_network(self, network_data: Dict[str, Any]) -> bool:
        """Save or update network metadata"""
        db_session = self.get_session()
        try:
            network_id = network_data.get('id')
            existing_network = db_session.query(Network).filter_by(id=network_id).first()
            
            if existing_network:
                # Update existing network
                for key, value in network_data.items():
                    if hasattr(existing_network, key) and key != 'id':
                        if key == 'vehicle_types' and isinstance(value, list):
                            existing_network.set_vehicle_types(value)
                        else:
                            setattr(existing_network, key, value)
                existing_network.last_used = datetime.utcnow()
                network = existing_network
            else:
                # Create new network
                network = Network(
                    id=network_id,
                    name=network_data.get('name'),
                    description=network_data.get('description'),
                    path=network_data.get('path'),
                    is_osm_scenario=network_data.get('is_osm_scenario', False)
                )
                if 'vehicle_types' in network_data:
                    network.set_vehicle_types(network_data['vehicle_types'])
                db_session.add(network)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving network: {e}")
            return False
        finally:
            db_session.close()
    
    def get_networks(self) -> List[Network]:
        """Get all networks"""
        db_session = self.get_session()
        try:
            return db_session.query(Network).order_by(Network.last_used.desc().nullslast(), 
                                                     Network.created_at.desc()).all()
        finally:
            db_session.close()
    
    def update_network_last_used(self, network_id: str) -> bool:
        """Update network last used timestamp"""
        db_session = self.get_session()
        try:
            network = db_session.query(Network).filter_by(id=network_id).first()
            if network:
                network.last_used = datetime.utcnow()
                db_session.commit()
                return True
            return False
        except Exception as e:
            db_session.rollback()
            print(f"Error updating network last used: {e}")
            return False
        finally:
            db_session.close()
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old session data"""
        db_session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Get old sessions
            old_sessions = db_session.query(Session).filter(Session.created_at < cutoff_date).all()
            session_ids = [s.id for s in old_sessions]
            
            if not session_ids:
                return 0
            
            # Delete related data
            db_session.query(Recommendation).filter(Recommendation.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(TimeSeries).filter(TimeSeries.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(Trip).filter(Trip.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(LiveData).filter(LiveData.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(KPI).filter(KPI.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(Configuration).filter(Configuration.session_id.in_(session_ids)).delete(synchronize_session=False)
            db_session.query(Session).filter(Session.id.in_(session_ids)).delete(synchronize_session=False)
            
            db_session.commit()
            return len(session_ids)
        except Exception as e:
            db_session.rollback()
            print(f"Error cleaning up old data: {e}")
            return 0
        finally:
            db_session.close()
    
    def initialize_networks_from_filesystem(self, networks_dir: str):
        """
        Initialize networks in database from filesystem
        
        Args:
            networks_dir: Path to networks directory
        """
        try:
            networks_path = Path(networks_dir)
            if not networks_path.exists():
                return
            
            # Scan for network directories
            for network_dir in networks_path.iterdir():
                if network_dir.is_dir():
                    network_id = network_dir.name
                    
                    # Check if network already exists in database
                    db_session = self.get_session()
                    try:
                        existing = db_session.query(Network).filter_by(id=network_id).first()
                        
                        if not existing:
                            # Find network files
                            net_files = list(network_dir.glob("*.net.xml"))
                            metadata_file = network_dir / "metadata.json"
                            
                            # Read metadata if available
                            description = None
                            is_osm_scenario = False
                            vehicle_types = []
                            
                            if metadata_file.exists():
                                try:
                                    with open(metadata_file, 'r') as f:
                                        metadata = json.load(f)
                                        description = metadata.get('description', '')
                                        is_osm_scenario = metadata.get('is_osm_scenario', False)
                                        vehicle_types = metadata.get('vehicle_types', [])
                                except Exception as e:
                                    print(f"Could not read metadata for {network_id}: {e}")
                            
                            # Create network entry
                            network_data = {
                                'id': network_id,
                                'name': network_id.replace('_', ' ').title(),
                                'description': description or f"Network: {network_id}",
                                'path': str(net_files[0]) if net_files else str(network_dir),
                                'is_osm_scenario': is_osm_scenario,
                                'vehicle_types': vehicle_types
                            }
                            
                            self.save_network(network_data)
                            print(f"Initialized network in database: {network_id}")
                    finally:
                        db_session.close()
                        
        except Exception as e:
            print(f"Error initializing networks from filesystem: {e}")
    
    def save_vehicle_emissions(self, session_id: str, emissions_data: List[Dict[str, Any]]) -> bool:
        """Save vehicle emissions data for session"""
        db_session = self.get_session()
        try:
            # Delete existing emissions data for this session
            db_session.query(VehicleEmissions).filter_by(session_id=session_id).delete()
            
            # Add new emissions data
            for emission in emissions_data:
                vehicle_emission = VehicleEmissions(session_id=session_id, **emission)
                db_session.add(vehicle_emission)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving vehicle emissions: {e}")
            return False
        finally:
            db_session.close()
    
    def save_edge_data(self, session_id: str, edge_data: List[Dict[str, Any]]) -> bool:
        """Save edge data for session"""
        db_session = self.get_session()
        try:
            # Delete existing edge data for this session
            db_session.query(EdgeData).filter_by(session_id=session_id).delete()
            
            # Add new edge data
            for edge in edge_data:
                edge_record = EdgeData(session_id=session_id, **edge)
                db_session.add(edge_record)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving edge data: {e}")
            return False
        finally:
            db_session.close()
    
    def save_safety_metrics(self, session_id: str, safety_data: Dict[str, Any]) -> bool:
        """Save safety metrics for session"""
        db_session = self.get_session()
        try:
            # Check if safety metrics already exist
            existing_safety = db_session.query(SafetyMetrics).filter_by(session_id=session_id).first()
            
            if existing_safety:
                # Update existing safety metrics
                for key, value in safety_data.items():
                    if hasattr(existing_safety, key):
                        if key in ['critical_periods', 'peak_collision_times', 'high_risk_edges', 'intersection_hotspots']:
                            # Handle JSON fields
                            setattr(existing_safety, key, json.dumps(value) if value else None)
                        else:
                            setattr(existing_safety, key, value)
                safety_metrics = existing_safety
            else:
                # Create new safety metrics
                # Convert list/dict fields to JSON strings
                processed_data = safety_data.copy()
                for json_field in ['critical_periods', 'peak_collision_times', 'high_risk_edges', 'intersection_hotspots']:
                    if json_field in processed_data and processed_data[json_field]:
                        processed_data[json_field] = json.dumps(processed_data[json_field])
                
                safety_metrics = SafetyMetrics(session_id=session_id, **processed_data)
                db_session.add(safety_metrics)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving safety metrics: {e}")
            return False
        finally:
            db_session.close()
    
    def save_route_analysis(self, session_id: str, route_data: Dict[str, Any]) -> bool:
        """Save route analysis for session"""
        db_session = self.get_session()
        try:
            # Check if route analysis already exists
            existing_route = db_session.query(RouteAnalysis).filter_by(session_id=session_id).first()
            
            if existing_route:
                # Update existing route analysis
                for key, value in route_data.items():
                    if hasattr(existing_route, key):
                        if key in ['most_used_routes', 'route_usage_distribution']:
                            # Handle JSON fields
                            setattr(existing_route, key, json.dumps(value) if value else None)
                        else:
                            setattr(existing_route, key, value)
                route_analysis = existing_route
            else:
                # Create new route analysis
                # Convert list/dict fields to JSON strings
                processed_data = route_data.copy()
                for json_field in ['most_used_routes', 'route_usage_distribution']:
                    if json_field in processed_data and processed_data[json_field]:
                        processed_data[json_field] = json.dumps(processed_data[json_field])
                
                route_analysis = RouteAnalysis(session_id=session_id, **processed_data)
                db_session.add(route_analysis)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving route analysis: {e}")
            return False
        finally:
            db_session.close()
    
    def save_temporal_patterns(self, session_id: str, temporal_data: Dict[str, Any]) -> bool:
        """Save temporal patterns for session"""
        db_session = self.get_session()
        try:
            # Check if temporal patterns already exist
            existing_temporal = db_session.query(TemporalPatterns).filter_by(session_id=session_id).first()
            
            if existing_temporal:
                # Update existing temporal patterns
                for key, value in temporal_data.items():
                    if hasattr(existing_temporal, key):
                        if key in ['hourly_flow_patterns', 'congestion_timeline']:
                            # Handle JSON fields
                            setattr(existing_temporal, key, json.dumps(value) if value else None)
                        else:
                            setattr(existing_temporal, key, value)
                temporal_patterns = existing_temporal
            else:
                # Create new temporal patterns
                # Convert list/dict fields to JSON strings
                processed_data = temporal_data.copy()
                for json_field in ['hourly_flow_patterns', 'congestion_timeline']:
                    if json_field in processed_data and processed_data[json_field]:
                        processed_data[json_field] = json.dumps(processed_data[json_field])
                
                temporal_patterns = TemporalPatterns(session_id=session_id, **processed_data)
                db_session.add(temporal_patterns)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"Error saving temporal patterns: {e}")
            return False
        finally:
            db_session.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        db_session = self.get_session()
        try:
            return {
                'total_sessions': db_session.query(Session).count(),
                'completed_sessions': db_session.query(Session).filter_by(status='completed').count(),
                'total_networks': db_session.query(Network).count(),
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
        finally:
            db_session.close()
