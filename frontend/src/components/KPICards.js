/**
 * KPI Cards Component
 * 
 * Displays key performance indicators in an intuitive card layout
 * with color-coded status indicators and trend information.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React from 'react';
import { 
  Clock, 
  TrendingUp, 
  Users, 
  Gauge, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  Activity,
  Car,
  Route,
  Zap
} from 'lucide-react';

const KPICards = ({ kpis, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 12 }).map((_, index) => (
          <div key={index} className="bg-white rounded-lg border p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="text-center py-8">
        <Activity className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-gray-600">No KPI data available</p>
      </div>
    );
  }

  const getStatusColor = (value, thresholds) => {
    if (value >= thresholds.good) return 'text-green-600 bg-green-50 border-green-200';
    if (value >= thresholds.warning) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getStatusIcon = (value, thresholds) => {
    if (value >= thresholds.good) return <CheckCircle className="w-5 h-5" />;
    if (value >= thresholds.warning) return <AlertTriangle className="w-5 h-5" />;
    return <XCircle className="w-5 h-5" />;
  };

  const formatValue = (value, unit = '') => {
    if (typeof value !== 'number') return 'N/A';
    if (value === 0) return `0${unit}`;
    
    // Format large numbers
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M${unit}`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k${unit}`;
    if (value < 1) return `${value.toFixed(3)}${unit}`;
    if (value < 10) return `${value.toFixed(2)}${unit}`;
    return `${Math.round(value)}${unit}`;
  };

  const formatTime = (seconds) => {
    if (typeof seconds !== 'number') return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}min`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatSpeed = (speedMs) => {
    if (typeof speedMs !== 'number') return 'N/A';
    const kmh = speedMs * 3.6;
    return `${kmh.toFixed(1)} km/h`;
  };

  const kpiData = [
    // Vehicle Statistics
    {
      title: 'Total Vehicles',
      value: kpis.total_vehicles_completed || 0,
      unit: '',
      icon: Car,
      description: 'Completed trips',
      color: 'text-blue-600 bg-blue-50 border-blue-200'
    },
    {
      title: 'Avg Travel Time',
      value: formatTime(kpis.avg_travel_time || 0),
      unit: '',
      icon: Clock,
      description: 'Per vehicle trip',
      color: getStatusColor(kpis.avg_travel_time || 0, { good: 0, warning: 300, bad: 600 }),
      statusIcon: getStatusIcon(600 - (kpis.avg_travel_time || 600), { good: 300, warning: 150, bad: 0 })
    },
    {
      title: 'Avg Speed',
      value: formatSpeed(kpis.avg_speed || 0),
      unit: '',
      icon: Gauge,
      description: 'Network average',
      color: getStatusColor(kpis.avg_speed || 0, { good: 10, warning: 5, bad: 0 }),
      statusIcon: getStatusIcon(kpis.avg_speed || 0, { good: 10, warning: 5, bad: 0 })
    },
    {
      title: 'Throughput',
      value: formatValue(kpis.throughput || 0, ' veh/h'),
      unit: '',
      icon: TrendingUp,
      description: 'Vehicles per hour',
      color: getStatusColor(kpis.throughput || 0, { good: 1000, warning: 500, bad: 0 }),
      statusIcon: getStatusIcon(kpis.throughput || 0, { good: 1000, warning: 500, bad: 0 })
    },

    // Performance Metrics
    {
      title: 'Avg Waiting Time',
      value: formatTime(kpis.avg_waiting_time || 0),
      unit: '',
      icon: Clock,
      description: 'Time stopped in traffic',
      color: getStatusColor(kpis.avg_waiting_time || 0, { good: 0, warning: 30, bad: 60 }),
      statusIcon: getStatusIcon(60 - (kpis.avg_waiting_time || 60), { good: 50, warning: 25, bad: 0 })
    },
    {
      title: 'Time Loss',
      value: formatTime(kpis.avg_time_loss || 0),
      unit: '',
      icon: AlertTriangle,
      description: 'Delay vs free flow',
      color: getStatusColor(kpis.avg_time_loss || 0, { good: 0, warning: 60, bad: 120 }),
      statusIcon: getStatusIcon(120 - (kpis.avg_time_loss || 120), { good: 100, warning: 50, bad: 0 })
    },
    {
      title: 'Congestion Index',
      value: formatValue(kpis.congestion_index || 0),
      unit: '',
      icon: Activity,
      description: 'Speed ratio to free flow',
      color: getStatusColor(kpis.congestion_index || 0, { good: 0.8, warning: 0.5, bad: 0 }),
      statusIcon: getStatusIcon(kpis.congestion_index || 0, { good: 0.8, warning: 0.5, bad: 0 })
    },
    {
      title: 'Flow Rate',
      value: formatValue(kpis.flow_rate || 0, ' veh/s'),
      unit: '',
      icon: Zap,
      description: 'Vehicles per second',
      color: getStatusColor(kpis.flow_rate || 0, { good: 1, warning: 0.5, bad: 0 }),
      statusIcon: getStatusIcon(kpis.flow_rate || 0, { good: 1, warning: 0.5, bad: 0 })
    },

    // Route Metrics
    {
      title: 'Avg Route Length',
      value: formatValue(kpis.avg_route_length || 0, ' m'),
      unit: '',
      icon: Route,
      description: 'Distance per trip',
      color: 'text-indigo-600 bg-indigo-50 border-indigo-200'
    },
    {
      title: 'Total Distance',
      value: formatValue((kpis.total_distance_traveled || 0) / 1000, ' km'),
      unit: '',
      icon: TrendingUp,
      description: 'All vehicles combined',
      color: 'text-purple-600 bg-purple-50 border-purple-200'
    },

    // Safety Metrics
    {
      title: 'Teleports',
      value: kpis.total_teleports || 0,
      unit: '',
      icon: AlertTriangle,
      description: 'Emergency relocations',
      color: kpis.total_teleports > 0 ? 'text-red-600 bg-red-50 border-red-200' : 'text-green-600 bg-green-50 border-green-200',
      statusIcon: kpis.total_teleports === 0 ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />
    },
    {
      title: 'Collisions',
      value: kpis.total_collisions || 0,
      unit: '',
      icon: XCircle,
      description: 'Vehicle accidents',
      color: kpis.total_collisions > 0 ? 'text-red-600 bg-red-50 border-red-200' : 'text-green-600 bg-green-50 border-green-200',
      statusIcon: kpis.total_collisions === 0 ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />
    }
  ];

  // Add environmental metrics if available
  if (kpis.total_co2 > 0 || kpis.total_fuel_consumption > 0) {
    kpiData.push(
      {
        title: 'CO2 Emissions',
        value: formatValue((kpis.total_co2 || 0) / 1000, ' g'),
        unit: '',
        icon: AlertTriangle,
        description: 'Total carbon dioxide',
        color: 'text-orange-600 bg-orange-50 border-orange-200'
      },
      {
        title: 'Fuel Consumption',
        value: formatValue((kpis.total_fuel_consumption || 0) / 1000, ' g'),
        unit: '',
        icon: Users,
        description: 'Total fuel used',
        color: 'text-teal-600 bg-teal-50 border-teal-200'
      }
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Performance Indicators</h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center">
            <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
            Good
          </div>
          <div className="flex items-center">
            <AlertTriangle className="w-4 h-4 text-yellow-500 mr-1" />
            Warning
          </div>
          <div className="flex items-center">
            <XCircle className="w-4 h-4 text-red-500 mr-1" />
            Critical
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon;
          return (
            <div key={index} className={`p-4 rounded-lg border ${kpi.color}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Icon className="w-5 h-5 mr-2" />
                  <h4 className="text-sm font-medium">{kpi.title}</h4>
                </div>
                {kpi.statusIcon && (
                  <div className="flex items-center">
                    {kpi.statusIcon}
                  </div>
                )}
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold">
                  {kpi.value}
                  {kpi.unit}
                </p>
                <p className="text-xs opacity-75 mt-1">{kpi.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default KPICards;
