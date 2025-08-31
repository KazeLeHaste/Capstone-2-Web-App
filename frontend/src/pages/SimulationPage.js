/**
 * Simulation Page Component
 * 
 * Main simulation control and visualization page.
 * Features live 2D map display, simulation controls, and real-time monitoring.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw,
  Zap,
  Clock,
  Car,
  Users,
  Activity,
  AlertCircle,
  CheckCircle,
  Settings,
  ArrowLeft,
  ArrowRight,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { api } from '../utils/apiClient';
import MapVisualization from '../components/MapVisualization';
import SimulationStats from '../components/SimulationStats';

const SimulationPage = ({ socket, simulationData, simulationStatus, onLoadingChange }) => {
  const [config, setConfig] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Real-time statistics
  const [stats, setStats] = useState({
    totalVehicles: 0,
    averageSpeed: 0,
    totalDistance: 0,
    simulationTime: 0
  });
  
  const intervalRef = useRef(null);
  
  useEffect(() => {
    // Load configuration from previous step
    const configData = localStorage.getItem('simulation_config');
    if (configData) {
      setConfig(JSON.parse(configData));
    }
    
    // Set up elapsed time tracking
    if (isRunning && !isPaused && startTime) {
      intervalRef.current = setInterval(() => {
        setElapsedTime(Date.now() - startTime);
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, isPaused, startTime]);
  
  useEffect(() => {
    // Update status based on simulation status
    if (simulationStatus === 'running') {
      setIsRunning(true);
      setIsPaused(false);
      if (!startTime) {
        setStartTime(Date.now());
      }
    } else if (simulationStatus === 'stopped' || simulationStatus === 'finished') {
      setIsRunning(false);
      setIsPaused(false);
      setStartTime(null);
      setElapsedTime(0);
    } else if (simulationStatus === 'error') {
      setIsRunning(false);
      setIsPaused(false);
      setError('Simulation encountered an error');
    }
  }, [simulationStatus]);
  
  useEffect(() => {
    // Update statistics from simulation data
    if (simulationData && simulationData.statistics) {
      setStats({
        totalVehicles: simulationData.statistics.total_vehicles || 0,
        averageSpeed: calculateAverageSpeed(simulationData.vehicles || []),
        totalDistance: calculateTotalDistance(simulationData.vehicles || []),
        simulationTime: simulationData.statistics.simulation_time || 0
      });
    }
  }, [simulationData]);
  
  useEffect(() => {
    // Update connection status
    if (socket) {
      setConnectionStatus(socket.connected ? 'connected' : 'disconnected');
    }
  }, [socket]);
  
  const calculateAverageSpeed = (vehicles) => {
    if (vehicles.length === 0) return 0;
    const totalSpeed = vehicles.reduce((sum, vehicle) => sum + (vehicle.speed || 0), 0);
    return (totalSpeed / vehicles.length).toFixed(1);
  };
  
  const calculateTotalDistance = (vehicles) => {
    // This is a simplified calculation - in a real implementation,
    // you would track cumulative distance over time
    return vehicles.length * 100; // Placeholder calculation
  };
  
  const handleStartSimulation = async () => {
    if (!config) {
      setError('No configuration found. Please configure the simulation first.');
      return;
    }
    
    try {
      setError(null);
      onLoadingChange(true);
      
      const response = await api.startSimulation({
        network: config.network,
        scenario: config.scenario,
        config: config.config
      });
      
      if (response.data.success) {
        setIsRunning(true);
        setStartTime(Date.now());
        setElapsedTime(0);
      } else {
        setError(response.data.error || 'Failed to start simulation');
      }
    } catch (err) {
      setError('Unable to start simulation. Please check your connection.');
      console.error('Error starting simulation:', err);
    } finally {
      onLoadingChange(false);
    }
  };
  
  const handleStopSimulation = async () => {
    try {
      setError(null);
      
      const response = await api.stopSimulation();
      
      if (response.data.success) {
        setIsRunning(false);
        setIsPaused(false);
        setStartTime(null);
        setElapsedTime(0);
      } else {
        setError(response.data.error || 'Failed to stop simulation');
      }
    } catch (err) {
      setError('Unable to stop simulation. Please check your connection.');
      console.error('Error stopping simulation:', err);
    }
  };
  
  const handlePauseResume = () => {
    // Note: This is a UI-only pause - SUMO doesn't support pause/resume
    // In a real implementation, you might need to implement this differently
    if (isPaused) {
      setIsPaused(false);
      setStartTime(Date.now() - elapsedTime);
    } else {
      setIsPaused(true);
    }
  };
  
  const handleReset = () => {
    setIsRunning(false);
    setIsPaused(false);
    setStartTime(null);
    setElapsedTime(0);
    setError(null);
    setStats({
      totalVehicles: 0,
      averageSpeed: 0,
      totalDistance: 0,
      simulationTime: 0
    });
  };
  
  const formatTime = (milliseconds) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    return `${hours.toString().padStart(2, '0')}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600';
      case 'stopped': return 'text-gray-600';
      case 'error': return 'text-red-600';
      case 'initializing': return 'text-yellow-600';
      case 'finished': return 'text-blue-600';
      default: return 'text-gray-400';
    }
  };
  
  const getStatusText = (status) => {
    switch (status) {
      case 'running': return 'Running';
      case 'stopped': return 'Stopped';
      case 'error': return 'Error';
      case 'initializing': return 'Initializing';
      case 'finished': return 'Finished';
      default: return 'Unknown';
    }
  };
  
  if (!config) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            No Configuration Found
          </h1>
          <p className="text-gray-600 mb-8">
            Please configure the simulation parameters before starting.
          </p>
          <Link to="/configuration" className="btn btn-primary">
            Configure Simulation
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`min-h-screen bg-gray-50 ${isFullscreen ? 'fixed inset-0 z-50' : 'py-8'}`}>
      <div className={`${isFullscreen ? 'h-full' : 'max-w-7xl mx-auto px-4'}`}>
        {/* Header */}
        {!isFullscreen && (
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Traffic Simulation
            </h1>
            <p className="text-gray-600">
              Network: <strong>{config.network}</strong> | 
              Scenario: <strong>{config.scenario}</strong>
            </p>
          </div>
        )}
        
        {/* Error Display */}
        {error && !isFullscreen && (
          <div className="alert alert-error mb-6">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}
        
        <div className={`grid ${isFullscreen ? 'grid-cols-1' : 'lg:grid-cols-4'} gap-6 ${isFullscreen ? 'h-full' : ''}`}>
          {/* Control Panel */}
          <div className={`${isFullscreen ? 'hidden' : 'lg:col-span-1'} space-y-6`}>
            {/* Simulation Controls */}
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>Controls</span>
                </h3>
              </div>
              <div className="card-body space-y-4">
                <div className="flex flex-col space-y-3">
                  {!isRunning ? (
                    <button
                      onClick={handleStartSimulation}
                      className="btn btn-success w-full flex items-center justify-center space-x-2"
                      disabled={simulationStatus === 'initializing'}
                    >
                      <Play className="w-4 h-4" />
                      <span>Start Simulation</span>
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={handlePauseResume}
                        className="btn btn-secondary w-full flex items-center justify-center space-x-2"
                      >
                        {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        <span>{isPaused ? 'Resume' : 'Pause'}</span>
                      </button>
                      
                      <button
                        onClick={handleStopSimulation}
                        className="btn btn-danger w-full flex items-center justify-center space-x-2"
                      >
                        <Square className="w-4 h-4" />
                        <span>Stop</span>
                      </button>
                    </>
                  )}
                  
                  <button
                    onClick={handleReset}
                    className="btn btn-outline w-full flex items-center justify-center space-x-2"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>Reset</span>
                  </button>
                </div>
              </div>
            </div>
            
            {/* Status Information */}
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>Status</span>
                </h3>
              </div>
              <div className="card-body space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Simulation</span>
                  <span className={`font-medium ${getStatusColor(simulationStatus)}`}>
                    {getStatusText(simulationStatus)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Connection</span>
                  <span className={`font-medium ${connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                    {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Elapsed Time</span>
                  <span className="font-medium font-mono">
                    {formatTime(elapsedTime)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Sim Time</span>
                  <span className="font-medium">
                    {stats.simulationTime.toFixed(1)}s
                  </span>
                </div>
              </div>
            </div>
            
            {/* Quick Stats */}
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Quick Stats</span>
                </h3>
              </div>
              <div className="card-body space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Vehicles</span>
                  <span className="font-medium">{stats.totalVehicles}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Avg Speed</span>
                  <span className="font-medium">{stats.averageSpeed} m/s</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total Distance</span>
                  <span className="font-medium">{(stats.totalDistance / 1000).toFixed(1)} km</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Map Visualization */}
          <div className={`${isFullscreen ? 'col-span-1 h-full' : 'lg:col-span-3'} relative`}>
            <div className="card h-full">
              <div className="card-header flex items-center justify-between">
                <h3 className="text-lg font-semibold">Live Simulation View</h3>
                <div className="flex items-center space-x-2">
                  {!isFullscreen && (
                    <span className="text-sm text-gray-600">
                      {stats.totalVehicles} vehicles active
                    </span>
                  )}
                  <button
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="btn btn-sm btn-secondary"
                  >
                    {isFullscreen ? (
                      <Minimize2 className="w-4 h-4" />
                    ) : (
                      <Maximize2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
              
              <div className="card-body p-0 h-full relative">
                <MapVisualization 
                  simulationData={simulationData}
                  isRunning={isRunning}
                  config={config}
                  isFullscreen={isFullscreen}
                />
                
                {/* Fullscreen controls overlay */}
                {isFullscreen && (
                  <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                      <span className="font-medium">{getStatusText(simulationStatus)}</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      Time: {formatTime(elapsedTime)}
                    </div>
                    <div className="text-sm text-gray-600">
                      Vehicles: {stats.totalVehicles}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        {!isFullscreen && (
          <div className="flex justify-between items-center mt-8">
            <Link to="/configuration" className="btn btn-secondary flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Configuration</span>
            </Link>
            
            <Link 
              to="/analytics" 
              className="btn btn-primary flex items-center space-x-2"
            >
              <span>View Analytics</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default SimulationPage;
