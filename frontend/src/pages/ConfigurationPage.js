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
    beginTime: 0, // Start time in seconds (SUMO --begin parameter)
    endTime: 1800, // End time in seconds (SUMO --end parameter) - default 30 minutes
    stepLength: 1.0, // Time step in seconds (SUMO --step-length parameter) - default 1.0s
    
    // Core SUMO Processing Parameters
    timeToTeleport: 300, // Time to teleport stuck vehicles in seconds (SUMO --time-to-teleport parameter) - default 300s
    
    // Traffic Intensity Control (SUMO Calibrator/Flow Parameters)
    trafficIntensity: 1.0, // Traffic intensity multiplier (1.0 = normal, 2.0 = double traffic, 0.5 = half traffic)
    
    // Optional Traffic Volume Control (if supported by backend)
    // This would require backend logic to modify route files or vehicle counts
    vehicleCount: null, // Optional: number of vehicles (requires route file modification)
    
    // Vehicle Types Configuration - Controls which vehicle types are included in simulation
    vehicleTypes: {
      passenger: { enabled: true, name: 'Passenger Cars' },
      bus: { enabled: true, name: 'Buses' },
      truck: { enabled: true, name: 'Trucks' },
      motorcycle: { enabled: true, name: 'Motorcycles' }
    },
    
    // Traffic Control Configuration - Controls traffic light behavior
    trafficControl: {
      method: 'fixed', // 'fixed' for static timer or 'adaptive' for actuated
      globalMode: true, // true = apply to all intersections, false = per-intersection control
      fixedTimer: {
        greenPhase: 30, // Green phase duration in seconds
        yellowPhase: 3, // Yellow phase duration in seconds
        redPhase: 30,   // Red phase duration in seconds (for cross traffic)
        allRedPhase: 2  // All-red phase duration in seconds
      },
      adaptive: {
        minGreenTime: 5,    // Minimum green time in seconds
        maxGreenTime: 60,   // Maximum green time in seconds
        detectorSensitivity: 1.0, // Detector sensitivity (0.5 = less sensitive, 2.0 = more sensitive)
        jamThreshold: 30,   // Jam threshold in vehicles/hour/lane
        phaseExtension: 5   // Phase extension time in seconds
      }
    },
    
    // Future extensibility placeholders (commented out for now)
    // trafficDensity: 1.0, // For OSM scenarios - multiply existing vehicle counts
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

  // Configuration change handler for traffic control
  const handleTrafficControlChange = (category, key, value) => {
    setConfig(prev => ({
      ...prev,
      trafficControl: {
        ...prev.trafficControl,
        [category]: category === 'method' || category === 'globalMode' ? value : {
          ...prev.trafficControl[category],
          [key]: value
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
          sumo_begin: config.beginTime,     // Maps to --begin parameter
          sumo_end: config.endTime,         // Maps to --end parameter  
          sumo_step_length: config.stepLength, // Maps to --step-length parameter
          sumo_time_to_teleport: config.timeToTeleport, // Maps to --time-to-teleport parameter
          
          // Traffic Intensity Control (for SUMO calibrators and flow generation)
          sumo_traffic_intensity: config.trafficIntensity, // Maps to flow rate multiplier in calibrators
          
          // Vehicle Types Configuration (maps to enabled vehicles in route selection)
          enabledVehicles: Object.keys(config.vehicleTypes).filter(
            type => config.vehicleTypes[type].enabled
          ), // Maps to vehicle type filtering in routes
          vehicleTypes: config.vehicleTypes, // Keep vehicle type configuration for frontend reference
          
          // Traffic Control Configuration (maps to traffic light XML generation)
          trafficControl: config.trafficControl, // Complete traffic control configuration for backend
          
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
        description: 'Urban line traffic - larger vehicles with access to dedicated bus lanes and stops'
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

        {/* Simplified Configuration Form */}
        <div className="config-grid">
          <div className="space-y-6">
            
            {/* Essential Simulation Settings */}
            <div className="config-section">
              <div className="config-section-header">
                <Clock className="config-section-icon" />
                <h2 className="config-section-title">Simulation Duration</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-gray-400" />
                  <span className="config-help-text">Set the time period for your simulation</span>
                </div>
              </div>
              <div className="space-y-4">
                {/* Start Time (Usually 0) */}
                <div className="config-form-group">
                  <label className="config-label">
                    Start Time (seconds)
                    <span className="config-help-text ml-2">Usually starts from 0</span>
                  </label>
                  <input
                    type="number"
                    value={config.beginTime}
                    onChange={(e) => handleConfigChange('beginTime', parseInt(e.target.value) || 0)}
                    className="config-input"
                    min="0"
                    max="86400"
                    step="60"
                    placeholder="0"
                  />
                </div>

                {/* End Time */}
                <div className="config-form-group">
                  <label className="config-label">
                    End Time: {formatDuration(config.endTime)}
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
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>5 min</span>
                    <span>2 hours</span>
                  </div>
                </div>
                
                {/* Custom End Time Input */}
                <div className="config-form-group">
                  <label className="config-label">Or specify exact end time (seconds)</label>
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
                <h2 className="config-section-title">Time Step</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-gray-400" />
                  <span className="config-help-text">Simulation accuracy vs. performance</span>
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
                    <option value={0.1}>0.1s (Highest precision - slower)</option>
                    <option value={0.5}>0.5s (High precision)</option>
                    <option value={1.0}>1.0s (Standard - recommended)</option>
                    <option value={2.0}>2.0s (Fast - less precise)</option>
                  </select>
                  <span className="config-help-text">
                    Smaller values = more accurate but slower simulation. 1.0s is recommended for most cases.
                  </span>
                </div>
              </div>
            </div>

            {/* Simulation Behavior */}
            <div className="config-section">
              <div className="config-section-header">
                <Car className="config-section-icon" />
                <h2 className="config-section-title">Simulation Behavior</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-gray-400" />
                  <span className="config-help-text">How the simulation handles stuck vehicles</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">
                    Time to Teleport (seconds)
                    <span className="config-help-text ml-2">Time before stuck vehicles are teleported</span>
                  </label>
                  <input
                    type="number"
                    value={config.timeToTeleport}
                    onChange={(e) => handleConfigChange('timeToTeleport', parseInt(e.target.value) || 300)}
                    className="config-input"
                    min="60"
                    max="3600"
                    step="30"
                    placeholder="300"
                  />
                  <span className="config-help-text">
                    Default: 300 seconds (5 minutes). Set to -1 to disable teleporting.
                  </span>
                </div>
              </div>
            </div>

            {/* Traffic Intensity Control */}
            <div className="config-section">
              <div className="config-section-header">
                <RefreshCw className="config-section-icon" />
                <h2 className="config-section-title">Traffic Intensity</h2>
                <div className="config-section-help">
                  <HelpCircle className="w-4 h-4 text-gray-400" />
                  <span className="config-help-text">Control the density of traffic in the simulation</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-form-group">
                  <label className="config-label">
                    Traffic Intensity Multiplier
                    <span className="config-help-text ml-2">1.0 = normal traffic, 2.0 = double traffic, 0.5 = half traffic</span>
                  </label>
                  <input
                    type="number"
                    value={config.trafficIntensity}
                    onChange={(e) => handleConfigChange('trafficIntensity', parseFloat(e.target.value) || 1.0)}
                    className="config-input"
                    min="0.1"
                    max="5.0"
                    step="0.1"
                    placeholder="1.0"
                  />
                  <span className="config-help-text">
                    Multiplies the base traffic volume. Range: 0.1x to 5.0x normal traffic.
                  </span>
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center text-sm text-blue-700">
                      <Info className="w-4 h-4 mr-2" />
                      <div>
                        <div><strong>Current Setting:</strong> {(config.trafficIntensity * 100).toFixed(0)}% of normal traffic</div>
                        <div className="text-blue-600">
                          {config.trafficIntensity < 0.8 ? "Light traffic conditions" :
                           config.trafficIntensity <= 1.2 ? "Normal traffic conditions" :
                           config.trafficIntensity <= 2.0 ? "Heavy traffic conditions" :
                           "Very heavy traffic conditions"}
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
                  <HelpCircle className="w-4 h-4 text-gray-400" />
                  <span className="config-help-text">Select which vehicle types to include in the simulation</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="config-info-panel">
                  <div className="info-panel-header">
                    <Info className="info-panel-icon" />
                    <div className="info-panel-content">
                      <p className="text-sm text-gray-700">
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

            {/* Traffic Control Configuration */}
            <div className="config-section">
              <div className="config-section-header">
                <Zap className="config-section-icon" />
                <h2 className="config-section-title">Traffic Control</h2>
                <HelpCircle 
                  className="config-help-icon" 
                  data-tooltip="Configure traffic light behavior at intersections"
                />
                <div className="config-section-description">
                  <span className="config-help-text">Configure traffic light control methods for intersections</span>
                </div>
              </div>
              
              <div className="space-y-6">
                {/* Traffic Control Method Selection */}
                <div className="config-form-group">
                  <label className="config-label">Control Method</label>
                  <div className="config-radio-group">
                    <label className="config-radio-option">
                      <input
                        type="radio"
                        name="trafficControlMethod"
                        value="fixed"
                        checked={config.trafficControl.method === 'fixed'}
                        onChange={(e) => handleTrafficControlChange('method', null, e.target.value)}
                        className="config-radio"
                      />
                      <div className="config-radio-content">
                        <span className="config-radio-title">Fixed Timer (Static)</span>
                        <span className="config-radio-description">
                          Traditional traffic lights with predetermined phase durations
                        </span>
                      </div>
                    </label>
                    
                    <label className="config-radio-option">
                      <input
                        type="radio"
                        name="trafficControlMethod"
                        value="adaptive"
                        checked={config.trafficControl.method === 'adaptive'}
                        onChange={(e) => handleTrafficControlChange('method', null, e.target.value)}
                        className="config-radio"
                      />
                      <div className="config-radio-content">
                        <span className="config-radio-title">Adaptive (Actuated)</span>
                        <span className="config-radio-description">
                          Smart traffic lights that adapt to real-time traffic conditions using sensors
                        </span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Global Mode Toggle */}
                <div className="config-form-group">
                  <div className="config-checkbox-container">
                    <label className="config-checkbox-label">
                      <input
                        type="checkbox"
                        checked={config.trafficControl.globalMode}
                        onChange={(e) => handleTrafficControlChange('globalMode', null, e.target.checked)}
                        className="config-checkbox"
                      />
                      <span className="config-checkbox-text">
                        Apply to all intersections
                        <small className="config-help-text block">
                          When enabled, these settings will be applied to all traffic lights in the network
                        </small>
                      </span>
                    </label>
                  </div>
                </div>

                {/* Fixed Timer Configuration */}
                {config.trafficControl.method === 'fixed' && (
                  <div className="config-subsection">
                    <h3 className="config-subsection-title">Fixed Timer Parameters</h3>
                    <div className="config-grid-2">
                      <div className="config-form-group">
                        <label className="config-label">
                          Green Phase Duration
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="5"
                          max="120"
                          value={config.trafficControl.fixedTimer.greenPhase}
                          onChange={(e) => handleTrafficControlChange('fixedTimer', 'greenPhase', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Duration of green light phase (5-120 seconds)</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          Yellow Phase Duration
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={config.trafficControl.fixedTimer.yellowPhase}
                          onChange={(e) => handleTrafficControlChange('fixedTimer', 'yellowPhase', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Duration of yellow light phase (1-10 seconds)</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          Red Phase Duration
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="5"
                          max="120"
                          value={config.trafficControl.fixedTimer.redPhase}
                          onChange={(e) => handleTrafficControlChange('fixedTimer', 'redPhase', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Duration of red light phase (5-120 seconds)</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          All-Red Phase Duration
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="10"
                          value={config.trafficControl.fixedTimer.allRedPhase}
                          onChange={(e) => handleTrafficControlChange('fixedTimer', 'allRedPhase', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Safety clearance time when all lights are red (0-10 seconds)</span>
                      </div>
                    </div>
                    
                    {/* Fixed Timer Preview */}
                    <div className="config-preview-box">
                      <div className="config-preview-header">
                        <Clock className="w-4 h-4" />
                        <span>Cycle Preview</span>
                      </div>
                      <div className="config-cycle-preview">
                        <span>Total Cycle Duration: {
                          config.trafficControl.fixedTimer.greenPhase + 
                          config.trafficControl.fixedTimer.yellowPhase + 
                          config.trafficControl.fixedTimer.redPhase + 
                          config.trafficControl.fixedTimer.allRedPhase
                        } seconds</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Adaptive Configuration */}
                {config.trafficControl.method === 'adaptive' && (
                  <div className="config-subsection">
                    <h3 className="config-subsection-title">Adaptive Parameters</h3>
                    <div className="config-grid-2">
                      <div className="config-form-group">
                        <label className="config-label">
                          Minimum Green Time
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="3"
                          max="30"
                          value={config.trafficControl.adaptive.minGreenTime}
                          onChange={(e) => handleTrafficControlChange('adaptive', 'minGreenTime', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Minimum duration for green phase regardless of demand</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          Maximum Green Time
                          <span className="config-unit">seconds</span>
                        </label>
                        <input
                          type="number"
                          min="20"
                          max="180"
                          value={config.trafficControl.adaptive.maxGreenTime}
                          onChange={(e) => handleTrafficControlChange('adaptive', 'maxGreenTime', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Maximum duration for green phase to prevent starvation</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          Detector Sensitivity
                          <span className="config-unit">multiplier</span>
                        </label>
                        <input
                          type="number"
                          min="0.1"
                          max="3.0"
                          step="0.1"
                          value={config.trafficControl.adaptive.detectorSensitivity}
                          onChange={(e) => handleTrafficControlChange('adaptive', 'detectorSensitivity', parseFloat(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Vehicle detection sensitivity (0.5 = less sensitive, 2.0 = more sensitive)</span>
                      </div>
                      
                      <div className="config-form-group">
                        <label className="config-label">
                          Jam Threshold
                          <span className="config-unit">vehicles</span>
                        </label>
                        <input
                          type="number"
                          min="5"
                          max="100"
                          value={config.trafficControl.adaptive.jamThreshold}
                          onChange={(e) => handleTrafficControlChange('adaptive', 'jamThreshold', parseInt(e.target.value))}
                          className="config-input"
                        />
                        <span className="config-help-text">Number of queued vehicles that triggers priority response</span>
                      </div>
                    </div>
                    
                    {/* Adaptive Configuration Info */}
                    <div className="config-info-box">
                      <Info className="w-4 h-4" />
                      <div>
                        <h4>How Adaptive Traffic Lights Work:</h4>
                        <ul className="list-disc list-inside text-sm space-y-1 mt-2">
                          <li>Sensors detect approaching vehicles and adjust timing dynamically</li>
                          <li>Phases extend when vehicles are detected, up to maximum duration</li>
                          <li>Empty approaches receive minimum green time to maintain flow</li>
                          <li>Jam threshold prevents excessive waiting times during congestion</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Traffic Control Summary */}
                <div className="config-summary-box">
                  <div className="config-summary-header">
                    <span className="config-summary-title">Traffic Control Summary</span>
                  </div>
                  <div className="config-summary-content">
                    <div className="config-summary-row">
                      <span className="config-summary-label">Method:</span>
                      <span className="config-summary-value">
                        {config.trafficControl.method === 'fixed' ? 'Fixed Timer (Static)' : 'Adaptive (Actuated)'}
                      </span>
                    </div>
                    <div className="config-summary-row">
                      <span className="config-summary-label">Application:</span>
                      <span className="config-summary-value">
                        {config.trafficControl.globalMode ? 'All intersections' : 'Per-intersection control'}
                      </span>
                    </div>
                    {config.trafficControl.method === 'fixed' && (
                      <div className="config-summary-row">
                        <span className="config-summary-label">Cycle Time:</span>
                        <span className="config-summary-value">
                          {config.trafficControl.fixedTimer.greenPhase + 
                           config.trafficControl.fixedTimer.yellowPhase + 
                           config.trafficControl.fixedTimer.redPhase + 
                           config.trafficControl.fixedTimer.allRedPhase} seconds
                        </span>
                      </div>
                    )}
                    {config.trafficControl.method === 'adaptive' && (
                      <div className="config-summary-row">
                        <span className="config-summary-label">Green Time Range:</span>
                        <span className="config-summary-value">
                          {config.trafficControl.adaptive.minGreenTime}-{config.trafficControl.adaptive.maxGreenTime} seconds
                        </span>
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
                <span className="config-preview-value">{config.beginTime}s</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">End Time:</span>
                <span className="config-preview-value">{config.endTime}s ({formatDuration(config.endTime)})</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Duration:</span>
                <span className="config-preview-value">{formatDuration(config.endTime - config.beginTime)}</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Step Length:</span>
                <span className="config-preview-value">{config.stepLength}s</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Time to Teleport:</span>
                <span className="config-preview-value">{config.timeToTeleport}s</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Traffic Intensity:</span>
                <span className="config-preview-value">{(config.trafficIntensity * 100).toFixed(0)}% ({config.trafficIntensity}x)</span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Vehicle Types:</span>
                <span className="config-preview-value">
                  {Object.values(config.vehicleTypes).filter(t => t.enabled).length} selected
                </span>
              </div>
              <div className="config-preview-item">
                <span className="config-preview-label">Traffic Control:</span>
                <span className="config-preview-value">
                  {config.trafficControl.method === 'fixed' ? 'Fixed Timer' : 'Adaptive'} 
                  ({config.trafficControl.globalMode ? 'Global' : 'Per-intersection'})
                </span>
              </div>
            </div>

            {/* Vehicle Types Detail */}
            <div className="mt-3 pt-3 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Enabled Vehicle Types:</h4>
              <div className="space-y-1">
                {Object.entries(config.vehicleTypes)
                  .filter(([_, typeConfig]) => typeConfig.enabled)
                  .map(([vehicleType, typeConfig]) => (
                    <div key={vehicleType} className="text-xs text-gray-600 flex justify-between">
                      <span>{typeConfig.name}</span>
                      <span className="text-gray-400">osm.{vehicleType}.rou.xml</span>
                    </div>
                  ))
                }
                {Object.values(config.vehicleTypes).filter(t => t.enabled).length === 0 && (
                  <div className="text-xs text-red-600">⚠ No vehicle types selected</div>
                )}
              </div>
            </div>

            {/* Traffic Control Detail */}
            <div className="mt-3 pt-3 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Traffic Control Configuration:</h4>
              <div className="space-y-1">
                <div className="text-xs text-gray-600 flex justify-between">
                  <span>Method:</span>
                  <span className="text-gray-800">
                    {config.trafficControl.method === 'fixed' ? 'Fixed Timer (Static)' : 'Adaptive (Actuated)'}
                  </span>
                </div>
                <div className="text-xs text-gray-600 flex justify-between">
                  <span>Application:</span>
                  <span className="text-gray-800">
                    {config.trafficControl.globalMode ? 'All intersections' : 'Per-intersection control'}
                  </span>
                </div>
                {config.trafficControl.method === 'fixed' && (
                  <>
                    <div className="text-xs text-gray-600 flex justify-between">
                      <span>Green Phase:</span>
                      <span className="text-gray-800">{config.trafficControl.fixedTimer.greenPhase}s</span>
                    </div>
                    <div className="text-xs text-gray-600 flex justify-between">
                      <span>Cycle Duration:</span>
                      <span className="text-gray-800">
                        {config.trafficControl.fixedTimer.greenPhase + 
                         config.trafficControl.fixedTimer.yellowPhase + 
                         config.trafficControl.fixedTimer.redPhase + 
                         config.trafficControl.fixedTimer.allRedPhase}s
                      </span>
                    </div>
                  </>
                )}
                {config.trafficControl.method === 'adaptive' && (
                  <>
                    <div className="text-xs text-gray-600 flex justify-between">
                      <span>Green Range:</span>
                      <span className="text-gray-800">
                        {config.trafficControl.adaptive.minGreenTime}-{config.trafficControl.adaptive.maxGreenTime}s
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 flex justify-between">
                      <span>Sensitivity:</span>
                      <span className="text-gray-800">{config.trafficControl.adaptive.detectorSensitivity}x</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* SUMO Command Preview */}
            <div className="config-command-preview">
              <h4 className="text-sm font-medium text-gray-700 mb-2">SUMO Parameters:</h4>
              <div className="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono">
                --begin {config.beginTime} --end {config.endTime} --step-length {config.stepLength} --time-to-teleport {config.timeToTeleport}
              </div>
              <div className="mt-2 text-xs text-gray-600 space-y-1">
                <div>Traffic intensity: {config.trafficIntensity}x multiplier applied via calibrators</div>
                <div>Vehicle types: {Object.keys(config.vehicleTypes).filter(t => config.vehicleTypes[t].enabled).length} enabled 
                  ({Object.keys(config.vehicleTypes).filter(t => config.vehicleTypes[t].enabled).join(', ') || 'none'})
                </div>
                <div>Traffic lights: {config.trafficControl.method === 'fixed' ? 'Static timer' : 'Actuated sensor'} control via additional files</div>
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
