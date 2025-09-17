"""
SUMO Controller Module - Passive Data Collection Implementation

Handles all SUMO simulation management including:
- Process lifecycle management
- TraCI communication with PASSIVE data collection
- Data retrieval without simulation stepping
- Network and scenario management

IMPORTANT: This controller uses passive data collection to preserve user control
over simulation timing and delay settings. It never calls traci.simulationStep()
and allows SUMO GUI to control all timing aspects.

Author: Traffic Simulator Team
Date: August 2025
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Optional, Any

# Import SUMO libraries (will be installed via requirements.txt)
try:
    import traci
    import sumolib
    SUMO_AVAILABLE = True
except ImportError:
    print("Warning: SUMO libraries not available. Install with: pip install traci sumolib")
    SUMO_AVAILABLE = False

class SumoController:
    """
    Main controller class for SUMO simulation management
    """
    
    def __init__(self):
        """
        Initialize SUMO controller
        """
        self.sumo_process = None
        self.simulation_running = False
        self.traci_port = 8813
        self.current_config = None
    
    def check_sumo_availability(self) -> bool:
        """
        Check if SUMO is available and properly installed
        
        Returns:
            bool: True if SUMO is available, False otherwise
        """
        if not SUMO_AVAILABLE:
            return False
        
        try:
            # Try to run SUMO help command
            result = subprocess.run(['sumo', '--help'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_available_networks(self) -> List[Dict[str, Any]]:
        """
        Get list of available SUMO network files
        Note: This method is deprecated. Use simulation_manager.get_available_networks() instead.
        
        Returns:
            List of network information dictionaries (empty - use simulation_manager instead)
        """
        return []
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get list of available simulation scenarios
        Note: This method is deprecated. Use simulation_manager instead.
        
        Returns:
            List of scenario information dictionaries (empty - use simulation_manager instead)
        """
        return []
    
    
    def start_simulation(self, config: Dict[str, Any]) -> bool:
        """
        Start SUMO simulation with given configuration
        
        Args:
            config: Dictionary containing simulation configuration
            
        Returns:
            bool: True if simulation started successfully, False otherwise
        """
        try:
            if not SUMO_AVAILABLE:
                raise Exception("SUMO libraries not available")
            
            if self.simulation_running:
                raise Exception("Simulation is already running")
            
            # Get scenario file path
            scenario_id = config.get('scenario')
            if not scenario_id:
                raise Exception("No scenario specified")
            
            # Note: This method now expects config files to be passed directly
            # since we no longer use the sumo_data directory structure
            config_file = config.get('config_file')
            if not config_file or not os.path.exists(config_file):
                raise Exception(f"Configuration file not found or not specified: {config_file}")
            
            # Start SUMO with TraCI
            sumo_binary = "sumo"  # Use "sumo-gui" for GUI version
            sumo_cmd = [
                sumo_binary,
                "-c", config_file,
                "--remote-port", str(self.traci_port),
                "--start"
            ]
            
            # Add traffic scale if specified
            traffic_scale = config.get('sumo_traffic_scale', config.get('traffic_scale', config.get('sumo_traffic_intensity', 1.0)))  # Legacy fallback
            if traffic_scale != 1.0:
                sumo_cmd.extend(["--scale", str(traffic_scale)])
            
            # Start SUMO process
            self.sumo_process = subprocess.Popen(
                sumo_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment for SUMO to start
            time.sleep(2)
            
            # Connect to SUMO via TraCI
            traci.init(self.traci_port)
            
            # CRITICAL: Send one simulationStep to actually start the simulation
            # This is required when TraCI is enabled - SUMO waits for TraCI to start the simulation
            print("Sending initial simulation step to start the simulation...")
            traci.simulationStep()
            initial_time = traci.simulation.getTime()
            print(f"Simulation started! Initial time: {initial_time}")
            print("Note: Further stepping will be controlled by the application logic")
            
            self.simulation_running = True
            self.current_config = config
            
            print(f"SUMO simulation started successfully with scenario: {scenario_id}")
            return True
            
        except Exception as e:
            print(f"Error starting SUMO simulation: {e}")
            self.cleanup()
            return False
    
    def stop_simulation(self):
        """
        Stop the current SUMO simulation
        """
        try:
            if self.simulation_running:
                traci.close()
                self.simulation_running = False
            
            if self.sumo_process:
                self.sumo_process.terminate()
                self.sumo_process.wait(timeout=5)
                self.sumo_process = None
            
            print("SUMO simulation stopped")
            
        except Exception as e:
            print(f"Error stopping SUMO simulation: {e}")
        finally:
            self.cleanup()
    
    def is_simulation_running(self) -> bool:
        """
        Check if simulation is currently running
        
        Returns:
            bool: True if simulation is running, False otherwise
        """
        if not self.simulation_running:
            return False
        
        try:
            # Check if simulation has ended
            if traci.simulation.getMinExpectedNumber() <= 0:
                return False
            return True
        except:
            return False

    def get_passive_simulation_data(self, last_collected_time: float = 0) -> Dict[str, Any]:
        """
        Get simulation data using fully passive collection approach.
        Only collects data if simulation time has progressed since last collection.
        
        Args:
            last_collected_time: The simulation time when data was last collected
            
        Returns:
            Dictionary containing simulation data, or empty dict if no new data
        """
        if not self.simulation_running:
            return {}
        
        try:
            # Check current simulation time without stepping
            current_time = traci.simulation.getTime()
            
            # Only collect data if simulation time has actually progressed
            if current_time <= last_collected_time:
                return {'simulation_time': current_time, 'data_collected': False}
            
            # Simulation has progressed - collect fresh data
            data = self.get_simulation_data()
            data['data_collected'] = True
            return data
            
        except Exception as e:
            print(f"Error in passive data collection: {e}")
            return {}
    
    def get_simulation_data(self) -> Dict[str, Any]:
        """
        Get current simulation data using passive collection approach.
        This method reads data without stepping the simulation, preserving user delay control.
        
        Returns:
            Dictionary containing simulation data
        """
        if not self.simulation_running:
            return {}
        
        try:
            # PASSIVE DATA COLLECTION: Only read current state, don't step simulation
            current_time = traci.simulation.getTime()
            
            # Get vehicle information
            vehicle_ids = traci.vehicle.getIDList()
            vehicles = []
            
            for veh_id in vehicle_ids:
                try:
                    position = traci.vehicle.getPosition(veh_id)
                    speed = traci.vehicle.getSpeed(veh_id)
                    angle = traci.vehicle.getAngle(veh_id)
                    route_id = traci.vehicle.getRouteID(veh_id)
                    vehicle_type = traci.vehicle.getTypeID(veh_id)
                    
                    vehicles.append({
                        'id': veh_id,
                        'position': {'x': position[0], 'y': position[1]},
                        'speed': speed,
                        'angle': angle,
                        'route': route_id,
                        'type': vehicle_type
                    })
                except Exception as e:
                    print(f"Error getting data for vehicle {veh_id}: {e}")
            
            # Get edge information
            edge_ids = traci.edge.getIDList()
            edges = []
            
            for edge_id in edge_ids:
                try:
                    vehicle_count = traci.edge.getLastStepVehicleNumber(edge_id)
                    mean_speed = traci.edge.getLastStepMeanSpeed(edge_id)
                    occupancy = traci.edge.getLastStepOccupancy(edge_id)
                    
                    edges.append({
                        'id': edge_id,
                        'vehicle_count': vehicle_count,
                        'mean_speed': mean_speed,
                        'occupancy': occupancy
                    })
                except Exception as e:
                    print(f"Error getting data for edge {edge_id}: {e}")
            
            # Get junction information
            junction_ids = traci.junction.getIDList()
            junctions = []
            
            for junction_id in junction_ids:
                try:
                    position = traci.junction.getPosition(junction_id)
                    junctions.append({
                        'id': junction_id,
                        'position': {'x': position[0], 'y': position[1]}
                    })
                except Exception as e:
                    print(f"Error getting data for junction {junction_id}: {e}")
            
            return {
                'timestamp': current_time,
                'simulation_time': current_time,
                'vehicles': vehicles,
                'edges': edges,
                'junctions': junctions,
                'statistics': {
                    'total_vehicles': len(vehicles),
                    'total_edges': len(edges),
                    'total_junctions': len(junctions),
                    'simulation_time': current_time
                }
            }
            
        except Exception as e:
            print(f"Error getting simulation data: {e}")
            return {}
    
    def cleanup(self):
        """
        Clean up resources and connections
        """
        try:
            if self.simulation_running:
                traci.close()
        except:
            pass
        
        if self.sumo_process:
            try:
                self.sumo_process.terminate()
                self.sumo_process.wait(timeout=5)
            except:
                try:
                    self.sumo_process.kill()
                except:
                    pass
            finally:
                self.sumo_process = None
        
        self.simulation_running = False
        self.current_config = None
