/**
 * Analytics Charts Component
 * 
 * Provides various chart visualizations for traffic simulation data
 * including time series, distribution charts, and comparative views.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { 
  TrendingUp, 
  BarChart3, 
  PieChart as PieIcon, 
  Clock,
  Users,
  Gauge
} from 'lucide-react';

const AnalyticsCharts = ({ analyticsData, loading = false }) => {
  const [selectedChart, setSelectedChart] = useState('timeSeries');

  // Define colors first to avoid temporal dead zone errors
  const colors = {
    primary: '#3B82F6',
    secondary: '#10B981',
    accent: '#F59E0B',
    danger: '#EF4444',
    purple: '#8B5CF6',
    teal: '#14B8A6'
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-4 bg-secondary rounded w-1/4 mb-4"></div>
          <div className="h-80 bg-secondary rounded"></div>
        </div>
      </div>
    );
  }

  if (!analyticsData || analyticsData.error) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="mx-auto h-12 w-12 text-secondary" />
        <h3 className="mt-2 text-lg font-medium text-primary">No Chart Data Available</h3>
        <p className="mt-1 text-secondary">
          {analyticsData?.error || 'Run a simulation to see analytics charts'}
        </p>
      </div>
    );
  }

  // Prepare time series data
  const timeSeriesData = analyticsData.time_series?.map(ts => ({
    time: new Date(ts.time * 1000).toLocaleTimeString(),
    timeSeconds: ts.time,
    running: ts.running_vehicles,
    halting: ts.halting_vehicles,
    speed: ts.mean_speed * 3.6, // Convert m/s to km/h
    waitingTime: ts.mean_waiting_time
  })) || [];

  // Prepare vehicle type data
  const vehicleTypeData = Object.entries(analyticsData.vehicle_type_breakdown || {}).map(([type, stats]) => ({
    type: type.charAt(0).toUpperCase() + type.slice(1),
    count: stats.count,
    avgSpeed: stats.avg_speed * 3.6, // Convert to km/h
    avgDistance: stats.avg_distance / 1000, // Convert to km
    avgTime: stats.avg_time / 60 // Convert to minutes
  }));

  // Prepare route distribution data
  const routeDistributionData = [
    { name: 'Short Routes (<2km)', value: 25, fill: '#8884d8' },
    { name: 'Medium Routes (2-5km)', value: 45, fill: '#82ca9d' },
    { name: 'Long Routes (5-10km)', value: 25, fill: '#ffc658' },
    { name: 'Very Long Routes (>10km)', value: 5, fill: '#ff7300' }
  ];

  // Performance comparison data
  const performanceData = [
    {
      metric: 'Avg Speed',
      actual: (analyticsData.kpis?.avg_speed || 0) * 3.6,
      target: 30,
      unit: 'km/h'
    },
    {
      metric: 'Throughput',
      actual: analyticsData.kpis?.throughput || 0,
      target: 1000,
      unit: 'veh/h'
    },
    {
      metric: 'Waiting Time',
      actual: analyticsData.kpis?.avg_waiting_time || 0,
      target: 30,
      unit: 'seconds'
    },
    {
      metric: 'Time Loss',
      actual: analyticsData.kpis?.avg_time_loss || 0,
      target: 60,
      unit: 'seconds'
    }
  ];

  // Temporal patterns (hourly breakdown)
  const temporalData = Array.from({ length: 24 }, (_, hour) => {
    const hourData = timeSeriesData.filter(ts => {
      const time = new Date(ts.timeSeconds * 1000);
      return time.getHours() === hour;
    });
    
    return {
      hour: `${hour}:00`,
      avgVehicles: hourData.length > 0 ? 
        hourData.reduce((sum, d) => sum + d.running, 0) / hourData.length : 0,
      avgSpeed: hourData.length > 0 ? 
        hourData.reduce((sum, d) => sum + d.speed, 0) / hourData.length : 0
    };
  });

  // Prepare emissions data
  const emissionsData = [
    {
      metric: 'CO2 Emissions',
      value: analyticsData.kpis?.total_co2 || 0,
      perKm: analyticsData.kpis?.avg_co2_per_km || 0,
      unit: 'kg',
      color: colors.danger
    },
    {
      metric: 'NOx Emissions',
      value: analyticsData.kpis?.total_nox || 0,
      perKm: (analyticsData.kpis?.total_nox || 0) / Math.max(analyticsData.kpis?.total_distance_traveled || 1, 1) * 1000,
      unit: 'g',
      color: colors.accent
    },
    {
      metric: 'Fuel Consumption',
      value: analyticsData.kpis?.total_fuel_consumption || 0,
      perKm: analyticsData.kpis?.avg_fuel_per_km || 0,
      unit: 'L',
      color: colors.primary
    },
    {
      metric: 'Energy Usage',
      value: analyticsData.kpis?.total_energy_consumption || 0,
      perKm: (analyticsData.kpis?.total_energy_consumption || 0) / Math.max(analyticsData.kpis?.total_distance_traveled || 1, 1) * 1000,
      unit: 'kWh',
      color: colors.secondary
    }
  ];

  // Prepare safety metrics data
  const safetyData = [
    {
      metric: 'Safety Score',
      value: analyticsData.kpis?.composite_safety_score || 0,
      max: 100,
      color: colors.secondary
    },
    {
      metric: 'Collision Density',
      value: analyticsData.kpis?.collision_density || 0,
      max: 1.0,
      color: colors.danger
    },
    {
      metric: 'Emergency Stops',
      value: analyticsData.kpis?.avg_emergency_stops || 0,
      max: 10,
      color: colors.accent
    },
    {
      metric: 'High Decel Events',
      value: analyticsData.kpis?.high_deceleration_events || 0,
      max: 50,
      color: colors.purple
    }
  ];

  // Prepare network performance data
  const networkData = [
    {
      metric: 'Avg Edge Occupancy',
      value: (analyticsData.kpis?.avg_edge_occupancy || 0) * 100,
      unit: '%',
      color: colors.primary
    },
    {
      metric: 'Max Edge Occupancy',
      value: (analyticsData.kpis?.max_edge_occupancy || 0) * 100,
      unit: '%',
      color: colors.danger
    },
    {
      metric: 'Network Efficiency',
      value: (analyticsData.kpis?.network_efficiency_index || 0) * 100,
      unit: '%',
      color: colors.secondary
    },
    {
      metric: 'Edge Utilization Variance',
      value: analyticsData.kpis?.edge_utilization_variance || 0,
      unit: '',
      color: colors.purple
    }
  ];

  // Prepare quality scores data
  const qualityScores = [
    {
      category: 'Environmental',
      score: analyticsData.kpis?.environmental_score || 0,
      color: colors.secondary
    },
    {
      category: 'Efficiency',
      score: analyticsData.kpis?.efficiency_score || 0,
      color: colors.primary
    },
    {
      category: 'Safety',
      score: analyticsData.kpis?.safety_score || 0,
      color: colors.accent
    },
    {
      category: 'Overall',
      score: analyticsData.kpis?.overall_performance_score || 0,
      color: colors.purple
    }
  ];

  const chartConfigs = {
    timeSeries: {
      title: 'Traffic Flow Over Time',
      icon: TrendingUp,
      description: 'Vehicle counts and speeds throughout the simulation'
    },
    vehicleTypes: {
      title: 'Vehicle Type Analysis',
      icon: Users,
      description: 'Breakdown by vehicle categories'
    },
    performance: {
      title: 'Performance vs Targets',
      icon: Gauge,
      description: 'Key metrics compared to target values'
    },
    temporal: {
      title: 'Hourly Traffic Patterns',
      icon: Clock,
      description: 'Traffic variation by time of day'
    },
    routes: {
      title: 'Route Distribution',
      icon: PieIcon,
      description: 'Distribution of route lengths'
    },
    emissions: {
      title: 'Environmental Impact',
      icon: TrendingUp,
      description: 'CO2, NOx, and fuel consumption analysis'
    },
    safety: {
      title: 'Safety Metrics',
      icon: BarChart3,
      description: 'Collision risk, emergency stops, and safety scores'
    },
    network: {
      title: 'Network Performance',
      icon: Users,
      description: 'Edge occupancy, density, and flow analysis'
    },
    quality: {
      title: 'Quality Scores',
      icon: Gauge,
      description: 'Environmental, efficiency, and safety scores'
    }
  };

  const renderChart = () => {
    switch (selectedChart) {
      case 'timeSeries':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="vehicles" orientation="left" />
              <YAxis yAxisId="speed" orientation="right" />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'speed' ? `${value.toFixed(1)} km/h` : value,
                  name === 'speed' ? 'Average Speed' : 
                  name === 'running' ? 'Running Vehicles' : 'Halting Vehicles'
                ]}
              />
              <Legend />
              <Area 
                yAxisId="vehicles"
                type="monotone" 
                dataKey="running" 
                stackId="1"
                stroke={colors.primary} 
                fill={colors.primary} 
                fillOpacity={0.6}
                name="Running"
              />
              <Area 
                yAxisId="vehicles"
                type="monotone" 
                dataKey="halting" 
                stackId="1"
                stroke={colors.danger} 
                fill={colors.danger}
                fillOpacity={0.6}
                name="Halting"
              />
              <Line 
                yAxisId="speed"
                type="monotone" 
                dataKey="speed" 
                stroke={colors.accent}
                strokeWidth={3}
                name="Speed"
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'vehicleTypes':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={vehicleTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis yAxisId="count" orientation="left" />
              <YAxis yAxisId="speed" orientation="right" />
              <Tooltip 
                formatter={(value, name) => [
                  name.includes('Speed') ? `${value.toFixed(1)} km/h` :
                  name.includes('Distance') ? `${value.toFixed(1)} km` :
                  name.includes('Time') ? `${value.toFixed(1)} min` : value,
                  name
                ]}
              />
              <Legend />
              <Bar yAxisId="count" dataKey="count" fill={colors.primary} name="Vehicle Count" />
              <Line yAxisId="speed" dataKey="avgSpeed" stroke={colors.secondary} name="Avg Speed" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'performance':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={performanceData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="metric" type="category" width={100} />
              <Tooltip 
                formatter={(value, name) => [
                  `${value.toFixed(1)} ${performanceData.find(d => d.metric === name)?.unit || ''}`,
                  name === 'actual' ? 'Actual Value' : 'Target Value'
                ]}
              />
              <Legend />
              <Bar dataKey="actual" fill={colors.primary} name="Actual" />
              <Bar dataKey="target" fill={colors.secondary} name="Target" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'temporal':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={temporalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis yAxisId="vehicles" orientation="left" />
              <YAxis yAxisId="speed" orientation="right" />
              <Tooltip />
              <Legend />
              <Line 
                yAxisId="vehicles"
                type="monotone" 
                dataKey="avgVehicles" 
                stroke={colors.primary}
                name="Avg Vehicles"
              />
              <Line 
                yAxisId="speed"
                type="monotone" 
                dataKey="avgSpeed" 
                stroke={colors.accent}
                name="Avg Speed (km/h)"
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'routes':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={routeDistributionData}
                cx="50%"
                cy="50%"
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {routeDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'emissions':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={emissionsData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  `${value.toFixed(2)} ${emissionsData.find(d => d.metric === name)?.unit || ''}`,
                  name
                ]}
              />
              <Legend />
              <Bar dataKey="value" name="Total" fill={colors.primary} />
              <Bar dataKey="perKm" name="Per Km" fill={colors.secondary} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'safety':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={safetyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  `${value.toFixed(2)}${name === 'Safety Score' ? '/100' : ''}`,
                  name
                ]}
              />
              <Legend />
              <Bar dataKey="value" name="Value">
                {safetyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'network':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={networkData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  `${value.toFixed(2)}${networkData.find(d => d.metric === name)?.unit || ''}`,
                  name
                ]}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke={colors.primary} 
                fill={colors.primary} 
                fillOpacity={0.6}
                name="Network Performance"
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'quality':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={qualityScores} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value) => [`${value.toFixed(1)}/100`, 'Score']}
              />
              <Legend />
              <Bar dataKey="score" name="Quality Score">
                {qualityScores.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Chart Selection */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(chartConfigs).map(([key, config]) => {
          const Icon = config.icon;
          return (
            <button
              key={key}
              onClick={() => setSelectedChart(key)}
              className={`btn ${
                selectedChart === key ? 'btn-primary' : 'btn-outline'
              }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {config.title}
            </button>
          );
        })}
      </div>

      {/* Chart Display */}
      <div className="analytics-chart-tile">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            {React.createElement(chartConfigs[selectedChart].icon, { className: "w-5 h-5 mr-2" })}
            {chartConfigs[selectedChart].title}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {chartConfigs[selectedChart].description}
          </p>
        </div>
        
        <div className="w-full">
          {renderChart()}
        </div>
      </div>

      {/* Chart Statistics */}
      {timeSeriesData.length > 0 && (
        <div className="analytics-chart-tile">
          <h4 className="text-md font-medium text-gray-900 mb-4">Chart Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Data Points</p>
              <p className="font-medium">{timeSeriesData.length}</p>
            </div>
            <div>
              <p className="text-gray-600">Peak Vehicles</p>
              <p className="font-medium">
                {Math.max(...timeSeriesData.map(d => d.running), 0)}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Avg Speed</p>
              <p className="font-medium">
                {timeSeriesData.length > 0 ? 
                  (timeSeriesData.reduce((sum, d) => sum + d.speed, 0) / timeSeriesData.length).toFixed(1) : 0
                } km/h
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsCharts;
