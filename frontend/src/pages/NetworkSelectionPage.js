/**
 * Network Selection Page Component
 * 
 * Allows users to select from available SUMO network files
 * or upload custom network configurations.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Network, 
  Upload, 
  Eye, 
  Download, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  Info,
  ArrowRight,
  MapPin,
  Clock,
  Users
} from 'lucide-react';
import { api } from '../utils/apiClient';

const NetworkSelectionPage = ({ socket, onLoadingChange }) => {
  const [networks, setNetworks] = useState([]);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadMode, setUploadMode] = useState(false);
  
  useEffect(() => {
    loadNetworks();
  }, []);
  
  const loadNetworks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getNetworks();
      
      if (response.data.success) {
        setNetworks(response.data.networks);
      } else {
        setError(response.data.error || 'Failed to load networks');
      }
    } catch (err) {
      setError('Unable to connect to server. Please check your connection.');
      console.error('Error loading networks:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleNetworkSelect = (network) => {
    setSelectedNetwork(network);
    
    // Store selected network in localStorage for next step
    localStorage.setItem('selected_network', JSON.stringify(network));
    
    // Notify parent of selection
    if (socket) {
      socket.emit('network_selected', { network: network.id });
    }
  };
  
  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Basic file validation
    if (!file.name.endsWith('.net.xml')) {
      setError('Please select a valid SUMO network file (.net.xml)');
      return;
    }
    
    // TODO: Implement file upload functionality
    console.log('File selected for upload:', file.name);
    setError('File upload functionality is not yet implemented. Please use one of the predefined networks.');
  };
  
  const NetworkCard = ({ network, isSelected, onSelect }) => (
    <div 
      className={`network-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(network)}
    >
      <div className="network-card-header">
        <div className="network-card-info">
          <div className={`network-icon ${isSelected ? 'selected' : ''}`}>
            <Network />
          </div>
          <div>
            <h3 className="network-card-title">{network.name}</h3>
            <p className="network-card-id">ID: {network.id}</p>
          </div>
        </div>
        
        {isSelected && (
          <CheckCircle className="check-icon" />
        )}
      </div>
      
      <p className="network-card-description">
        {network.description}
      </p>
      
      <div className="network-card-footer">
        <div className="network-card-meta">
          <div className="network-card-meta-item">
            <MapPin />
            <span>Network</span>
          </div>
          <div className="network-card-meta-item">
            <Users />
            <span>Multi-agent</span>
          </div>
        </div>
        
        <div className="network-card-actions">
          <button 
            className="network-card-action"
            onClick={(e) => {
              e.stopPropagation();
              console.log('Preview network:', network.id);
            }}
          >
            <Eye />
          </button>
          <button 
            className="network-card-action"
            onClick={(e) => {
              e.stopPropagation();
              console.log('Download network:', network.id);
            }}
          >
            <Download />
          </button>
        </div>
      </div>
    </div>
  );
  
  return (
    <div className="network-page">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Select Traffic Network
          </h1>
          <p className="text-gray-600">
            Choose a predefined network or upload your own SUMO network file to begin simulation.
          </p>
        </div>
        
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
            onClick={() => setUploadMode(!uploadMode)}
            className="btn btn-outline flex items-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Custom Network</span>
          </button>
        </div>
        
        {/* Upload Section */}
        {uploadMode && (
          <div className="bg-white rounded-lg p-6 mb-8 border-2 border-dashed border-gray-300">
            <div className="text-center">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Upload SUMO Network File
              </h3>
              <p className="text-gray-600 mb-4">
                Select a .net.xml file exported from SUMO or created with netconvert
              </p>
              
              <input
                type="file"
                accept=".xml,.net.xml"
                onChange={handleUpload}
                className="hidden"
                id="network-upload"
              />
              
              <label
                htmlFor="network-upload"
                className="btn btn-primary cursor-pointer"
              >
                Choose File
              </label>
              
              <div className="mt-4 text-sm text-gray-500">
                <p>Supported formats: .net.xml</p>
                <p>Maximum file size: 10MB</p>
              </div>
            </div>
          </div>
        )}
        
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
              <p className="text-gray-600">Loading available networks...</p>
            </div>
          </div>
        )}
        
        {/* Networks Grid */}
        {!loading && networks.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Available Networks ({networks.length})
              </h2>
              
              {selectedNetwork && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">Network Selected</span>
                </div>
              )}
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {networks.map((network) => (
                <NetworkCard
                  key={network.id}
                  network={network}
                  isSelected={selectedNetwork?.id === network.id}
                  onSelect={handleNetworkSelect}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* No Networks Available */}
        {!loading && networks.length === 0 && !error && (
          <div className="text-center py-12">
            <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No Networks Available
            </h3>
            <p className="text-gray-600 mb-4">
              No SUMO network files were found. You can upload your own network file or check the server configuration.
            </p>
            <button
              onClick={() => setUploadMode(true)}
              className="btn btn-primary"
            >
              Upload Network File
            </button>
          </div>
        )}
        
        {/* Selected Network Info */}
        {selectedNetwork && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
              
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  Selected Network: {selectedNetwork.name}
                </h3>
                <p className="text-blue-800 mb-4">
                  {selectedNetwork.description}
                </p>
                
                <div className="flex items-center space-x-6 text-sm text-blue-700">
                  <div className="flex items-center space-x-1">
                    <Info className="w-4 h-4" />
                    <span>ID: {selectedNetwork.id}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>Ready for configuration</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Link to="/" className="btn btn-secondary">
            ← Back to Home
          </Link>
          
          {selectedNetwork && (
            <Link 
              to="/configuration" 
              className="btn btn-primary flex items-center space-x-2"
            >
              <span>Continue to Configuration</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
        
        {/* Help Section */}
        <div className="mt-12 bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Need Help?
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Network Requirements</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• Valid SUMO network file (.net.xml)</li>
                <li>• Properly connected road network</li>
                <li>• Contains edges and junctions</li>
                <li>• Compatible with SUMO version 1.15+</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Creating Networks</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• Use SUMO's netconvert tool</li>
                <li>• Import from OpenStreetMap</li>
                <li>• Create with netedit GUI</li>
                <li>• Generate programmatically</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkSelectionPage;
