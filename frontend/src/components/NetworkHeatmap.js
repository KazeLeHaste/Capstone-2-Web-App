/**
 * Network Heatmap Component
 * 
 * Provides spatial visualization of network performance data
 * including edge occupancy, density, and traffic flow heatmaps.
 * 
 * Author: Traffic Simulator Team
 * Date: December 2025
 */

import React, { useState, useMemo } from 'react';
import { MapPin, Thermometer, Activity, TrendingUp, Info } from 'lucide-react';

const NetworkHeatmap = ({ analyticsData, loading = false }) => {
  const [selectedMetric, setSelectedMetric] = useState('occupancy');
  const [showLegend, setShowLegend] = useState(true);

  const networkData = analyticsData?.network_analysis;
  
  // Metrics configuration
  const metrics = {
    occupancy: {
      title: 'Edge Occupancy',
      icon: Activity,
      description: 'Vehicle presence on road segments',
      unit: '%',
      colorScale: ['#10B981', '#F59E0B', '#EF4444'], // Green to Red
      dataKey: 'avg_occupancy'
    },
    density: {
      title: 'Traffic Density',
      icon: TrendingUp,
      description: 'Vehicle density per road segment',
      unit: 'veh/km',
      colorScale: ['#3B82F6', '#8B5CF6', '#EF4444'], // Blue to Purple to Red
      dataKey: 'avg_density'
    },
    waitingTime: {
      title: 'Waiting Time',
      icon: Thermometer,
      description: 'Average waiting time per edge',
      unit: 'sec',
      colorScale: ['#10B981', '#F59E0B', '#EF4444'], // Green to Red
      dataKey: 'avg_waiting_time'
    },
    efficiency: {
      title: 'Edge Efficiency',
      icon: TrendingUp,
      description: 'Traffic flow efficiency index',
      unit: '',
      colorScale: ['#EF4444', '#F59E0B', '#10B981'], // Red to Green (reversed)
      dataKey: 'efficiency_index'
    }
  };

  const currentMetric = metrics[selectedMetric];

  // Color interpolation function
  function interpolateColor(colors, value) {
    if (value <= 0) return colors[0];
    if (value >= 1) return colors[colors.length - 1];
    
    const scaledValue = value * (colors.length - 1);
    const lowerIndex = Math.floor(scaledValue);
    const upperIndex = Math.ceil(scaledValue);
    const t = scaledValue - lowerIndex;
    
    if (lowerIndex === upperIndex) return colors[lowerIndex];
    
    // Simple color interpolation (hex colors)
    const lowerColor = hexToRgb(colors[lowerIndex]);
    const upperColor = hexToRgb(colors[upperIndex]);
    
    const r = Math.round(lowerColor.r + (upperColor.r - lowerColor.r) * t);
    const g = Math.round(lowerColor.g + (upperColor.g - lowerColor.g) * t);
    const b = Math.round(lowerColor.b + (upperColor.b - lowerColor.b) * t);
    
    return `rgb(${r}, ${g}, ${b})`;
  }

  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  }

  // Process network performance data for visualization
  const processedData = useMemo(() => {
    if (!networkData?.edge_performance) return [];

    return Object.entries(networkData.edge_performance).map(([edgeId, data]) => {
      const value = data[currentMetric.dataKey] || 0;
      const normalizedValue = Math.min(Math.max(value, 0), 1); // Normalize to 0-1
      
      return {
        id: edgeId,
        value: value,
        normalizedValue: normalizedValue,
        color: interpolateColor(currentMetric.colorScale, normalizedValue),
        performance: data
      };
    }).sort((a, b) => b.value - a.value);
  }, [networkData, selectedMetric, currentMetric]);

  // Get statistics for current metric
  const stats = useMemo(() => {
    if (processedData.length === 0) return { min: 0, max: 0, avg: 0 };
    
    const values = processedData.map(d => d.value);
    return {
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((sum, v) => sum + v, 0) / values.length
    };
  }, [processedData]);

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

  if (!analyticsData || analyticsData.error || !analyticsData.network_analysis) {
    return (
      <div className="text-center py-12">
        <MapPin className="mx-auto h-12 w-12 text-secondary" />
        <h3 className="mt-2 text-lg font-medium text-primary">No Network Data Available</h3>
        <p className="mt-1 text-secondary">
          Network analysis data is required for heatmap visualization
        </p>
      </div>
    );
  }

  // Color interpolation function
  function interpolateColor(colors, value) {
    if (value <= 0) return colors[0];
    if (value >= 1) return colors[colors.length - 1];
    
    const scaledValue = value * (colors.length - 1);
    const lowerIndex = Math.floor(scaledValue);
    const upperIndex = Math.ceil(scaledValue);
    const t = scaledValue - lowerIndex;
    
    if (lowerIndex === upperIndex) return colors[lowerIndex];
    
    // Simple color interpolation (hex colors)
    const lowerColor = hexToRgb(colors[lowerIndex]);
    const upperColor = hexToRgb(colors[upperIndex]);
    
    const r = Math.round(lowerColor.r + (upperColor.r - lowerColor.r) * t);
    const g = Math.round(lowerColor.g + (upperColor.g - lowerColor.g) * t);
    const b = Math.round(lowerColor.b + (upperColor.b - lowerColor.b) * t);
    
    return `rgb(${r}, ${g}, ${b})`;
  }

  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  }

  return (
    <div className="space-y-6">
      {/* Metric Selection */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(metrics).map(([key, metric]) => {
          const Icon = metric.icon;
          return (
            <button
              key={key}
              onClick={() => setSelectedMetric(key)}
              className={`btn ${
                selectedMetric === key ? 'btn-primary' : 'btn-outline'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{metric.title}</span>
            </button>
          );
        })}
      </div>

      {/* Header with metric info */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <currentMetric.icon className="w-6 h-6 text-primary" />
              <div>
                <h3 className="card-title">{currentMetric.title}</h3>
                <p className="text-secondary">{currentMetric.description}</p>
              </div>
            </div>
            <button
              onClick={() => setShowLegend(!showLegend)}
              className="btn btn-outline btn-sm"
            >
              <Info className="w-4 h-4" />
              <span>Legend</span>
            </button>
          </div>
        </div>
        
        <div className="card-body">
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {stats.min.toFixed(2)}
              </div>
              <div className="text-secondary">Minimum</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {stats.avg.toFixed(2)}
              </div>
              <div className="text-secondary">Average</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {stats.max.toFixed(2)}
              </div>
              <div className="text-secondary">Maximum</div>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="card">
          <div className="card-header">
            <h4 className="card-title">Color Scale</h4>
          </div>
          <div className="card-body">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div 
                  className="h-4 rounded dynamic-gradient-bar"
                  style={{
                    background: `linear-gradient(to right, ${currentMetric.colorScale.join(', ')})`
                  }}
                ></div>
                <div className="flex justify-between text-xs text-secondary mt-1">
                  <span>Low</span>
                  <span>Medium</span>
                  <span>High</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Network Visualization (List-based for now, could be enhanced with actual map) */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-color">
          <h4 className="card-title">Network Segments</h4>
          <p className="text-secondary">Sorted by {currentMetric.title.toLowerCase()}</p>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {processedData.length === 0 ? (
            <div className="p-8 text-center text-secondary">
              No network data available
            </div>
          ) : (
            <div className="space-y-1">
              {processedData.slice(0, 50).map((edge, index) => (
                <div 
                  key={edge.id}
                  className="flex items-center space-x-4 p-3 border-b border-color hover:bg-secondary"
                >
                  <div className="flex-shrink-0">
                    <div 
                      className="w-4 h-4 rounded dynamic-color-indicator"
                      style={{ backgroundColor: edge.color }}
                    ></div>
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-primary">
                      Edge {edge.id}
                    </div>
                    <div className="text-xs text-secondary">
                      Rank: #{index + 1}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-primary">
                      {edge.value.toFixed(2)} {currentMetric.unit}
                    </div>
                    <div className="text-xs text-secondary">
                      {(edge.normalizedValue * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NetworkHeatmap;