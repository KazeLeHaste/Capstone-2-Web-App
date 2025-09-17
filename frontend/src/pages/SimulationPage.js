/**
 * Simulation Page Component
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
  Activity,
  Car,
  Clock,
  TrendingUp,
  AlertCircle,
  Settings,
  ArrowLeft,
  Download,
  Zap,
  BarChart3,
  Monitor,
  ZoomIn,
  ZoomOut,
  Save
} from 'lucide-react';
import { apiClient } from '../utils/apiClient';

const SimulationPage = ({ socket }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const intervalRef = useRef(null);
  
  const [sessionData, setSessionData] = useState(null);
  const [config, setConfig] = useState(null);
  const [simulationState, setSimulationState] = useState('ready'); // ready, launching, running, paused, stopped, error, finished
  const [error, setError] = useState(null);
  const [sumoProcess, setSumoProcess] = useState(null);
  const [sessionSaved, setSessionSaved] = useState(false);
  
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
  
  // Real-time tracking (separate from simulation time)
  const [realTimeStats, setRealTimeStats] = useState({
    startTime: null,
    elapsedRealTime: 0
  });
  
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Zoom control state
  const [currentZoom, setCurrentZoom] = useState(100.0);
  const [isZoomLoading, setIsZoomLoading] = useState(false);

  useEffect(() => {
    loadSessionData();
    
    // Setup socket listeners for live data
    if (socket) {
      console.log('Socket available, setting up listeners');
      setConnectionStatus(socket.connected ? 'connected' : 'disconnected');
      
      socket.on('simulation_stats', handleStatsUpdate);
      socket.on('simulation_data', handleStatsUpdate); // Also listen for simulation_data
      socket.on('simulation_status', handleStatusUpdate);
      socket.on('session_completed', handleSessionCompleted);
      socket.on('connection_status', setConnectionStatus);
      socket.on('connect', () => setConnectionStatus('connected'));
      socket.on('disconnect', () => setConnectionStatus('disconnected'));
      
      // Zoom control event listeners
      socket.on('zoom_changed', (data) => {
        if (data.processId === sumoProcess?.processId) {
          setCurrentZoom(data.zoomLevel);
        }
      });
      
      socket.on('view_centered', (data) => {
        if (data.processId === sumoProcess?.processId && data.zoomLevel) {
          setCurrentZoom(data.zoomLevel);
        }
      });
      
      return () => {
        socket.off('simulation_stats', handleStatsUpdate);
        socket.off('simulation_data', handleStatsUpdate);
        socket.off('simulation_status', handleStatusUpdate);
        socket.off('session_completed', handleSessionCompleted);
        socket.off('connection_status', setConnectionStatus);
        socket.off('connect');
        socket.off('disconnect');
        socket.off('zoom_changed');
        socket.off('view_centered');
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
  
  // Real-time elapsed time tracking
  useEffect(() => {
    let realTimeInterval;
    
    if (simulationState === 'running' && realTimeStats.startTime) {
      realTimeInterval = setInterval(() => {
        setRealTimeStats(prev => ({
          ...prev,
          elapsedRealTime: Date.now() - prev.startTime
        }));
      }, 1000); // Update every second
    }
    
    return () => {
      if (realTimeInterval) {
        clearInterval(realTimeInterval);
      }
    };
  }, [simulationState, realTimeStats.startTime]);

  const loadSessionData = () => {
    console.log('SimulationPage: Loading session data...', location.state);
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
      
      // Update zoom level if available
      if (data.zoom_level !== undefined) {
        setCurrentZoom(data.zoom_level);
      }
    } else if (stats.simulation_time !== undefined) {
      // Direct format from TraCI
      setLiveStats({
        simulationTime: stats.simulation_time || 0,
        runningVehicles: stats.active_vehicles || 0,
        averageSpeed: stats.avg_speed || 0,
        throughput: stats.throughput || 0
      });
      
      // Update zoom level if available
      if (stats.zoom_level !== undefined) {
        setCurrentZoom(stats.zoom_level);
      }
    } else {
      // Legacy format
      setLiveStats(stats);
    }
  };

  const handleStatusUpdate = (status) => {
    console.log('Status update received:', status);
    
    if (status.status === 'completed' || status.status === 'stopped') {
      setSimulationState('finished');
      console.log(`Simulation ${status.status}: ${status.message}`);
      
      // Reset real-time tracking
      setRealTimeStats({
        startTime: null,
        elapsedRealTime: 0
      });
      
      // Show completion notification
      if (status.reason) {
        console.log(`Completion reason: ${status.reason}`);
      }
    } else {
      setSimulationState(status.status || status.state);
    }
    
    if (status.error) {
      setError(status.error);
    }
  };

  const handleSessionCompleted = (completionData) => {
    console.log('Session completed:', completionData);
    
    // Update simulation state to finished
    setSimulationState('finished');
    
    // Clear the SUMO process reference since it's no longer running
    setSumoProcess(null);
    
    // Show completion message
    const message = `Simulation completed: ${completionData.reason}`;
    console.log(message);
    
    // Mark session as saved if the backend indicates it can be analyzed
    if (completionData.can_analyze) {
      setSessionSaved(true);
    }
    
    // Update session data to indicate it can be analyzed
    if (sessionData) {
      setSessionData(prev => ({
        ...prev,
        can_analyze: completionData.can_analyze || false,
        completed_at: completionData.completed_at
      }));
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
        enableLiveData: true  // Re-enabled for optimized TraCI implementation
      };

      const response = await apiClient.post('/api/simulation/launch', launchData);
      
      if (response.data.success) {
        setSumoProcess(response.data.process);
        setSimulationState('running');
        
        // Start real-time tracking
        setRealTimeStats(prev => ({
          ...prev,
          startTime: Date.now(),
          elapsedRealTime: 0
        }));
        
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

  const handleSaveSession = async () => {
    if (!sessionData?.sessionId) return;

    try {
      setError(null); // Clear any previous errors
      
      // Force save session data by calling a backend endpoint
      const response = await apiClient.post('/api/simulation/save-session', {
        sessionId: sessionData.sessionId,
        sessionPath: sessionData.sessionPath,
        force: true // Force save even if already saved
      });
      
      if (response.data.success) {
        // Update session data to indicate it's saved and can be analyzed
        setSessionData(prev => ({
          ...prev,
          can_analyze: true,
          saved_at: new Date().toISOString()
        }));
        
        // Mark as saved
        setSessionSaved(true);
        
        // Show success message (you could add a toast notification here)
        console.log('Session saved successfully');
      } else {
        setError('Failed to save session: ' + (response.data.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error saving session:', err);
      setError('Failed to save session data');
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

  // Zoom control functions
  const fetchCurrentZoom = async () => {
    if (!sumoProcess?.processId) return;
    
    try {
      const response = await apiClient.get(`/api/simulation/zoom/${sumoProcess.processId}`);
      if (response.data.success) {
        setCurrentZoom(response.data.zoomLevel);
      }
    } catch (error) {
      console.warn('Failed to fetch zoom level:', error);
    }
  };

  const handleZoomIn = async () => {
    if (!sumoProcess?.processId || isZoomLoading) return;
    
    setIsZoomLoading(true);
    try {
      const newZoom = currentZoom * 1.2; // 20% increase, no max limit
      const response = await apiClient.post(`/api/simulation/zoom/${sumoProcess.processId}`, {
        zoomLevel: newZoom
      });
      
      if (response.data.success) {
        setCurrentZoom(newZoom);
      }
    } catch (error) {
      console.error('Failed to zoom in:', error);
    } finally {
      setIsZoomLoading(false);
    }
  };

  const handleZoomOut = async () => {
    if (!sumoProcess?.processId || isZoomLoading) return;
    
    setIsZoomLoading(true);
    try {
      const newZoom = currentZoom / 1.2; // 20% decrease, no min limit
      const response = await apiClient.post(`/api/simulation/zoom/${sumoProcess.processId}`, {
        zoomLevel: newZoom
      });
      
      if (response.data.success) {
        setCurrentZoom(newZoom);
      }
    } catch (error) {
      console.error('Failed to zoom out:', error);
    } finally {
      setIsZoomLoading(false);
    }
  };


  // Poll zoom level periodically when simulation is running
  useEffect(() => {
    if (simulationState === 'running' && sumoProcess?.processId) {
      const zoomInterval = setInterval(fetchCurrentZoom, 2000); // Check every 2 seconds
      
      // Fetch initial zoom level
      fetchCurrentZoom();
      
      return () => clearInterval(zoomInterval);
    }
  }, [simulationState, sumoProcess?.processId]);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatRealTime = (milliseconds) => {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = () => {
    switch (simulationState) {
      case 'running': return 'text-primary';
      case 'paused': return 'text-muted';
      case 'stopped': return 'text-muted';
      case 'finished': return 'text-primary';
      case 'error': return 'text-danger';
      case 'launching': return 'text-primary';
      default: return 'text-muted';
    }
  };

  const getStatusText = () => {
    switch (simulationState) {
      case 'ready': return 'Ready to Launch';
      case 'launching': return 'Launching...';
      case 'running': return 'Running';
      case 'paused': return 'Paused';
      case 'stopped': return 'Stopped';
      case 'finished': return 'Completed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  if (!sessionData || !config) {
    return (
      <div className="simulation-page">
        <div className="simulation-container">
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-danger mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-primary mb-2">
              Session Data Required
            </h2>
            <p className="text-secondary mb-6">
              Please complete the configuration and network selection process.
            </p>
            <Link
              to="/configuration"
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
      case 'connected': return 'text-primary';
      case 'disconnected': return 'text-danger';
      case 'no_socket': return 'text-muted';
      default: return 'text-muted';
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
            <p className="text-secondary">
              Network: <strong>{sessionData.networkName}</strong> | 
              Session: <code className="code-block">{sessionData.sessionId}</code>
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
                      disabled
                      className="simulation-control-btn disabled"
                      title="Controls disabled - use SUMO GUI directly"
                    >
                      <Pause className="w-4 h-4" />
                      Pause
                    </button>
                    <button
                      disabled
                      className="simulation-control-btn disabled"
                      title="Controls disabled - use SUMO GUI directly"
                    >
                      <Square className="w-4 h-4" />
                      Stop
                    </button>
                  </>
                )}
                
                {simulationState === 'paused' && (
                  <>
                    <button
                      disabled
                      className="simulation-control-btn disabled"
                      title="Controls disabled - use SUMO GUI directly"
                    >
                      <Play className="w-4 h-4" />
                      Resume
                    </button>
                    <button
                      disabled
                      className="simulation-control-btn disabled"
                      title="Controls disabled - use SUMO GUI directly"
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
                
                {simulationState === 'finished' && sessionData?.sessionId && (
                  <>
                    {sessionSaved || sessionData?.can_analyze ? (
                      <Link
                        to={`/analytics?session=${sessionData.sessionId}`}
                        className="simulation-control-btn primary"
                      >
                        <BarChart3 className="w-4 h-4" />
                        View Results
                      </Link>
                    ) : (
                      <button
                        onClick={handleSaveSession}
                        className="simulation-control-btn primary"
                      >
                        <Save className="w-4 h-4" />
                        Save Session
                      </button>
                    )}
                    <button
                      onClick={handleLaunchSimulation}
                      className="simulation-control-btn"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Run Again
                    </button>
                  </>
                )}
              </div>
              
              {/* Zoom Controls */}
              {(simulationState === 'running' || simulationState === 'paused') && sumoProcess?.processId && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-medium text-blue-900">View Controls</div>
                  </div>
                  
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={handleZoomOut}
                      disabled={isZoomLoading}
                      className="simulation-control-btn secondary"
                      title="Zoom Out (20%)"
                    >
                      <ZoomOut className="w-4 h-4" />
                    </button>
                    
                    <div className="px-4 py-2 bg-primary border border-primary rounded-md min-w-[100px] text-center">
                      <span className="text-sm font-medium text-primary">
                        {currentZoom.toFixed(1)}%
                      </span>
                    </div>
                    
                    <button
                      onClick={handleZoomIn}
                      disabled={isZoomLoading}
                      className="simulation-control-btn secondary"
                      title="Zoom In (20%)"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>
                    
                    
                  </div>
                </div>
              )}
              
          
              
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
                  <span className="font-medium">Simulation Duration:</span>
                  {" "}
                  {config.config.original_config 
                    ? Math.floor(((config.config.sumo_end || 0) - (config.config.sumo_begin || 0)) / 60)
                    : Math.floor((config.config.duration || 0) / 60)
                  } min
                  <span className="text-xs text-gray-500 block">Simulated time to cover</span>
                </div>
                {simulationState === 'running' && realTimeStats.startTime && (
                  <div>
                    <span className="font-medium">Real-time Elapsed:</span>
                    {" "}
                    {formatRealTime(realTimeStats.elapsedRealTime)}
                    <span className="text-xs text-gray-500 block">Actual time spent (affected by delay)</span>
                  </div>
                )}
                <div>
                  {config.config.original_config ? (
                    // Current configuration structure - show traffic scale
                    <>
                      <span className="font-medium">Traffic Scale:</span> {(config.config.sumo_traffic_scale || config.config.traffic_scale || config.config.sumo_traffic_intensity || 1.0)}x
                    </>
                  ) : (
                    // Legacy configuration structure - show traffic scale fallback
                    <>
                      <span className="font-medium">Traffic Scale:</span> {(config.config.trafficVolume || 1.0)}x
                    </>
                  )}
                </div>
                <div>
                  {config.config.original_config ? (
                    // Simplified configuration structure
                    <>
                      <span className="font-medium">Step Length:</span> {config.config.sumo_step_length || 1.0}s
                    </>
                  ) : (
                    // Legacy configuration structure
                    <>
                      <span className="font-medium">Step Length:</span> {config.config.stepLength || 1.0}s
                    </>
                  )}
                </div>
                <div>
                  {config.config.original_config ? (
                    <span className="font-medium">Configuration:</span>
                  ) : (
                    <span className="font-medium">Modifications:</span>
                  )}
                  {" "}
                  {config.config.original_config 
                    ? "Simplified (Essential parameters only)"
                    : `${(config.config.speedLimits || []).length + (config.config.roadClosures || []).length} items`
                  }
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
                  <code className="code-block">{sessionData.sessionId}</code>
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
          
          <div className="text-sm text-muted">
            {simulationState === 'running' ? (
              <span className="text-primary font-medium">Simulation is running in SUMO GUI</span>
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

export default SimulationPage;
