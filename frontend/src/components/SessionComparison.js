/**
 * Session Comparison Component
 * 
 * Provides side-by-side comparison of multiple simulation sessions
 * with KPI comparisons, charts, and performance analysis.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { 
  GitCompare,
  AlertTriangle,
  CheckCircle,
  RotateCcw,
  Download,
  Filter,
  Trophy
} from 'lucide-react';
import axios from 'axios';

const SessionComparison = ({ selectedSessions, onClose }) => {
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [viewMode, setViewMode] = useState('overview'); // overview, detailed, radar

  const loadComparisonData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.post('/api/analytics/compare', {
        session_ids: selectedSessions
      });

      if (response.data.success) {
        setComparisonData(response.data.comparison);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  }, [selectedSessions]);

  useEffect(() => {
    if (selectedSessions && selectedSessions.length >= 2) {
      loadComparisonData();
    }
  }, [selectedSessions, loadComparisonData]);

  const exportComparison = () => {
    if (!comparisonData) return;
    
    const dataStr = JSON.stringify(comparisonData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `session_comparison_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <div className="text-center">
            <RotateCcw className="animate-spin mx-auto h-8 w-8 text-blue-500" />
            <p className="mt-4 text-gray-600">Comparing sessions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <div className="text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-red-500" />
            <p className="mt-4 text-gray-600">{error}</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!comparisonData) {
    return null;
  }

  // Prepare chart data
  const kpiComparison = comparisonData.kpi_comparison || {};
  const sessions = comparisonData.sessions || [];
  
  // Create comparative metrics data
  const metricsForChart = Object.entries(kpiComparison).map(([kpi, data]) => {
    const chartPoint = { metric: kpi.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) };
    
    sessions.forEach(sessionId => {
      if (data.values && data.values[sessionId] !== undefined) {
        chartPoint[sessionId.substring(0, 8)] = data.values[sessionId];
      }
    });
    
    return chartPoint;
  });

  // Filter metrics for display
  const importantMetrics = [
    'avg_speed', 'avg_travel_time', 'avg_waiting_time', 
    'throughput', 'total_vehicles_completed', 'avg_time_loss'
  ];
  
  const filteredMetrics = metricsForChart.filter(metric => 
    selectedMetric === 'all' || 
    importantMetrics.some(im => metric.metric.toLowerCase().includes(im.replace(/_/g, ' ')))
  );

  // Prepare radar chart data
  const radarData = importantMetrics.map(metric => {
    const metricData = kpiComparison[metric];
    if (!metricData || !metricData.values) return null;
    
    const dataPoint = {
      metric: metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      fullMark: Math.max(...Object.values(metricData.values)) * 1.2
    };
    
    sessions.forEach((sessionId, index) => {
      const value = metricData.values[sessionId];
      if (value !== undefined) {
        // Normalize values for radar chart (0-100 scale)
        const normalized = metric.includes('time') || metric.includes('loss') ? 
          Math.max(0, 100 - (value / dataPoint.fullMark * 100)) : // Invert for time-based metrics
          (value / dataPoint.fullMark * 100);
        dataPoint[`Session ${index + 1}`] = normalized;
      }
    });
    
    return dataPoint;
  }).filter(Boolean);

  // Best performing session info
  const bestSession = comparisonData.best_performing_session;
  const bestSessionData = comparisonData.session_data?.[bestSession];

  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <GitCompare className="w-6 h-6 text-blue-600 mr-3" />
              <div>
                <h2 className="text-xl font-bold text-gray-900">Session Comparison</h2>
                <p className="text-sm text-gray-600">
                  Comparing {sessions.length} simulation sessions
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={exportComparison}
                className="flex items-center px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Best Performing Session */}
            {bestSession && bestSessionData && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <div className="flex items-center mb-4">
                  <Trophy className="w-6 h-6 text-yellow-600 mr-3" />
                  <h3 className="text-lg font-semibold text-green-900">Best Performing Session</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-green-700 font-medium">Session ID</p>
                    <p className="text-green-900">{bestSession}</p>
                  </div>
                  <div>
                    <p className="text-sm text-green-700 font-medium">Network</p>
                    <p className="text-green-900">
                      {bestSessionData.session_data?.metadata?.network_id || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-green-700 font-medium">Overall Score</p>
                    <p className="text-green-900">Highest Performance</p>
                  </div>
                </div>
              </div>
            )}

            {/* View Mode Selector */}
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value)}
                className="border rounded px-3 py-2 text-sm"
              >
                <option value="overview">Overview Comparison</option>
                <option value="detailed">Detailed Metrics</option>
                <option value="radar">Performance Radar</option>
              </select>
              
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="border rounded px-3 py-2 text-sm"
              >
                <option value="all">All Metrics</option>
                <option value="important">Key Metrics Only</option>
              </select>
            </div>

            {/* Overview Mode */}
            {viewMode === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* KPI Comparison Chart */}
                <div className="bg-white border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">KPI Comparison</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={filteredMetrics.slice(0, 6)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="metric" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      {sessions.map((session, index) => (
                        <Bar 
                          key={session} 
                          dataKey={session.substring(0, 8)} 
                          fill={colors[index % colors.length]}
                          name={`Session ${index + 1}`}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Session Summary Cards */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Session Summaries</h3>
                  {sessions.map((sessionId, index) => {
                    const sessionData = comparisonData.session_data[sessionId];
                    const kpis = sessionData?.kpis || {};
                    const isWinner = sessionId === bestSession;
                    
                    return (
                      <div 
                        key={sessionId} 
                        className={`border rounded-lg p-4 ${
                          isWinner ? 'border-green-300 bg-green-50' : 'border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-gray-900">
                            Session {index + 1}
                            {isWinner && (
                              <Trophy className="inline-block w-4 h-4 text-yellow-500 ml-2" />
                            )}
                          </h4>
                          <span className="text-xs text-gray-500">
                            {sessionId.substring(0, 8)}...
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <span className="text-gray-600">Avg Speed:</span>
                            <span className="ml-1 font-medium">
                              {((kpis.avg_speed || 0) * 3.6).toFixed(1)} km/h
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Throughput:</span>
                            <span className="ml-1 font-medium">
                              {(kpis.throughput || 0).toFixed(0)} veh/h
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Waiting Time:</span>
                            <span className="ml-1 font-medium">
                              {(kpis.avg_waiting_time || 0).toFixed(1)}s
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Vehicles:</span>
                            <span className="ml-1 font-medium">
                              {kpis.total_vehicles_completed || 0}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Detailed Mode */}
            {viewMode === 'detailed' && (
              <div className="space-y-6">
                <div className="bg-white border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Metrics Comparison</h3>
                  <ResponsiveContainer width="100%" height={600}>
                    <BarChart data={filteredMetrics} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="metric" type="category" width={150} />
                      <Tooltip />
                      <Legend />
                      {sessions.map((session, index) => (
                        <Bar 
                          key={session} 
                          dataKey={session.substring(0, 8)} 
                          fill={colors[index % colors.length]}
                          name={`Session ${index + 1}`}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Detailed Comparison Table */}
                <div className="bg-white border rounded-lg overflow-hidden">
                  <h3 className="text-lg font-semibold text-gray-900 p-6 border-b">Metric Details</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Metric
                          </th>
                          {sessions.map((session, index) => (
                            <th key={session} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Session {index + 1}
                            </th>
                          ))}
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Best
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {Object.entries(kpiComparison).map(([kpi, data]) => (
                          <tr key={kpi} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm font-medium text-gray-900">
                              {kpi.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </td>
                            {sessions.map(session => (
                              <td key={session} className="px-6 py-4 text-sm text-gray-500">
                                {data.values?.[session]?.toFixed(2) || 'N/A'}
                              </td>
                            ))}
                            <td className="px-6 py-4 text-sm">
                              <span className="inline-flex items-center text-green-600">
                                <CheckCircle className="w-4 h-4 mr-1" />
                                {sessions.findIndex(s => s === data.best_session) + 1 || 'N/A'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Radar Mode */}
            {viewMode === 'radar' && radarData.length > 0 && (
              <div className="bg-white border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Radar</h3>
                <ResponsiveContainer width="100%" height={500}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" />
                    <PolarRadiusAxis angle={60} domain={[0, 100]} />
                    {sessions.map((session, index) => (
                      <Radar
                        key={session}
                        name={`Session ${index + 1}`}
                        dataKey={`Session ${index + 1}`}
                        stroke={colors[index % colors.length]}
                        fill={colors[index % colors.length]}
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                    ))}
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
                <p className="text-sm text-gray-600 mt-4 text-center">
                  Larger areas indicate better performance. Time-based metrics are inverted for intuitive visualization.
                </p>
              </div>
            )}

            {/* Recommendations Comparison */}
            <div className="bg-white border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {sessions.map((sessionId, index) => {
                  const sessionRecs = comparisonData.recommendation_comparison?.all_recommendations?.[sessionId] || [];
                  const highPriority = sessionRecs.filter(r => r.priority === 'high').length;
                  const mediumPriority = sessionRecs.filter(r => r.priority === 'medium').length;
                  const lowPriority = sessionRecs.filter(r => r.priority === 'low').length;
                  
                  return (
                    <div key={sessionId} className="border rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">
                        Session {index + 1}
                        {sessionId === bestSession && (
                          <Trophy className="inline-block w-4 h-4 text-yellow-500 ml-2" />
                        )}
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-red-600">High Priority:</span>
                          <span className="font-medium">{highPriority}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-yellow-600">Medium Priority:</span>
                          <span className="font-medium">{mediumPriority}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-blue-600">Low Priority:</span>
                          <span className="font-medium">{lowPriority}</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span className="text-gray-600">Total:</span>
                          <span className="font-medium">{sessionRecs.length}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionComparison;
