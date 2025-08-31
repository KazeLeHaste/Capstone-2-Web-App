/**
 * Socket Utilities
 * 
 * Provides helper functions and hooks for WebSocket communication
 * with the Flask backend for real-time simulation data.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';

/**
 * Custom hook for managing WebSocket connection
 */
export const useSocket = (url = 'http://localhost:5000') => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  
  useEffect(() => {
    const newSocket = io(url, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true
    });
    
    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setConnectionError(null);
    });
    
    newSocket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setConnectionError(error.message);
      setIsConnected(false);
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
    };
  }, [url]);
  
  const emit = useCallback((event, data) => {
    if (socket && isConnected) {
      socket.emit(event, data);
    } else {
      console.warn('Cannot emit: Socket not connected');
    }
  }, [socket, isConnected]);
  
  const on = useCallback((event, callback) => {
    if (socket) {
      socket.on(event, callback);
      return () => socket.off(event, callback);
    }
  }, [socket]);
  
  const off = useCallback((event, callback) => {
    if (socket) {
      socket.off(event, callback);
    }
  }, [socket]);
  
  return {
    socket,
    isConnected,
    connectionError,
    emit,
    on,
    off
  };
};

/**
 * Custom hook for listening to simulation data
 */
export const useSimulationData = (socket) => {
  const [simulationData, setSimulationData] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  useEffect(() => {
    if (!socket) return;
    
    const handleSimulationData = (data) => {
      setSimulationData(data.data);
      setLastUpdate(new Date(data.timestamp));
    };
    
    socket.on('simulation_data', handleSimulationData);
    
    return () => {
      socket.off('simulation_data', handleSimulationData);
    };
  }, [socket]);
  
  const requestCurrentData = useCallback(() => {
    if (socket) {
      socket.emit('request_simulation_data');
    }
  }, [socket]);
  
  return {
    simulationData,
    lastUpdate,
    requestCurrentData
  };
};

/**
 * Custom hook for monitoring simulation status
 */
export const useSimulationStatus = (socket) => {
  const [status, setStatus] = useState('unknown');
  const [message, setMessage] = useState('');
  const [lastStatusUpdate, setLastStatusUpdate] = useState(null);
  
  useEffect(() => {
    if (!socket) return;
    
    const handleStatusUpdate = (data) => {
      setStatus(data.status);
      setMessage(data.message || '');
      setLastStatusUpdate(new Date(data.timestamp));
    };
    
    socket.on('simulation_status', handleStatusUpdate);
    
    return () => {
      socket.off('simulation_status', handleStatusUpdate);
    };
  }, [socket]);
  
  const requestStatus = useCallback(() => {
    if (socket) {
      socket.emit('request_status');
    }
  }, [socket]);
  
  return {
    status,
    message,
    lastStatusUpdate,
    requestStatus
  };
};

/**
 * Custom hook for handling WebSocket errors
 */
export const useSocketErrors = (socket) => {
  const [errors, setErrors] = useState([]);
  
  useEffect(() => {
    if (!socket) return;
    
    const handleError = (error) => {
      const errorEntry = {
        id: Date.now(),
        message: error.message || 'Unknown error',
        type: error.type || 'general',
        timestamp: new Date()
      };
      
      setErrors(prev => [...prev, errorEntry]);
      
      // Auto-remove error after 10 seconds
      setTimeout(() => {
        setErrors(prev => prev.filter(e => e.id !== errorEntry.id));
      }, 10000);
    };
    
    socket.on('error', handleError);
    
    return () => {
      socket.off('error', handleError);
    };
  }, [socket]);
  
  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);
  
  const removeError = useCallback((id) => {
    setErrors(prev => prev.filter(e => e.id !== id));
  }, []);
  
  return {
    errors,
    clearErrors,
    removeError
  };
};

/**
 * Socket event constants
 */
export const SOCKET_EVENTS = {
  // Connection events
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  CONNECT_ERROR: 'connect_error',
  
  // Data events
  SIMULATION_DATA: 'simulation_data',
  SIMULATION_STATUS: 'simulation_status',
  NETWORK_UPDATE: 'network_update',
  CONFIG_UPDATE: 'config_update',
  ANALYTICS_DATA: 'analytics_data',
  
  // Request events
  REQUEST_SIMULATION_DATA: 'request_simulation_data',
  REQUEST_STATUS: 'request_status',
  
  // Server events
  WELCOME: 'welcome',
  ERROR: 'error',
  DISCONNECT_NOTICE: 'disconnect_notice'
};

/**
 * Utility functions for socket communication
 */
export const socketUtils = {
  /**
   * Emit event with error handling
   */
  safeEmit: (socket, event, data) => {
    try {
      if (socket && socket.connected) {
        socket.emit(event, data);
        return true;
      } else {
        console.warn(`Cannot emit ${event}: Socket not connected`);
        return false;
      }
    } catch (error) {
      console.error(`Error emitting ${event}:`, error);
      return false;
    }
  },
  
  /**
   * Add event listener with automatic cleanup
   */
  addListener: (socket, event, callback) => {
    if (socket) {
      socket.on(event, callback);
      return () => socket.off(event, callback);
    }
    return () => {};
  },
  
  /**
   * Check socket connection status
   */
  isConnected: (socket) => {
    return socket && socket.connected;
  },
  
  /**
   * Get socket connection info
   */
  getConnectionInfo: (socket) => {
    if (!socket) {
      return { connected: false, id: null };
    }
    
    return {
      connected: socket.connected,
      id: socket.id,
      transport: socket.io.engine.transport.name
    };
  }
};

/**
 * Default socket configuration
 */
export const defaultSocketConfig = {
  transports: ['websocket', 'polling'],
  timeout: 20000,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  forceNew: false
};

export default {
  useSocket,
  useSimulationData,
  useSimulationStatus,
  useSocketErrors,
  SOCKET_EVENTS,
  socketUtils,
  defaultSocketConfig
};
