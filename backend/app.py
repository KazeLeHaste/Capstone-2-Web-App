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
from sumo_controller import SumoController
from websocket_handler import WebSocketHandler
from simulation_manager import SimulationManager
from analytics_engine import TrafficAnalyticsEngine

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic_simulator_secret_key_2025'

# Enable CORS for React frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"], async_mode='threading')

# Initialize SUMO controller and WebSocket handler
sumo_controller = SumoController()
websocket_handler = WebSocketHandler(socketio, sumo_controller)
sim_manager = SimulationManager(websocket_handler=websocket_handler)
analytics_engine = TrafficAnalyticsEngine()

# Add request logging
@app.before_request
def log_request_info():
    print(f"DEBUG: {request.method} {request.url} from {request.remote_addr}")
    if request.is_json and request.get_json():
        print(f"DEBUG: Request data: {request.get_json()}")

# Global variables for simulation state
simulation_active = False
simulation_thread = None

@app.route('/')
def home():
    """
    API health check endpoint
    Returns basic application information
    """
    return jsonify({
        'message': 'Traffic Simulator Backend API',
        'version': '1.0.0',
        'status': 'running',
        'sumo_available': sumo_controller.check_sumo_availability()
    })

@app.route('/api/status')
def api_status():
    """
    Get current application and simulation status
    """
    return jsonify({
        'backend_status': 'running',
        'simulation_active': simulation_active,
        'sumo_available': sumo_controller.check_sumo_availability(),
        'connected_clients': len(websocket_handler.connected_clients)
    })

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
        scenarios = sumo_controller.get_available_scenarios()
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
    Start SUMO simulation with specified configuration
    Expects JSON payload with network and scenario information
    """
    global simulation_active, simulation_thread
    
    try:
        data = request.get_json()
        
        if simulation_active:
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
        
        # Start simulation in separate thread
        simulation_thread = threading.Thread(
            target=run_simulation_thread,
            args=(data,)
        )
        simulation_thread.daemon = True
        simulation_thread.start()
        
        simulation_active = True
        
        return jsonify({
            'success': True,
            'message': 'Simulation started successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/simulation/stop', methods=['POST'])
def stop_legacy_simulation():
    """
    Stop the currently running SUMO simulation (legacy endpoint)
    """
    global simulation_active
    
    try:
        if not simulation_active:
            return jsonify({
                'success': False,
                'error': 'No simulation is currently running'
            }), 400
        
        # Stop SUMO simulation
        sumo_controller.stop_simulation()
        simulation_active = False
        
        # Notify all connected clients
        websocket_handler.broadcast_simulation_status('stopped')
        
        return jsonify({
            'success': True,
            'message': 'Simulation stopped successfully'
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
    """
    try:
        if not simulation_active:
            return jsonify({
                'success': False,
                'error': 'No simulation is currently running'
            }), 400
        
        data = sumo_controller.get_simulation_data()
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_simulation_thread(config):
    """
    Run SUMO simulation in separate thread
    Handles simulation lifecycle and data broadcasting
    """
    global simulation_active
    
    try:
        # Initialize simulation
        websocket_handler.broadcast_simulation_status('initializing')
        success = sumo_controller.start_simulation(config)
        
        if not success:
            simulation_active = False
            websocket_handler.broadcast_simulation_status('error')
            return
        
        websocket_handler.broadcast_simulation_status('running')
        
        # Main simulation loop
        while simulation_active and sumo_controller.is_simulation_running():
            try:
                # Get current simulation data
                sim_data = sumo_controller.get_simulation_data()
                
                # Broadcast data to all connected clients
                websocket_handler.broadcast_simulation_data(sim_data)
                
                # Step simulation forward
                sumo_controller.step_simulation()
                
                # Control simulation speed (adjust as needed)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                break
        
        # Simulation ended
        simulation_active = False
        websocket_handler.broadcast_simulation_status('finished')
        sumo_controller.cleanup()
        
    except Exception as e:
        print(f"Error in simulation thread: {e}")
        simulation_active = False
        websocket_handler.broadcast_simulation_status('error')
        sumo_controller.cleanup()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """
    Handle client WebSocket connection
    """
    print(f"Client connected: {request.sid}")
    websocket_handler.add_client(request.sid)
    
    # Send current status to newly connected client
    emit('simulation_status', {
        'active': simulation_active,
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
    if simulation_active:
        try:
            data = sumo_controller.get_simulation_data()
            emit('simulation_data', data)
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
def stop_simulation(process_id):
    """
    Stop running simulation
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

@app.route('/api/simulation/pause/<int:process_id>', methods=['POST'])
def pause_simulation(process_id):
    """
    Pause running simulation
    """
    print(f"DEBUG: Pause simulation called for process ID: {process_id}")
    try:
        # Call the simulation manager to pause the simulation
        result = sim_manager.pause_simulation(process_id)
        print(f"DEBUG: Pause result: {result}")
        
        if result["success"]:
            socketio.emit('simulation_paused', {
                'processId': process_id,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pausing simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/resume/<int:process_id>', methods=['POST'])
def resume_simulation(process_id):
    """
    Resume paused simulation
    """
    print(f"DEBUG: Resume simulation called for process ID: {process_id}")
    try:
        # Call the simulation manager to resume the simulation
        result = sim_manager.resume_simulation(process_id)
        print(f"DEBUG: Resume result: {result}")
        
        if result["success"]:
            socketio.emit('simulation_resumed', {
                'processId': process_id,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resuming simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/zoom/<int:process_id>', methods=['GET'])
def get_zoom_level(process_id):
    """
    Get current zoom level from SUMO GUI
    """
    try:
        result = sim_manager.get_zoom_level(process_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting zoom level: {str(e)}'
        }), 500

@app.route('/api/simulation/zoom/<int:process_id>', methods=['POST'])
def set_zoom_level(process_id):
    """
    Set zoom level in SUMO GUI
    """
    try:
        data = request.json
        zoom_level = data.get('zoomLevel', 100.0)
        
        # Validate zoom level (reasonable range)
        if not 1.0 <= zoom_level <= 10000.0:
            return jsonify({
                'success': False,
                'message': 'Zoom level must be between 1% and 10000%'
            }), 400
        
        result = sim_manager.set_zoom_level(process_id, zoom_level)
        
        if result["success"]:
            socketio.emit('zoom_changed', {
                'processId': process_id,
                'zoomLevel': zoom_level,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting zoom level: {str(e)}'
        }), 500

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
        analytics_data = analytics_engine.analyze_session(str(session_path))
        
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
        
        # Validate sessions exist
        session_paths = []
        for session_id in session_ids:
            session_path = sim_manager.sessions_dir / session_id
            if not session_path.exists():
                return jsonify({
                    'success': False,
                    'message': f'Session {session_id} not found'
                }), 404
            session_paths.append(str(session_path))
        
        # Perform comparison
        comparison_data = analytics_engine.compare_sessions(session_paths)
        
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
        sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
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
        analytics_data = analytics_engine.analyze_session(str(session_path))
        
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
# END NEW SIMULATION WORKFLOW ENDPOINTS
# ============================================================================

if __name__ == '__main__':
    print("Starting Traffic Simulator Backend...")
    print("Backend API: http://localhost:5000")
    print("WebSocket: ws://localhost:5000")
    print("Make sure SUMO is installed and accessible from PATH")
    
    # Start Flask-SocketIO server
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
