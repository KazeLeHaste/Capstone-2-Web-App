/**
 * Network Selection Page Component
 * 
 * Works with saved configurations to allow users to select predefined networks.
 * Copies selected networks to session folders and applies configurations.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Network, 
  CheckCircle, 
  RefreshCw, 
  MapPin,
  Users,
  ArrowLeft,
  AlertCircle,
  Info,
  FileText,
  Folder,
  Copy,
  Settings,
  Clock,
  Car
} from 'lucide-react';
import { apiClient } from '../utils/apiClient';

const NetworkSelectionPage = ({ socket, onLoadingChange }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [networks, setNetworks] = useState([]);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copying, setCopying] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // Configuration from previous step
  const [sessionConfig, setSessionConfig] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    console.log('NetworkSelectionPage: Component mounted');
    // Load session configuration
    loadSessionConfiguration();
    loadNetworks();
  }, []);

  const loadSessionConfiguration = () => {
    console.log('Loading session configuration...');
    try {
      // Try to get config from navigation state first
      if (location.state?.sessionId && location.state?.config) {
        console.log('Found config in navigation state:', location.state);
        setSessionId(location.state.sessionId);
        setSessionConfig(location.state.config);
        return;
      }

      // Fallback to localStorage
      const storedSessionId = localStorage.getItem('simulation_session_id');
      const storedConfig = localStorage.getItem('simulation_config');
      
      if (storedSessionId && storedConfig) {
        setSessionId(storedSessionId);
        setSessionConfig(JSON.parse(storedConfig));
      } else {
        setError('No configuration found. Please complete the configuration step first.');
      }
    } catch (err) {
      console.error('Error loading session configuration:', err);
      setError('Invalid configuration data. Please restart the configuration process.');
    }
  };

  const loadNetworks = async () => {
    console.log('Loading networks...');
    try {
      setLoading(true);
      if (onLoadingChange) onLoadingChange(true);

      const response = await apiClient.get('/api/networks/available');
      console.log('Networks API response:', response.data);
      
      if (response.data.success) {
        setNetworks(response.data.networks || []);
      } else {
        setError(response.data.message || 'Failed to load networks');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load networks');
      console.error('Error loading networks:', err);
    } finally {
      setLoading(false);
      if (onLoadingChange) onLoadingChange(false);
    }
  };

  const handleNetworkSelect = (network) => {
    setSelectedNetwork(network);
    setError(null);
  };

  const handleCopyAndProceed = async () => {
    if (!selectedNetwork || !sessionId || !sessionConfig) {
      setError('Missing required data for network setup');
      return;
    }

    try {
      setCopying(true);
      setError(null);

      // Copy network to session folder and apply configurations
      const requestData = {
        sessionId,
        networkId: selectedNetwork.id,
        networkPath: selectedNetwork.path,
        config: sessionConfig.config
      };

      const response = await apiClient.post('/api/simulation/setup-network', requestData);
      
      if (response.data.success) {
        setSuccess(true);
        
        // Store session data for simulation
        const sessionData = {
          sessionId,
          networkId: selectedNetwork.id,
          networkName: selectedNetwork.name,
          sessionPath: response.data.sessionPath,
          configApplied: true,
          timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('simulation_session_data', JSON.stringify(sessionData));
        
        // Notify via socket if available
        if (socket) {
          socket.emit('network_setup_complete', sessionData);
        }
        
        // Navigate to simulation launch after a brief delay
        setTimeout(() => {
          navigate('/simulation', { 
            state: { sessionData, config: sessionConfig } 
          });
        }, 1500);
      } else {
        setError(response.data.message || 'Failed to setup network');
      }

    } catch (err) {
      setError(err.response?.data?.message || 'Failed to setup network');
      console.error('Error setting up network:', err);
    } finally {
      setCopying(false);
    }
  };

  const handleReturnToConfig = () => {
    // Clear current session data
    localStorage.removeItem('simulation_session_id');
    localStorage.removeItem('simulation_config');
    navigate('/configuration');
  };

  const NetworkCard = ({ network, isSelected, onSelect }) => (
    <div 
      className={`network-card ${isSelected ? 'selected' : ''} ${network.isOsmScenario ? 'osm-scenario' : ''}`}
      onClick={() => onSelect(network)}
    >
      <div className="network-card-header">
        <div className="network-card-info">
          <div className={`network-icon ${isSelected ? 'selected' : ''}`}>
            <Network />
          </div>
          <div className="network-card-text">
            <h3 className="network-card-title">{network.name}</h3>
            <p className="network-card-id">ID: {network.id}</p>
            {network.isOsmScenario && (
              <span className="osm-badge">
                🌍 OSM Realistic Traffic
              </span>
            )}
          </div>
        </div>
        
        {isSelected && (
          <CheckCircle className="check-icon" />
        )}
      </div>
      
      <p className="network-card-description">
        {network.description}
      </p>
      
      {/* OSM Scenario Features */}
      {network.isOsmScenario && network.vehicleTypes && network.vehicleTypes.length > 0 && (
        <div className="osm-features">
          <h4 className="osm-features-title">Available Vehicle Types:</h4>
          <div className="vehicle-types-list">
            {network.vehicleTypes.map((vehicleType) => (
              <span key={vehicleType} className="vehicle-type-badge">
                {vehicleType === 'passenger' && <Car className="w-3 h-3" />}
                {vehicleType === 'truck' && '🚛'}
                {vehicleType === 'bus' && '🚌'}
                {vehicleType === 'motorcycle' && '🏍️'}
                {vehicleType}
              </span>
            ))}
          </div>
        </div>
      )}
      
      <div className="network-card-stats">
        <div className="network-stat">
          <MapPin className="w-4 h-4" />
          <span>{network.edges || 0} edges</span>
        </div>
        <div className="network-stat">
          <Users className="w-4 h-4" />
          <span>{network.junctions || 0} junctions</span>
        </div>
        <div className="network-stat">
          <FileText className="w-4 h-4" />
          <span>{network.fileSize || 'Unknown'}</span>
        </div>
        {network.lanes && (
          <div className="network-stat">
            <span>{network.lanes} lanes</span>
          </div>
        )}
      </div>
      
      <div className="network-card-footer">
        <div className="network-card-meta">
          <div className="network-card-meta-item">
            <Clock className="w-4 h-4" />
            <span>Modified: {network.lastModified || 'Unknown'}</span>
          </div>
          {network.routeSource && (
            <div className="network-card-meta-item">
              <span className={`route-source-badge ${network.isOsmScenario ? 'osm' : 'generated'}`}>
                {network.routeSource}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (!sessionConfig || !sessionId) {
    return (
      <div className="network-page">
        <div className="network-container">
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-error mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-primary mb-2">
              Configuration Required
            </h2>
            <p className="text-secondary mb-6">
              Please complete the simulation configuration before selecting a network.
            </p>
            <Link
              to="/configuration"
              className="btn btn-primary"
            >
              Go to Configuration
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="network-page">
      <div className="network-container">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">
            Select Network
          </h1>
          <p className="text-secondary">
            Choose a predefined network to apply your configuration. The selected network will be copied to your session folder.
          </p>
          
          {sessionConfig && (
            <div className="mt-4 p-4 info-block rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Settings className="w-5 h-5 text-info" />
                <span className="font-medium text-info-dark">Active Configuration</span>
              </div>
              <div className="text-sm text-info-dark">
                Session: <code className="code-block px-1 rounded">{sessionId}</code> | 
                {/* Handle both simplified and legacy configuration structures */}
                {sessionConfig.config.original_config ? (
                  // Simplified configuration structure
                  <>
                    Duration: {Math.floor((sessionConfig.config.sumo_end - sessionConfig.config.sumo_begin) / 60)}min | 
                    Step: {sessionConfig.config.sumo_step_length}s | 
                    Teleport: {sessionConfig.config.sumo_time_to_teleport}s | 
                    Traffic: {((sessionConfig.config.sumo_traffic_intensity || 1.0) * 100).toFixed(0)}%
                  </>
                ) : (
                  // Legacy configuration structure (backward compatibility)
                  <>
                    Duration: {Math.floor((sessionConfig.config.duration || 1800) / 60)}min | 
                    Traffic: {Math.round((sessionConfig.config.trafficVolume || 0.5) * 100)}% | 
                    Modifications: {(sessionConfig.config.speedLimits || []).length + (sessionConfig.config.roadClosures || []).length} items
                  </>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Error/Success Messages */}
        {error && (
          <div className="alert alert-error mb-6">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert alert-success mb-6">
            <CheckCircle className="w-5 h-5" />
            <span>Network setup completed successfully! Launching simulation...</span>
          </div>
        )}
        
        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <button
            onClick={loadNetworks}
            disabled={loading}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Networks</span>
          </button>
          
          <button
            onClick={handleReturnToConfig}
            className="btn btn-outline flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Modify Configuration</span>
          </button>
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
              <p className="text-secondary">Loading available networks...</p>
            </div>
          </div>
        )}
        
        {/* Networks Grid */}
        {!loading && (
          <>
            {networks.length > 0 ? (
              <>
                <div className="networks-header">
                  <h2 className="networks-title">Available Networks</h2>
                  <div className="networks-status">
                    <CheckCircle />
                    <span className="networks-status-text">{networks.length} networks found</span>
                  </div>
                </div>
                
                <div className="networks-grid">
                  {networks.map((network) => (
                    <NetworkCard
                      key={network.id}
                      network={network}
                      isSelected={selectedNetwork?.id === network.id}
                      onSelect={handleNetworkSelect}
                    />
                  ))}
                </div>
                
                {/* Selection Actions */}
                {selectedNetwork && (
                  <div className="mt-8 p-6 success-block rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-success-dark mb-1">
                          Selected: {selectedNetwork.name}
                        </h3>
                        <p className="text-success-dark">
                          This network will be copied to your session folder and your configuration will be applied.
                        </p>
                      </div>
                      <button
                        onClick={handleCopyAndProceed}
                        disabled={copying}
                        className="btn btn-success flex items-center space-x-2"
                      >
                        {copying ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>Setting up...</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span>Setup & Continue</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="no-networks-container">
                <div className="no-networks-icon">
                  <Folder />
                </div>
                <h3 className="no-networks-title">No Networks Available</h3>
                <p className="no-networks-description">
                  No SUMO network files were found. Please ensure networks are available in the configured directory.
                </p>
                <button
                  onClick={loadNetworks}
                  className="btn btn-primary"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </button>
              </div>
            )}
          </>
        )}
        
        {/* Information Panel */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          <div className="info-panel">
            <div className="info-panel-header">
              <Info className="info-panel-icon" />
              <h3 className="info-panel-title">Network Selection</h3>
            </div>
            <div className="info-panel-content">
              <ul className="list-spaced">
                <li>Original network files are never modified</li>
                <li>Each session gets its own network copy</li>
                <li>Your configuration is applied to the copied files</li>
                <li>Network modifications are isolated per session</li>
              </ul>
            </div>
          </div>
          
          <div className="info-panel">
            <div className="info-panel-header">
              <FileText className="info-panel-icon" />
              <h3 className="info-panel-title">Configuration Applied</h3>
            </div>
            <div className="info-panel-content">
              <ul className="list-spaced">
                <li>Speed limit changes to specified edges</li>
                <li>Road closures during simulation time</li>
                <li>Traffic volume and vehicle type distribution</li>
                <li>Advanced SUMO parameters and models</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-default">
          <Link 
            to="/configuration" 
            className="btn btn-secondary flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Configuration</span>
          </Link>
          
          <div className="flex items-center space-x-4">
            {selectedNetwork ? (
              <span className="text-success text-sm font-medium">
                Network selected: {selectedNetwork.name}
              </span>
            ) : (
              <span className="text-secondary text-sm">
                Select a network to continue
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkSelectionPage;
