"""
Multi-Session API Endpoints

New API endpoints supporting multiple concurrent simulations
with database-driven session management.

Author: Traffic Simulator Team
Date: September 2025
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any

# This will be integrated into the main app.py
multi_session_api = Blueprint('multi_session', __name__)

def create_multi_session_endpoints(app, enhanced_session_manager, db_service):
    """Create API endpoints for multi-session functionality"""
    
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
