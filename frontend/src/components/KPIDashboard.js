/**
 * KPI Dashboard Component
 * 
 * Displays key performance indicators and statistics in a dashboard layout
 * with visual indicators and trend information.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React from 'react';
import { 
  Activity,
  Clock,
  Gauge,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Zap,
  MapPin,
  Car,
  Timer
} from 'lucide-react';

const KPIDashboard = ({ kpis, loading = false }) => {
  
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg border p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="text-center py-12">
        <Activity className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">No KPIs Available</h3>
        <p className="mt-1 text-gray-500">Run a simulation to see performance indicators</p>
      </div>
    );
  }

  // Helper function to format values
  const formatValue = (value, unit = '', decimals = 1) => {
    if (typeof value !== 'number' || isNaN(value)) return 'N/A';
    return `${value.toFixed(decimals)}${unit}`;
  };

  // Helper function to get trend indicator
  const getTrendIndicator = (value, threshold, inverse = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 
      <TrendingUp className="w-4 h-4 text-green-500" /> : 
      <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  // Helper function to get status color
  const getStatusColor = (value, thresholds, inverse = false) => {
    if (typeof value !== 'number' || isNaN(value)) return 'gray';
    
    const { good, warning } = thresholds;
    
    if (inverse) {
      if (value <= good) return 'green';
      if (value <= warning) return 'yellow';
      return 'red';
    } else {
      if (value >= good) return 'green';
      if (value >= warning) return 'yellow';
      return 'red';
    }
  };

  // Define KPI configurations
  const kpiConfigs = [
    {
      id: 'vehicles',
      title: 'Total Vehicles',
      icon: Car,
      value: kpis.total_vehicles_completed || 0,
      unit: '',
      decimals: 0,
      description: 'Completed trips',
      color: 'blue',
      additionalInfo: `${kpis.total_vehicles_running || 0} still running`
    },
    {
      id: 'avgSpeed',
      title: 'Average Speed',
      icon: Gauge,
      value: (kpis.avg_speed || 0) * 3.6, // Convert m/s to km/h
      unit: ' km/h',
      decimals: 1,
      description: 'Network average',
      thresholds: { good: 25, warning: 15 },
      color: getStatusColor((kpis.avg_speed || 0) * 3.6, { good: 25, warning: 15 })
    },
    {
      id: 'avgTravelTime',
      title: 'Avg Travel Time',
      icon: Clock,
      value: (kpis.avg_travel_time || 0) / 60, // Convert seconds to minutes
      unit: ' min',
      decimals: 1,
      description: 'Per trip average',
      thresholds: { good: 15, warning: 30 },
      inverse: true,
      color: getStatusColor((kpis.avg_travel_time || 0) / 60, { good: 15, warning: 30 }, true)
    },
    {
      id: 'avgWaitingTime',
      title: 'Avg Waiting Time',
      icon: Timer,
      value: kpis.avg_waiting_time || 0,
      unit: ' s',
      decimals: 1,
      description: 'Time spent waiting',
      thresholds: { good: 30, warning: 60 },
      inverse: true,
      color: getStatusColor(kpis.avg_waiting_time || 0, { good: 30, warning: 60 }, true)
    },
    {
      id: 'throughput',
      title: 'Throughput',
      icon: Activity,
      value: kpis.throughput || 0,
      unit: ' veh/h',
      decimals: 0,
      description: 'Vehicles per hour',
      thresholds: { good: 800, warning: 400 },
      color: getStatusColor(kpis.throughput || 0, { good: 800, warning: 400 })
    },
    {
      id: 'avgRouteLength',
      title: 'Avg Route Length',
      icon: MapPin,
      value: (kpis.avg_route_length || 0) / 1000, // Convert meters to km
      unit: ' km',
      decimals: 2,
      description: 'Average distance',
      color: 'blue'
    },
    {
      id: 'totalDistance',
      title: 'Total Distance',
      icon: Zap,
      value: (kpis.total_distance_traveled || 0) / 1000, // Convert to km
      unit: ' km',
      decimals: 0,
      description: 'All vehicles combined',
      color: 'purple'
    },
    {
      id: 'timeLoss',
      title: 'Time Loss',
      icon: AlertTriangle,
      value: (kpis.avg_time_loss || 0) / 60, // Convert to minutes
      unit: ' min',
      decimals: 1,
      description: 'Due to congestion',
      thresholds: { good: 2, warning: 5 },
      inverse: true,
      color: getStatusColor((kpis.avg_time_loss || 0) / 60, { good: 2, warning: 5 }, true)
    }
  ];

  // Safety metrics (if available)
  const safetyMetrics = [];
  if (kpis.total_teleports > 0) {
    safetyMetrics.push({
      id: 'teleports',
      title: 'Teleports',
      icon: AlertTriangle,
      value: kpis.total_teleports,
      unit: '',
      decimals: 0,
      description: 'Traffic issues',
      color: 'red'
    });
  }
  
  if (kpis.total_collisions > 0) {
    safetyMetrics.push({
      id: 'collisions',
      title: 'Collisions',
      icon: AlertTriangle,
      value: kpis.total_collisions,
      unit: '',
      decimals: 0,
      description: 'Safety incidents',
      color: 'red'
    });
  }

  // Environmental metrics (if available)
  const environmentalMetrics = [];
  if (kpis.total_co2 > 0) {
    environmentalMetrics.push({
      id: 'co2',
      title: 'CO2 Emissions',
      icon: AlertTriangle,
      value: (kpis.total_co2 || 0) / 1000, // Convert mg to g
      unit: ' g',
      decimals: 1,
      description: 'Total emissions',
      color: 'red'
    });
  }

  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    red: 'bg-red-50 border-red-200',
    purple: 'bg-purple-50 border-purple-200',
    gray: 'bg-gray-50 border-gray-200'
  };

  const iconColorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    gray: 'text-gray-600'
  };

  const textColorClasses = {
    blue: 'text-blue-900',
    green: 'text-green-900',
    yellow: 'text-yellow-900',
    red: 'text-red-900',
    purple: 'text-purple-900',
    gray: 'text-gray-900'
  };

  return (
    <div className="space-y-6">
      {/* Main KPIs */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Performance Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpiConfigs.map((kpi) => {
            const Icon = kpi.icon;
            const colorClass = colorClasses[kpi.color] || colorClasses.gray;
            const iconColorClass = iconColorClasses[kpi.color] || iconColorClasses.gray;
            const textColorClass = textColorClasses[kpi.color] || textColorClasses.gray;

            return (
              <div key={kpi.id} className={`bg-white rounded-lg border p-6 ${colorClass}`}>
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`w-6 h-6 ${iconColorClass}`} />
                  {kpi.thresholds && kpi.value !== null && !isNaN(kpi.value) && 
                    getTrendIndicator(kpi.value, kpi.thresholds.warning, kpi.inverse)
                  }
                </div>
                
                <div className={`text-2xl font-bold ${textColorClass} mb-1`}>
                  {formatValue(kpi.value, kpi.unit, kpi.decimals)}
                </div>
                
                <div className="text-sm font-medium text-gray-900 mb-1">
                  {kpi.title}
                </div>
                
                <div className="text-xs text-gray-600">
                  {kpi.description}
                </div>
                
                {kpi.additionalInfo && (
                  <div className="text-xs text-gray-500 mt-2">
                    {kpi.additionalInfo}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Safety Metrics */}
      {safetyMetrics.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
            Safety Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {safetyMetrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div key={metric.id} className="bg-white rounded-lg border border-red-200 p-6">
                  <Icon className="w-6 h-6 text-red-600 mb-2" />
                  <div className="text-2xl font-bold text-red-900 mb-1">
                    {formatValue(metric.value, metric.unit, metric.decimals)}
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-1">
                    {metric.title}
                  </div>
                  <div className="text-xs text-gray-600">
                    {metric.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Environmental Metrics */}
      {environmentalMetrics.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
            Environmental Impact
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {environmentalMetrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div key={metric.id} className="bg-white rounded-lg border border-green-200 p-6">
                  <Icon className="w-6 h-6 text-green-600 mb-2" />
                  <div className="text-2xl font-bold text-green-900 mb-1">
                    {formatValue(metric.value, metric.unit, metric.decimals)}
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-1">
                    {metric.title}
                  </div>
                  <div className="text-xs text-gray-600">
                    {metric.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* KPI Summary */}
      <div className="bg-white rounded-lg border p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Performance Summary</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Traffic Flow</h5>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Efficiency:</span>
                <span className={kpis.avg_speed > 8 ? 'text-green-600' : 'text-red-600'}>
                  {kpis.avg_speed > 8 ? 'Good' : 'Poor'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Congestion:</span>
                <span className={kpis.avg_waiting_time < 60 ? 'text-green-600' : 'text-red-600'}>
                  {kpis.avg_waiting_time < 60 ? 'Low' : 'High'}
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Network Usage</h5>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Utilization:</span>
                <span className={kpis.throughput > 500 ? 'text-green-600' : 'text-yellow-600'}>
                  {kpis.throughput > 500 ? 'High' : 'Moderate'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Capacity:</span>
                <span className="text-gray-900">
                  {((kpis.total_vehicles_completed || 0) / Math.max(kpis.throughput || 1, 1) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Overall Rating</h5>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Performance:</span>
                <span className={
                  kpis.avg_speed > 8 && kpis.avg_waiting_time < 60 && kpis.throughput > 500
                    ? 'text-green-600' 
                    : kpis.avg_speed > 5 && kpis.avg_waiting_time < 120
                    ? 'text-yellow-600' 
                    : 'text-red-600'
                }>
                  {kpis.avg_speed > 8 && kpis.avg_waiting_time < 60 && kpis.throughput > 500
                    ? 'Excellent' 
                    : kpis.avg_speed > 5 && kpis.avg_waiting_time < 120
                    ? 'Good' 
                    : 'Needs Improvement'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Safety:</span>
                <span className={kpis.total_teleports === 0 && kpis.total_collisions === 0 ? 'text-green-600' : 'text-red-600'}>
                  {kpis.total_teleports === 0 && kpis.total_collisions === 0 ? 'Good' : 'Issues Detected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KPIDashboard;
