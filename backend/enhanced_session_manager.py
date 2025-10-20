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
        # Update SUMO config file first
        sumocfg_files = list(session_dir.glob("*.sumocfg"))
        if sumocfg_files:
            self._update_sumo_config(sumocfg_files[0], config)
        
        # Apply traffic control configuration to network file
        if config.get('trafficControl') and config['trafficControl'].get('method') != 'existing':
            self._apply_traffic_control_configuration(session_dir, network_id, config['trafficControl'])
        
        # Update vehicle types configuration
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
            
            # Add Buhos additional file if Buhos method is selected
            traffic_control = config.get('trafficControl', {})
            if traffic_control.get('method') == 'buhos':
                input_elem = root.find('.//input')
                if input_elem is not None:
                    additional_files_elem = input_elem.find('.//additional-files')
                    if additional_files_elem is not None:
                        # Get existing additional files
                        existing_files = additional_files_elem.get('value', '')
                        # Add Buhos file to the list
                        buhos_file = 'buhos_traffic_lights.add.xml'
                        if buhos_file not in existing_files:
                            if existing_files:
                                new_files = f"{existing_files},{buhos_file}"
                            else:
                                new_files = buhos_file
                            additional_files_elem.set('value', new_files)
                            print(f"Added Buhos additional file to SUMO configuration: {buhos_file}")
                    else:
                        # Create additional-files element if it doesn't exist
                        additional_files_elem = ET.SubElement(input_elem, 'additional-files')
                        additional_files_elem.set('value', 'buhos_traffic_lights.add.xml')
                        print(f"Created additional-files element with Buhos file")
            
            # Save the updated config
            tree.write(config_file, encoding='utf-8', xml_declaration=True)
            print(f"Updated SUMO configuration file: {config_file}")
            
        except Exception as e:
            print(f"Error updating SUMO config: {e}")
    
    def _apply_traffic_control_configuration(self, session_dir: Path, network_id: str, traffic_control: Dict[str, Any]):
        """Apply traffic control configuration using netconvert"""
        method = traffic_control.get('method', 'existing')
        
        if method == 'existing':
            return  # Keep current traffic lights as-is
        
        # Find the network file (could be .net.xml or .net.xml.gz)
        network_file = session_dir / f"{network_id}.net.xml"
        network_gz_file = session_dir / f"{network_id}.net.xml.gz"
        
        # Handle compressed network files
        actual_network_file = network_file if network_file.exists() else network_gz_file
        if not actual_network_file.exists():
            print(f"Warning: Network file not found: {network_file} or {network_gz_file}")
            return
        
        try:
            self._modify_traffic_lights_with_netconvert(actual_network_file, traffic_control)
            print(f"Successfully applied {method} traffic control to {network_id}")
        except Exception as e:
            print(f"Error applying traffic control configuration: {e}")
    
    def _modify_traffic_lights_with_netconvert(self, network_file: Path, config: Dict[str, Any]):
        """Use netconvert to modify traffic lights according to configuration"""
        import subprocess
        import tempfile
        import shutil
        
        method = config['method']
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_file:
            temp_output = Path(tmp_file.name)
        
        try:
            # Build netconvert command
            cmd = ['netconvert']
            
            # Input file
            if str(network_file).endswith('.gz'):
                # For compressed files, we need to decompress first
                with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_input:
                    temp_input = Path(tmp_input.name)
                
                # Decompress the network file
                import gzip
                with gzip.open(network_file, 'rb') as f_in:
                    with open(temp_input, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                cmd.extend(['-s', str(temp_input)])
            else:
                cmd.extend(['-s', str(network_file)])
            
            cmd.extend(['-o', str(temp_output)])
            
            # Apply configuration based on method
            if method == 'fixed':
                cmd.extend([
                    '--tls.rebuild',  # Rebuild all traffic light programs
                    '--tls.default-type', 'static',
                    '--tls.cycle.time', str(config.get('cycleTime', 90))
                ])
            
            elif method == 'adaptive':
                adaptive_settings = config.get('adaptiveSettings', {})
                cmd.extend([
                    '--tls.rebuild',  # Rebuild all traffic light programs
                    '--tls.default-type', 'actuated',
                    '--tls.min-dur', str(adaptive_settings.get('minDuration', 5)),
                    '--tls.max-dur', str(adaptive_settings.get('maxDuration', 50))
                ])
                
                # Create additional file for actuated parameters
                self._create_actuated_additional_file(
                    network_file.parent, 
                    adaptive_settings
                )
            
            elif method == 'add_adaptive':
                adaptive_settings = config.get('adaptiveSettings', {})
                speed_threshold_ms = adaptive_settings.get('speedThreshold', 50) * 0.277778  # km/h to m/s
                
                cmd.extend([
                    '--tls.guess',  # Guess where to add traffic lights
                    '--tls.guess.threshold', str(speed_threshold_ms * 5),  # SUMO uses sum of speeds
                    '--tls.default-type', 'actuated',
                    '--tls.min-dur', str(adaptive_settings.get('minDuration', 5)),
                    '--tls.max-dur', str(adaptive_settings.get('maxDuration', 50))
                ])
                
                # Create additional file for actuated parameters
                self._create_actuated_additional_file(
                    network_file.parent, 
                    adaptive_settings
                )
            
            elif method == 'buhos':
                # Buhos Method: Create custom traffic light programs with long phases
                # No netconvert modifications needed - we'll use additional file to override programs
                buhos_settings = config.get('buhosSettings', {})
                
                # Create the Buhos additional file BEFORE running netconvert
                # This will override the default programs
                self._create_buhos_additional_file(
                    network_file.parent,
                    network_file,
                    buhos_settings
                )
                
                # We still run netconvert but just to process the network
                # The additional file will be loaded separately
                print(f"Buhos Method: Created additional file with {buhos_settings.get('phaseDuration', 600)}s phases")
                
                # Don't rebuild traffic lights - keep existing structure
                # The additional file will override with Buhos programs
            
            # Execute netconvert only if we need to modify the network
            if method != 'buhos':
                print(f"Running netconvert with command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    print(f"netconvert stderr: {result.stderr}")
                    raise Exception(f"netconvert failed with return code {result.returncode}: {result.stderr}")
                
                # Replace original file with modified version
                if str(network_file).endswith('.gz'):
                    # Compress the output and replace
                    with open(temp_output, 'rb') as f_in:
                        with gzip.open(network_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                            
                    # Clean up temporary input file
                    if 'temp_input' in locals():
                        temp_input.unlink()
                else:
                    shutil.move(str(temp_output), str(network_file))
                
                print(f"Successfully applied {method} traffic control configuration")
            else:
                # For Buhos, we don't need to modify the network file
                print(f"Buhos Method: Network file unchanged, using additional file for traffic light override")
            
        except subprocess.TimeoutExpired:
            raise Exception("netconvert operation timed out")
        except FileNotFoundError:
            raise Exception("netconvert not found. Please ensure SUMO is properly installed and in PATH")
        except Exception as e:
            raise Exception(f"Failed to modify traffic lights: {str(e)}")
        finally:
            # Clean up temporary files
            if temp_output.exists():
                temp_output.unlink()
    
    def _create_actuated_additional_file(self, session_dir: Path, adaptive_settings: Dict[str, Any]):
        """Create additional file with actuated traffic light parameters"""
        additional_file = session_dir / "traffic_lights.add.xml"
        
        max_gap = adaptive_settings.get('maxGap', 3.0)
        detector_gap = adaptive_settings.get('detectorGap', 2.0)
        
        content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
           xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Global actuated traffic light parameters -->
    <!-- Individual TLS configurations can be added here if needed -->
    <!--
    Example for specific traffic light:
    <tlLogic id="TLS_ID" programID="actuated" type="actuated">
        <param key="max-gap" value="{max_gap}"/>
        <param key="detector-gap" value="{detector_gap}"/>
        <param key="show-detectors" value="true"/>
    </tlLogic>
    -->
</additional>'''
        
        try:
            additional_file.write_text(content)
            print(f"Created actuated traffic light parameters file: {additional_file}")
        except Exception as e:
            print(f"Warning: Could not create additional file: {e}")
    
    def _extract_tls_info_from_network(self, network_file: Path) -> List[Dict[str, Any]]:
        """
        Extract traffic light information from network file
        
        Returns:
            List of dictionaries containing TLS ID and phase information
        """
        import xml.etree.ElementTree as ET
        import gzip
        
        try:
            # Read network file (handle both compressed and uncompressed)
            if str(network_file).endswith('.gz'):
                with gzip.open(network_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
            else:
                with open(network_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            root = ET.fromstring(content)
            tls_info_list = []
            
            # Find all traffic light logics
            for tl_logic in root.findall('.//tlLogic'):
                tls_id = tl_logic.get('id')
                tls_type = tl_logic.get('type', 'static')
                program_id = tl_logic.get('programID', '0')
                
                # Get phases
                phases = []
                for phase in tl_logic.findall('.//phase'):
                    phase_info = {
                        'duration': phase.get('duration'),
                        'state': phase.get('state'),
                        'name': phase.get('name', '')
                    }
                    phases.append(phase_info)
                
                tls_info = {
                    'id': tls_id,
                    'type': tls_type,
                    'programID': program_id,
                    'phases': phases,
                    'num_phases': len(phases),
                    'state_length': len(phases[0]['state']) if phases else 0
                }
                tls_info_list.append(tls_info)
            
            print(f"Found {len(tls_info_list)} traffic light(s) in network")
            for tls in tls_info_list:
                print(f"  - TLS '{tls['id']}': {tls['num_phases']} phases, {tls['state_length']} connections")
            
            return tls_info_list
            
        except Exception as e:
            print(f"Warning: Could not extract TLS info from network: {e}")
            return []
    
    def _create_buhos_additional_file(self, session_dir: Path, network_file: Path, buhos_settings: Dict[str, Any]):
        """
        Create additional file with Buhos Method traffic light programs
        
        This creates extremely long green phases for each direction sequentially
        """
        import xml.etree.ElementTree as ET
        
        # Extract traffic light information from network
        tls_info_list = self._extract_tls_info_from_network(network_file)
        
        if not tls_info_list:
            print("Warning: No traffic lights found in network - Buhos method will not be applied")
            return
        
        # Get Buhos settings
        phase_duration = buhos_settings.get('phaseDuration', 600)  # Default 10 minutes
        all_red_time = buhos_settings.get('allRedTime', 5)  # Default 5 seconds
        phase_order = buhos_settings.get('phaseOrder', 'NS-EW')  # NS-EW or EW-NS
        
        # Create additional file
        additional_file = session_dir / "buhos_traffic_lights.add.xml"
        
        # Build XML content
        root = ET.Element('additional')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation', 'http://sumo.dlr.de/xsd/additional_file.xsd')
        
        # Add comment
        comment = ET.Comment(f'''
        Buhos Method Traffic Light Programs
        - Phase Duration: {phase_duration}s ({phase_duration/60:.1f} minutes) per direction
        - All-Red Time: {all_red_time}s clearance between phases
        - Phase Order: {phase_order}
        - Total Cycle: {(phase_duration * 2 + all_red_time * 4)}s (~{(phase_duration * 2 + all_red_time * 4)/60:.1f} minutes)
        ''')
        root.append(comment)
        
        # Create Buhos program for each traffic light
        for tls_info in tls_info_list:
            tls_id = tls_info['id']
            state_length = tls_info['state_length']
            
            if state_length == 0:
                print(f"Warning: TLS '{tls_id}' has no phases, skipping")
                continue
            
            # Create Buhos-style states
            # We need to determine which connections are NS and which are EW
            # For simplicity, we'll split the state string roughly in half
            half_point = state_length // 2
            
            # Create state patterns for Buhos method
            # North-South green: First half green, second half red
            ns_green_state = 'G' * half_point + 'r' * (state_length - half_point)
            ns_yellow_state = 'y' * half_point + 'r' * (state_length - half_point)
            
            # East-West green: First half red, second half green
            ew_green_state = 'r' * half_point + 'G' * (state_length - half_point)
            ew_yellow_state = 'r' * half_point + 'y' * (state_length - half_point)
            
            # All red state
            all_red_state = 'r' * state_length
            
            # Create tlLogic element
            tl_logic = ET.SubElement(root, 'tlLogic')
            tl_logic.set('id', tls_id)
            tl_logic.set('type', 'static')
            tl_logic.set('programID', 'buhos')
            tl_logic.set('offset', '0')
            
            # Determine phase order
            if phase_order == 'NS-EW':
                first_green = ns_green_state
                first_yellow = ns_yellow_state
                first_name = 'NS_Buhos'
                second_green = ew_green_state
                second_yellow = ew_yellow_state
                second_name = 'EW_Buhos'
            else:  # EW-NS
                first_green = ew_green_state
                first_yellow = ew_yellow_state
                first_name = 'EW_Buhos'
                second_green = ns_green_state
                second_yellow = ns_yellow_state
                second_name = 'NS_Buhos'
            
            # Phase 1: First direction BUHOS (long green)
            phase1 = ET.SubElement(tl_logic, 'phase')
            phase1.set('duration', str(phase_duration))
            phase1.set('state', first_green)
            phase1.set('name', first_name)
            
            # Phase 2: First direction yellow
            phase2 = ET.SubElement(tl_logic, 'phase')
            phase2.set('duration', '5')
            phase2.set('state', first_yellow)
            phase2.set('name', f'{first_name}_Yellow')
            
            # Phase 3: All red clearance
            phase3 = ET.SubElement(tl_logic, 'phase')
            phase3.set('duration', str(all_red_time))
            phase3.set('state', all_red_state)
            phase3.set('name', 'All_Red_1')
            
            # Phase 4: Second direction BUHOS (long green)
            phase4 = ET.SubElement(tl_logic, 'phase')
            phase4.set('duration', str(phase_duration))
            phase4.set('state', second_green)
            phase4.set('name', second_name)
            
            # Phase 5: Second direction yellow
            phase5 = ET.SubElement(tl_logic, 'phase')
            phase5.set('duration', '5')
            phase5.set('state', second_yellow)
            phase5.set('name', f'{second_name}_Yellow')
            
            # Phase 6: All red clearance
            phase6 = ET.SubElement(tl_logic, 'phase')
            phase6.set('duration', str(all_red_time))
            phase6.set('state', all_red_state)
            phase6.set('name', 'All_Red_2')
            
            print(f"Created Buhos program for TLS '{tls_id}': {phase_duration}s per direction")
        
        # Write XML to file with pretty printing
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(additional_file, encoding='utf-8', xml_declaration=True)
        
        print(f"Created Buhos traffic light programs file: {additional_file}")
        print(f"  - Cycle time: {(phase_duration * 2 + all_red_time * 2 + 10)}s (~{(phase_duration * 2 + all_red_time * 2 + 10)/60:.1f} minutes)")
        print(f"  - Each direction gets {phase_duration}s ({phase_duration/60:.1f} minutes) of continuous green")
    
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
