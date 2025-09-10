/**
 * Fixed Analytics Page Component
 * 
 * Comprehensive analytics dashboard with consistent styling
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { 
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
  const [activeTab, setActiveTab] = useState('kpis');
  const [showComparison, setShowComparison] = useState(false);
  const [selectedSessionsForComparison, setSelectedSessionsForComparison] = useState([]);

  const loadAvailableSessions = useCallback(async () => {
    try {
      const response = await axios.get('/api/analytics/sessions');
      if (response.data.success) {
        setAvailableSessions(response.data.sessions);
        
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

  useEffect(() => {
    loadAvailableSessions();
  }, [loadAvailableSessions]);

  useEffect(() => {
    if (selectedSession) {
      loadSessionAnalytics(selectedSession);
    }
  }, [selectedSession, loadSessionAnalytics]);

  const handleSessionChange = (sessionId) => {
    setSelectedSession(sessionId);
    setError(null);
  };

  const handleRefresh = () => {
    if (selectedSession) {
      loadSessionAnalytics(selectedSession);
    }
    loadAvailableSessions();
  };

  const handleExportPDF = async () => {
    if (!analyticsData) return;
    
    try {
      await exportAnalyticsAsPDF(analyticsData, selectedSession);
    } catch (error) {
      console.error('PDF export failed:', error);
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
      setSelectedSessionsForComparison([]);
    }
  };

  const handleSessionSelectionForComparison = (sessionId, checked) => {
    if (checked) {
      if (selectedSessionsForComparison.length < 4) {
        setSelectedSessionsForComparison([...selectedSessionsForComparison, sessionId]);
      }
    } else {
      setSelectedSessionsForComparison(selectedSessionsForComparison.filter(id => id !== sessionId));
    }
  };

  const canStartComparison = selectedSessionsForComparison.length >= 2;

  const tabs = [
    { id: 'kpis', name: 'KPIs', icon: TrendingUp },
    { id: 'charts', name: 'Charts', icon: LineChart },
    { id: 'recommendations', name: 'Recommendations', icon: AlertCircle },
  ];

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div className="analytics-header-content">
          <div className="analytics-header-inner">
            <div className="analytics-title-section">
              <Link to="/simulation" className="btn btn-outline btn-sm">
                <ArrowLeft />
                Back
              </Link>
              <h1 className="analytics-title">
                <Activity />
                Analytics Dashboard
              </h1>
            </div>
            
            <div className="analytics-actions">
              <select
                value={selectedSession}
                onChange={(e) => handleSessionChange(e.target.value)}
                className="form-control"
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

              <button
                onClick={handleRefresh}
                disabled={!selectedSession || loading}
                className="btn btn-outline btn-sm"
                title="Refresh Data"
              >
                <RefreshCw className={loading ? 'animate-spin' : ''} />
              </button>

              <button
                onClick={handleCompareToggle}
                className="btn btn-secondary btn-sm"
              >
                <GitCompare />
                Compare
              </button>

              <button
                onClick={handleExportPDF}
                disabled={!analyticsData}
                className="btn btn-primary btn-sm"
              >
                <Download />
                Export PDF
              </button>

              <button
                onClick={handleExportData}
                disabled={!analyticsData}
                className="btn btn-outline btn-sm"
              >
                <FileText />
                Export Data
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Session Comparison Selector */}
      {showComparison && (
        <div className="alert alert-info">
          <div className="analytics-content">
            <div className="flex items-center justify-between flex-wrap gap-md">
              <div className="flex-1">
                <h3 className="font-medium mb-sm">
                  Select sessions to compare (choose 2-4 sessions):
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-sm">
                  {availableSessions
                    .filter(session => session.can_analyze)
                    .slice(0, 8)
                    .map(session => (
                      <label key={session.session_id} className="flex items-center gap-sm">
                        <input
                          type="checkbox"
                          checked={selectedSessionsForComparison.includes(session.session_id)}
                          onChange={(e) => handleSessionSelectionForComparison(session.session_id, e.target.checked)}
                          disabled={!selectedSessionsForComparison.includes(session.session_id) && selectedSessionsForComparison.length >= 4}
                          className="form-control"
                        />
                        <span className="text-sm">
                          {session.network_id || 'Unknown'} - {new Date(session.created_at).toLocaleDateString()}
                        </span>
                      </label>
                    ))}
                </div>
              </div>
              
              <div className="btn-group">
                <button
                  onClick={() => setShowComparison(false)}
                  className="btn btn-outline btn-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Open comparison modal with selected sessions
                  }}
                  disabled={!canStartComparison}
                  className="btn btn-primary btn-sm"
                >
                  Compare ({selectedSessionsForComparison.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="analytics-content">
        {/* Session Info Bar */}
        {selectedSession && (
          <div className="card mb-lg">
            <div className="card-body">
              <div className="flex items-center justify-between flex-wrap gap-md">
                <div className="flex items-center gap-lg flex-wrap">
                  <div className="flex items-center gap-sm">
                    <Database />
                    <div>
                      <p className="font-medium">Session ID</p>
                      <p className="text-sm text-muted">{selectedSession}</p>
                    </div>
                  </div>
                
                  {analyticsData?.analysis_timestamp && (
                    <div className="flex items-center gap-sm">
                      <Calendar />
                      <div>
                        <p className="font-medium">Analyzed</p>
                        <p className="text-sm text-muted">
                          {new Date(analyticsData.analysis_timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  )}

                  {simulationStatus === 'running' && (
                    <div className="status-indicator status-running">
                      <div className="status-dot"></div>
                      Live Session
                    </div>
                  )}
                </div>

                {analyticsData?.recommendations && (
                  <div className="text-right">
                    <p className="font-medium">
                      {analyticsData.recommendations.length} Recommendations
                    </p>
                    <p className="text-sm text-muted">
                      {analyticsData.recommendations.filter(r => r.priority === 'high').length} High Priority
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="alert alert-error">
            <AlertCircle />
            <div>
              <h3 className="font-medium">Error Loading Analytics</h3>
              <p className="mt-xs">{error}</p>
            </div>
          </div>
        )}

        {/* No Session Selected State */}
        {!selectedSession && !loading && (
          <div className="card">
            <div className="card-body text-center py-xl">
              <Eye className="icon-large icon-muted icon-center mb-md" />
              <h3 className="mb-sm">Select a Session to Analyze</h3>
              <p className="text-muted mb-md">
                Choose a simulation session from the dropdown above to view detailed analytics.
              </p>
              {availableSessions.filter(s => s.can_analyze).length === 0 && (
                <p className="text-sm text-muted">
                  No analyzable sessions found. Run a simulation to generate analytics data.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="card">
            <div className="card-body text-center py-xl">
              <RefreshCw className="icon-medium icon-primary icon-center animate-spin mb-md" />
              <p>Loading analytics data...</p>
            </div>
          </div>
        )}

        {/* Analytics Content */}
        {analyticsData && !loading && !error && (
          <div className="space-y-lg">
            {/* Tab Navigation */}
            <div className="card">
              <div className="card-header">
                <div className="btn-group">
                  {tabs.map(tab => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-outline'}`}
                      >
                        <Icon />
                        {tab.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Tab Content */}
            <div className="card">
              <div className="card-body">
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
