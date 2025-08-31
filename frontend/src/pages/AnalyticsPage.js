/**
 * Analytics Page Component
 * 
 * Displays comprehensive analytics and statistics from traffic simulation results.
 * Features charts, graphs, and exportable reports.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Clock, 
  Activity,
  Download,
  RefreshCw,
  ArrowLeft,
  FileText,
  PieChart,
  LineChart,
  Info,
  AlertCircle
} from 'lucide-react';

const AnalyticsPage = ({ socket, simulationData, simulationStatus }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('vehicles');
  const [timeRange, setTimeRange] = useState('all');
  
  useEffect(() => {
    if (simulationData) {
      updateAnalytics(simulationData);
    }
  }, [simulationData]);
  
  useEffect(() => {
    // Listen for analytics data from socket
    if (socket) {
      socket.on('analytics_data', handleAnalyticsData);
      
      return () => {
        socket.off('analytics_data', handleAnalyticsData);
      };
    }
  }, [socket]);
  
  const handleAnalyticsData = (data) => {
    setAnalyticsData(data.data);
  };
  
  const updateAnalytics = (data) => {
    if (!data) return;
    
    const newDataPoint = {
      timestamp: data.timestamp || Date.now(),
      vehicles: data.statistics?.total_vehicles || 0,
      averageSpeed: calculateAverageSpeed(data.vehicles || []),
      totalDistance: calculateTotalDistance(data.vehicles || []),
      density: calculateDensity(data.edges || []),
      flow: calculateFlow(data.edges || [])
    };
    
    setTimeSeriesData(prev => {
      const updated = [...prev, newDataPoint];
      // Keep only last 100 data points to prevent memory issues
      return updated.slice(-100);
    });
  };
  
  const calculateAverageSpeed = (vehicles) => {
    if (vehicles.length === 0) return 0;
    const totalSpeed = vehicles.reduce((sum, vehicle) => sum + (vehicle.speed || 0), 0);
    return totalSpeed / vehicles.length;
  };
  
  const calculateTotalDistance = (vehicles) => {
    return vehicles.reduce((sum, vehicle) => sum + (vehicle.distance || 0), 0);
  };
  
  const calculateDensity = (edges) => {
    if (edges.length === 0) return 0;
    const totalOccupancy = edges.reduce((sum, edge) => sum + (edge.occupancy || 0), 0);
    return totalOccupancy / edges.length;
  };
  
  const calculateFlow = (edges) => {
    if (edges.length === 0) return 0;
    const totalFlow = edges.reduce((sum, edge) => sum + (edge.vehicle_count || 0), 0);
    return totalFlow;
  };
  
  const getCurrentStats = () => {
    if (!simulationData) return null;
    
    const vehicles = simulationData.vehicles || [];
    const edges = simulationData.edges || [];
    
    return {
      totalVehicles: vehicles.length,
      averageSpeed: calculateAverageSpeed(vehicles).toFixed(1),
      maxSpeed: vehicles.length > 0 ? Math.max(...vehicles.map(v => v.speed || 0)).toFixed(1) : 0,
      totalDistance: (calculateTotalDistance(vehicles) / 1000).toFixed(1),
      density: (calculateDensity(edges) * 100).toFixed(1),
      totalEdges: edges.length,
      averageVehiclesPerEdge: edges.length > 0 ? (calculateFlow(edges) / edges.length).toFixed(1) : 0,
      simulationTime: simulationData.statistics?.simulation_time || 0
    };
  };
  
  const getVehicleTypeDistribution = () => {
    if (!simulationData?.vehicles) return [];
    
    const distribution = {};
    simulationData.vehicles.forEach(vehicle => {
      const type = vehicle.type || 'unknown';
      distribution[type] = (distribution[type] || 0) + 1;
    });
    
    return Object.entries(distribution).map(([type, count]) => ({
      type,
      count,
      percentage: simulationData.vehicles.length > 0 ? (count / simulationData.vehicles.length * 100).toFixed(1) : 0
    }));
  };
  
  const getSpeedDistribution = () => {
    if (!simulationData?.vehicles) return [];
    
    const speedRanges = [
      { range: '0-5 m/s', min: 0, max: 5, count: 0 },
      { range: '5-10 m/s', min: 5, max: 10, count: 0 },
      { range: '10-15 m/s', min: 10, max: 15, count: 0 },
      { range: '15-20 m/s', min: 15, max: 20, count: 0 },
      { range: '>20 m/s', min: 20, max: Infinity, count: 0 }
    ];
    
    simulationData.vehicles.forEach(vehicle => {
      const speed = vehicle.speed || 0;
      const range = speedRanges.find(r => speed >= r.min && speed < r.max);
      if (range) range.count++;
    });
    
    return speedRanges;
  };
  
  const getTimeSeries = () => {
    const filteredData = timeRange === 'all' 
      ? timeSeriesData 
      : timeSeriesData.slice(-parseInt(timeRange));
    
    return filteredData.map((point, index) => ({
      ...point,
      index,
      time: new Date(point.timestamp).toLocaleTimeString()
    }));
  };
  
  const handleExportData = () => {
    const data = {
      currentStats: getCurrentStats(),
      vehicleTypes: getVehicleTypeDistribution(),
      speedDistribution: getSpeedDistribution(),
      timeSeries: getTimeSeries(),
      exportTime: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `traffic_simulation_analytics_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  const currentStats = getCurrentStats();
  const vehicleTypes = getVehicleTypeDistribution();
  const speedDistribution = getSpeedDistribution();
  const timeSeries = getTimeSeries();
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Simulation Analytics
              </h1>
              <p className="text-gray-600">
                Real-time analysis and statistics from your traffic simulation
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleExportData}
                disabled={!currentStats}
                className="btn btn-outline flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export Data</span>
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
        
        {/* Status */}
        <div className="mb-6">
          <div className={`inline-flex items-center space-x-2 px-3 py-2 rounded-lg ${
            simulationStatus === 'running' ? 'bg-green-100 text-green-800' :
            simulationStatus === 'finished' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            <Activity className="w-4 h-4" />
            <span className="font-medium">
              Simulation Status: {simulationStatus === 'running' ? 'Running' : 
                              simulationStatus === 'finished' ? 'Finished' : 'Stopped'}
            </span>
          </div>
        </div>
        
        {!currentStats && (
          <div className="text-center py-12">
            <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No Analytics Data Available
            </h3>
            <p className="text-gray-600 mb-4">
              Start a simulation to generate analytics data and insights.
            </p>
            <Link to="/simulation" className="btn btn-primary">
              Go to Simulation
            </Link>
          </div>
        )}
        
        {currentStats && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="card">
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total Vehicles</p>
                      <p className="text-2xl font-bold text-gray-900">{currentStats.totalVehicles}</p>
                    </div>
                    <Users className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Average Speed</p>
                      <p className="text-2xl font-bold text-gray-900">{currentStats.averageSpeed} <span className="text-sm text-gray-500">m/s</span></p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-green-600" />
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total Distance</p>
                      <p className="text-2xl font-bold text-gray-900">{currentStats.totalDistance} <span className="text-sm text-gray-500">km</span></p>
                    </div>
                    <Activity className="w-8 h-8 text-purple-600" />
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Simulation Time</p>
                      <p className="text-2xl font-bold text-gray-900">{currentStats.simulationTime.toFixed(0)} <span className="text-sm text-gray-500">s</span></p>
                    </div>
                    <Clock className="w-8 h-8 text-orange-600" />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Charts Section */}
            <div className="grid lg:grid-cols-2 gap-8 mb-8">
              {/* Vehicle Type Distribution */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <PieChart className="w-5 h-5" />
                    <span>Vehicle Type Distribution</span>
                  </h3>
                </div>
                <div className="card-body">
                  {vehicleTypes.length > 0 ? (
                    <div className="space-y-4">
                      {vehicleTypes.map((type, index) => (
                        <div key={type.type} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`w-4 h-4 rounded ${
                              index === 0 ? 'bg-blue-500' : 
                              index === 1 ? 'bg-red-500' : 'bg-green-500'
                            }`}></div>
                            <span className="font-medium capitalize">{type.type}</span>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold">{type.count}</div>
                            <div className="text-sm text-gray-500">{type.percentage}%</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">No vehicle data available</p>
                  )}
                </div>
              </div>
              
              {/* Speed Distribution */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <BarChart3 className="w-5 h-5" />
                    <span>Speed Distribution</span>
                  </h3>
                </div>
                <div className="card-body">
                  <div className="space-y-3">
                    {speedDistribution.map((range, index) => (
                      <div key={range.range} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{range.range}</span>
                        <div className="flex items-center space-x-3">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ 
                                width: currentStats.totalVehicles > 0 
                                  ? `${(range.count / currentStats.totalVehicles * 100)}%` 
                                  : '0%' 
                              }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600 w-8">{range.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Time Series */}
            <div className="card mb-8">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <LineChart className="w-5 h-5" />
                    <span>Time Series Data</span>
                  </h3>
                  
                  <div className="flex items-center space-x-3">
                    <select
                      value={selectedMetric}
                      onChange={(e) => setSelectedMetric(e.target.value)}
                      className="text-sm border rounded px-2 py-1"
                    >
                      <option value="vehicles">Vehicle Count</option>
                      <option value="averageSpeed">Average Speed</option>
                      <option value="density">Traffic Density</option>
                      <option value="flow">Traffic Flow</option>
                    </select>
                    
                    <select
                      value={timeRange}
                      onChange={(e) => setTimeRange(e.target.value)}
                      className="text-sm border rounded px-2 py-1"
                    >
                      <option value="all">All Data</option>
                      <option value="50">Last 50 Points</option>
                      <option value="20">Last 20 Points</option>
                      <option value="10">Last 10 Points</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="card-body">
                {timeSeries.length > 0 ? (
                  <div className="h-64 relative">
                    <div className="absolute inset-0 flex items-end space-x-1 px-4 pb-4">
                      {timeSeries.map((point, index) => {
                        const maxValue = Math.max(...timeSeries.map(p => p[selectedMetric] || 0));
                        const height = maxValue > 0 ? (point[selectedMetric] / maxValue) * 100 : 0;
                        
                        return (
                          <div
                            key={index}
                            className="flex-1 bg-blue-500 rounded-t opacity-80 hover:opacity-100 transition-opacity"
                            style={{ height: `${height}%`, minHeight: '2px' }}
                            title={`${point.time}: ${point[selectedMetric]?.toFixed?.(2) || point[selectedMetric]}`}
                          ></div>
                        );
                      })}
                    </div>
                    
                    <div className="absolute bottom-0 left-4 right-4 text-xs text-gray-500 text-center">
                      Time →
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center">
                    <p className="text-gray-500">No time series data available yet</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Detailed Statistics */}
            <div className="grid md:grid-cols-2 gap-8">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Performance Metrics</h3>
                </div>
                <div className="card-body space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Speed Recorded</span>
                    <span className="font-medium">{currentStats.maxSpeed} m/s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Traffic Density</span>
                    <span className="font-medium">{currentStats.density}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Network Edges</span>
                    <span className="font-medium">{currentStats.totalEdges}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Vehicles/Edge</span>
                    <span className="font-medium">{currentStats.averageVehiclesPerEdge}</span>
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <Info className="w-5 h-5" />
                    <span>Analysis Summary</span>
                  </h3>
                </div>
                <div className="card-body">
                  <div className="space-y-3 text-sm">
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                      <h4 className="font-medium text-blue-900">Traffic Flow</h4>
                      <p className="text-blue-800">
                        {currentStats.averageSpeed > 10 ? 'Good' : 
                         currentStats.averageSpeed > 5 ? 'Moderate' : 'Congested'} traffic flow 
                        with average speed of {currentStats.averageSpeed} m/s
                      </p>
                    </div>
                    
                    <div className="p-3 bg-green-50 border border-green-200 rounded">
                      <h4 className="font-medium text-green-900">Vehicle Distribution</h4>
                      <p className="text-green-800">
                        {currentStats.totalVehicles} vehicles currently active in the simulation
                      </p>
                    </div>
                    
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <h4 className="font-medium text-yellow-900">Network Utilization</h4>
                      <p className="text-yellow-800">
                        {currentStats.density}% average occupancy across {currentStats.totalEdges} road segments
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
        
        {/* Navigation */}
        <div className="flex justify-between items-center mt-8">
          <Link to="/simulation" className="btn btn-secondary flex items-center space-x-2">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Simulation</span>
          </Link>
          
          <Link to="/" className="btn btn-primary">
            Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
