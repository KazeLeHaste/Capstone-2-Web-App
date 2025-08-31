/**
 * Configuration Page Component
 * 
 * Allows users to configure simulation parameters including
 * scenario selection, timing, and traffic generation settings.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Settings, 
  Clock, 
  Car, 
  Truck, 
  Play, 
  Save, 
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  ArrowRight,
  ArrowLeft,
  FileText,
  Zap
} from 'lucide-react';
import { api } from '../utils/apiClient';

const ConfigurationPage = ({ socket, onLoadingChange }) => {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Configuration state
  const [config, setConfig] = useState({
    duration: 3600, // seconds
    stepLength: 1, // seconds
    randomSeed: 42,
    teleportTime: 300, // seconds
    vehicleTypes: {
      car: { enabled: true, percentage: 80 },
      truck: { enabled: true, percentage: 20 }
    },
    trafficDensity: 'medium', // low, medium, high
    customParams: {}
  });
  
  useEffect(() => {
    loadInitialData();
  }, []);
  
  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load selected network from previous step
      const networkData = localStorage.getItem('selected_network');
      if (networkData) {
        setSelectedNetwork(JSON.parse(networkData));
      }
      
      // Load available scenarios
      const response = await api.getScenarios();
      if (response.data.success) {
        setScenarios(response.data.scenarios);
        
        // Auto-select first scenario if available
        if (response.data.scenarios.length > 0) {
          setSelectedScenario(response.data.scenarios[0]);
        }
      } else {
        setError(response.data.error || 'Failed to load scenarios');
      }
    } catch (err) {
      setError('Unable to connect to server. Please check your connection.');
      console.error('Error loading configuration data:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
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
  
  const handleSaveConfiguration = async () => {
    if (!selectedScenario) {
      setError('Please select a scenario before saving configuration');
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      
      const configData = {
        network: selectedNetwork?.id,
        scenario: selectedScenario.id,
        config: config
      };
      
      // Store configuration for next step
      localStorage.setItem('simulation_config', JSON.stringify(configData));
      
      // Notify via socket if available
      if (socket) {
        socket.emit('config_updated', configData);
      }
      
      console.log('Configuration saved:', configData);
      
    } catch (err) {
      setError('Failed to save configuration');
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
  
  const getTrafficDensityConfig = (density) => {
    const configs = {
      low: { multiplier: 0.5, description: 'Light traffic, fewer vehicles' },
      medium: { multiplier: 1.0, description: 'Normal traffic conditions' },
      high: { multiplier: 1.5, description: 'Heavy traffic, more congestion' }
    };
    return configs[density] || configs.medium;
  };
  
  if (!selectedNetwork) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            No Network Selected
          </h1>
          <p className="text-gray-600 mb-8">
            Please select a network first before configuring the simulation.
          </p>
          <Link to="/network" className="btn btn-primary">
            Select Network
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="config-page">
      <div className="config-container">
        {/* Header */}
        <div className="config-header">
          <h1 className="config-title">
            Configure Simulation
          </h1>
          <p className="config-subtitle">
            Set up simulation parameters for network: <strong>{selectedNetwork.name}</strong>
          </p>
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="alert alert-error mb-8">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}
        
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading configuration options...</p>
            </div>
          </div>
        )}
        
        {!loading && (
          <div className="config-grid">
            {/* Main Configuration */}
            <div className="space-y-6">
              
              {/* Scenario Selection */}
              <div className="config-section">
                <div className="config-section-header">
                  <FileText className="config-section-icon" />
                  <h2 className="config-section-title">Scenario Selection</h2>
                </div>
                <div>
                  {scenarios.length > 0 ? (
                    <div className="config-scenario-grid">
                      {scenarios.map((scenario) => (
                        <div
                          key={scenario.id}
                          className={`config-scenario-card ${
                            selectedScenario?.id === scenario.id ? 'selected' : ''
                          }`}
                          onClick={() => setSelectedScenario(scenario)}
                        >
                          <div className="config-scenario-header">
                            <div>
                              <h4 className="config-scenario-title">{scenario.name}</h4>
                              <p className="config-scenario-description">{scenario.description}</p>
                            </div>
                            {selectedScenario?.id === scenario.id && (
                              <CheckCircle className="check-icon" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600">No scenarios available</p>
                  )}
                </div>
              </div>
              
              {/* Timing Configuration */}
              <div className="config-section">
                <div className="config-section-header">
                  <Clock className="config-section-icon" />
                  <h2 className="config-section-title">Timing Settings</h2>
                </div>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="config-form-group">
                      <label className="config-label">
                        Simulation Duration: {getDurationText(config.duration)}
                      </label>
                      <input
                        type="range"
                        min="60"
                        max="7200"
                        step="60"
                        value={config.duration}
                        onChange={(e) => handleConfigChange('duration', parseInt(e.target.value))}
                        className="config-range w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>1 min</span>
                        <span>2 hours</span>
                      </div>
                    </div>
                    
                    <div className="config-form-group">
                      <label className="config-label">Step Length (seconds)</label>
                      <select
                        value={config.stepLength}
                        onChange={(e) => handleConfigChange('stepLength', parseFloat(e.target.value))}
                        className="config-select"
                      >
                        <option value={0.1}>0.1s (High precision)</option>
                        <option value={0.5}>0.5s (Good precision)</option>
                        <option value={1}>1s (Standard)</option>
                        <option value={2}>2s (Fast)</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="config-form-group">
                      <label className="config-label">Random Seed</label>
                      <input
                        type="number"
                        value={config.randomSeed}
                        onChange={(e) => handleConfigChange('randomSeed', parseInt(e.target.value))}
                        className="config-input"
                        min="1"
                        max="999999"
                      />
                    </div>
                    
                    <div className="config-form-group">
                      <label className="config-label">Teleport Time (seconds)</label>
                      <input
                        type="number"
                        value={config.teleportTime}
                        onChange={(e) => handleConfigChange('teleportTime', parseInt(e.target.value))}
                        className="config-input"
                        min="60"
                        max="1800"
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
                    <label className="config-label">Traffic Density</label>
                    <div className="grid grid-cols-3 gap-3">
                      {['low', 'medium', 'high'].map((density) => {
                        const densityConfig = getTrafficDensityConfig(density);
                        return (
                          <button
                            key={density}
                            onClick={() => handleConfigChange('trafficDensity', density)}
                            className={`config-scenario-card ${
                              config.trafficDensity === density ? 'selected' : ''
                            }`}
                          >
                            <div className="font-medium capitalize">{density}</div>
                            <div className="config-help-text mt-1">
                              {densityConfig.description}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="config-section-title">Vehicle Types</h3>
                    
                    <div className="config-vehicle-types">
                      <div className="config-vehicle-type">
                        <div className="config-vehicle-info">
                          <Car className="config-vehicle-icon" />
                          <div>
                            <div className="font-medium">Cars</div>
                            <div className="config-help-text">Standard passenger vehicles</div>
                          </div>
                        </div>
                        <div className="config-vehicle-controls">
                          <input
                            type="checkbox"
                            checked={config.vehicleTypes.car.enabled}
                            onChange={(e) => handleVehicleTypeChange('car', 'enabled', e.target.checked)}
                            className="config-checkbox"
                          />
                          <span className="config-help-text">
                            {config.vehicleTypes.car.percentage}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="config-vehicle-type">
                        <div className="config-vehicle-info">
                          <Truck className="config-vehicle-icon" />
                          <div>
                            <div className="font-medium">Trucks</div>
                            <div className="config-help-text">Heavy commercial vehicles</div>
                          </div>
                        </div>
                        <div className="config-vehicle-controls">
                          <input
                            type="checkbox"
                            checked={config.vehicleTypes.truck.enabled}
                            onChange={(e) => handleVehicleTypeChange('truck', 'enabled', e.target.checked)}
                            className="config-checkbox"
                          />
                          <span className="config-help-text">
                            {config.vehicleTypes.truck.percentage}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Configuration Summary */}
            <div className="space-y-6">
              <div className="config-section">
                <div className="config-section-header">
                  <h3 className="config-section-title">Configuration Summary</h3>
                </div>
                <div className="space-y-3">
                  <div className="text-sm">
                    <div className="font-medium text-gray-900">Network</div>
                    <div className="text-gray-600">{selectedNetwork.name}</div>
                  </div>
                  
                  {selectedScenario && (
                    <div className="text-sm">
                      <div className="font-medium text-gray-900">Scenario</div>
                      <div className="text-gray-600">{selectedScenario.name}</div>
                    </div>
                  )}
                  
                  <div className="text-sm">
                    <div className="font-medium text-gray-900">Duration</div>
                    <div className="text-gray-600">{getDurationText(config.duration)}</div>
                  </div>
                  
                  <div className="text-sm">
                    <div className="font-medium text-gray-900">Traffic Density</div>
                    <div className="text-gray-600 capitalize">{config.trafficDensity}</div>
                  </div>
                  
                  <div className="text-sm">
                    <div className="font-medium text-gray-900">Step Length</div>
                    <div className="text-gray-600">{config.stepLength}s</div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <button
                    onClick={handleSaveConfiguration}
                    disabled={saving || !selectedScenario}
                    className="btn btn-primary w-full flex items-center justify-center space-x-2"
                  >
                    {saving ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        <span>Save Configuration</span>
                      </>
                    )}
                  </button>
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
                    <li>• Higher step length = faster simulation, lower precision</li>
                    <li>• Longer duration provides more comprehensive results</li>
                    <li>• High traffic density may cause congestion</li>
                    <li>• Random seed ensures reproducible results</li>
                    <li>• Teleport time prevents infinite jams</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Navigation */}
        <div className="config-buttons">
          <div className="config-nav-buttons">
            <Link to="/network" className="btn btn-secondary flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Network</span>
            </Link>
          </div>
          
          <div className="config-action-buttons">
            <Link 
              to="/simulation" 
              className="btn btn-primary flex items-center space-x-2"
            >
              <span>Start Simulation</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPage;
