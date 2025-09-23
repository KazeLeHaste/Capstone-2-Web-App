/**
 * Simplified Configuration Page Component
 * 
 * Contains only Basic & Essential Simulation Configuration Options.
 * Users set core SUMO parameters before selecting a network.
 * Parameters are correctly applied to SUMO configuration files when simulation is launched.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Clock, 
  Car, 
  Zap,
  Save,
  ArrowLeft,
  Info,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  RefreshCw,
  Bus,
  Truck,
  Bike,
  User
} from 'lucide-react';
import { api } from '../utils/apiClient';

// Helper function to get vehicle type icon
const getVehicleTypeIcon = (vehicleType) => {
  const iconProps = { size: 20, strokeWidth: 2 };
  
  switch (vehicleType) {
    case 'passenger':
      return <Car {...iconProps} />;
    case 'bus':
      return <Bus {...iconProps} />;
    case 'truck':
      return <Truck {...iconProps} />;
    case 'motorcycle':
      return <Bike {...iconProps} />;
    case 'bicycle':
      return <Bike {...iconProps} />;
    case 'pedestrian':
      return <User {...iconProps} />;
    default:
      return <Car {...iconProps} />;
  }
};

const ConfigurationPage = ({ socket }) => {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Simplified configuration state with only essential SUMO parameters
  const [config, setConfig] = useState({
    // Core SUMO Time Parameters (as per SUMO documentation --begin, --end, --step-length)
    beginTime: 0, // Start time in seconds (SUMO --begin parameter) - automatically set to 0
    endTime: 1800, // End time in seconds (SUMO --end parameter) - default 30 minutes
    stepLength: 1.0, // Simulation time step in seconds (1.0 = normal time progression)
    
    // GUI Simulation Control Parameters
    simulationDelay: 50, // Delay between visual updates in milliseconds (SUMO-GUI --delay parameter)
    
    // Traffic Scale Control (SUMO --scale parameter)
    trafficScale: 1.0, // Traffic scale factor - 1.0 = normal traffic, 2.0 = double traffic, etc.
    
    // Vehicle Types Configuration - Controls which vehicle types are included in simulation
    vehicleTypes: {
      passenger: { enabled: true, name: 'Private Vehicles' },
      bus: { enabled: true, name: 'Buses/Jeepneys' },
      truck: { enabled: true, name: 'Trucks' },
      motorcycle: { enabled: true, name: 'Motorcycles' }
    },
    
  });

  useEffect(() => {
    // Generate a unique session ID for this configuration session
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  }, []);

  // Configuration change handler for vehicle types
  const handleVehicleTypeChange = (vehicleType, enabled) => {
    setConfig(prev => ({
      ...prev,
      vehicleTypes: {
        ...prev.vehicleTypes,
        [vehicleType]: {
          ...prev.vehicleTypes[vehicleType],
          enabled: enabled
        }
      }
    }));
  };



  // Simplified configuration change handler for basic parameters only
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Save configuration and navigate to network selection
  const handleSaveConfiguration = async () => {
    if (!sessionId) {
      setError('Session ID not available');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      // Prepare configuration data with SUMO-compatible parameter names
      const configData = {
        sessionId,
        timestamp: new Date().toISOString(),
        config: {
          // Core SUMO Time parameters (mapped to SUMO command-line arguments)
          sumo_begin: config.beginTime,     // Maps to --begin parameter (always 0)
          sumo_end: config.endTime,         // Maps to --end parameter  
          sumo_step_length: config.stepLength, // Maps to --step-length parameter
          
          // GUI Control parameters
          sumo_gui_delay: config.simulationDelay, // Maps to --delay parameter for SUMO-GUI
          
          // Traffic Scale Control (SUMO --scale parameter)
          traffic_scale: config.trafficScale, // Traffic scale factor for SUMO
          
          // Vehicle Types Configuration (maps to enabled vehicles in route selection)
          enabledVehicles: Object.keys(config.vehicleTypes).filter(
            type => config.vehicleTypes[type].enabled
          ), // Maps to vehicle type filtering in routes
          vehicleTypes: config.vehicleTypes, // Keep vehicle type configuration for frontend reference
          
          // Keep original config for frontend reference
          original_config: config
        }
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

  // Helper function to format time duration for display
  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m${remainingSeconds > 0 ? ` ${remainingSeconds}s` : ''}`;
    } else if (minutes > 0) {
      return `${minutes}m${remainingSeconds > 0 ? ` ${remainingSeconds}s` : ''}`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  // Helper function to get vehicle type information from SUMO documentation
  const getVehicleTypeInfo = (vehicleType) => {
    const vehicleTypeInfo = {
      passenger: {
        maxSpeed: '55.6 m/s (200 km/h)',
        length: '5.0 m',
        access: 'All roads except restricted',
        description: 'Standard passenger cars - most common vehicle type with access to regular roads'
      },
      bus: {
        maxSpeed: '27.8 m/s (100 km/h)',
        length: '12.0 m',
        access: 'Roads + bus lanes',
        description: 'Urban line traffic - larger public utility vehicles'
      },
      truck: {
        maxSpeed: '25.0 m/s (90 km/h)',
        length: '7.5 m',
        access: 'Roads (speed restricted)',
        description: 'Commercial freight vehicles - heavier vehicles with different speed limits on some roads'
      },
      motorcycle: {
        maxSpeed: '55.6 m/s (200 km/h)',
        length: '2.5 m',
        access: 'Most roads (no pedestrian)',
        description: 'Two-wheeled motorized vehicles - smaller, more agile with different lane permissions'
      }
    };
    
    return vehicleTypeInfo[vehicleType] || {
      maxSpeed: 'Variable',
      length: 'Variable',
      access: 'Depends on type',
      description: 'Vehicle type information not available'
    };
  };

  return (
    <div className="config-page">
      <div className="config-container">
        {/* Header */}
        <div className="config-header">
          <h1 className="config-title">
            Basic Simulation Configuration
          </h1>
          <p className="config-subtitle">
            Configure essential simulation parameters. These settings will be applied when you launch your simulation with SUMO GUI.
          </p>
          
          {sessionId && (
            <div className="text-sm text-secondary mt-2">
              Session ID: <code className="code-block px-2 py-1 rounded">{sessionId}</code>
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

        {/* Simplified Configuration Form */}
        <div className="config-grid">
          <div className="space-y-6">
            
            {/* Essential Simulation Settings */}
            <div className="config-section">
              <div className="config-section-header">
                <Clock className="config-section-icon" />
                <h2 className="config-section-title">Simulation Duration</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-muted" />
                  <span className="config-help-text">Set the time period for your simulation (starts at 0 seconds)</span>
                </div>
              </div>
              <div className="space-y-4">
                {/* End Time */}
                <div className="config-form-group">
                  <label className="config-label">
                    Simulation Duration: {formatDuration(config.endTime)}
                  </label>
                  <input
                    type="range"
                    min="300"
                    max="7200"
                    step="300"
                    value={config.endTime}
                    onChange={(e) => handleConfigChange('endTime', parseInt(e.target.value))}
                    className="config-range w-full"
                  />
                  <div className="flex justify-between text-xs text-muted mt-1">
                    <span>5 min</span>
                    <span>2 hours</span>
                  </div>
                </div>
                
                {/* Custom End Time Input */}
                <div className="config-form-group">
                  <label className="config-label">Or specify exact duration (seconds)</label>
                  <input
                    type="number"
                    value={config.endTime}
                    onChange={(e) => handleConfigChange('endTime', parseInt(e.target.value) || 1800)}
                    className="config-input"
                    min="60"
                    max="86400"
                    step="60"
                    placeholder="1800"
                  />
                  <span className="config-help-text">Common values: 1800 (30 min), 3600 (1 hour), 7200 (2 hours)</span>
                </div>
              </div>
            </div>

            {/* Time Step Configuration */}
            <div className="config-section">
              <div className="config-section-header">
                <Zap className="config-section-icon" />
                <h2 className="config-section-title">Simulation Time Progression</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-muted" />
                  <span className="config-help-text">Controls how simulation time advances</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">Step Length (seconds)</label>
                  <select
                    value={config.stepLength}
                    onChange={(e) => handleConfigChange('stepLength', parseFloat(e.target.value))}
                    className="config-select"
                  >
                    <option value={0.1}>0.1s (Slow motion - high precision)</option>
                    <option value={0.5}>0.5s (Detailed simulation)</option>
                    <option value={1.0}>1.0s (Normal speed - default)</option>
                    <option value={2.0}>2.0s (Fast simulation)</option>
                  </select>
                  <span className="config-help-text">
                    Controls simulation time progression. 1.0s = normal time, 0.1s = detailed updates every 0.1 sim seconds (more vehicle position updates).
                  </span>
                </div>
              </div>
            </div>

            {/* Simulation Display Speed Control */}
            <div className="config-section">
              <div className="config-section-header">
                <RefreshCw className="config-section-icon" />
                <h2 className="config-section-title">Visual Display Speed</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-muted" />
                  <span className="config-help-text">Control GUI animation speed (visual only)</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">GUI Update Delay (milliseconds)</label>
                  <input
                    type="number"
                    value={config.simulationDelay}
                    onChange={(e) => handleConfigChange('simulationDelay', parseInt(e.target.value) || 0)}
                    className="config-input"
                    min="0"
                    max="5000"
                    step="50"
                    placeholder="50"
                  />
                  <span className="config-help-text">
                    Controls visual animation speed only. Higher delay = slower visual playback (more real-time elapsed). Does not affect simulation time or logic - only viewing speed.
                  </span>
                </div>
              </div>
            </div>



            {/* Traffic Scale Control */}
            <div className="config-section">
              <div className="config-section-header">
                <Car className="config-section-icon" />
                <h2 className="config-section-title">Traffic Scale</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-muted" />
                  <span className="config-help-text">Control the traffic density multiplier in the simulation</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">
                    Traffic Scale Factor
                    <span className="config-help-text ml-2">Higher numbers = more vehicles</span>
                  </label>
                  <input
                    type="number"
                    value={config.trafficScale}
                    onChange={(e) => handleConfigChange('trafficScale', parseFloat(e.target.value) || 1.0)}
                    className="config-input"
                    min="0.1"
                    max="10.0"
                    step="0.1"
                    placeholder="1.0"
                  />
                  <span className="config-help-text">
                    Traffic density multiplier. 1.0 = normal traffic, 2.0 = double traffic, 0.5 = half traffic. Range: 0.1-10.0.
                  </span>
                  <div className="mt-2 p-3 info-block rounded-lg">
                    <div className="flex items-center text-sm text-info-dark">
                      <Info className="w-4 h-4 mr-2" />
                      <div>
                        <div><strong>Current Setting:</strong> {config.trafficScale}x traffic scale</div>
                        <div className="text-info">
                          {config.trafficScale <= 0.5 ? "Light traffic" :
                           config.trafficScale <= 1.5 ? "Normal traffic" :
                           config.trafficScale <= 3.0 ? "Heavy traffic" :
                           "Very heavy traffic"}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Vehicle Types Selection */}
            <div className="config-section">
              <div className="config-section-header">
                <Car className="config-section-icon" />
                <h2 className="config-section-title">Vehicle Types</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-muted" />
                  <span className="config-help-text">Select which vehicle types to include in the simulation</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-info-panel">
                  <div className="info-panel-header">
                    <Info className="info-panel-icon" />
                    <div className="info-panel-content">
                      <p className="text-sm text-secondary">
                        Vehicle types correspond to different route files and SUMO vClass definitions. 
                        Each type has different characteristics like size, speed limits, and lane permissions.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Vehicle Type Checkboxes */}
                <div className="config-vehicle-types">
                  {Object.entries(config.vehicleTypes).map(([vehicleType, typeConfig]) => {
                    const enabled = typeConfig.enabled;
                    const vehicleInfo = getVehicleTypeInfo(vehicleType);
                    
                    return (
                      <div key={vehicleType} className={`config-vehicle-type ${enabled ? 'enabled' : ''}`}>
                        <div className="config-vehicle-checkbox-wrapper">
                          <input
                            type="checkbox"
                            id={`vehicle-${vehicleType}`}
                            checked={enabled}
                            onChange={(e) => handleVehicleTypeChange(vehicleType, e.target.checked)}
                            className="config-checkbox"
                          />
                        </div>
                        
                        <div className="config-vehicle-info">
                          <div className={`config-vehicle-icon ${vehicleType}`}>
                            {getVehicleTypeIcon(vehicleType)}
                          </div>
                          
                          <div className="config-vehicle-content">
                            <label htmlFor={`vehicle-${vehicleType}`} className="config-vehicle-label">
                              {typeConfig.name}
                              <span className="config-vehicle-type-code">{vehicleType}</span>
                            </label>
                            
                            <div className="config-vehicle-specs">
                              <div className="config-vehicle-spec">
                                <span className="config-vehicle-spec-label">Max Speed</span>
                                <span className="config-vehicle-spec-value">{vehicleInfo.maxSpeed}</span>
                              </div>
                              <div className="config-vehicle-spec">
                                <span className="config-vehicle-spec-label">Length</span>
                                <span className="config-vehicle-spec-value">{vehicleInfo.length}</span>
                              </div>
                              <div className="config-vehicle-spec">
                                <span className="config-vehicle-spec-label">Access</span>
                                <span className="config-vehicle-spec-value">{vehicleInfo.access}</span>
                              </div>
                            </div>
                            
                            <div className="config-vehicle-description">
                              {vehicleInfo.description}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Selected Types Summary */}
                <div className="config-vehicle-summary">
                  <div className="config-vehicle-summary-header">
                    <Car className="config-vehicle-summary-icon" />
                    <h3 className="config-vehicle-summary-title">Vehicle Selection Summary</h3>
                  </div>
                  
                  <div className="config-vehicle-summary-content">
                    <div className="config-vehicle-summary-row">
                      <span className="config-vehicle-summary-label">Selected Types:</span>
                      <span className="config-vehicle-summary-value">
                        {Object.entries(config.vehicleTypes)
                          .filter(([_, typeConfig]) => typeConfig.enabled)
                          .map(([type, _]) => config.vehicleTypes[type].name)
                          .join(', ') || 'None selected'}
                      </span>
                    </div>
                    
                    {Object.values(config.vehicleTypes).filter(t => t.enabled).length === 0 ? (
                      <div className="config-vehicle-summary-warning">
                        <AlertCircle />
                        <span>Warning: No vehicle types selected - simulation may be empty</span>
                      </div>
                    ) : (
                      <div className="config-vehicle-summary-row">
                        <span className="config-vehicle-summary-label">Route Files:</span>
                        <div className="config-vehicle-route-files">
                          {Object.keys(config.vehicleTypes)
                            .filter(t => config.vehicleTypes[t].enabled)
                            .map(t => `osm.${t}.rou.xml`)
                            .join(', ')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>



            {/* Future Feature Placeholders - Commented for now */}
            {/*
            <div className="config-section">
              <div className="config-section-header">
                <Car className="config-section-icon" />
                <h2 className="config-section-title">Traffic Volume (Future Feature)</h2>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">Number of Vehicles</label>
                  <input
                    type="number"
                    value={config.vehicleCount || ''}
                    onChange={(e) => handleConfigChange('vehicleCount', parseInt(e.target.value) || null)}
                    className="config-input"
                    placeholder="Leave empty to use route file defaults"
                    disabled
                  />
                  <span className="config-help-text">
                    Coming soon: Ability to modify vehicle count from route files
                  </span>
                </div>
              </div>
            </div>
            */}

            {/* Information Panel */}
            <div className="config-info-panel">
              <div className="info-panel-header">
                <Info className="info-panel-icon" />
                <div className="info-panel-content">
                  <h3 className="info-panel-title">What happens next?</h3>
                  <ul className="list-spaced">
                    <li>Your configuration will be saved to a session</li>
                    <li>You'll select a network file to apply these settings</li>
                    <li>Route files are automatically matched to networks</li>
                    <li>SUMO GUI will launch in game mode for interactive simulation</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Configuration Preview Panel */}
          <div className="config-preview-panel">
            <h3 className="config-preview-title">Configuration Summary</h3>
            <div className="config-preview-content">
              <div className="config-preview-item">
                <span className="config-preview-label">Start Time:</span>
                <span className="config-preview-value">0s (fixed)</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Duration:</span>
                <span className="config-preview-value">{formatDuration(config.endTime)}</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Time Step:</span>
                <span className="config-preview-value">{config.stepLength}s per step</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">GUI Delay:</span>
                <span className="config-preview-value">{config.simulationDelay}ms</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Traffic Scale:</span>
                <span className="config-preview-value">{config.trafficScale}x</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Vehicle Types:</span>
                <span className="config-preview-value">
                  {Object.values(config.vehicleTypes).filter(t => t.enabled).length} selected
                </span>
              </div>
            </div>

            {/* Vehicle Types Detail */}
            <div className="mt-3 pt-3 border-t border-default">
              <h4 className="text-sm font-medium text-secondary mb-2">Enabled Vehicle Types:</h4>
              <div className="space-y-1">
                {Object.entries(config.vehicleTypes)
                  .filter(([_, typeConfig]) => typeConfig.enabled)
                  .map(([vehicleType, typeConfig]) => (
                    <div key={vehicleType} className="text-xs text-secondary flex justify-between">
                      <span>{typeConfig.name}</span>
                      <span className="text-muted">osm.{vehicleType}.rou.xml</span>
                    </div>
                  ))
                }
                {Object.values(config.vehicleTypes).filter(t => t.enabled).length === 0 && (
                  <div className="text-xs text-error">⚠ No vehicle types selected</div>
                )}
              </div>
            </div>

            {/* SUMO Command Preview */}
            <div className="config-command-preview">
              <h4 className="text-sm font-medium text-gray-700 mb-2">SUMO Parameters:</h4>
              <div className="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono">
                --begin {config.beginTime} --end {config.endTime} --step-length {config.stepLength} --delay {config.simulationDelay} --scale {config.trafficScale}
              </div>
              <div className="mt-2 text-xs text-gray-600 space-y-1">
                <div>Traffic scale: {config.trafficScale}x multiplier</div>
                <div>Vehicle types: {Object.keys(config.vehicleTypes).filter(t => config.vehicleTypes[t].enabled).length} enabled 
                  ({Object.keys(config.vehicleTypes).filter(t => config.vehicleTypes[t].enabled).join(', ') || 'none'})
                </div>
                <div>Traffic lights: Default behavior (uses network configuration)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="config-actions">
          <div className="config-back-button">
            <Link
              to="/"
              className="btn btn-secondary flex items-center space-x-2"
            >
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

export default ConfigurationPage;
