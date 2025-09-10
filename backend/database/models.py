"""
Database Models for Traffic Simulator

Defines SQLAlchemy models for session management, configuration storage,
and analytics data persistence.

Author: Traffic Simulator Team
Date: September 2025
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()

class Session(Base):
    """Session table - core session management"""
    __tablename__ = 'sessions'
    
    id = Column(String, primary_key=True)  # session_timestamp_id format
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default='created')  # created, configured, running, completed, failed
    network_id = Column(String)
    network_name = Column(String)
    session_path = Column(String)
    can_analyze = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Multi-session support fields
    traci_port = Column(Integer, nullable=True)  # TraCI port for this session
    process_id = Column(Integer, nullable=True)  # SUMO process ID
    launched_at = Column(DateTime, nullable=True)  # When simulation was launched
    enable_gui = Column(Boolean, default=True)  # Whether GUI is enabled
    is_active = Column(Boolean, default=False)  # Whether session is currently active
    temp_directory = Column(String, nullable=True)  # Temporary session directory
    
    # Relationships
    configuration = relationship("Configuration", back_populates="session", uselist=False)
    live_data = relationship("LiveData", back_populates="session")
    kpis = relationship("KPI", back_populates="session", uselist=False)
    trips = relationship("Trip", back_populates="session")
    time_series = relationship("TimeSeries", back_populates="session")
    recommendations = relationship("Recommendation", back_populates="session")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'network_id': self.network_id,
            'network_name': self.network_name,
            'session_path': self.session_path,
            'can_analyze': self.can_analyze,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'traci_port': self.traci_port,
            'process_id': self.process_id,
            'launched_at': self.launched_at.isoformat() if self.launched_at else None,
            'enable_gui': self.enable_gui,
            'is_active': self.is_active,
            'temp_directory': self.temp_directory
        }

class Configuration(Base):
    """Configuration table - user settings per session"""
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    sumo_begin = Column(Integer)
    sumo_end = Column(Integer)
    sumo_step_length = Column(Float)
    sumo_time_to_teleport = Column(Integer)
    sumo_traffic_intensity = Column(Float)
    enabled_vehicles = Column(Text)  # JSON array
    traffic_control_method = Column(String)
    traffic_control_config = Column(Text)  # JSON object
    vehicle_types_config = Column(Text)  # JSON object
    speed_limits = Column(Text)  # JSON array
    road_closures = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="configuration")
    
    def get_enabled_vehicles(self) -> List[str]:
        """Get enabled vehicles as list"""
        return json.loads(self.enabled_vehicles) if self.enabled_vehicles else []
    
    def set_enabled_vehicles(self, vehicles: List[str]):
        """Set enabled vehicles from list"""
        self.enabled_vehicles = json.dumps(vehicles)
    
    def get_traffic_control_config(self) -> Dict[str, Any]:
        """Get traffic control config as dict"""
        return json.loads(self.traffic_control_config) if self.traffic_control_config else {}
    
    def set_traffic_control_config(self, config: Dict[str, Any]):
        """Set traffic control config from dict"""
        self.traffic_control_config = json.dumps(config)
    
    def get_vehicle_types_config(self) -> Dict[str, Any]:
        """Get vehicle types config as dict"""
        return json.loads(self.vehicle_types_config) if self.vehicle_types_config else {}
    
    def set_vehicle_types_config(self, config: Dict[str, Any]):
        """Set vehicle types config from dict"""
        self.vehicle_types_config = json.dumps(config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sumo_begin': self.sumo_begin,
            'sumo_end': self.sumo_end,
            'sumo_step_length': self.sumo_step_length,
            'sumo_time_to_teleport': self.sumo_time_to_teleport,
            'sumo_traffic_intensity': self.sumo_traffic_intensity,
            'enabled_vehicles': self.get_enabled_vehicles(),
            'traffic_control_method': self.traffic_control_method,
            'traffic_control_config': self.get_traffic_control_config(),
            'vehicle_types_config': self.get_vehicle_types_config(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LiveData(Base):
    """Live simulation data - real-time metrics"""
    __tablename__ = 'live_data'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    simulation_time = Column(Integer)
    active_vehicles = Column(Integer)
    avg_speed = Column(Float)
    throughput = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(Text)  # JSON for additional metrics
    
    # Relationships
    session = relationship("Session", back_populates="live_data")
    
    def get_raw_data(self) -> Dict[str, Any]:
        """Get raw data as dict"""
        return json.loads(self.raw_data) if self.raw_data else {}
    
    def set_raw_data(self, data: Dict[str, Any]):
        """Set raw data from dict"""
        self.raw_data = json.dumps(data)

class KPI(Base):
    """KPIs table - post-simulation analytics"""
    __tablename__ = 'kpis'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    total_vehicles_loaded = Column(Integer)
    total_vehicles_completed = Column(Integer)
    total_vehicles_running = Column(Integer)
    total_vehicles_waiting = Column(Integer)
    avg_travel_time = Column(Float)
    max_travel_time = Column(Float)
    avg_waiting_time = Column(Float)
    max_waiting_time = Column(Float)
    avg_speed = Column(Float)
    avg_relative_speed = Column(Float)
    avg_route_length = Column(Float)
    total_distance_traveled = Column(Float)
    avg_density = Column(Float)
    max_density = Column(Float)
    congestion_index = Column(Float)
    throughput = Column(Float)
    flow_rate = Column(Float)
    avg_time_loss = Column(Float)
    total_teleports = Column(Integer)
    total_collisions = Column(Integer)
    simulation_duration = Column(Float)
    total_co2 = Column(Float)
    total_co = Column(Float)
    total_nox = Column(Float)
    total_fuel_consumption = Column(Float)
    notes = Column(Text)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="kpis")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert KPIs to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'total_vehicles_loaded': self.total_vehicles_loaded,
            'total_vehicles_completed': self.total_vehicles_completed,
            'total_vehicles_running': self.total_vehicles_running,
            'total_vehicles_waiting': self.total_vehicles_waiting,
            'avg_travel_time': self.avg_travel_time,
            'max_travel_time': self.max_travel_time,
            'avg_waiting_time': self.avg_waiting_time,
            'max_waiting_time': self.max_waiting_time,
            'avg_speed': self.avg_speed,
            'avg_relative_speed': self.avg_relative_speed,
            'avg_route_length': self.avg_route_length,
            'total_distance_traveled': self.total_distance_traveled,
            'avg_density': self.avg_density,
            'max_density': self.max_density,
            'congestion_index': self.congestion_index,
            'throughput': self.throughput,
            'flow_rate': self.flow_rate,
            'avg_time_loss': self.avg_time_loss,
            'total_teleports': self.total_teleports,
            'total_collisions': self.total_collisions,
            'simulation_duration': self.simulation_duration,
            'total_co2': self.total_co2,
            'total_co': self.total_co,
            'total_nox': self.total_nox,
            'total_fuel_consumption': self.total_fuel_consumption,
            'notes': self.notes,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None
        }

class Trip(Base):
    """Individual trip data - detailed vehicle information"""
    __tablename__ = 'trips'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    vehicle_id = Column(String)
    vehicle_type = Column(String)
    depart_time = Column(Float)
    arrival_time = Column(Float)
    duration = Column(Float)
    route_length = Column(Float)
    waiting_time = Column(Float)
    time_loss = Column(Float)
    avg_speed = Column(Float)
    depart_speed = Column(Float)
    arrival_speed = Column(Float)
    
    # Relationships
    session = relationship("Session", back_populates="trips")

class TimeSeries(Base):
    """Time series data - for trend analysis"""
    __tablename__ = 'time_series'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    time_step = Column(Float)
    running_vehicles = Column(Integer)
    halting_vehicles = Column(Integer)
    mean_speed = Column(Float)
    mean_waiting_time = Column(Float)
    teleports = Column(Integer)
    collisions = Column(Integer)
    
    # Relationships
    session = relationship("Session", back_populates="time_series")

class Recommendation(Base):
    """Recommendations - AI/rule-based suggestions"""
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    rule_id = Column(String)
    priority = Column(String)
    category = Column(String)
    message = Column(Text)
    kpi_name = Column(String)
    actual_value = Column(Float)
    threshold_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="recommendations")

class Network(Base):
    """Networks metadata - for better network management"""
    __tablename__ = 'networks'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    path = Column(String)
    is_osm_scenario = Column(Boolean, default=False)
    vehicle_types = Column(Text)  # JSON array of available types
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    def get_vehicle_types(self) -> List[str]:
        """Get vehicle types as list"""
        return json.loads(self.vehicle_types) if self.vehicle_types else []
    
    def set_vehicle_types(self, types: List[str]):
        """Set vehicle types from list"""
        self.vehicle_types = json.dumps(types)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert network to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'is_osm_scenario': self.is_osm_scenario,
            'vehicle_types': self.get_vehicle_types(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
