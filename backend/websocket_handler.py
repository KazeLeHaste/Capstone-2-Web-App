"""
WebSocket Handler Module

Manages real-time communication between the Flask backend and React frontend.
Handles WebSocket connections, data broadcasting, and client management.

Author: Traffic Simulator Team
Date: August 2025
"""

import json
import time
from typing import Dict, List, Any, Set
from flask_socketio import emit, disconnect

class WebSocketHandler:
    """
    Handles WebSocket communication for real-time simulation data
    """
    
    def __init__(self, socketio, sumo_controller):
        """
        Initialize WebSocket handler
        
        Args:
            socketio: Flask-SocketIO instance
            sumo_controller: SumoController instance for data access
        """
        self.socketio = socketio
        self.sumo_controller = sumo_controller
        self.connected_clients: Set[str] = set()
        self.last_broadcast_time = 0
        self.broadcast_interval = 0.1  # 100ms between broadcasts
        
    def add_client(self, client_id: str):
        """
        Add a new client connection
        
        Args:
            client_id: Unique client identifier
        """
        self.connected_clients.add(client_id)
        print(f"Client {client_id} connected. Total clients: {len(self.connected_clients)}")
        
        # Send welcome message to new client
        self.socketio.emit('welcome', {
            'message': 'Connected to Traffic Simulator',
            'client_id': client_id,
            'timestamp': time.time()
        }, room=client_id)
    
    def remove_client(self, client_id: str):
        """
        Remove a client connection
        
        Args:
            client_id: Unique client identifier
        """
        if client_id in self.connected_clients:
            self.connected_clients.remove(client_id)
            print(f"Client {client_id} disconnected. Total clients: {len(self.connected_clients)}")
    
    def broadcast_simulation_data(self, data: Dict[str, Any]):
        """
        Broadcast simulation data to all connected clients
        
        Args:
            data: Simulation data dictionary
        """
        current_time = time.time()
        
        # Throttle broadcasts to avoid overwhelming clients
        if current_time - self.last_broadcast_time < self.broadcast_interval:
            return
        
        if not self.connected_clients:
            return
        
        try:
            # Add metadata to the data
            broadcast_data = {
                'type': 'simulation_data',
                'timestamp': current_time,
                'data': data
            }
            
            # Debug: Print the data being broadcast
            print(f"Broadcasting simulation data: sim_time={data.get('simulation_time', 'N/A')}, vehicles={data.get('active_vehicles', 'N/A')}")
            
            # Broadcast to all connected clients
            self.socketio.emit('simulation_data', broadcast_data)
            self.last_broadcast_time = current_time
            
        except Exception as e:
            print(f"Error broadcasting simulation data: {e}")
    
    def broadcast_simulation_status(self, status: str, message: str = None):
        """
        Broadcast simulation status change to all connected clients
        
        Args:
            status: Status string ('initializing', 'running', 'stopped', 'error', 'finished')
            message: Optional status message
        """
        if not self.connected_clients:
            return
        
        try:
            status_data = {
                'type': 'simulation_status',
                'status': status,
                'message': message or f'Simulation status: {status}',
                'timestamp': time.time()
            }
            
            self.socketio.emit('simulation_status', status_data)
            print(f"Broadcasted status: {status} to {len(self.connected_clients)} clients")
            
        except Exception as e:
            print(f"Error broadcasting simulation status: {e}")
    
    def broadcast_error(self, error_message: str, error_type: str = 'general'):
        """
        Broadcast error message to all connected clients
        
        Args:
            error_message: Error message to broadcast
            error_type: Type of error ('simulation', 'network', 'general')
        """
        if not self.connected_clients:
            return
        
        try:
            error_data = {
                'type': 'error',
                'error_type': error_type,
                'message': error_message,
                'timestamp': time.time()
            }
            
            self.socketio.emit('error', error_data)
            print(f"Broadcasted error: {error_message}")
            
        except Exception as e:
            print(f"Error broadcasting error message: {e}")
    
    def send_to_client(self, client_id: str, event: str, data: Dict[str, Any]):
        """
        Send data to a specific client
        
        Args:
            client_id: Target client identifier
            event: WebSocket event name
            data: Data to send
        """
        if client_id not in self.connected_clients:
            print(f"Client {client_id} not found in connected clients")
            return
        
        try:
            self.socketio.emit(event, data, room=client_id)
        except Exception as e:
            print(f"Error sending data to client {client_id}: {e}")
    
    def get_client_count(self) -> int:
        """
        Get number of connected clients
        
        Returns:
            Number of connected clients
        """
        return len(self.connected_clients)
    
    def is_client_connected(self, client_id: str) -> bool:
        """
        Check if a specific client is connected
        
        Args:
            client_id: Client identifier to check
            
        Returns:
            True if client is connected, False otherwise
        """
        return client_id in self.connected_clients
    
    def broadcast_network_update(self, network_data: Dict[str, Any]):
        """
        Broadcast network configuration update to all clients
        
        Args:
            network_data: Network configuration data
        """
        if not self.connected_clients:
            return
        
        try:
            update_data = {
                'type': 'network_update',
                'data': network_data,
                'timestamp': time.time()
            }
            
            self.socketio.emit('network_update', update_data)
            print(f"Broadcasted network update to {len(self.connected_clients)} clients")
            
        except Exception as e:
            print(f"Error broadcasting network update: {e}")
    
    def broadcast_config_update(self, config_data: Dict[str, Any]):
        """
        Broadcast simulation configuration update to all clients
        
        Args:
            config_data: Configuration data
        """
        if not self.connected_clients:
            return
        
        try:
            update_data = {
                'type': 'config_update',
                'data': config_data,
                'timestamp': time.time()
            }
            
            self.socketio.emit('config_update', update_data)
            print(f"Broadcasted config update to {len(self.connected_clients)} clients")
            
        except Exception as e:
            print(f"Error broadcasting config update: {e}")
    
    def broadcast_analytics_data(self, analytics_data: Dict[str, Any]):
        """
        Broadcast analytics and statistics data to all clients
        
        Args:
            analytics_data: Analytics data dictionary
        """
        if not self.connected_clients:
            return
        
        try:
            broadcast_data = {
                'type': 'analytics_data',
                'data': analytics_data,
                'timestamp': time.time()
            }
            
            self.socketio.emit('analytics_data', broadcast_data)
            
        except Exception as e:
            print(f"Error broadcasting analytics data: {e}")
    
    def handle_client_message(self, client_id: str, message_type: str, data: Dict[str, Any]):
        """
        Handle incoming message from client
        
        Args:
            client_id: Client identifier
            message_type: Type of message
            data: Message data
        """
        try:
            if message_type == 'request_simulation_data':
                # Send current simulation data to requesting client
                if self.sumo_controller.simulation_running:
                    sim_data = self.sumo_controller.get_simulation_data()
                    self.send_to_client(client_id, 'simulation_data', {
                        'type': 'simulation_data',
                        'data': sim_data,
                        'timestamp': time.time()
                    })
                else:
                    self.send_to_client(client_id, 'error', {
                        'type': 'error',
                        'message': 'No simulation is currently running',
                        'timestamp': time.time()
                    })
            
            elif message_type == 'request_status':
                # Send current status to requesting client
                status_data = {
                    'simulation_running': self.sumo_controller.simulation_running,
                    'connected_clients': len(self.connected_clients),
                    'sumo_available': self.sumo_controller.check_sumo_availability()
                }
                self.send_to_client(client_id, 'status_response', status_data)
            
            elif message_type == 'ping':
                # Respond to ping with pong
                self.send_to_client(client_id, 'pong', {
                    'timestamp': time.time()
                })
            
            else:
                print(f"Unknown message type from client {client_id}: {message_type}")
                
        except Exception as e:
            print(f"Error handling client message: {e}")
            self.send_to_client(client_id, 'error', {
                'type': 'error',
                'message': f'Error processing message: {str(e)}',
                'timestamp': time.time()
            })
    
    def disconnect_client(self, client_id: str, reason: str = None):
        """
        Disconnect a specific client
        
        Args:
            client_id: Client identifier
            reason: Optional reason for disconnection
        """
        try:
            if reason:
                self.send_to_client(client_id, 'disconnect_notice', {
                    'reason': reason,
                    'timestamp': time.time()
                })
            
            disconnect(client_id)
            self.remove_client(client_id)
            
        except Exception as e:
            print(f"Error disconnecting client {client_id}: {e}")
    
    def disconnect_all_clients(self, reason: str = None):
        """
        Disconnect all connected clients
        
        Args:
            reason: Optional reason for disconnection
        """
        try:
            if reason:
                self.socketio.emit('disconnect_notice', {
                    'reason': reason,
                    'timestamp': time.time()
                })
            
            # Create a copy of the set to avoid modification during iteration
            clients_to_disconnect = self.connected_clients.copy()
            
            for client_id in clients_to_disconnect:
                disconnect(client_id)
            
            self.connected_clients.clear()
            print("All clients disconnected")
            
        except Exception as e:
            print(f"Error disconnecting all clients: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics
        
        Returns:
            Dictionary with connection statistics
        """
        return {
            'connected_clients': len(self.connected_clients),
            'last_broadcast_time': self.last_broadcast_time,
            'broadcast_interval': self.broadcast_interval,
            'client_list': list(self.connected_clients)
        }
