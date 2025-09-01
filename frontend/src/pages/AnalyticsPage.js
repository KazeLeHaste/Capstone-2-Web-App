/**
 * Enhanced Analytics Page Component
 * 
 * Comprehensive analytics dashboard with KPI tracking, visualizations,
 * recommendations, session comparison, and report export functionality.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { 
  BarChart3, 
  TrendingUp, 
  Activity,
  Download,
  RefreshCw,
  ArrowLeft,
  FileText,
  LineChart,
  AlertCircle,
  AlertTriangle,
  GitCompare,
  Eye,
  Calendar,
  Database
} from 'lucide-react';

// Import our new components
import KPIDashboard from '../components/KPIDashboard';
import AnalyticsCharts from '../components/AnalyticsCharts';
import RecommendationsPanel from '../components/RecommendationsPanel';
import SessionComparison from '../components/SessionComparison';
import { exportAnalyticsAsPDF } from '../utils/reportExport';

const AnalyticsPage = ({ socket, simulationData, simulationStatus }) => {
  const [searchParams] = useSearchParams();
  const sessionIdFromUrl = searchParams.get('session');
  
  // State management
  const [analyticsData, setAnalyticsData] = useState(null);
  const [availableSessions, setAvailableSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(sessionIdFromUrl || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showComparison, setShowComparison] = useState(false);
  const [selectedSessionsForComparison, setSelectedSessionsForComparison] = useState([]);
  const [refreshInterval, setRefreshInterval] = useState(null);

  const loadAvailableSessions = useCallback(async () => {
    try {
      const response = await axios.get('/api/analytics/sessions');
      if (response.data.success) {
        setAvailableSessions(response.data.sessions);
        
        // Auto-select the first analyzable session if none selected
        if (!selectedSession && response.data.sessions.length > 0) {
          const firstAnalyzable = response.data.sessions.find(s => s.can_analyze);
          if (firstAnalyzable) {
            setSelectedSession(firstAnalyzable.session_id);
          }
        }
      }
    } catch (err) {
      console.error('Error loading sessions:', err);
    }
  }, [selectedSession]);

  const loadSessionAnalytics = useCallback(async (sessionId, silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }

      const response = await axios.get(`/api/analytics/session/${sessionId}`);
      
      if (response.data.success) {
        setAnalyticsData(response.data.analytics);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Failed to load analytics data';
      setError(errorMessage);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  // Load available sessions on component mount
  useEffect(() => {
    loadAvailableSessions();
  }, [loadAvailableSessions]);

  // Load analytics for selected session
  useEffect(() => {
    if (selectedSession) {
      loadSessionAnalytics(selectedSession);
    }
  }, [selectedSession, loadSessionAnalytics]);

  // Auto-refresh for live sessions
  useEffect(() => {
    if (simulationStatus === 'running' && selectedSession) {
      const interval = setInterval(() => {
        loadSessionAnalytics(selectedSession, true); // Silent refresh
      }, 10000); // Refresh every 10 seconds
      
      setRefreshInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [simulationStatus, selectedSession, refreshInterval, loadSessionAnalytics]);

  const handleSessionChange = (sessionId) => {
    setSelectedSession(sessionId);
    setAnalyticsData(null);
    setError(null);
  };

  const handleRefresh = () => {
    if (selectedSession) {
      loadSessionAnalytics(selectedSession);
    }
  };

  const handleExportPDF = async () => {
    if (!analyticsData || !selectedSession) return;
    
    try {
      await exportAnalyticsAsPDF(analyticsData, selectedSession);
    } catch (err) {
      alert('Failed to export PDF: ' + err.message);
    }
  };

  const handleExportData = () => {
    if (!analyticsData) return;
    
    const exportData = {
      session_id: selectedSession,
      exported_at: new Date().toISOString(),
      kpis: analyticsData.kpis,
      recommendations: analyticsData.recommendations,
      time_series: analyticsData.time_series
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics_${selectedSession}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCompareToggle = () => {
    setShowComparison(!showComparison);
    if (!showComparison) {
      // Reset comparison selection
      setSelectedSessionsForComparison([]);
    }
  };

  const handleSessionSelectionForComparison = (sessionId, checked) => {
    if (checked) {
      if (selectedSessionsForComparison.length < 4) { // Limit to 4 sessions
        setSelectedSessionsForComparison([...selectedSessionsForComparison, sessionId]);
      }
    } else {
      setSelectedSessionsForComparison(selectedSessionsForComparison.filter(id => id !== sessionId));
    }
  };

  const canStartComparison = selectedSessionsForComparison.length >= 2;

  // Tab configurations
  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'kpis', name: 'KPIs', icon: TrendingUp },
    { id: 'charts', name: 'Charts', icon: LineChart },
    { id: 'recommendations', name: 'Recommendations', icon: AlertCircle },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/simulation" className="text-gray-400 hover:text-gray-600 mr-4">
                <ArrowLeft className="w-6 h-6" />
              </Link>
              <h1 className="text-xl font-semibold text-gray-900 flex items-center">
                <Activity className="w-6 h-6 mr-3 text-blue-600" />
                Analytics Dashboard
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Session Selector */}
              <select
                value={selectedSession}
                onChange={(e) => handleSessionChange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="">Select a session...</option>
                {availableSessions
                  .filter(session => session.can_analyze)
                  .map(session => (
                    <option key={session.session_id} value={session.session_id}>
                      {session.network_id || 'Unknown Network'} - {
                        new Date(session.created_at).toLocaleDateString()
                      }
                    </option>
                  ))}
              </select>

              {/* Action Buttons */}
              <button
                onClick={handleRefresh}
                disabled={!selectedSession || loading}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                title="Refresh Data"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>

              <button
                onClick={handleCompareToggle}
                className="flex items-center px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <GitCompare className="w-4 h-4 mr-2" />
                Compare Sessions
              </button>

              <button
                onClick={handleExportPDF}
                disabled={!analyticsData}
                className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export PDF
              </button>

              <div className="relative">
                <button
                  onClick={handleExportData}
                  disabled={!analyticsData}
                  className="flex items-center px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Export Data
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Session Comparison Selector */}
      {showComparison && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-blue-900 mb-2">
                  Select sessions to compare (choose 2-4 sessions):
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {availableSessions
                    .filter(session => session.can_analyze)
                    .slice(0, 8) // Limit displayed sessions
                    .map(session => (
                      <label key={session.session_id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedSessionsForComparison.includes(session.session_id)}
                          onChange={(e) => handleSessionSelectionForComparison(session.session_id, e.target.checked)}
                          disabled={!selectedSessionsForComparison.includes(session.session_id) && selectedSessionsForComparison.length >= 4}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-blue-800">
                          {session.network_id || 'Unknown'} - {new Date(session.created_at).toLocaleDateString()}
                        </span>
                      </label>
                    ))}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowComparison(false)}
                  className="px-3 py-2 text-sm text-blue-700 hover:text-blue-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Open comparison modal with selected sessions
                    // This will be handled by the SessionComparison component
                  }}
                  disabled={!canStartComparison}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
                >
                  Compare ({selectedSessionsForComparison.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Session Info Bar */}
        {selectedSession && (
          <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <div className="flex items-center">
                  <Database className="w-5 h-5 text-gray-400 mr-2" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Session ID</p>
                    <p className="text-xs text-gray-500">{selectedSession}</p>
                  </div>
                </div>
                
                {analyticsData?.analysis_timestamp && (
                  <div className="flex items-center">
                    <Calendar className="w-5 h-5 text-gray-400 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Analyzed</p>
                      <p className="text-xs text-gray-500">
                        {new Date(analyticsData.analysis_timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}

                {simulationStatus === 'running' && (
                  <div className="flex items-center">
                    <div className="flex items-center px-2 py-1 bg-green-100 text-green-800 rounded-full">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                      <span className="text-xs font-medium">Live Session</span>
                    </div>
                  </div>
                )}
              </div>

              {analyticsData?.recommendations && (
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {analyticsData.recommendations.length} Recommendations
                  </p>
                  <p className="text-xs text-gray-500">
                    {analyticsData.recommendations.filter(r => r.priority === 'high').length} High Priority
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-400 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Error Loading Analytics</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* No Session Selected State */}
        {!selectedSession && !loading && (
          <div className="text-center py-12">
            <Eye className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Session to Analyze</h3>
            <p className="mt-2 text-gray-500">
              Choose a simulation session from the dropdown above to view detailed analytics.
            </p>
            {availableSessions.filter(s => s.can_analyze).length === 0 && (
              <p className="mt-2 text-sm text-gray-400">
                No analyzable sessions found. Run a simulation to generate analytics data.
              </p>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <RefreshCw className="mx-auto h-8 w-8 text-blue-500 animate-spin" />
            <p className="mt-4 text-gray-600">Loading analytics data...</p>
          </div>
        )}

        {/* Analytics Content */}
        {analyticsData && !loading && !error && (
          <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                {tabs.map(tab => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {tab.name}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <KPIDashboard kpis={analyticsData.kpis} loading={false} />
                  
                  {analyticsData.recommendations && analyticsData.recommendations.length > 0 && (
                    <div className="bg-white rounded-lg border p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Recommendations</h3>
                      <div className="space-y-3">
                        {analyticsData.recommendations
                          .filter(r => r.priority === 'high')
                          .slice(0, 3)
                          .map((rec, index) => (
                            <div key={index} className="flex items-start p-3 bg-red-50 border border-red-200 rounded-lg">
                              <AlertTriangle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
                              <div>
                                <p className="text-sm font-medium text-red-800">{rec.category.toUpperCase()}</p>
                                <p className="text-sm text-red-700">{rec.message}</p>
                              </div>
                            </div>
                          ))}
                        {analyticsData.recommendations.filter(r => r.priority === 'high').length === 0 && (
                          <div className="text-center py-4 text-green-600">
                            <p>No high-priority recommendations. Performance looks good!</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'kpis' && (
                <KPIDashboard kpis={analyticsData.kpis} loading={false} />
              )}

              {activeTab === 'charts' && (
                <AnalyticsCharts analyticsData={analyticsData} loading={false} />
              )}

              {activeTab === 'recommendations' && (
                <RecommendationsPanel 
                  recommendations={analyticsData.recommendations} 
                  loading={false} 
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Session Comparison Modal */}
      {canStartComparison && (
        <SessionComparison
          selectedSessions={selectedSessionsForComparison}
          onClose={() => {
            setShowComparison(false);
            setSelectedSessionsForComparison([]);
          }}
        />
      )}
    </div>
  );
};

export default AnalyticsPage;

