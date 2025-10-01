"""
OSM Web Wizard Integration Service

Handles launching OSM Web Wizard and managing scenario imports.
Integrates with the existing OSM scenario importer to provide seamless
network creation capabilities within the web application.

Author: Traffic Simulator Team
Date: October 2025
"""

import os
import sys
import json
import shutil
import subprocess
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import threading


class OSMService:
    """
    Service for managing OSM Web Wizard integration and scenario imports
    """
    
    def __init__(self, osm_scenarios_dir: str = "osm_importer/osm_scenarios", 
                 target_networks_dir: str = "networks", 
                 db_service=None):
        """
        Initialize the OSM service
        
        Args:
            osm_scenarios_dir: Directory where OSM Web Wizard will create scenarios
            target_networks_dir: Directory where imported networks will be stored
            db_service: Database service instance for network management
        """
        # Get the backend directory path (where this script is located)
        backend_dir = Path(__file__).parent
        
        # Set up directory paths relative to backend
        self.osm_scenarios_dir = backend_dir / ".." / osm_scenarios_dir
        self.target_networks_dir = backend_dir / target_networks_dir
        self.processed_dir = self.osm_scenarios_dir / "processed"
        
        # Resolve paths to absolute
        self.osm_scenarios_dir = self.osm_scenarios_dir.resolve()
        self.target_networks_dir = self.target_networks_dir.resolve()
        self.processed_dir = self.processed_dir.resolve()
        
        # Database service
        self.db_service = db_service
        
        # OSM Web Wizard process tracking
        self.wizard_process = None
        self.wizard_port = 8010
        self.wizard_url = f"http://localhost:{self.wizard_port}"
        
        # Ensure directories exist
        self.osm_scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.target_networks_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"OSM Service initialized:")
        print(f"  Scenarios dir: {self.osm_scenarios_dir}")
        print(f"  Networks dir: {self.target_networks_dir}")
        print(f"  Processed dir: {self.processed_dir}")
    
    def get_sumo_tools_path(self) -> Optional[Path]:
        """
        Find SUMO tools directory from environment or common locations
        
        Returns:
            Path to SUMO tools directory or None if not found
        """
        # Check SUMO_HOME environment variable
        sumo_home = os.environ.get('SUMO_HOME')
        if sumo_home:
            tools_path = Path(sumo_home) / "tools"
            if tools_path.exists():
                return tools_path
        
        # Common SUMO installation paths
        common_paths = [
            r"C:\Program Files (x86)\Eclipse\Sumo\tools",
            r"C:\Program Files\Eclipse\Sumo\tools",
            r"/usr/share/sumo/tools",
            r"/opt/sumo/tools",
            r"/usr/local/share/sumo/tools"
        ]
        
        for path_str in common_paths:
            path = Path(path_str)
            if path.exists():
                return path
        
        return None
    
    def launch_osm_wizard(self) -> Dict[str, Any]:
        """
        Launch OSM Web Wizard in the osm_scenarios directory
        
        Returns:
            Dictionary with launch result and wizard information
        """
        try:
            # Check if wizard is already running
            if self.is_wizard_running():
                return {
                    'success': True,
                    'message': 'OSM Web Wizard is already running',
                    'url': self.wizard_url,
                    'port': self.wizard_port,
                    'already_running': True
                }
            
            # Find SUMO tools directory
            sumo_tools_path = self.get_sumo_tools_path()
            if not sumo_tools_path:
                return {
                    'success': False,
                    'error': 'SUMO tools directory not found. Please ensure SUMO is installed and SUMO_HOME is set.',
                    'details': 'Check that SUMO is installed and environment variables are configured correctly.'
                }
            
            # OSM Web Wizard script path
            wizard_script = sumo_tools_path / "osmWebWizard.py"
            if not wizard_script.exists():
                return {
                    'success': False,
                    'error': f'osmWebWizard.py not found at {wizard_script}',
                    'details': 'SUMO installation may be incomplete or corrupted.'
                }
            
            # Prepare command to launch OSM Web Wizard
            cmd = [
                sys.executable,  # Use current Python interpreter
                str(wizard_script),
                "--port", str(self.wizard_port)
            ]
            
            print(f"Launching OSM Web Wizard with command: {' '.join(cmd)}")
            print(f"Working directory: {self.osm_scenarios_dir}")
            
            # Launch the process in the osm_scenarios directory
            self.wizard_process = subprocess.Popen(
                cmd,
                cwd=str(self.osm_scenarios_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait a moment for the process to start
            time.sleep(2)
            
            # Check if process is still running
            if self.wizard_process.poll() is not None:
                # Process has already terminated
                stdout, stderr = self.wizard_process.communicate()
                return {
                    'success': False,
                    'error': 'OSM Web Wizard failed to start',
                    'details': f'stdout: {stdout}\nstderr: {stderr}',
                    'command': ' '.join(cmd)
                }
            
            return {
                'success': True,
                'message': 'OSM Web Wizard launched successfully',
                'url': self.wizard_url,
                'port': self.wizard_port,
                'process_id': self.wizard_process.pid,
                'working_directory': str(self.osm_scenarios_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to launch OSM Web Wizard: {str(e)}',
                'details': f'Exception type: {type(e).__name__}'
            }
    
    def is_wizard_running(self) -> bool:
        """
        Check if OSM Web Wizard is currently running
        
        Returns:
            True if wizard is running, False otherwise
        """
        try:
            # Check if we have a process reference and it's still running
            if self.wizard_process and self.wizard_process.poll() is None:
                return True
            
            # Check if any process is listening on the wizard port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.wizard_port))
            sock.close()
            
            return result == 0
            
        except Exception:
            return False
    
    def stop_wizard(self) -> Dict[str, Any]:
        """
        Stop the OSM Web Wizard process
        
        Returns:
            Dictionary with stop result
        """
        try:
            if not self.wizard_process:
                return {
                    'success': True,
                    'message': 'No wizard process to stop'
                }
            
            # Terminate the process gracefully
            if os.name == 'nt':  # Windows
                self.wizard_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:  # Unix-like
                self.wizard_process.terminate()
            
            # Wait for process to terminate
            try:
                self.wizard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.wizard_process.kill()
                self.wizard_process.wait()
            
            self.wizard_process = None
            
            return {
                'success': True,
                'message': 'OSM Web Wizard stopped successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to stop OSM Web Wizard: {str(e)}'
            }
    
    def get_wizard_status(self) -> Dict[str, Any]:
        """
        Get current status of OSM Web Wizard
        
        Returns:
            Dictionary with wizard status information
        """
        is_running = self.is_wizard_running()
        
        status = {
            'running': is_running,
            'url': self.wizard_url if is_running else None,
            'port': self.wizard_port,
            'process_id': self.wizard_process.pid if self.wizard_process and self.wizard_process.poll() is None else None
        }
        
        return status
    
    def scan_new_scenarios(self) -> Dict[str, Any]:
        """
        Scan for new unprocessed OSM scenarios
        
        Returns:
            Dictionary with list of new scenarios and their metadata
        """
        try:
            scenarios = []
            
            # Look for timestamped directories (OSM Web Wizard format: YYYY-MM-DD-HH-MM-SS)
            for item in self.osm_scenarios_dir.iterdir():
                if not item.is_dir():
                    continue
                
                # Skip processed directory
                if item.name == "processed":
                    continue
                
                # Check if this looks like an OSM Web Wizard timestamp
                if self._is_osm_timestamp_format(item.name):
                    scenario_info = self._analyze_scenario_folder(item)
                    if scenario_info:
                        scenarios.append(scenario_info)
            
            # Sort by creation time (newest first)
            scenarios.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'scenarios': scenarios,
                'count': len(scenarios)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to scan scenarios: {str(e)}',
                'scenarios': []
            }
    
    def _is_osm_timestamp_format(self, folder_name: str) -> bool:
        """
        Check if folder name matches OSM Web Wizard timestamp format
        
        Args:
            folder_name: Name of the folder to check
            
        Returns:
            True if it matches the expected format
        """
        try:
            # OSM Web Wizard creates folders like: 2025-10-01-14-30-15
            parts = folder_name.split('-')
            if len(parts) != 6:
                return False
            
            # Check if all parts are numeric
            return all(part.isdigit() for part in parts)
            
        except Exception:
            return False
    
    def _analyze_scenario_folder(self, folder_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze an OSM scenario folder to extract metadata
        
        Args:
            folder_path: Path to the scenario folder
            
        Returns:
            Dictionary with scenario information or None if invalid
        """
        try:
            # Basic folder info
            stat = folder_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            
            # Count files
            files = list(folder_path.glob('*'))
            file_count = len([f for f in files if f.is_file()])
            
            # Check for required OSM Web Wizard files
            has_network = any(f.name.endswith('.net.xml') or f.name.endswith('.net.xml.gz') for f in files)
            has_config = any(f.name.endswith('.sumocfg') for f in files)
            
            if not (has_network and has_config):
                return None  # Not a valid OSM scenario
            
            # Detect vehicle types from route files
            vehicle_types = []
            route_patterns = ['.passenger.', '.bus.', '.truck.', '.motorcycle.']
            for pattern in route_patterns:
                if any(pattern in f.name for f in files):
                    vehicle_type = pattern.strip('.')
                    vehicle_types.append(vehicle_type)
            
            # Parse timestamp from folder name
            try:
                # Format: 2025-10-01-14-30-15
                parts = folder_path.name.split('-')
                if len(parts) == 6:
                    year, month, day, hour, minute, second = map(int, parts)
                    timestamp = datetime(year, month, day, hour, minute, second)
                else:
                    timestamp = created_at
            except Exception:
                timestamp = created_at
            
            return {
                'folder_name': folder_path.name,
                'folder_path': str(folder_path),
                'created_at': timestamp.isoformat(),
                'created_at_formatted': timestamp.strftime('%B %d, %Y at %I:%M %p'),
                'file_count': file_count,
                'has_network': has_network,
                'has_config': has_config,
                'vehicle_types': vehicle_types,
                'vehicle_types_display': self._format_vehicle_types(vehicle_types),
                'size_mb': sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024),
                'status': 'ready_for_import'
            }
            
        except Exception as e:
            print(f"Error analyzing scenario folder {folder_path}: {e}")
            return None
    
    def _format_vehicle_types(self, vehicle_types: List[str]) -> str:
        """
        Format vehicle types for display with emojis
        
        Args:
            vehicle_types: List of vehicle type names
            
        Returns:
            Formatted string with emojis
        """
        emoji_map = {
            'passenger': '🚗',
            'bus': '🚌', 
            'truck': '🚛',
            'motorcycle': '🏍️'
        }
        
        return ' '.join(emoji_map.get(vtype, '🚗') for vtype in vehicle_types)
    
    def import_scenario(self, source_folder: str, target_name: str, 
                       enhance_diversity: bool = False) -> Dict[str, Any]:
        """
        Import an OSM scenario using the existing OSM importer
        
        Args:
            source_folder: Name of the source scenario folder
            target_name: Custom name for the imported network
            enhance_diversity: Whether to enhance route diversity
            
        Returns:
            Dictionary with import result
        """
        try:
            # Import the OSM scenario importer
            from utils.osm_scenario_importer import OSMScenarioImporter
            
            # Initialize the importer with correct paths
            importer = OSMScenarioImporter(
                osm_scenarios_dir=str(self.osm_scenarios_dir),
                target_networks_dir=str(self.target_networks_dir)
            )
            
            # Import the scenario
            result = importer.import_scenario(
                scenario_name=source_folder,
                target_name=target_name,
                enhance_diversity=enhance_diversity
            )
            
            if result['success']:
                # Move processed folder to avoid re-detection
                self._move_to_processed(source_folder)
                
                # Update database if available
                if self.db_service:
                    try:
                        # Add network to database
                        self.db_service.initialize_networks_from_filesystem(str(self.target_networks_dir))
                    except Exception as e:
                        print(f"Warning: Failed to update database: {e}")
                
                return {
                    'success': True,
                    'message': f'Successfully imported scenario as "{target_name}"',
                    'network_name': target_name,
                    'network_path': result.get('target_path'),
                    'vehicle_types': result.get('vehicle_types', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Import failed'),
                    'details': result.get('message', '')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to import scenario: {str(e)}',
                'details': f'Exception type: {type(e).__name__}'
            }
    
    def _move_to_processed(self, folder_name: str) -> None:
        """
        Move a processed scenario folder to avoid re-detection
        
        Args:
            folder_name: Name of the folder to move
        """
        try:
            source_path = self.osm_scenarios_dir / folder_name
            target_path = self.processed_dir / folder_name
            
            if source_path.exists():
                # If target exists, add timestamp to make it unique
                if target_path.exists():
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    target_path = self.processed_dir / f"{folder_name}_{timestamp}"
                
                shutil.move(str(source_path), str(target_path))
                print(f"Moved processed scenario: {folder_name} -> processed/{target_path.name}")
            
        except Exception as e:
            print(f"Warning: Failed to move processed folder {folder_name}: {e}")
    
    def preview_scenario(self, folder_name: str) -> Dict[str, Any]:
        """
        Get detailed preview information for a specific scenario
        
        Args:
            folder_name: Name of the scenario folder
            
        Returns:
            Dictionary with detailed scenario information
        """
        try:
            folder_path = self.osm_scenarios_dir / folder_name
            if not folder_path.exists():
                return {
                    'success': False,
                    'error': f'Scenario folder "{folder_name}" not found'
                }
            
            # Get basic info
            scenario_info = self._analyze_scenario_folder(folder_path)
            if not scenario_info:
                return {
                    'success': False,
                    'error': f'Invalid scenario folder: {folder_name}'
                }
            
            # Add detailed file information
            files = []
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    files.append({
                        'name': file_path.name,
                        'size_kb': file_path.stat().st_size / 1024,
                        'type': self._get_file_type(file_path.name)
                    })
            
            files.sort(key=lambda x: x['name'])
            scenario_info['files'] = files
            
            return {
                'success': True,
                'scenario': scenario_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to preview scenario: {str(e)}'
            }
    
    def _get_file_type(self, filename: str) -> str:
        """
        Determine the type of an OSM Web Wizard file
        
        Args:
            filename: Name of the file
            
        Returns:
            Human-readable file type description
        """
        if filename.endswith('.net.xml') or filename.endswith('.net.xml.gz'):
            return 'Network'
        elif filename.endswith('.sumocfg'):
            return 'Configuration'
        elif '.rou.' in filename:
            return 'Routes'
        elif '.trips.' in filename:
            return 'Trips'
        elif filename.endswith('.poly.xml') or filename.endswith('.poly.xml.gz'):
            return 'Polygons'
        elif filename.endswith('.add.xml'):
            return 'Additional'
        else:
            return 'Other'
    
    def cleanup_wizard(self) -> None:
        """
        Cleanup wizard process on service shutdown
        """
        if self.wizard_process:
            try:
                self.stop_wizard()
            except Exception as e:
                print(f"Warning: Failed to cleanup wizard process: {e}")