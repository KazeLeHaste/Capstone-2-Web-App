"""
Enhanced Session Manager for Multi-Session Support

This module provides improved session management with:
- Multiple concurrent simulations
- Database-driven configuration
- Dynamic resource allocation
- Automatic cleanup

Author: Traffic Simulator Team
Date: September 2025
"""

import os
import tempfile
import threading
import time
import uuid
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import shutil

class EnhancedSessionManager:
    """Enhanced session manager supporting multiple concurrent simulations"""
    
    def __init__(self, base_networks_dir: str = "networks", db_service=None, websocket_handler=None):
        """
        Initialize enhanced session manager
        
        Args:
            base_networks_dir: Directory containing network templates
            db_service: Database service for persistent storage
            websocket_handler: WebSocket handler for live data
        """
        # Ensure the base_networks_dir is absolute or relative to the backend directory
        if not os.path.isabs(base_networks_dir):
            # If running from backend directory, use the current directory
            # If running from root directory, add backend/ prefix
            backend_dir = Path(__file__).parent  # This is the backend directory
            networks_dir = backend_dir / base_networks_dir
            if not networks_dir.exists():
                # Try relative to current working directory
                networks_dir = Path(base_networks_dir)
            self.base_networks_dir = networks_dir
        else:
            self.base_networks_dir = Path(base_networks_dir)
            
        self.db_service = db_service
        self.websocket_handler = websocket_handler
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.port_allocator = PortAllocator(start_port=8813)
        self.temp_dir = Path(tempfile.gettempdir()) / "traffic_simulator_sessions"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Cleanup thread
        self.cleanup_interval = 300  # 5 minutes
        self.session_timeout = 3600  # 1 hour
        self._start_cleanup_thread()
    
    def create_session(self, network_id: str, config: Dict[str, Any], 
                      enable_gui: bool = True) -> Dict[str, Any]:
        """
        Create a new simulation session with isolated resources
        
        Args:
            network_id: Network to use for simulation
            config: Simulation configuration
            enable_gui: Whether to enable SUMO GUI
            
        Returns:
            Session information with session_id and resources
        """
        try:
            # Generate unique session ID
            session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            
            # Allocate resources
            traci_port = self.port_allocator.allocate()
            session_dir = self.temp_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Create session record in database
            if self.db_service:
                self.db_service.create_session(
                    session_id=session_id,
                    network_id=network_id,
                    session_path=str(session_dir),
                    traci_port=traci_port,
                    enable_gui=enable_gui,
                    temp_directory=str(session_dir)
                )
                self.db_service.save_configuration(session_id, config)
            
            # Prepare network files from template
            network_files = self._prepare_network_files(network_id, session_dir, config)
            
            # Create session tracking
            session_info = {
                'session_id': session_id,
                'network_id': network_id,
                'session_dir': session_dir,
                'traci_port': traci_port,
                'config': config,
                'enable_gui': enable_gui,
                'network_files': network_files,
                'created_at': datetime.now(),
                'status': 'created',
                'process': None,
                'data_thread': None
            }
            
            self.active_sessions[session_id] = session_info
            
            return {
                'success': True,
                'session_id': session_id,
                'session_path': str(session_dir),
                'traci_port': traci_port,
                'network_files': network_files
            }
            
        except Exception as e:
            # Cleanup on error
            if 'traci_port' in locals():
                self.port_allocator.release(traci_port)
            if 'session_dir' in locals() and session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
            
            return {
                'success': False,
                'message': f'Failed to create session: {str(e)}'
            }
    
    def launch_simulation(self, session_id: str) -> Dict[str, Any]:
        """
        Launch SUMO simulation for the specified session
        
        Args:
            session_id: Session to launch
            
        Returns:
            Launch result with process information
        """
        if session_id not in self.active_sessions:
            return {
                'success': False,
                'message': f'Session {session_id} not found'
            }
        
        session_info = self.active_sessions[session_id]
        
        try:
            # Build SUMO command
            sumo_cmd = self._build_sumo_command(session_info)
            
            # Launch SUMO process
            process = subprocess.Popen(
                sumo_cmd,
                cwd=session_info['session_dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Update session info
            session_info['process'] = process
            session_info['status'] = 'running'
            session_info['launched_at'] = datetime.now()
            
            # Start data collection if TraCI is enabled
            if not session_info['enable_gui'] or session_info['config'].get('enable_live_data', True):
                data_thread = threading.Thread(
                    target=self._collect_live_data,
                    args=(session_id,),
                    daemon=True
                )
                data_thread.start()
                session_info['data_thread'] = data_thread
            
            # Update database
            if self.db_service:
                self.db_service.set_session_active(
                    session_id, True, 
                    process_id=process.pid,
                    launched_at=session_info['launched_at']
                )
                self.db_service.update_session_status(session_id, 'running')
            
            return {
                'success': True,
                'session_id': session_id,
                'process_id': process.pid,
                'traci_port': session_info['traci_port']
            }
            
        except Exception as e:
            session_info['status'] = 'failed'
            return {
                'success': False,
                'message': f'Failed to launch simulation: {str(e)}'
            }
    
    def stop_simulation(self, session_id: str) -> Dict[str, Any]:
        """Stop simulation and cleanup resources"""
        if session_id not in self.active_sessions:
            return {
                'success': False,
                'message': f'Session {session_id} not found'
            }
        
        session_info = self.active_sessions[session_id]
        
        try:
            # Stop data collection thread if running
            if session_info.get('data_thread') and session_info['data_thread'].is_alive():
                session_info['status'] = 'stopping'  # Signal thread to stop
                session_info['data_thread'].join(timeout=2)
            
            # TraCI connection cleanup removed - no longer using TraCI
            
            # Stop SUMO process forcefully if needed
            if session_info['process'] and session_info['process'].poll() is None:
                print(f"Terminating SUMO process for session {session_id}")
                session_info['process'].terminate()
                
                # Wait for graceful termination
                try:
                    session_info['process'].wait(timeout=5)
                    print(f"SUMO process terminated gracefully for session {session_id}")
                except subprocess.TimeoutExpired:
                    print(f"Force killing SUMO process for session {session_id}")
                    session_info['process'].kill()
                    session_info['process'].wait()
            
            # Update status
            session_info['status'] = 'completed'
            session_info['completed_at'] = datetime.now()
            
            # Update database
            if self.db_service:
                self.db_service.update_session_status(
                    session_id, 'completed',
                    completed_at=session_info['completed_at']
                )
            
            return {
                'success': True,
                'message': f'Session {session_id} stopped successfully'
            }
            
        except Exception as e:
            print(f"Error stopping session {session_id}: {e}")
            return {
                'success': False,
                'message': f'Error stopping session: {str(e)}'
            }
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up session resources including files and database records
        
        Args:
            session_id: Session to clean up
            
        Returns:
            True if cleanup successful
        """
        if session_id not in self.active_sessions:
            return True  # Already cleaned up
        
        session_info = self.active_sessions[session_id]
        
        try:
            # Stop simulation if running
            self.stop_simulation(session_id)
            
            # Release port
            self.port_allocator.release(session_info['traci_port'])
            
            # Clean up files
            if session_info['session_dir'].exists():
                shutil.rmtree(session_info['session_dir'], ignore_errors=True)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up session {session_id}: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all active sessions"""
        return [
            {
                'session_id': session_id,
                'network_id': info['network_id'],
                'status': info['status'],
                'created_at': info['created_at'].isoformat(),
                'traci_port': info['traci_port']
            }
            for session_id, info in self.active_sessions.items()
        ]
    
    def _prepare_network_files(self, network_id: str, session_dir: Path, config: Dict[str, Any]) -> Dict[str, str]:
        """Prepare network files from templates for the session"""
        # Handle network_id with or without .net extension
        # Network directories are named without .net extension
        if network_id.endswith('.net'):
            network_dir_name = network_id[:-4]  # Remove .net extension
        else:
            network_dir_name = network_id
        
        network_source = self.base_networks_dir / network_dir_name
        
        if not network_source.exists():
            raise FileNotFoundError(f"Network {network_id} not found at {network_source}")
        
        # Copy network files to session directory
        network_files = {}
        for file_path in network_source.glob("*"):
            if file_path.is_file():
                dest_path = session_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                network_files[file_path.suffix] = str(dest_path)
        
        # Modify configuration files based on config
        self._apply_configuration_to_files(session_dir, network_dir_name, config)
        
        return network_files
    
    def _apply_configuration_to_files(self, session_dir: Path, network_id: str, config: Dict[str, Any]):
        """Apply configuration parameters to SUMO files"""
        # Update SUMO config file
        sumocfg_files = list(session_dir.glob("*.sumocfg"))
        if sumocfg_files:
            self._update_sumo_config(sumocfg_files[0], config)
        
        # Generate additional files (traffic lights, routes, etc.)
        if config.get('trafficControl'):
            self._generate_traffic_lights(session_dir, network_id, config['trafficControl'])
        
        if config.get('enabledVehicles'):
            self._update_vehicle_types(session_dir, config['enabledVehicles'])
    
    def _update_sumo_config(self, config_file: Path, config: Dict[str, Any]):
        """Update SUMO configuration file with session parameters"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Update timing parameters
            time_elem = root.find('.//time')
            if time_elem is None:
                time_elem = ET.SubElement(root, 'time')
            
            # Set begin and end times
            begin_time = config.get('sumo_begin', 0)
            end_time = config.get('sumo_end', 3600)
            
            time_elem.set('begin', str(begin_time))
            time_elem.set('end', str(end_time))
            
            # Save the updated config
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"Error updating SUMO config: {e}")
    
    def _generate_traffic_lights(self, session_dir: Path, network_id: str, traffic_control: Dict[str, Any]):
        """Generate traffic light configuration files"""
        # This would integrate with existing traffic light generation logic
        # For now, just create a placeholder
        tls_file = session_dir / f"{network_id}_tls.xml"
        if not tls_file.exists():
            # Create minimal traffic light file
            tls_content = """<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Traffic light configurations will be generated here -->
</additional>"""
            tls_file.write_text(tls_content)
    
    def _update_vehicle_types(self, session_dir: Path, enabled_vehicles: List[str]):
        """Update vehicle type configuration"""
        # This would integrate with existing vehicle type logic
        # For now, just log the enabled vehicles
        print(f"Enabled vehicles for session: {enabled_vehicles}")
    
    def _build_sumo_command(self, session_info: Dict[str, Any]) -> List[str]:
        """Build SUMO command line based on session configuration"""
        config = session_info['config']
        
        # Base command
        sumo_path = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin"
        if session_info['enable_gui']:
            cmd = [os.path.join(sumo_path, "sumo-gui.exe")]
        else:
            cmd = [os.path.join(sumo_path, "sumo.exe")]
        
        # Configuration file
        sumocfg_files = list(session_info['session_dir'].glob("*.sumocfg"))
        if sumocfg_files:
            cmd.extend(["-c", sumocfg_files[0].name])
        
        # TraCI port
        cmd.extend(["--remote-port", str(session_info['traci_port'])])
        
        # Other parameters
        cmd.extend([
            "--time-to-teleport", "300",
            "--no-warnings"
        ])
        
        traffic_scale = config.get('sumo_traffic_scale', config.get('traffic_scale', config.get('sumo_traffic_intensity', 1.0)))  # Legacy fallback
        if traffic_scale != 1.0:
            cmd.extend(["--scale", str(traffic_scale)])
        
        if not session_info['enable_gui']:
            cmd.extend(["--quit-on-end", "--start"])
        else:
            cmd.extend(["--start", "--game"])
        
        return cmd
    
    def _collect_live_data(self, session_id: str):
        """TraCI data collection has been disabled - method kept for compatibility"""
        print(f"Live data collection disabled for session {session_id} - running in pure GUI mode")
        return
    
    def _start_cleanup_thread(self):
        """Start background thread for session cleanup"""
        def cleanup_expired_sessions():
            while True:
                try:
                    current_time = datetime.now()
                    sessions_to_cleanup = []
                    
                    for session_id, session_info in self.active_sessions.items():
                        # Check if session has timed out
                        age = current_time - session_info['created_at']
                        if age > timedelta(seconds=self.session_timeout):
                            sessions_to_cleanup.append(session_id)
                        
                        # Check if process has died
                        if session_info['process'] and session_info['process'].poll() is not None:
                            if session_info['status'] == 'running':
                                session_info['status'] = 'completed'
                                sessions_to_cleanup.append(session_id)
                    
                    # Cleanup expired sessions
                    for session_id in sessions_to_cleanup:
                        print(f"Cleaning up expired session: {session_id}")
                        self.cleanup_session(session_id)
                    
                    time.sleep(self.cleanup_interval)
                    
                except Exception as e:
                    print(f"Error in cleanup thread: {e}")
                    time.sleep(self.cleanup_interval)
        
        cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()


class PortAllocator:
    """Manages TraCI port allocation for multiple SUMO instances"""
    
    def __init__(self, start_port: int = 8813, max_ports: int = 100):
        self.start_port = start_port
        self.max_ports = max_ports
        self.allocated_ports: Set[int] = set()
        self.lock = threading.Lock()
    
    def allocate(self) -> int:
        """Allocate an available port"""
        with self.lock:
            for port in range(self.start_port, self.start_port + self.max_ports):
                if port not in self.allocated_ports:
                    self.allocated_ports.add(port)
                    return port
            raise RuntimeError("No available ports for TraCI")
    
    def release(self, port: int):
        """Release an allocated port"""
        with self.lock:
            self.allocated_ports.discard(port)
    
    def get_allocated_ports(self) -> List[int]:
        """Get list of currently allocated ports"""
        with self.lock:
            return list(self.allocated_ports)
