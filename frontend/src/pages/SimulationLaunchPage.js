/**
 * Simulation Launch Page Component
 * 
 * Final step in the configuration-first workflow. Launches SUMO simulation
 * with applied configurations and provides live monitoring capabilities.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw,
  ExternalLink,
  Activity,
  Car,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Settings,
  ArrowLeft,
  RefreshCw,
  Download,
  Eye,
  Zap,
  BarChart3,
  MapPin,
  Monitor
} from 'lucide-react';
import { apiClient } from '../utils/apiClient';

const SimulationLaunchPage = ({ socket }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const intervalRef = useRef(null);
  
  const [sessionData, setSessionData] = useState(null);
  const [config, setConfig] = useState(null);
  const [simulationState, setSimulationState] = useState('ready'); // ready, launching, running, paused, stopped, error
  const [error, setError] = useState(null);
  const [sumoProcess, setSumoProcess] = useState(null);
  
  // Live statistics
  const [liveStats, setLiveStats] = useState({
    simulationTime: 0,
    totalVehicles: 0,
    runningVehicles: 0,
    waitingVehicles: 0,
    averageSpeed: 0,
    averageWaitingTime: 0,
    throughput: 0,
    emissions: {
      co2: 0,
      nox: 0,
      fuel: 0
    }
  });
  
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    loadSessionData();
    
    // Setup socket listeners for live data
    if (socket) {
      console.log('Socket available, setting up listeners');
      setConnectionStatus(socket.connected ? 'connected' : 'disconnected');
      
      socket.on('simulation_stats', handleStatsUpdate);
      socket.on('simulation_data', handleStatsUpdate); // Also listen for simulation_data
      socket.on('simulation_status', handleStatusUpdate);
      socket.on('connection_status', setConnectionStatus);
      socket.on('connect', () => setConnectionStatus('connected'));
      socket.on('disconnect', () => setConnectionStatus('disconnected'));
      
      return () => {
        socket.off('simulation_stats', handleStatsUpdate);
        socket.off('simulation_data', handleStatsUpdate);
        socket.off('simulation_status', handleStatusUpdate);
        socket.off('connection_status', setConnectionStatus);
        socket.off('connect');
        socket.off('disconnect');
      };
    } else {
      console.log('No socket available');
      setConnectionStatus('no_socket');
    }
  }, [socket]);

  useEffect(() => {
    // Start live data polling when simulation is running
    if (simulationState === 'running' && sumoProcess?.processId) {
      startLiveDataPolling();
    } else {
      stopLiveDataPolling();
    }
    
    return () => stopLiveDataPolling();
  }, [simulationState, sumoProcess]);

  const loadSessionData = () => {
    console.log('SimulationLaunchPage: Loading session data...', location.state);
    try {
      // Try to get data from navigation state first
      if (location.state?.sessionData && location.state?.config) {
        console.log('Found session data in navigation state');
        setSessionData(location.state.sessionData);
        setConfig(location.state.config);
        return;
      }

      // Fallback to localStorage
      const storedSessionData = localStorage.getItem('simulation_session_data');
      const storedConfig = localStorage.getItem('simulation_config');
      
      if (storedSessionData && storedConfig) {
        setSessionData(JSON.parse(storedSessionData));
        setConfig(JSON.parse(storedConfig));
      } else {
        setError('No session data found. Please complete the setup process.');
      }
    } catch (err) {
      console.error('Error loading session data:', err);
      setError('Invalid session data. Please restart the setup process.');
    }
  };

  const handleStatsUpdate = (stats) => {
    console.log('Received stats update:', stats);
    
    // Handle different data formats
    if (stats.data) {
      // WebSocket format: {type: 'simulation_data', data: {...}}
      const data = stats.data;
      setLiveStats({
        simulationTime: data.simulation_time || 0,
        runningVehicles: data.active_vehicles || 0,
        averageSpeed: data.avg_speed || 0,
        throughput: data.throughput || 0
      });
    } else if (stats.simulation_time !== undefined) {
      // Direct format from TraCI
      setLiveStats({
        simulationTime: stats.simulation_time || 0,
        runningVehicles: stats.active_vehicles || 0,
        averageSpeed: stats.avg_speed || 0,
        throughput: stats.throughput || 0
      });
    } else {
      // Legacy format
      setLiveStats(stats);
    }
  };

  const handleStatusUpdate = (status) => {
    setSimulationState(status.state);
    if (status.error) {
      setError(status.error);
    }
  };

  const startLiveDataPolling = () => {
    // Disabled HTTP polling since we're using WebSocket for real-time data
    // This prevents the flickering between two data sources
    console.log('WebSocket data collection active, HTTP polling disabled');
    return;
    
    if (intervalRef.current) return;
    
    intervalRef.current = setInterval(async () => {
      try {
        if (sumoProcess?.processId) {
          const response = await apiClient.get(`/api/simulation/stats/${sumoProcess.processId}`);
          if (response.data.success && response.data.stats) {
            // Only update if we actually got stats (not just WebSocket message)
            setLiveStats(response.data.stats);
          }
        }
      } catch (err) {
        console.warn('Error polling live data:', err);
      }
    }, 1000); // Poll every second
  };

  const stopLiveDataPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const handleLaunchSimulation = async () => {
    console.log('Launching simulation...', { sessionData, config });
    if (!sessionData || !config) {
      setError('Missing session data or configuration');
      return;
    }

    try {
      setSimulationState('launching');
      setError(null);

      const launchData = {
        sessionId: sessionData.sessionId,
        sessionPath: sessionData.sessionPath,
        config: config.config,
        enableGui: true, // Launch SUMO GUI
        enableLiveData: true
      };

      const response = await apiClient.post('/api/simulation/launch', launchData);
      
      if (response.data.success) {
        setSumoProcess(response.data.process);
        setSimulationState('running');
        
        // Notify via socket if available
        if (socket) {
          socket.emit('simulation_launched', {
            sessionId: sessionData.sessionId,
            processId: response.data.process.processId
          });
        }
      } else {
        setError(response.data.message || 'Failed to launch simulation');
        setSimulationState('error');
      }

    } catch (err) {
      setError(err.response?.data?.message || 'Failed to launch simulation');
      setSimulationState('error');
      console.error('Error launching simulation:', err);
    }
  };

  const handlePauseSimulation = async () => {
    if (!sumoProcess?.processId) return;
    
    console.log('DEBUG: Pausing simulation, processId:', sumoProcess.processId);

    try {
      const response = await apiClient.post(`/api/simulation/pause/${sumoProcess.processId}`);
      console.log('DEBUG: Pause response:', response.data);
      if (response.data.success) {
        setSimulationState('paused');
        console.log('DEBUG: Simulation state set to paused');
      }
    } catch (err) {
      console.error('Error pausing simulation:', err);
      setError('Failed to pause simulation');
    }
  };

  const handleResumeSimulation = async () => {
    if (!sumoProcess?.processId) return;
    
    console.log('DEBUG: Resuming simulation, processId:', sumoProcess.processId);

    try {
      const response = await apiClient.post(`/api/simulation/resume/${sumoProcess.processId}`);
      console.log('DEBUG: Resume response:', response.data);
      if (response.data.success) {
        setSimulationState('running');
        console.log('DEBUG: Simulation state set to running');
      }
    } catch (err) {
      console.error('Error resuming simulation:', err);
      setError('Failed to resume simulation');
    }
  };

  const handleStopSimulation = async () => {
    if (!sumoProcess?.processId) return;

    try {
      const response = await apiClient.post(`/api/simulation/stop/${sumoProcess.processId}`);
      if (response.data.success) {
        setSimulationState('stopped');
        setSumoProcess(null);
        stopLiveDataPolling();
      }
    } catch (err) {
      console.error('Error stopping simulation:', err);
      setError('Failed to stop simulation');
    }
  };

  const handleViewResults = () => {
    if (sessionData) {
      navigate('/analytics', {
        state: {
          sessionId: sessionData.sessionId,
          sessionPath: sessionData.sessionPath
        }
      });
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = () => {
    switch (simulationState) {
      case 'running': return 'text-green-600';
      case 'paused': return 'text-yellow-600';
      case 'stopped': return 'text-gray-600';
      case 'error': return 'text-red-600';
      case 'launching': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (simulationState) {
      case 'ready': return 'Ready to Launch';
      case 'launching': return 'Launching...';
      case 'running': return 'Running';
      case 'paused': return 'Paused';
      case 'stopped': return 'Stopped';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  if (!sessionData || !config) {
    return (
      <div className="simulation-page">
        <div className="simulation-container">
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Session Data Required
            </h2>
            <p className="text-gray-600 mb-6">
              Please complete the configuration and network selection process.
            </p>
            <Link
              to="/simulation-setup"
              className="btn btn-primary"
            >
              Start Configuration
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'no_socket': return 'No WebSocket';
      default: return 'Unknown';
    }
  };

  const getConnectionStatusClass = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'disconnected': return 'text-red-600';
      case 'no_socket': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="simulation-page">
      <div className="simulation-container">
        {/* Header */}
        <div className="simulation-header">
          <div>
            <h1 className="simulation-title">
              Simulation Launch
            </h1>
            <p className="text-gray-600">
              Network: <strong>{sessionData.networkName}</strong> | 
              Session: <code className="bg-gray-100 px-1 rounded text-xs">{sessionData.sessionId}</code>
            </p>
          </div>
          
          <div className={`simulation-status ${simulationState}`}>
            <div className="w-2 h-2 rounded-full bg-current"></div>
            <span className={getStatusColor()}>{getStatusText()}</span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="alert alert-error mb-6">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        <div className="simulation-grid">
          {/* Main Control Panel */}
          <div className="simulation-main">
            
            {/* Control Panel */}
            <div className="simulation-controls">
              <div className="simulation-controls-header">
                <h2 className="simulation-controls-title">Simulation Controls</h2>
                <div className={`simulation-connection ${connectionStatus}`}>
                  <div className={`w-2 h-2 rounded-full ${getConnectionStatusClass()}`}></div>
                  <span className={getConnectionStatusClass()}>{getConnectionStatusText()}</span>
                </div>
              </div>
              
              <div className="simulation-control-buttons">
                {/* Launch button - force visibility */}
                {simulationState === 'ready' && sessionData?.sessionId && config && (
                  <button
                    onClick={handleLaunchSimulation}
                    className="simulation-control-btn primary"
                  >
                    <Play className="w-4 h-4" />
                    Launch SUMO
                  </button>
                )}
                
                {simulationState === 'running' && (
                  <>
                    <button
                      onClick={handlePauseSimulation}
                      className="simulation-control-btn"
                    >
                      <Pause className="w-4 h-4" />
                      Pause
                    </button>
                    <button
                      onClick={handleStopSimulation}
                      className="simulation-control-btn"
                    >
                      <Square className="w-4 h-4" />
                      Stop
                    </button>
                  </>
                )}
                
                {simulationState === 'paused' && (
                  <>
                    <button
                      onClick={handleResumeSimulation}
                      className="simulation-control-btn primary"
                    >
                      <Play className="w-4 h-4" />
                      Resume
                    </button>
                    <button
                      onClick={handleStopSimulation}
                      className="simulation-control-btn"
                    >
                      <Square className="w-4 h-4" />
                      Stop
                    </button>
                  </>
                )}
                
                {(simulationState === 'stopped' || simulationState === 'error') && (
                  <button
                    onClick={handleLaunchSimulation}
                    className="simulation-control-btn primary"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Restart
                  </button>
                )}
              </div>
              
              {sumoProcess && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <div className="text-sm">
                    <div className="font-medium text-blue-900">SUMO Process</div>
                    <div className="text-blue-700">
                      PID: {sumoProcess.processId} | Port: {sumoProcess.port || 'N/A'}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Live Statistics */}
            {simulationState === 'running' && (
              <div className="bg-white rounded-lg p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Live Statistics</h2>
                  <div className="text-sm text-gray-500">
                    Updates every second
                  </div>
                </div>
                
                <div className="simulation-stats-grid">
                  <div className="simulation-stat-card">
                    <Clock className="simulation-stat-icon" />
                    <div className="simulation-stat-value">
                      {formatTime(liveStats.simulationTime)}
                    </div>
                    <div className="simulation-stat-label">Simulation Time</div>
                  </div>
                  
                  <div className="simulation-stat-card">
                    <Car className="simulation-stat-icon" />
                    <div className="simulation-stat-value">
                      {liveStats.runningVehicles}
                    </div>
                    <div className="simulation-stat-label">Active Vehicles</div>
                  </div>
                  
                  <div className="simulation-stat-card">
                    <TrendingUp className="simulation-stat-icon" />
                    <div className="simulation-stat-value">
                      {liveStats.averageSpeed.toFixed(1)} km/h
                    </div>
                    <div className="simulation-stat-label">Avg Speed</div>
                  </div>
                  
                  <div className="simulation-stat-card">
                    <Activity className="simulation-stat-icon" />
                    <div className="simulation-stat-value">
                      {liveStats.throughput}
                    </div>
                    <div className="simulation-stat-label">Throughput/hr</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="simulation-sidebar">
            
            {/* Configuration Summary */}
            <div className="config-section">
              <div className="config-section-header">
                <Settings className="config-section-icon" />
                <h3 className="config-section-title">Configuration</h3>
              </div>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Duration:</span> {Math.floor(config.config.duration / 60)} min
                </div>
                <div>
                  <span className="font-medium">Traffic Volume:</span> {Math.round(config.config.trafficVolume * 100)}%
                </div>
                <div>
                  <span className="font-medium">Step Length:</span> {config.config.stepLength}s
                </div>
                <div>
                  <span className="font-medium">Modifications:</span> {config.config.speedLimits.length + config.config.roadClosures.length} items
                </div>
              </div>
            </div>

            {/* Session Info */}
            <div className="config-section">
              <div className="config-section-header">
                <Monitor className="config-section-icon" />
                <h3 className="config-section-title">Session Info</h3>
              </div>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Network:</span> {sessionData.networkName}
                </div>
                <div>
                  <span className="font-medium">Session ID:</span>
                  <br />
                  <code className="text-xs bg-gray-100 px-1 rounded">{sessionData.sessionId}</code>
                </div>
                <div>
                  <span className="font-medium">Created:</span> {new Date(sessionData.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="config-section">
              <div className="config-section-header">
                <Zap className="config-section-icon" />
                <h3 className="config-section-title">Actions</h3>
              </div>
              <div className="space-y-2">
                <button
                  onClick={handleViewResults}
                  className="btn btn-outline w-full flex items-center justify-center space-x-2"
                  disabled={simulationState === 'ready' || simulationState === 'launching'}
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>View Results</span>
                </button>
                
                <button
                  onClick={() => window.open('/api/simulation/download-results/' + sessionData.sessionId)}
                  className="btn btn-outline w-full flex items-center justify-center space-x-2"
                  disabled={simulationState === 'ready' || simulationState === 'launching'}
                >
                  <Download className="w-4 h-4" />
                  <span>Download Data</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="simulation-nav">
          <div className="simulation-nav-buttons">
            <Link 
              to="/network-selection" 
              className="btn btn-secondary flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Networks</span>
            </Link>
          </div>
          
          <div className="text-sm text-gray-500">
            {simulationState === 'running' ? (
              <span className="text-green-600 font-medium">Simulation is running in SUMO GUI</span>
            ) : simulationState === 'ready' ? (
              <span>Click "Launch SUMO" to start the simulation</span>
            ) : (
              <span>Simulation: {getStatusText()}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationLaunchPage;
