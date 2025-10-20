"""
Traffic Simulator Flask Backend

Main Flask application serving as the backend for the traffic simulator web application.
Provides REST API endpoints and WebSocket communication for SUMO integration.

Author: Traffic Simulator Team
Date: August 2025
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from websocket_handler import WebSocketHandler
from simulation_manager import SimulationManager
from analytics_engine import TrafficAnalyticsEngine
from database.service import DatabaseService
from enhanced_session_manager import EnhancedSessionManager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic_simulator_secret_key_2025'

# Enable CORS for React frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"], async_mode='threading')

# Initialize database service
db_service = DatabaseService()

# Initialize networks in database from filesystem  
db_service.initialize_networks_from_filesystem(str(Path(__file__).parent / "networks"))

# Initialize WebSocket handler (without singleton SumoController)
websocket_handler = WebSocketHandler(socketio)
sim_manager = SimulationManager(websocket_handler=websocket_handler, db_service=db_service)
analytics_engine = TrafficAnalyticsEngine(db_service=db_service)

# Initialize enhanced session manager for multi-session support
enhanced_session_manager = EnhancedSessionManager(
    base_networks_dir="networks",
    db_service=db_service,
    websocket_handler=websocket_handler
)

# Initialize OSM service for network creation
from osm_service import OSMService
osm_service = OSMService(
    osm_scenarios_dir="osm_importer/osm_scenarios",
    target_networks_dir="networks",
    db_service=db_service
)

# Add request logging
@app.before_request
def log_request_info():
    print(f"DEBUG: {request.method} {request.url} from {request.remote_addr}")
    if request.is_json and request.get_json():
        print(f"DEBUG: Request data: {request.get_json()}")

# Legacy simulation state removed - now using multi-session architecture

@app.route('/')
def home():
    """
    API health check endpoint
    Returns basic application information
    """
    # Check SUMO availability using the enhanced session manager
    sumo_available = False
    try:
        import subprocess
        result = subprocess.run(['sumo', '--help'], capture_output=True, text=True, timeout=5)
        sumo_available = result.returncode == 0
    except:
        sumo_available = False
    
    return jsonify({
        'message': 'Traffic Simulator Backend API',
        'version': '2.0.0',  # Updated version for multi-session architecture
        'status': 'running',
        'sumo_available': sumo_available
    })

@app.route('/api/status')
def api_status():
    """
    Get current application and simulation status
    """
    # Check SUMO availability
    sumo_available = False
    try:
        import subprocess
        result = subprocess.run(['sumo', '--help'], capture_output=True, text=True, timeout=5)
        sumo_available = result.returncode == 0
    except:
        sumo_available = False
    
    # Check SUMO availability
    sumo_available = False
    try:
        import subprocess
        result = subprocess.run(['sumo', '--help'], capture_output=True, text=True, timeout=5)
        sumo_available = result.returncode == 0
    except:
        sumo_available = False
    
    return jsonify({
        'backend_status': 'running',
        'simulation_active': len(enhanced_session_manager.active_sessions) > 0,
        'active_sessions': len(enhanced_session_manager.active_sessions),
        'sumo_available': sumo_available,
        'connected_clients': len(websocket_handler.connected_clients)
    })

@app.route('/api/simulation/sync', methods=['POST'])
def sync_simulation_state():
    """
    Force synchronization of frontend with backend simulation state
    """
    try:
        # Get active sessions from both systems
        enhanced_sessions = enhanced_session_manager.get_active_sessions()
        legacy_sessions = []
        
        # Also check legacy sim_manager for backward compatibility
        for session_id, data in sim_manager.active_processes.items():
            process = data["process"]
            if process.poll() is None:  # Process is still running
                legacy_sessions.append({
                    'session_id': session_id,
                    'process_id': data["info"]["processId"],
                    'start_time': data["info"]["startTime"]
                })
        
        # Combine both types of sessions
        all_sessions = enhanced_sessions + legacy_sessions
        
        # If no active sessions, broadcast that all simulations are completed
        if not all_sessions:
            websocket_handler.broadcast_simulation_status('idle', 'No active simulations', {})
        
        return jsonify({
            'success': True,
            'simulation_active': len(all_sessions) > 0,
            'active_sessions': all_sessions,
            'enhanced_sessions': len(enhanced_sessions),
            'legacy_sessions': len(legacy_sessions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks')
def get_networks():
    """
    Get list of available SUMO network files including OSM scenarios
    Returns predefined networks and OSM scenarios for simulation
    """
    try:
        networks_data = sim_manager.get_available_networks()
        return jsonify({
            'success': True,
            'networks': networks_data.get('networks', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scenarios')
def get_scenarios():
    """
    Get list of available simulation scenarios
    """
    try:
        # Use simulation manager instead of singleton controller
        scenarios = sim_manager.get_available_networks().get('networks', [])
        return jsonify({
            'success': True,
            'scenarios': scenarios
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """
    Start SUMO simulation with specified configuration (backward compatible)
    Now uses multi-session architecture but provides single-session interface
    """
    try:
        data = request.get_json()
        
        # Check if any session is already running (for backward compatibility)
        if len(enhanced_session_manager.active_sessions) > 0:
            return jsonify({
                'success': False,
                'error': 'Simulation is already running'
            }), 400
        
        # Validate required parameters
        required_fields = ['network', 'scenario']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract network ID and create configuration
        network_id = data.get('network')
        config = {
            'network': network_id,
            'scenario': data.get('scenario'),
            'traffic_scale': data.get('traffic_scale', 1.0),
            'simulation_time': data.get('simulation_time', 3600),
            'enable_gui': data.get('enable_gui', True)
        }
        
        # Create session using enhanced session manager
        session_result = enhanced_session_manager.create_session(
            network_id=network_id,
            config=config,
            enable_gui=config['enable_gui']
        )
        
        if not session_result['success']:
            return jsonify({
                'success': False,
                'error': session_result['message']
            }), 500
        
        # Launch the simulation
        session_id = session_result['session_id']
        launch_result = enhanced_session_manager.launch_simulation(session_id)
        
        if not launch_result['success']:
            # Cleanup session if launch failed
            enhanced_session_manager.cleanup_session(session_id)
            return jsonify({
                'success': False,
                'error': launch_result['message']
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Simulation started successfully',
            'session_id': session_id,
            'process_id': launch_result['process_id']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """
    Stop the currently running SUMO simulation (backward compatible)
    Now uses multi-session architecture
    """
    try:
        active_sessions = enhanced_session_manager.get_active_sessions()
        
        if not active_sessions:
            return jsonify({
                'success': False,
                'error': 'No simulation is currently running'
            }), 400
        
        # Stop all active sessions (for backward compatibility with single-session interface)
        stopped_sessions = []
        for session in active_sessions:
            session_id = session['session_id']
            stop_result = enhanced_session_manager.stop_simulation(session_id)
            if stop_result['success']:
                stopped_sessions.append(session_id)
        
        # Notify all connected clients
        websocket_handler.broadcast_simulation_status('stopped', 'All simulations stopped', {
            'stopped_sessions': stopped_sessions
        })
        
        return jsonify({
            'success': True,
            'message': f'Stopped {len(stopped_sessions)} simulation(s) successfully',
            'stopped_sessions': stopped_sessions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/simulation/data')
def get_simulation_data():
    """
    Get current simulation data (vehicles, network status)
    Backward compatible - returns data from first active session
    """
    try:
        active_sessions = enhanced_session_manager.get_active_sessions()
        
        if not active_sessions:
            return jsonify({
                'success': False,
                'error': 'No simulation is currently running'
            }), 400
        
        # For backward compatibility, return data from the first active session
        first_session = active_sessions[0]
        session_id = first_session['session_id']
        
        # Get live data from database if available
        if db_service:
            live_data = db_service.get_latest_live_data(session_id, limit=1)
            if live_data:
                data = live_data[0].to_dict()
                return jsonify({
                    'success': True,
                    'data': data,
                    'session_id': session_id
                })
        
        # Fallback to basic session info
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'status': first_session.get('status', 'running'),
                'timestamp': first_session.get('created_at', ''),
                'vehicles': [],
                'edges': [],
                'junctions': []
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Legacy run_simulation_thread removed - now using EnhancedSessionManager

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """
    Handle client WebSocket connection
    """
    print(f"Client connected: {request.sid}")
    websocket_handler.add_client(request.sid)
    
    # Send current status to newly connected client
    active_sessions = enhanced_session_manager.get_active_sessions()
    emit('simulation_status', {
        'active': len(active_sessions) > 0,
        'active_sessions': len(active_sessions),
        'message': 'Connected to traffic simulator'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client WebSocket disconnection
    """
    print(f"Client disconnected: {request.sid}")
    websocket_handler.remove_client(request.sid)

@socketio.on('request_simulation_data')
def handle_data_request():
    """
    Handle client request for current simulation data
    """
    active_sessions = enhanced_session_manager.get_active_sessions()
    if active_sessions:
        try:
            # Get data from first active session for backward compatibility
            session_id = active_sessions[0]['session_id']
            if db_service:
                live_data = db_service.get_latest_live_data(session_id, limit=1)
                if live_data:
                    emit('simulation_data', live_data[0].to_dict())
                    return
            
            # Fallback
            emit('simulation_data', {
                'session_id': session_id,
                'timestamp': time.time(),
                'vehicles': [],
                'edges': [],
                'junctions': []
            })
        except Exception as e:
            emit('error', {'message': str(e)})
    else:
        emit('error', {'message': 'No simulation is currently running'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ============================================================================
# NEW SIMULATION WORKFLOW ENDPOINTS
# Configuration-first workflow with network copying and session management
# ============================================================================

@app.route('/api/simulation/save-config', methods=['POST', 'OPTIONS'])
def save_simulation_config():
    """
    Save simulation configuration for a session
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        return jsonify({'status': 'ok'}), 200
        
    try:
        data = request.get_json()
        print(f"DEBUG: Received configuration data: {data}")  # Debug logging
        
        session_id = data.get('sessionId')
        config = data.get('config')
        
        print(f"DEBUG: Session ID: {session_id}, Config: {config}")  # Debug logging
        
        if not session_id or not config:
            print("DEBUG: Missing session ID or config")  # Debug logging
            return jsonify({
                'success': False,
                'message': 'Session ID and configuration are required'
            }), 400
        
        result = sim_manager.save_session_config(session_id, data)
        print(f"DEBUG: Save result: {result}")  # Debug logging
        
        if result['success']:
            # Emit configuration saved event
            socketio.emit('config_saved', {
                'sessionId': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving configuration: {str(e)}'
        }), 500

@app.route('/api/networks/available', methods=['GET'])
def get_available_networks():
    """
    Get list of available SUMO networks
    """
    try:
        result = sim_manager.get_available_networks()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading networks: {str(e)}',
            'networks': []
        }), 500

@app.route('/api/simulation/setup-network', methods=['POST'])
def setup_simulation_network():
    """
    Copy selected network to session folder and apply configurations
    """
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        network_id = data.get('networkId')
        network_path = data.get('networkPath')
        config = data.get('config')
        
        if not all([session_id, network_id, network_path, config]):
            return jsonify({
                'success': False,
                'message': 'All parameters are required: sessionId, networkId, networkPath, config'
            }), 400
        
        result = sim_manager.setup_session_network(session_id, network_id, network_path, config)
        
        if result['success']:
            # Emit network setup complete event
            socketio.emit('network_setup_complete', {
                'sessionId': session_id,
                'networkId': network_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting up network: {str(e)}'
        }), 500

@app.route('/api/simulation/launch', methods=['POST'])
def launch_simulation():
    """
    Launch SUMO simulation with configured parameters
    """
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        session_path = data.get('sessionPath')
        config = data.get('config')
        enable_gui = data.get('enableGui', True)
        enable_live_data = data.get('enableLiveData', True)
        
        if not all([session_id, session_path, config]):
            return jsonify({
                'success': False,
                'message': 'Session ID, session path, and config are required'
            }), 400
        
        result = sim_manager.launch_simulation(
            session_id, session_path, config, enable_gui, enable_live_data
        )
        
        if result['success']:
            # Emit simulation launched event
            socketio.emit('simulation_launched', {
                'sessionId': session_id,
                'processId': result['process']['processId'],
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error launching simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/stats/<int:process_id>', methods=['GET'])
def get_simulation_stats(process_id):
    """
    Get live simulation statistics
    Note: This endpoint is disabled when WebSocket real-time data is active
    to prevent interference with live data streams
    """
    try:
        # Check if WebSocket is handling live data
        active_sessions = sim_manager.active_processes
        for session_id, data in active_sessions.items():
            if data["info"]["processId"] == process_id:
                # Return minimal response to indicate WebSocket is handling data
                return jsonify({
                    'success': True,
                    'message': 'Live data available via WebSocket',
                    'stats': None  # Don't return competing stats
                })
        
        # If no WebSocket, fall back to HTTP stats
        result = sim_manager.get_simulation_stats(process_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting simulation stats: {str(e)}'
        }), 500

@app.route('/api/simulation/stop/<int:process_id>', methods=['POST'])
def stop_simulation_by_process_id(process_id):
    """
    Stop running simulation by process ID
    """
    try:
        result = sim_manager.stop_simulation(process_id)
        
        if result['success']:
            # Emit simulation stopped event
            socketio.emit('simulation_stopped', {
                'processId': process_id,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping simulation: {str(e)}'
        }), 500

# Pause functionality removed - use SUMO GUI controls directly

# Resume functionality removed - use SUMO GUI controls directly

# Zoom control endpoints removed - zoom is now hardcoded to 225 in GUI settings

@app.route('/api/simulation/center-view/<int:process_id>', methods=['POST'])
def center_view(process_id):
    """
    Center the view to show the entire network
    """
    try:
        result = sim_manager.center_view(process_id)
        
        if result["success"]:
            socketio.emit('view_centered', {
                'processId': process_id,
                'zoomLevel': result.get('zoomLevel'),
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error centering view: {str(e)}'
        }), 500

@app.route('/api/simulation/download-results/<session_id>', methods=['GET'])
def download_simulation_results(session_id):
    """
    Download simulation results for a session
    """
    try:
        # In a real implementation, this would create a ZIP file
        # containing all simulation outputs
        return jsonify({
            'success': True,
            'message': 'Results download would be implemented here',
            'sessionId': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error downloading results: {str(e)}'
        }), 500

@app.route('/api/simulation/cleanup/<session_id>', methods=['DELETE'])
def cleanup_simulation_session(session_id):
    """
    Clean up simulation session files and processes
    """
    try:
        result = sim_manager.cleanup_session(session_id)
        
        if result['success']:
            # Emit session cleaned up event
            socketio.emit('session_cleaned_up', {
                'sessionId': session_id,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cleaning up session: {str(e)}'
        }), 500

@app.route('/api/simulation/save-session', methods=['POST'])
def save_simulation_session():
    """
    Manually save simulation session data and statistics
    """
    try:
        data = request.json
        session_id = data.get('sessionId')
        session_path = data.get('sessionPath')
        force = data.get('force', False)
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required'
            }), 400
        
        # If session path is not provided, try to infer it
        if not session_path:
            session_path = str(sim_manager.sessions_dir / session_id)
        
        session_path = Path(session_path)
        
        # Check if session directory exists
        if not session_path.exists():
            return jsonify({
                'success': False,
                'message': f'Session directory not found: {session_path}'
            }), 404
        
        # Check if session is already saved (has metadata)
        metadata_file = session_path / 'session_metadata.json'
        if metadata_file.exists() and not force:
            return jsonify({
                'success': True,
                'message': 'Session already saved',
                'already_saved': True
            })
        
        # Try to parse SUMO output files and save session data
        try:
            session_stats = sim_manager._parse_sumo_output_files(session_path)
            current_time = datetime.now().isoformat()
            
            if session_stats:
                # Save session statistics
                stats_file = session_path / "session_statistics.json"
                with open(stats_file, 'w') as f:
                    json.dump({
                        'session_id': session_id,
                        'saved_at': current_time,
                        'completion_reason': 'Manual save',
                        'statistics': session_stats,
                        'can_analyze': True
                    }, f, indent=2)
                
                # Save session metadata for the analytics API
                config_file = session_path / "config.json"
                network_id = "unknown"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                            network_id = config_data.get('network_id', 'unknown')
                            if network_id == 'unknown':
                                # Try to infer from SUMO files
                                sumo_files = list(session_path.glob('*.sumocfg'))
                                if sumo_files:
                                    network_id = sumo_files[0].stem
                    except:
                        pass
                
                metadata = {
                    'session_id': session_id,
                    'created_at': current_time,
                    'completed_at': current_time,
                    'completion_reason': 'Manual save',
                    'network_id': network_id,
                    'can_analyze': True,
                    'has_statistics': True,
                    'status': 'saved'
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return jsonify({
                    'success': True,
                    'message': 'Session saved successfully',
                    'has_statistics': True,
                    'can_analyze': True
                })
            
            else:
                # No statistics found, save basic metadata
                metadata = {
                    'session_id': session_id,
                    'created_at': current_time,
                    'completed_at': current_time,
                    'completion_reason': 'Manual save (no data)',
                    'network_id': 'unknown',
                    'can_analyze': False,
                    'has_statistics': False,
                    'status': 'saved_no_data'
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return jsonify({
                    'success': True,
                    'message': 'Session saved (no simulation data found)',
                    'has_statistics': False,
                    'can_analyze': False
                })
                
        except Exception as parse_error:
            # Failed to parse, save basic metadata
            metadata = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'completion_reason': 'Manual save (with errors)',
                'network_id': 'unknown',
                'can_analyze': False,
                'has_statistics': False,
                'status': 'saved_with_errors',
                'error': str(parse_error)
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return jsonify({
                'success': False,
                'message': f'Session saved with errors: {str(parse_error)}',
                'has_statistics': False,
                'can_analyze': False
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving session: {str(e)}'
        }), 500

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/analytics/session/<session_id>', methods=['GET'])
def get_session_analytics(session_id):
    """
    Get comprehensive analytics for a simulation session
    """
    try:
        # Find session directory
        session_path = sim_manager.sessions_dir / session_id
        
        if not session_path.exists():
            return jsonify({
                'success': False,
                'message': f'Session {session_id} not found'
            }), 404
        
        # Analyze session
        analytics_data = analytics_engine.analyze_session(str(session_path), session_id)
        
        if 'error' in analytics_data:
            return jsonify({
                'success': False,
                'message': analytics_data['error']
            }), 500
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'analytics': analytics_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error analyzing session: {str(e)}'
        }), 500

@app.route('/api/analytics/compare', methods=['POST'])
def compare_sessions():
    """
    Compare multiple simulation sessions
    """
    try:
        data = request.get_json()
        session_ids = data.get('session_ids', [])
        
        if len(session_ids) < 2:
            return jsonify({
                'success': False,
                'message': 'At least 2 sessions are required for comparison'
            }), 400
        
        # Validate sessions exist and gather metadata
        session_paths = []
        session_metadata = {}
        
        for session_id in session_ids:
            session_path = sim_manager.sessions_dir / session_id
            if not session_path.exists():
                return jsonify({
                    'success': False,
                    'message': f'Session {session_id} not found'
                }), 404
            session_paths.append(str(session_path))
            
            # Get session metadata from database
            db_session = db_service.get_session_by_id(session_id)
            db_config = db_service.get_configuration(session_id)
            
            metadata = {
                'network_id': db_session.network_id if db_session else 'Unknown',
                'network_name': db_session.network_name if db_session else 'Unknown Network',
                'configuration': {}
            }
            
            # Add configuration details if available
            if db_config:
                metadata['configuration'] = {
                    'traffic_control_method': db_config.traffic_control_method or 'None',
                    'sumo_begin': db_config.sumo_begin,
                    'sumo_end': db_config.sumo_end,
                    'sumo_step_length': db_config.sumo_step_length,
                    'sumo_time_to_teleport': db_config.sumo_time_to_teleport,
                    'sumo_traffic_intensity': db_config.sumo_traffic_intensity,
                    'enabled_vehicles': db_config.get_enabled_vehicles(),
                    'traffic_control_config': db_config.get_traffic_control_config(),
                    'vehicle_types_config': db_config.get_vehicle_types_config()
                }
            
            session_metadata[session_id] = metadata
        
        # Perform comparison
        comparison_data = analytics_engine.compare_sessions(session_paths)
        
        # Add metadata to comparison data
        comparison_data['session_metadata'] = session_metadata
        
        return jsonify({
            'success': True,
            'comparison': comparison_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error comparing sessions: {str(e)}'
        }), 500

@app.route('/api/analytics/sessions', methods=['GET'])
def list_analyzed_sessions():
    """
    Get list of sessions available for analysis
    """
    try:
        sessions = []
        
        # Scan sessions directory
        for session_dir in sim_manager.sessions_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith('.'):
                # Check if session has output files
                has_tripinfo = bool(list(session_dir.glob('*.tripinfos.xml')))
                has_summary = bool(list(session_dir.glob('*summary.xml')))
                has_stats = bool(list(session_dir.glob('*.stats.xml')))
                
                # Load session metadata if available
                metadata_file = session_dir / 'session_metadata.json'
                metadata = {}
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                session_info = {
                    'session_id': session_dir.name,
                    'path': str(session_dir),
                    'has_tripinfo': has_tripinfo,
                    'has_summary': has_summary,
                    'has_stats': has_stats,
                    'can_analyze': has_tripinfo or has_summary,
                    'metadata': metadata,
                    'created_at': metadata.get('created_at'),
                    'network_id': metadata.get('network_id')
                }
                
                sessions.append(session_info)
        
        # Sort by creation time (newest first)
        def sort_key(session):
            created_at = session.get('created_at')
            if created_at is None:
                return '0'
            return str(created_at)
        
        sessions.sort(key=sort_key, reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total_count': len(sessions),
            'analyzable_count': sum(1 for s in sessions if s['can_analyze'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error listing sessions: {str(e)}'
        }), 500

@app.route('/api/analytics/kpis/<session_id>', methods=['GET'])
def get_session_kpis(session_id):
    """
    Get just the KPIs for a session (lightweight endpoint)
    """
    try:
        session_path = sim_manager.sessions_dir / session_id
        
        if not session_path.exists():
            return jsonify({
                'success': False,
                'message': f'Session {session_id} not found'
            }), 404
        
        # Quick KPI extraction
        tripinfo_file = analytics_engine._find_file(session_path, "*.tripinfos.xml")
        stats_file = analytics_engine._find_file(session_path, "*.stats.xml")
        summary_file = analytics_engine._find_file(session_path, "*summary.xml")
        
        kpis = analytics_engine._extract_kpis(tripinfo_file, stats_file, summary_file)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'kpis': kpis.__dict__,
            'extracted_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error extracting KPIs: {str(e)}'
        }), 500

@app.route('/api/analytics/recommendations/<session_id>', methods=['GET'])
def get_session_recommendations(session_id):
    """
    Get recommendations for a session
    """
    try:
        session_path = sim_manager.sessions_dir / session_id
        
        if not session_path.exists():
            return jsonify({
                'success': False,
                'message': f'Session {session_id} not found'
            }), 404
        
        # Extract KPIs and generate recommendations
        tripinfo_file = analytics_engine._find_file(session_path, "*.tripinfos.xml")
        stats_file = analytics_engine._find_file(session_path, "*.stats.xml")
        summary_file = analytics_engine._find_file(session_path, "*summary.xml")
        
        kpis = analytics_engine._extract_kpis(tripinfo_file, stats_file, summary_file)
        recommendations = analytics_engine._generate_recommendations(kpis)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'high_priority_count': sum(1 for r in recommendations if r['priority'] == 'high'),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating recommendations: {str(e)}'
        }), 500

@app.route('/api/analytics/export/<session_id>', methods=['GET'])
def export_session_analytics(session_id):
    """
    Export session analytics as JSON file
    """
    try:
        session_path = sim_manager.sessions_dir / session_id
        
        if not session_path.exists():
            return jsonify({
                'success': False,
                'message': f'Session {session_id} not found'
            }), 404
        
        # Get full analytics
        analytics_data = analytics_engine.analyze_session(str(session_path), session_id)
        
        if 'error' in analytics_data:
            return jsonify({
                'success': False,
                'message': analytics_data['error']
            }), 500
        
        # Create export data
        export_data = {
            'export_info': {
                'session_id': session_id,
                'exported_at': datetime.now().isoformat(),
                'export_version': '1.0'
            },
            'analytics': analytics_data
        }
        
        # Return as downloadable JSON
        response = jsonify(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_{session_id}.json'
        response.headers['Content-Type'] = 'application/json'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting analytics: {str(e)}'
        }), 500

# ============================================================================
# END ANALYTICS ENDPOINTS
# ============================================================================

# ============================================================================
# DATABASE-POWERED ENDPOINTS
# ============================================================================

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """
    Get list of recent sessions from database
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        sessions = db_service.get_recent_sessions(limit)
        
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving sessions: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """
    Get detailed session information including configuration
    """
    try:
        session = db_service.get_session_by_id(session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        config = db_service.get_configuration(session_id)
        
        result = {
            'success': True,
            'session': session.to_dict(),
            'configuration': config.to_dict() if config else None
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving session details: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/analytics', methods=['GET'])
def get_session_analytics_db(session_id):
    """
    Get session analytics from database
    """
    try:
        analytics_data = db_service.get_session_analytics(session_id)
        
        if not analytics_data:
            return jsonify({
                'success': False,
                'message': 'Session not found or no analytics available'
            }), 404
        
        return jsonify({
            'success': True,
            **analytics_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving analytics: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/live-data', methods=['GET'])
def get_session_live_data(session_id):
    """
    Get live data history for session
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        live_data = db_service.get_live_data(session_id, limit)
        
        data_list = []
        for data in live_data:
            data_dict = {
                'simulation_time': data.simulation_time,
                'active_vehicles': data.active_vehicles,
                'avg_speed': data.avg_speed,
                'throughput': data.throughput,
                'timestamp': data.timestamp.isoformat(),
                **data.get_raw_data()
            }
            data_list.append(data_dict)
        
        return jsonify({
            'success': True,
            'live_data': data_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving live data: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete session and all related data
    """
    try:
        success = db_service.delete_session(session_id)
        
        if success:
            # Also try to delete session files if they exist
            try:
                session_dir = sim_manager.sessions_dir / session_id
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
            except Exception as file_error:
                print(f"Warning: Failed to delete session files: {file_error}")
            
            return jsonify({
                'success': True,
                'message': 'Session deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Session not found or could not be deleted'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting session: {str(e)}'
        }), 500

@app.route('/api/networks/database', methods=['GET'])
def get_networks_from_database():
    """
    Get networks from database
    """
    try:
        networks = db_service.get_networks()
        
        return jsonify({
            'success': True,
            'networks': [network.to_dict() for network in networks]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving networks: {str(e)}'
        }), 500

@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """
    Get database statistics
    """
    try:
        stats = db_service.get_database_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving database stats: {str(e)}'
        }), 500

@app.route('/api/database/cleanup', methods=['POST'])
def cleanup_old_data():
    """
    Clean up old session data
    """
    try:
        days_old = request.json.get('days', 30) if request.is_json else 30
        deleted_count = db_service.cleanup_old_data(days_old)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old sessions',
            'deleted_sessions': deleted_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cleaning up data: {str(e)}'
        }), 500

# ============================================================================
# ============================================================================
# ENHANCED MULTI-SESSION ENDPOINTS (V2)
# ============================================================================

@app.route('/api/v2/sessions', methods=['POST'])
def create_session_v2():
    """Create a new simulation session with enhanced management"""
    try:
        data = request.get_json()
        network_id = data.get('networkId')
        config = data.get('config', {})
        enable_gui = data.get('enableGui', True)
        
        if not network_id:
            return jsonify({
                'success': False,
                'message': 'Network ID is required'
            }), 400
        
        # Create session using enhanced manager
        result = enhanced_session_manager.create_session(
            network_id=network_id,
            config=config,
            enable_gui=enable_gui
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating session: {str(e)}'
        }), 500

@app.route('/api/v2/sessions/<session_id>/launch', methods=['POST'])
def launch_session_v2(session_id: str):
    """Launch simulation for specific session"""
    try:
        result = enhanced_session_manager.launch_simulation(session_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error launching session: {str(e)}'
        }), 500

@app.route('/api/v2/sessions/<session_id>/stop', methods=['POST'])
def stop_session_v2(session_id: str):
    """Stop simulation for specific session"""
    try:
        result = enhanced_session_manager.stop_simulation(session_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping session: {str(e)}'
        }), 500

@app.route('/api/v2/sessions/<session_id>', methods=['DELETE'])
def cleanup_session_v2(session_id: str):
    """Clean up session resources"""
    try:
        success = enhanced_session_manager.cleanup_session(session_id)
        return jsonify({
            'success': success,
            'message': f'Session {session_id} cleaned up' if success else 'Cleanup failed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cleaning up session: {str(e)}'
        }), 500

@app.route('/api/v2/sessions', methods=['GET'])
def get_active_sessions_v2():
    """Get all active sessions"""
    try:
        sessions = enhanced_session_manager.get_active_sessions()
        
        # Enhance with database information
        if db_service:
            for session in sessions:
                db_session = db_service.get_session_by_id(session['session_id'])
                if db_session:
                    session.update(db_session.to_dict())
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving sessions: {str(e)}'
        }), 500

@app.route('/api/v2/sessions/<session_id>/status', methods=['GET'])
def get_session_status_v2(session_id: str):
    """Get detailed status of specific session"""
    try:
        # Get from enhanced manager
        active_sessions = enhanced_session_manager.get_active_sessions()
        session_info = next((s for s in active_sessions if s['session_id'] == session_id), None)
        
        if not session_info:
            # Check database for completed sessions
            if db_service:
                db_session = db_service.get_session_by_id(session_id)
                if db_session:
                    return jsonify({
                        'success': True,
                        'session': db_session.to_dict()
                    })
            
            return jsonify({
                'success': False,
                'message': f'Session {session_id} not found'
            }), 404
        
        # Enhance with database information
        if db_service:
            db_session = db_service.get_session_by_id(session_id)
            if db_session:
                session_info.update(db_session.to_dict())
        
        return jsonify({
            'success': True,
            'session': session_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving session status: {str(e)}'
        }), 500

@app.route('/api/v2/sessions/<session_id>/live-data', methods=['GET'])
def get_session_live_data_v2(session_id: str):
    """Get live data for specific session"""
    try:
        if not db_service:
            return jsonify({
                'success': False,
                'message': 'Database service not available'
            }), 500
        
        # Get latest live data from database
        live_data = db_service.get_latest_live_data(session_id, limit=100)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'data': [data.to_dict() for data in live_data]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving live data: {str(e)}'
        }), 500

@app.route('/api/v2/resource-usage', methods=['GET'])
def get_resource_usage_v2():
    """Get current resource usage (ports, sessions, etc.)"""
    try:
        active_sessions = enhanced_session_manager.get_active_sessions()
        allocated_ports = enhanced_session_manager.port_allocator.get_allocated_ports()
        
        return jsonify({
            'success': True,
            'resource_usage': {
                'active_sessions': len(active_sessions),
                'allocated_ports': allocated_ports,
                'max_sessions': enhanced_session_manager.port_allocator.max_ports,
                'available_ports': enhanced_session_manager.port_allocator.max_ports - len(allocated_ports)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving resource usage: {str(e)}'
        }), 500

# END ENHANCED MULTI-SESSION ENDPOINTS
# ============================================================================

# ============================================================================
# END DATABASE-POWERED ENDPOINTS
# ============================================================================

# ============================================================================
# END NEW SIMULATION WORKFLOW ENDPOINTS
# ============================================================================

# ============================================================================
# OSM WEB WIZARD INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/osm/launch-wizard', methods=['POST'])
def launch_osm_wizard():
    """Launch OSM Web Wizard in osm_scenarios directory"""
    try:
        result = osm_service.launch_osm_wizard()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to launch OSM Web Wizard: {str(e)}'
        }), 500

@app.route('/api/osm/wizard-status', methods=['GET'])
def get_wizard_status():
    """Check if OSM Web Wizard is currently running"""
    try:
        status = osm_service.get_wizard_status()
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get wizard status: {str(e)}'
        }), 500

@app.route('/api/osm/stop-wizard', methods=['POST'])
def stop_osm_wizard():
    """Stop the OSM Web Wizard process"""
    try:
        result = osm_service.stop_wizard()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to stop wizard: {str(e)}'
        }), 500

@app.route('/api/osm/scan-scenarios', methods=['GET'])
def scan_new_scenarios():
    """Scan for new unprocessed OSM scenarios"""
    try:
        result = osm_service.scan_new_scenarios()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to scan scenarios: {str(e)}',
            'scenarios': []
        }), 500

@app.route('/api/osm/import-scenario', methods=['POST'])
def import_osm_scenario():
    """Import selected OSM scenario with custom name"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'source_folder' not in data or 'target_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: source_folder and target_name'
            }), 400
        
        source_folder = data['source_folder']
        target_name = data['target_name']
        enhance_diversity = data.get('enhance_diversity', False)
        
        # Validate target name (basic sanitization)
        if not target_name or not target_name.replace('_', '').replace('-', '').isalnum():
            return jsonify({
                'success': False,
                'error': 'Target name must contain only letters, numbers, hyphens, and underscores'
            }), 400
        
        result = osm_service.import_scenario(source_folder, target_name, enhance_diversity)
        
        if result['success']:
            # Emit network import event via WebSocket
            socketio.emit('network_imported', {
                'network_name': target_name,
                'source': source_folder,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to import scenario: {str(e)}'
        }), 500

@app.route('/api/osm/preview-scenario', methods=['GET'])
def preview_scenario():
    """Get detailed preview of a specific scenario"""
    try:
        folder_name = request.args.get('folder_name')
        if not folder_name:
            return jsonify({
                'success': False,
                'error': 'Missing folder_name parameter'
            }), 400
        
        result = osm_service.preview_scenario(folder_name)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to preview scenario: {str(e)}'
        }), 500

# ============================================================================
# END OSM WEB WIZARD INTEGRATION ENDPOINTS
# ============================================================================

if __name__ == '__main__':
    print("Starting Traffic Simulator Backend...")
    print("Backend API: http://localhost:5000")
    print("WebSocket: ws://localhost:5000")
    print("Make sure SUMO is installed and accessible from PATH")
    
    try:
        # Start Flask-SocketIO server
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    finally:
        # Cleanup OSM service on shutdown
        try:
            osm_service.cleanup_wizard()
        except:
            pass
