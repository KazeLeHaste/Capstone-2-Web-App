/**
 * Safety Analysis Component
 * 
 * Provides comprehensive safety metrics visualization including
 * collision analysis, risk assessments, and safety trend monitoring.
 * 
 * Author: Traffic Simulator Team
 * Date: December 2025
 */

import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Shield, AlertTriangle, Clock, MapPin, TrendingDown, Award, Zap } from 'lucide-react';

const SafetyAnalysis = ({ analyticsData, loading = false }) => {
  const [selectedView, setSelectedView] = useState('overview');

  const kpis = analyticsData?.kpis || {};
  const timeSeries = analyticsData?.time_series || [];
  
  // Time-based safety events (from time series)
  const safetyTimeData = timeSeries.map((ts, index) => ({
    time: index,
    timeLabel: new Date(ts.time * 1000).toLocaleTimeString(),
    collisions: ts.collisions || 0,
    teleports: ts.teleports || 0,
    halting: ts.halting_vehicles || 0,
    safetyIndex: Math.max(0, 100 - (ts.collisions || 0) * 20 - (ts.teleports || 0) * 5)
  }));

  // Critical periods analysis
  const criticalPeriods = useMemo(() => {
    const periods = [];
    
    safetyTimeData.forEach((data, index) => {
      if (data.collisions > 0 || data.teleports > 2) {
        periods.push({
          time: data.timeLabel,
          timeIndex: index,
          collisions: data.collisions,
          teleports: data.teleports,
          severity: data.collisions > 0 ? 'High' : 'Medium'
        });
      }
    });
    
    return periods;
  }, [safetyTimeData]);

  const safetyScore = kpis.composite_safety_score || 0;
  const collisionDensity = kpis.collision_density || 0;
  const teleportDensity = kpis.teleport_density || 0;
  const emergencyStops = kpis.avg_emergency_stops || 0;

  // Safety improvement suggestions
  const suggestions = useMemo(() => {
    const improvements = [];
    
    if (safetyScore < 70) {
      improvements.push({
        type: 'critical',
        title: 'Overall Safety Critical',
        message: 'Safety score is below acceptable levels. Immediate action required.',
        priority: 'High',
        icon: AlertTriangle
      });
    }
    
    if (collisionDensity > 0.1) {
      improvements.push({
        type: 'warning',
        title: 'High Collision Risk',
        message: 'Consider implementing traffic calming measures or speed limits.',
        priority: 'High',
        icon: Shield
      });
    }
    
    if (teleportDensity > 2) {
      improvements.push({
        type: 'info',
        title: 'Flow Disruption',
        message: 'Frequent teleports indicate severe congestion. Optimize signal timing.',
        priority: 'Medium',
        icon: TrendingDown
      });
    }
    
    if (emergencyStops > 5) {
      improvements.push({
        type: 'warning',
        title: 'Excessive Emergency Stops',
        message: 'High emergency braking suggests potential safety hazards.',
        priority: 'Medium',
        icon: AlertTriangle
      });
    }
    
    return improvements;
  }, [safetyScore, collisionDensity, teleportDensity, emergencyStops]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-4 bg-secondary rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-secondary rounded"></div>
        </div>
      </div>
    );
  }

  if (!analyticsData || analyticsData.error) {
    return (
      <div className="text-center py-12">
        <Shield className="mx-auto h-12 w-12 text-secondary" />
        <h3 className="mt-2 text-lg font-medium text-primary">No Safety Data Available</h3>
        <p className="mt-1 text-secondary">
          Run a simulation to analyze safety metrics and risk factors
        </p>
      </div>
    );
  }
  
  // Safety metrics
  const highDecelEvents = kpis.high_deceleration_events || 0;
  
  // Safety categories for radar chart
  const safetyRadarData = [
    {
      category: 'Collision Risk',
      score: Math.max(0, 100 - collisionDensity * 50),
      fullMark: 100
    },
    {
      category: 'Flow Stability',
      score: Math.max(0, 100 - teleportDensity * 20),
      fullMark: 100
    },
    {
      category: 'Emergency Response',
      score: Math.max(0, 100 - emergencyStops * 10),
      fullMark: 100
    },
    {
      category: 'Speed Management',
      score: Math.max(0, 100 - (kpis.avg_speed || 0) / 50 * 100),
      fullMark: 100
    },
    {
      category: 'Traffic Control',
      score: kpis.efficiency_score || 0,
      fullMark: 100
    },
    {
      category: 'Overall Safety',
      score: safetyScore,
      fullMark: 100
    }
  ];

  // Risk factors analysis
  const riskFactors = [
    {
      factor: 'High Speed Variance',
      risk: Math.min(100, (kpis.edge_utilization_variance || 0) * 100),
      impact: 'High',
      color: '#EF4444',
      icon: Zap
    },
    {
      factor: 'Congestion Density',
      risk: Math.min(100, (kpis.avg_density || 0) * 2),
      impact: 'Medium',
      color: '#F59E0B',
      icon: MapPin
    },
    {
      factor: 'Network Bottlenecks',
      risk: Math.min(100, (1 - (kpis.network_efficiency_index || 1)) * 100),
      impact: 'High',
      color: '#EF4444',
      icon: AlertTriangle
    },
    {
      factor: 'Time Loss Events',
      risk: Math.min(100, (kpis.avg_time_loss || 0) / 2),
      impact: 'Medium',
      color: '#8B5CF6',
      icon: Clock
    }
  ];

  const viewConfigs = {
    overview: {
      title: 'Safety Overview',
      description: 'Key safety metrics and overall assessment'
    },
    trends: {
      title: 'Safety Trends',
      description: 'Time-based safety event analysis'
    },
    risks: {
      title: 'Risk Assessment',
      description: 'Detailed risk factor analysis'
    },
    improvements: {
      title: 'Safety Improvements',
      description: 'Recommendations and action items'
    }
  };

  const renderView = () => {
    switch (selectedView) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Safety Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg border border-gray-200 text-center">
                <Shield className="mx-auto w-8 h-8 text-green-600 mb-2" />
                <div className="text-3xl font-bold text-green-600 mb-1">
                  {safetyScore.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Safety Score</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full progress-bar-dynamic safety-score"
                    style={{ width: `${safetyScore}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg border border-gray-200 text-center">
                <AlertTriangle className="mx-auto w-8 h-8 text-red-600 mb-2" />
                <div className="text-3xl font-bold text-red-600 mb-1">
                  {collisionDensity.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">Collision Density</div>
              </div>

              <div className="bg-white p-6 rounded-lg border border-gray-200 text-center">
                <TrendingDown className="mx-auto w-8 h-8 text-orange-600 mb-2" />
                <div className="text-3xl font-bold text-orange-600 mb-1">
                  {teleportDensity.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Teleport Density</div>
              </div>

              <div className="bg-white p-6 rounded-lg border border-gray-200 text-center">
                <Zap className="mx-auto w-8 h-8 text-purple-600 mb-2" />
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {emergencyStops.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Emergency Stops</div>
              </div>
            </div>

            {/* Safety Radar Chart */}
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Safety Profile</h4>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={safetyRadarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="category" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="Safety Score"
                    dataKey="score"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}/100`, 'Score']} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'trends':
        return (
          <div className="space-y-6">
            {/* Safety Trends Over Time */}
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Safety Events Timeline</h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={safetyTimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timeLabel" />
                  <YAxis yAxisId="events" orientation="left" />
                  <YAxis yAxisId="index" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="events" dataKey="collisions" fill="#EF4444" name="Collisions" />
                  <Bar yAxisId="events" dataKey="teleports" fill="#F59E0B" name="Teleports" />
                  <Line 
                    yAxisId="index" 
                    type="monotone" 
                    dataKey="safetyIndex" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="Safety Index"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Critical Periods */}
            {criticalPeriods.length > 0 && (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Critical Periods</h4>
                <div className="space-y-3">
                  {criticalPeriods.map((period, index) => (
                    <div key={index} className={`p-4 rounded-lg border-l-4 ${
                      period.severity === 'High' ? 'bg-red-50 border-red-500' : 'bg-yellow-50 border-yellow-500'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-semibold text-gray-900">
                            Time: {period.time}
                          </div>
                          <div className="text-sm text-gray-600">
                            {period.collisions > 0 && `${period.collisions} collision(s)`}
                            {period.collisions > 0 && period.teleports > 0 && ', '}
                            {period.teleports > 0 && `${period.teleports} teleport(s)`}
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          period.severity === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {period.severity} Risk
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'risks':
        return (
          <div className="space-y-6">
            {/* Risk Factors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {riskFactors.map((risk) => {
                const Icon = risk.icon;
                return (
                  <div key={risk.factor} className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center space-x-3 mb-4">
                      <Icon className="w-6 h-6 dynamic-color-icon" style={{ color: risk.color }} />
                      <h4 className="text-lg font-semibold text-gray-900">{risk.factor}</h4>
                    </div>
                    <div className="text-2xl font-bold mb-2 dynamic-color-text" style={{ color: risk.color }}>
                      {risk.risk.toFixed(1)}%
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className="h-2 rounded-full progress-bar-dynamic risk-factor"
                        style={{ 
                          backgroundColor: risk.color,
                          width: `${risk.risk}%` 
                        }}
                      ></div>
                    </div>
                    <div className={`inline-block px-2 py-1 rounded text-xs ${
                      risk.impact === 'High' ? 'bg-red-100 text-red-800' :
                      risk.impact === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {risk.impact} Impact
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Risk Distribution Chart */}
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Risk Factor Distribution</h4>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={riskFactors}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="factor" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Risk Level']} />
                  <Bar dataKey="risk" name="Risk Level">
                    {riskFactors.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'improvements':
        return (
          <div className="space-y-6">
            {/* Safety Recommendations */}
            {suggestions.length > 0 ? (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Safety Recommendations</h4>
                <div className="space-y-4">
                  {suggestions.map((suggestion, index) => {
                    const Icon = suggestion.icon;
                    return (
                      <div key={index} className={`p-4 rounded-lg border-l-4 ${
                        suggestion.type === 'critical' ? 'bg-red-50 border-red-500' :
                        suggestion.type === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                        'bg-blue-50 border-blue-500'
                      }`}>
                        <div className="flex items-start space-x-3">
                          <Icon className={`w-5 h-5 mt-1 ${
                            suggestion.type === 'critical' ? 'text-red-500' :
                            suggestion.type === 'warning' ? 'text-yellow-500' :
                            'text-blue-500'
                          }`} />
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h5 className="font-semibold text-gray-900">{suggestion.title}</h5>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                suggestion.priority === 'High' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {suggestion.priority} Priority
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mt-1">{suggestion.message}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 rounded-lg border border-gray-200 text-center">
                <Award className="mx-auto w-12 h-12 text-green-600 mb-4" />
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Excellent Safety Performance!</h4>
                <p className="text-gray-600">No critical safety issues detected. Keep up the good work!</p>
              </div>
            )}

            {/* Action Items */}
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h4>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <div className="font-medium text-gray-900">Monitor High-Risk Periods</div>
                    <div className="text-sm text-gray-600">Increase surveillance during identified critical time periods</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <div className="font-medium text-gray-900">Optimize Signal Timing</div>
                    <div className="text-sm text-gray-600">Adjust traffic light cycles to reduce stops and delays</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <div className="font-medium text-gray-900">Implement Speed Management</div>
                    <div className="text-sm text-gray-600">Consider variable speed limits based on traffic conditions</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* View Selection */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(viewConfigs).map(([key, config]) => (
          <button
            key={key}
            onClick={() => setSelectedView(key)}
            className={`btn ${
              selectedView === key ? 'btn-primary' : 'btn-outline'
            }`}
          >
            {config.title}
          </button>
        ))}
      </div>

      {/* Current View Header */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-900">
          {viewConfigs[selectedView].title}
        </h3>
        <p className="text-gray-600 mt-1">
          {viewConfigs[selectedView].description}
        </p>
      </div>

      {/* View Content */}
      {renderView()}
    </div>
  );
};

export default SafetyAnalysis;