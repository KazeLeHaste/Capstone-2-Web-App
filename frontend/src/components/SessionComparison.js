import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/apiClient';
import { ChevronDown, ChevronUp } from 'lucide-react';

const SessionComparison = ({ selectedSessions, onClose }) => {
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedConfigs, setExpandedConfigs] = useState({}); // Track which configs are expanded
  
  const handleClose = () => {
    if (onClose && typeof onClose === 'function') {
      onClose();
    }
  };

  const toggleConfig = (sessionId) => {
    setExpandedConfigs(prev => ({
      ...prev,
      [sessionId]: !prev[sessionId]
    }));
  };

  // Helper function to format network name with traffic control method
  const getSessionDisplayName = (sessionId) => {
    const metadata = comparisonData?.session_metadata?.[sessionId];
    if (!metadata) return sessionId.substring(0, 12);
    
    const networkName = metadata.network_name || metadata.network_id || 'Unknown Network';
    const trafficMethod = metadata.configuration?.traffic_control_method || 'None';
    
    // Format the network name nicely (capitalize words)
    const formattedNetwork = networkName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    
    return `${formattedNetwork} (${trafficMethod})`;
  };

  // Load comparison data
  useEffect(() => {
    const loadComparisonData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await apiClient.post('/api/analytics/compare', {
          session_ids: selectedSessions
        });

        if (response.data.success) {
          setComparisonData(response.data.comparison);
        } else {
          setError(response.data.message || 'Failed to load comparison data');
        }
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load comparison data');
      } finally {
        setLoading(false);
      }
    };

    if (selectedSessions && selectedSessions.length >= 2) {
      loadComparisonData();
    }
  }, [selectedSessions]);

  if (loading) {
    return (
      <div className="session-comparison-backdrop">
        <div className="session-comparison-modal">
          <div className="session-comparison-loading">
            <h2 className="session-comparison-loading-title">
              Loading Comparison...
            </h2>
            <div className="session-comparison-loading-subtitle">
              Please wait while we analyze the sessions...
            </div>
            <div className="session-comparison-spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="session-comparison-backdrop">
        <div className="session-comparison-modal">
          <div className="session-comparison-error">
            <h2 className="session-comparison-error-title">
              Comparison Error
            </h2>
            <p className="session-comparison-error-message">
              {error}
            </p>
            <button 
              onClick={handleClose}
              className="session-comparison-button"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main comparison view
  const kpiComparison = comparisonData?.kpi_comparison || {};
  const sessions = comparisonData?.sessions || [];
  const bestSession = comparisonData?.best_performing_session;

  return (
    <div className="session-comparison-backdrop">
      <div className="session-comparison-modal">
        {/* Header */}
        <div className="session-comparison-header">
          <div>
            <h2 className="session-comparison-title">
              Session Comparison
            </h2>
            <p className="session-comparison-subtitle">
              Comparing {sessions.length} simulation sessions
            </p>
          </div>
          <button 
            onClick={handleClose}
            className="session-comparison-button secondary"
          >
            Close
          </button>
        </div>

        {/* Content */}
        <div className="session-comparison-content">
          {/* Best Performing Session */}
          {bestSession && (
            <div className="session-comparison-best-session">
              <h3 className="session-comparison-best-title">
                🏆 Best Performing Session
              </h3>
              <p className="session-comparison-best-subtitle">
                {getSessionDisplayName(bestSession)} achieved the highest overall performance
              </p>
            </div>
          )}

          {/* Session Summary Cards */}
          <div className="session-comparison-grid">
            {sessions.map((sessionId, index) => {
              const sessionData = comparisonData.session_data?.[sessionId];
              const kpis = sessionData?.kpis || {};
              const isWinner = sessionId === bestSession;
              const metadata = comparisonData?.session_metadata?.[sessionId];
              const config = metadata?.configuration || {};
              const isExpanded = expandedConfigs[sessionId];
              
              return (
                <div 
                  key={sessionId} 
                  className={`session-comparison-card ${isWinner ? 'winner' : ''}`}
                >
                  <div className="session-comparison-card-header">
                    <div className="session-comparison-card-header-content">
                      <h4 className="session-comparison-card-title">
                        {getSessionDisplayName(sessionId)} {isWinner && '🏆'}
                      </h4>
                      <span className="session-comparison-card-id">
                        Session ID: {sessionId.substring(0, 12)}...
                      </span>
                    </div>
                    <button 
                      className="session-config-toggle"
                      onClick={() => toggleConfig(sessionId)}
                      title={isExpanded ? "Hide configuration" : "Show configuration"}
                    >
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </button>
                  </div>

                  {/* Collapsible Configuration */}
                  {isExpanded && (
                    <div className="session-config-details">
                      <div className="session-config-section">
                        <h5 className="session-config-heading">SUMO Parameters</h5>
                        <div className="session-config-grid">
                          <div className="session-config-item">
                            <span className="session-config-label">Begin Time:</span>
                            <span className="session-config-value">{config.sumo_begin || 'N/A'}s</span>
                          </div>
                          <div className="session-config-item">
                            <span className="session-config-label">End Time:</span>
                            <span className="session-config-value">{config.sumo_end || 'N/A'}s</span>
                          </div>
                          <div className="session-config-item">
                            <span className="session-config-label">Step Length:</span>
                            <span className="session-config-value">{config.sumo_step_length || 'N/A'}s</span>
                          </div>
                          <div className="session-config-item">
                            <span className="session-config-label">Time to Teleport:</span>
                            <span className="session-config-value">{config.sumo_time_to_teleport || 'N/A'}s</span>
                          </div>
                          <div className="session-config-item">
                            <span className="session-config-label">Traffic Intensity:</span>
                            <span className="session-config-value">{config.sumo_traffic_intensity || 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {config.enabled_vehicles && config.enabled_vehicles.length > 0 && (
                        <div className="session-config-section">
                          <h5 className="session-config-heading">Enabled Vehicles</h5>
                          <div className="session-config-tags">
                            {config.enabled_vehicles.map((vehicle, idx) => (
                              <span key={idx} className="session-config-tag">
                                {vehicle}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {config.traffic_control_config && Object.keys(config.traffic_control_config).length > 0 && (
                        <div className="session-config-section">
                          <h5 className="session-config-heading">Traffic Control Settings</h5>
                          <div className="session-config-grid">
                            {Object.entries(config.traffic_control_config).map(([key, value]) => {
                              // Skip if value is an object or array (render only primitive values)
                              if (typeof value === 'object' && value !== null) {
                                return null;
                              }
                              
                              return (
                                <div key={key} className="session-config-item">
                                  <span className="session-config-label">
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                  </span>
                                  <span className="session-config-value">
                                    {typeof value === 'boolean' 
                                      ? (value ? 'Yes' : 'No') 
                                      : String(value)
                                    }
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="session-comparison-metrics">
                    <div className="session-comparison-metric">
                      <span className="session-comparison-metric-label">Avg Speed:</span>
                      <div className="session-comparison-metric-value">
                        {(() => {
                          const speed = kpis.avg_speed;
                          if (speed === null || speed === undefined) return 'N/A';
                          const speedNum = typeof speed === 'number' ? speed : parseFloat(speed);
                          return isNaN(speedNum) ? 'N/A' : (speedNum * 3.6).toFixed(1) + ' km/h';
                        })()}
                      </div>
                    </div>
                    <div className="session-comparison-metric">
                      <span className="session-comparison-metric-label">Throughput:</span>
                      <div className="session-comparison-metric-value">
                        {(() => {
                          const throughput = kpis.throughput;
                          if (throughput === null || throughput === undefined) return 'N/A';
                          const throughputNum = typeof throughput === 'number' ? throughput : parseFloat(throughput);
                          return isNaN(throughputNum) ? 'N/A' : throughputNum.toFixed(0) + ' veh/h';
                        })()}
                      </div>
                    </div>
                    <div className="session-comparison-metric">
                      <span className="session-comparison-metric-label">Wait Time:</span>
                      <div className="session-comparison-metric-value">
                        {(() => {
                          const waitTime = kpis.avg_waiting_time;
                          if (waitTime === null || waitTime === undefined) return 'N/A';
                          const waitTimeNum = typeof waitTime === 'number' ? waitTime : parseFloat(waitTime);
                          return isNaN(waitTimeNum) ? 'N/A' : waitTimeNum.toFixed(1) + 's';
                        })()}
                      </div>
                    </div>
                    <div className="session-comparison-metric">
                      <span className="session-comparison-metric-label">Vehicles:</span>
                      <div className="session-comparison-metric-value">
                        {(() => {
                          const vehicles = kpis.total_vehicles_completed;
                          if (vehicles === null || vehicles === undefined) return 'N/A';
                          const vehiclesNum = typeof vehicles === 'number' ? vehicles : parseInt(vehicles);
                          return isNaN(vehiclesNum) ? 'N/A' : vehiclesNum.toString();
                        })()}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detailed Comparison Table */}
          <div className="session-comparison-table-container">
            <div className="session-comparison-table-header">
              <h3 className="session-comparison-table-title">
                Detailed Metrics Comparison
              </h3>
            </div>
            
            <div className="session-comparison-table-scroll">
              <table className="session-comparison-table">
                <thead>
                  <tr>
                    <th className="session-comparison-metric-name">
                      Metric
                    </th>
                    {sessions.map((sessionId) => (
                      <th key={sessionId}>
                        {getSessionDisplayName(sessionId)}
                      </th>
                    ))}
                    <th>
                      Best
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(kpiComparison).map(([kpi, data]) => (
                    <tr key={kpi}>
                      <td className="session-comparison-metric-name">
                        {kpi.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      {sessions.map(session => (
                        <td key={session}>
                          {(() => {
                            const value = data.values?.[session];
                            if (value === null || value === undefined) return 'N/A';
                            if (typeof value === 'number') return value.toFixed(2);
                            if (typeof value === 'string' && !isNaN(parseFloat(value))) return parseFloat(value).toFixed(2);
                            return String(value);
                          })()}
                        </td>
                      ))}
                      <td className="session-comparison-best-indicator">
                        {getSessionDisplayName(data.best_session) || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionComparison;