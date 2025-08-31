/**
 * Simulation Setup Page Component
 * 
 * Configuration-first approach where users set simulation parameters
 * before selecting a network. This ensures configurations are saved
 * and can be applied to any selected network.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Settings, 
  Clock, 
  Car, 
  Truck, 
  Traffic,
  MapPin,
  Zap,
  Save,
  ArrowRight,
  ArrowLeft,
  Info,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Plus,
  Minus,
  Edit
} from 'lucide-react';
import { api } from '../utils/apiClient';

const SimulationSetupPage = ({ socket }) => {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Configuration state
  const [config, setConfig] = useState({
    // Basic simulation settings
    duration: 3600, // seconds
    stepLength: 1.0, // seconds
    randomSeed: 42,
    
    // Traffic settings
    trafficVolume: 0.5, // 0-1 scale
    trafficDensity: 1.0, // OSM scenario density multiplier
    
    // Vehicle types for both generated and OSM scenarios
    vehicleTypes: {
      passenger: { enabled: true, percentage: 75, maxSpeed: 50 },
      truck: { enabled: true, percentage: 15, maxSpeed: 40 },
      bus: { enabled: true, percentage: 10, maxSpeed: 45 },
      motorcycle: { enabled: false, percentage: 5, maxSpeed: 60 }
    },
    
    // OSM scenario specific settings
    enabledVehicles: ['passenger', 'bus', 'truck'], // For OSM scenarios
    preserveRealisticTiming: true,
    useRushHourPatterns: false,
    
    // Network modifications
    speedLimits: [], // { edgeId: string, speedLimit: number }
    roadClosures: [], // { edgeId: string, startTime: number, endTime: number }
    trafficLights: [], // { junctionId: string, program: object }
    
    // Advanced settings
    departureSpread: 300, // seconds
    routeChoiceModel: 'gawron',
    laneChangingModel: 'LC2013',
    carFollowingModel: 'Krauss',
    
    // Output settings
    outputFrequency: 60, // seconds
    enableVisualization: true,
    saveTrajectories: false
  });

  useEffect(() => {
    // Generate a unique session ID
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  }, []);

  const handleConfigChange = (section, key, value) => {
    if (section) {
      setConfig(prev => ({
        ...prev,
        [section]: {
          ...prev[section],
          [key]: value
        }
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        [key]: value
      }));
    }
  };

  const handleVehicleTypeChange = (type, field, value) => {
    setConfig(prev => ({
      ...prev,
      vehicleTypes: {
        ...prev.vehicleTypes,
        [type]: {
          ...prev.vehicleTypes[type],
          [field]: value
        }
      }
    }));
  };

  const handleEnabledVehicleChange = (vehicleType, enabled) => {
    setConfig(prev => {
      const enabledVehicles = enabled 
        ? [...prev.enabledVehicles.filter(v => v !== vehicleType), vehicleType]
        : prev.enabledVehicles.filter(v => v !== vehicleType);
      
      return {
        ...prev,
        enabledVehicles
      };
    });
  };

  const addSpeedLimit = () => {
    setConfig(prev => ({
      ...prev,
      speedLimits: [
        ...prev.speedLimits,
        { id: Date.now(), edgeId: '', speedLimit: 30 }
      ]
    }));
  };

  const removeSpeedLimit = (id) => {
    setConfig(prev => ({
      ...prev,
      speedLimits: prev.speedLimits.filter(item => item.id !== id)
    }));
  };

  const updateSpeedLimit = (id, field, value) => {
    setConfig(prev => ({
      ...prev,
      speedLimits: prev.speedLimits.map(item =>
        item.id === id ? { ...item, [field]: value } : item
      )
    }));
  };

  const addRoadClosure = () => {
    setConfig(prev => ({
      ...prev,
      roadClosures: [
        ...prev.roadClosures,
        { id: Date.now(), edgeId: '', startTime: 0, endTime: 1800 }
      ]
    }));
  };

  const removeRoadClosure = (id) => {
    setConfig(prev => ({
      ...prev,
      roadClosures: prev.roadClosures.filter(item => item.id !== id)
    }));
  };

  const updateRoadClosure = (id, field, value) => {
    setConfig(prev => ({
      ...prev,
      roadClosures: prev.roadClosures.map(item =>
        item.id === id ? { ...item, [field]: value } : item
      )
    }));
  };

  const handleSaveConfiguration = async () => {
    if (!sessionId) {
      setError('Session ID not available');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const configData = {
        sessionId,
        timestamp: new Date().toISOString(),
        config
      };

      // Save configuration to backend
      const response = await api.post('/api/simulation/save-config', configData);
      
      if (response.data.success) {
        setSuccess(true);
        
        // Store session ID for next step
        localStorage.setItem('simulation_session_id', sessionId);
        localStorage.setItem('simulation_config', JSON.stringify(configData));
        
        // Notify via socket if available
        if (socket) {
          socket.emit('config_saved', configData);
        }
        
        // Navigate to network selection after a brief delay
        setTimeout(() => {
          navigate('/network-selection', { 
            state: { sessionId, config: configData } 
          });
        }, 1500);
      } else {
        setError(response.data.message || 'Failed to save configuration');
      }

    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save configuration');
      console.error('Error saving configuration:', err);
    } finally {
      setSaving(false);
    }
  };

  const getDurationText = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getTrafficVolumeText = (volume) => {
    if (volume <= 0.3) return 'Low';
    if (volume <= 0.7) return 'Medium';
    return 'High';
  };

  return (
    <div className="config-page">
      <div className="config-container">
        {/* Header */}
        <div className="config-header">
          <h1 className="config-title">
            Simulation Configuration
          </h1>
          <p className="config-subtitle">
            Configure simulation parameters before selecting your network. 
            These settings will be applied to your chosen network.
          </p>
          
          {sessionId && (
            <div className="text-sm text-gray-600 mt-2">
              Session ID: <code className="bg-gray-100 px-2 py-1 rounded">{sessionId}</code>
            </div>
          )}
        </div>

        {/* Success/Error Messages */}
        {error && (
          <div className="alert alert-error mb-6">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert alert-success mb-6">
            <CheckCircle className="w-5 h-5" />
            <span>Configuration saved successfully! Redirecting to network selection...</span>
          </div>
        )}

        <div className="config-grid">
          {/* Main Configuration */}
          <div className="space-y-6">
            
            {/* Basic Settings */}
            <div className="config-section">
              <div className="config-section-header">
                <Clock className="config-section-icon" />
                <h2 className="config-section-title">Basic Settings</h2>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">
                    Simulation Duration: {getDurationText(config.duration)}
                  </label>
                  <input
                    type="range"
                    min="300"
                    max="7200"
                    step="300"
                    value={config.duration}
                    onChange={(e) => handleConfigChange(null, 'duration', parseInt(e.target.value))}
                    className="config-range w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>5 min</span>
                    <span>2 hours</span>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="config-form-group">
                    <label className="config-label">Step Length (seconds)</label>
                    <select
                      value={config.stepLength}
                      onChange={(e) => handleConfigChange(null, 'stepLength', parseFloat(e.target.value))}
                      className="config-select"
                    >
                      <option value={0.1}>0.1s (Highest precision)</option>
                      <option value={0.5}>0.5s (High precision)</option>
                      <option value={1.0}>1.0s (Standard)</option>
                      <option value={2.0}>2.0s (Fast)</option>
                    </select>
                  </div>

                  <div className="config-form-group">
                    <label className="config-label">Random Seed</label>
                    <input
                      type="number"
                      value={config.randomSeed}
                      onChange={(e) => handleConfigChange(null, 'randomSeed', parseInt(e.target.value))}
                      className="config-input"
                      min="1"
                      max="999999"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Traffic Settings */}
            <div className="config-section">
              <div className="config-section-header">
                <Car className="config-section-icon" />
                <h2 className="config-section-title">Traffic Settings</h2>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">
                    Traffic Volume: {getTrafficVolumeText(config.trafficVolume)} ({Math.round(config.trafficVolume * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={config.trafficVolume}
                    onChange={(e) => handleConfigChange(null, 'trafficVolume', parseFloat(e.target.value))}
                    className="config-range w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Light</span>
                    <span>Heavy</span>
                  </div>
                </div>

                {/* OSM Scenario Settings */}
                <div className="config-form-group">
                  <label className="config-label">
                    Traffic Density (OSM Scenarios): {Math.round(config.trafficDensity * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="2.0"
                    step="0.1"
                    value={config.trafficDensity}
                    onChange={(e) => handleConfigChange(null, 'trafficDensity', parseFloat(e.target.value))}
                    className="config-range w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Light (10%)</span>
                    <span>Normal (100%)</span>
                    <span>Heavy (200%)</span>
                  </div>
                  <p className="config-help-text">
                    Scales traffic density for OSM Web Wizard scenarios while preserving realistic patterns
                  </p>
                </div>

                <div className="space-y-3">
                  <h3 className="font-medium text-gray-900">OSM Vehicle Types</h3>
                  <p className="config-help-text">
                    For OSM scenarios: Select which vehicle types to include. Disabled types will be excluded from simulation.
                  </p>
                  
                  {['passenger', 'bus', 'truck', 'motorcycle'].map((vehicleType) => (
                    <div key={vehicleType} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {vehicleType === 'passenger' && <Car className="w-5 h-5 text-blue-600" />}
                        {vehicleType === 'truck' && <Truck className="w-5 h-5 text-green-600" />}
                        {vehicleType === 'bus' && <Car className="w-5 h-5 text-orange-600" />}
                        {vehicleType === 'motorcycle' && <Car className="w-5 h-5 text-red-600" />}
                        <span className="font-medium capitalize">{vehicleType}</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={config.enabledVehicles.includes(vehicleType)}
                        onChange={(e) => handleEnabledVehicleChange(vehicleType, e.target.checked)}
                        className="config-checkbox"
                      />
                    </div>
                  ))}
                </div>

                <div className="space-y-3">
                  <h3 className="font-medium text-gray-900">Generated Network Vehicle Types</h3>
                  <p className="config-help-text">
                    For generated networks: Configure vehicle distribution and speeds
                  </p>
                  
                  {Object.entries(config.vehicleTypes).map(([type, settings]) => (
                    <div key={type} className="config-vehicle-type">
                      <div className="config-vehicle-info">
                        {type === 'passenger' && <Car className="config-vehicle-icon" />}
                        {type === 'truck' && <Truck className="config-vehicle-icon" />}
                        {type === 'bus' && <Car className="config-vehicle-icon" />}
                        <div>
                          <div className="font-medium capitalize">{type}</div>
                          <div className="config-help-text">Max Speed: {settings.maxSpeed} km/h</div>
                        </div>
                      </div>
                      <div className="config-vehicle-controls">
                        <input
                          type="checkbox"
                          checked={settings.enabled}
                          onChange={(e) => handleVehicleTypeChange(type, 'enabled', e.target.checked)}
                          className="config-checkbox"
                        />
                        <span className="config-help-text w-12">
                          {settings.percentage}%
                        </span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={settings.percentage}
                          onChange={(e) => handleVehicleTypeChange(type, 'percentage', parseInt(e.target.value))}
                          className="config-range w-20"
                          disabled={!settings.enabled}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Network Modifications */}
            <div className="config-section">
              <div className="config-section-header">
                <MapPin className="config-section-icon" />
                <h2 className="config-section-title">Network Modifications</h2>
              </div>
              <div className="space-y-4">
                
                {/* Speed Limits */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">Speed Limit Changes</h3>
                    <button
                      onClick={addSpeedLimit}
                      className="btn btn-outline btn-sm flex items-center space-x-1"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  
                  {config.speedLimits.length === 0 ? (
                    <p className="config-help-text">No speed limit changes configured</p>
                  ) : (
                    <div className="space-y-2">
                      {config.speedLimits.map((item) => (
                        <div key={item.id} className="flex items-center space-x-2 p-2 border rounded">
                          <input
                            type="text"
                            placeholder="Edge ID (e.g., edge1)"
                            value={item.edgeId}
                            onChange={(e) => updateSpeedLimit(item.id, 'edgeId', e.target.value)}
                            className="config-input flex-1"
                          />
                          <input
                            type="number"
                            placeholder="Speed"
                            value={item.speedLimit}
                            onChange={(e) => updateSpeedLimit(item.id, 'speedLimit', parseInt(e.target.value))}
                            className="config-input w-20"
                            min="10"
                            max="200"
                          />
                          <span className="text-sm text-gray-500">km/h</span>
                          <button
                            onClick={() => removeSpeedLimit(item.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Minus className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Road Closures */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">Road Closures</h3>
                    <button
                      onClick={addRoadClosure}
                      className="btn btn-outline btn-sm flex items-center space-x-1"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  
                  {config.roadClosures.length === 0 ? (
                    <p className="config-help-text">No road closures configured</p>
                  ) : (
                    <div className="space-y-2">
                      {config.roadClosures.map((item) => (
                        <div key={item.id} className="flex items-center space-x-2 p-2 border rounded">
                          <input
                            type="text"
                            placeholder="Edge ID"
                            value={item.edgeId}
                            onChange={(e) => updateRoadClosure(item.id, 'edgeId', e.target.value)}
                            className="config-input flex-1"
                          />
                          <input
                            type="number"
                            placeholder="Start"
                            value={item.startTime}
                            onChange={(e) => updateRoadClosure(item.id, 'startTime', parseInt(e.target.value))}
                            className="config-input w-20"
                            min="0"
                          />
                          <span className="text-xs text-gray-500">to</span>
                          <input
                            type="number"
                            placeholder="End"
                            value={item.endTime}
                            onChange={(e) => updateRoadClosure(item.id, 'endTime', parseInt(e.target.value))}
                            className="config-input w-20"
                            min="0"
                          />
                          <span className="text-sm text-gray-500">sec</span>
                          <button
                            onClick={() => removeRoadClosure(item.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Minus className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="config-section">
              <div className="config-section-header">
                <Settings className="config-section-icon" />
                <h2 className="config-section-title">Advanced Settings</h2>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="config-form-group">
                  <label className="config-label">Route Choice Model</label>
                  <select
                    value={config.routeChoiceModel}
                    onChange={(e) => handleConfigChange(null, 'routeChoiceModel', e.target.value)}
                    className="config-select"
                  >
                    <option value="gawron">Gawron</option>
                    <option value="logit">Logit</option>
                    <option value="lohse">Lohse</option>
                  </select>
                </div>

                <div className="config-form-group">
                  <label className="config-label">Lane Changing Model</label>
                  <select
                    value={config.laneChangingModel}
                    onChange={(e) => handleConfigChange(null, 'laneChangingModel', e.target.value)}
                    className="config-select"
                  >
                    <option value="LC2013">LC2013</option>
                    <option value="SL2015">SL2015</option>
                    <option value="DK2008">DK2008</option>
                  </select>
                </div>

                <div className="config-form-group">
                  <label className="config-label">Car Following Model</label>
                  <select
                    value={config.carFollowingModel}
                    onChange={(e) => handleConfigChange(null, 'carFollowingModel', e.target.value)}
                    className="config-select"
                  >
                    <option value="Krauss">Krauss</option>
                    <option value="IDM">IDM</option>
                    <option value="EIDM">EIDM</option>
                    <option value="PWagner2009">PWagner2009</option>
                  </select>
                </div>

                <div className="config-form-group">
                  <label className="config-label">Output Frequency (seconds)</label>
                  <input
                    type="number"
                    value={config.outputFrequency}
                    onChange={(e) => handleConfigChange(null, 'outputFrequency', parseInt(e.target.value))}
                    className="config-input"
                    min="1"
                    max="300"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.enableVisualization}
                    onChange={(e) => handleConfigChange(null, 'enableVisualization', e.target.checked)}
                    className="config-checkbox"
                  />
                  <span className="config-label">Enable Visualization</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.saveTrajectories}
                    onChange={(e) => handleConfigChange(null, 'saveTrajectories', e.target.checked)}
                    className="config-checkbox"
                  />
                  <span className="config-label">Save Vehicle Trajectories</span>
                </label>
              </div>
            </div>
          </div>

          {/* Configuration Summary Sidebar */}
          <div className="space-y-6">
            <div className="config-section">
              <div className="config-section-header">
                <h3 className="config-section-title">Configuration Summary</h3>
              </div>
              <div className="space-y-3">
                <div className="text-sm">
                  <div className="font-medium text-gray-900">Duration</div>
                  <div className="text-gray-600">{getDurationText(config.duration)}</div>
                </div>
                
                <div className="text-sm">
                  <div className="font-medium text-gray-900">Traffic Volume</div>
                  <div className="text-gray-600">{getTrafficVolumeText(config.trafficVolume)}</div>
                </div>
                
                <div className="text-sm">
                  <div className="font-medium text-gray-900">Vehicle Types</div>
                  <div className="text-gray-600">
                    {Object.entries(config.vehicleTypes)
                      .filter(([_, settings]) => settings.enabled)
                      .map(([type, settings]) => `${type.charAt(0).toUpperCase() + type.slice(1)}: ${settings.percentage}%`)
                      .join(', ')
                    }
                  </div>
                </div>
                
                <div className="text-sm">
                  <div className="font-medium text-gray-900">Modifications</div>
                  <div className="text-gray-600">
                    {config.speedLimits.length} speed limits, {config.roadClosures.length} closures
                  </div>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="config-section">
              <div className="config-section-header">
                <Info className="config-section-icon" />
                <h3 className="config-section-title">Configuration Tips</h3>
              </div>
              <div>
                <ul className="config-help-text space-y-2">
                  <li>• Configurations are applied to your selected network</li>
                  <li>• Original network files are never modified</li>
                  <li>• Use Edge IDs from your network for modifications</li>
                  <li>• Higher traffic volume may cause congestion</li>
                  <li>• Save before proceeding to network selection</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="config-buttons">
          <div className="config-nav-buttons">
            <Link to="/" className="btn btn-secondary flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Home</span>
            </Link>
          </div>
          
          <div className="config-action-buttons">
            <button
              onClick={handleSaveConfiguration}
              disabled={saving}
              className="btn btn-primary flex items-center space-x-2"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save & Continue</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationSetupPage;
