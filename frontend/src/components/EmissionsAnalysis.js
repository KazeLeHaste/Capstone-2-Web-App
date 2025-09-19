/**
 * Emissions Analysis Component
 * 
 * Provides detailed environmental impact visualization including
 * emissions breakdowns, fuel consumption, and sustainability metrics.
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
import { Leaf, Zap, Fuel, TreePine, AlertTriangle, Award } from 'lucide-react';

const EmissionsAnalysis = ({ analyticsData, loading = false }) => {
  const [selectedView, setSelectedView] = useState('overview');
  
  const kpis = analyticsData?.kpis || {};
  
  // Environmental metrics
  const environmentalScore = kpis.environmental_score || 0;
  const overallScore = kpis.overall_performance_score || 0;

  // Sustainability recommendations (moved up to avoid hooks rule violation)
  const recommendations = useMemo(() => {
    const recs = [];
    
    if ((kpis.total_co2 || 0) > 50) {
      recs.push({
        type: 'warning',
        title: 'High CO2 Emissions',
        message: 'Consider promoting electric vehicles or optimizing traffic flow',
        icon: AlertTriangle
      });
    }

    if ((kpis.avg_fuel_per_km || 0) > 0.1) {
      recs.push({
        type: 'info',
        title: 'Fuel Efficiency',
        message: 'Implementing eco-driving strategies could reduce fuel consumption',
        icon: Fuel
      });
    }

    if (environmentalScore < 60) {
      recs.push({
        type: 'error',
        title: 'Environmental Performance',
        message: 'Overall environmental score is below average - review traffic management',
        icon: Leaf
      });
    }

    return recs;
  }, [kpis, environmentalScore]);

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
        <Leaf className="mx-auto h-12 w-12 text-secondary" />
        <h3 className="mt-2 text-lg font-medium text-primary">No Emissions Data Available</h3>
        <p className="mt-1 text-secondary">
          Run a simulation with emissions output enabled to see environmental analysis
        </p>
      </div>
    );
  }
  
  // Emissions breakdown data
  const emissionsBreakdown = [
    {
      pollutant: 'CO2',
      value: kpis.total_co2 || 0,
      perKm: kpis.avg_co2_per_km || 0,
      unit: 'kg',
      color: '#EF4444',
      icon: AlertTriangle,
      impact: 'High',
      description: 'Primary greenhouse gas'
    },
    {
      pollutant: 'NOx',
      value: kpis.total_nox || 0,
      perKm: (kpis.total_nox || 0) / Math.max(kpis.total_distance_traveled || 1, 1) * 1000,
      unit: 'g',
      color: '#F59E0B',
      icon: AlertTriangle,
      impact: 'Medium',
      description: 'Nitrogen oxides - air quality concern'
    },
    {
      pollutant: 'CO',
      value: kpis.total_co || 0,
      perKm: (kpis.total_co || 0) / Math.max(kpis.total_distance_traveled || 1, 1) * 1000,
      unit: 'g',
      color: '#8B5CF6',
      icon: AlertTriangle,
      impact: 'Medium',
      description: 'Carbon monoxide - health hazard'
    },
    {
      pollutant: 'HC',
      value: kpis.total_hc || 0,
      perKm: (kpis.total_hc || 0) / Math.max(kpis.total_distance_traveled || 1, 1) * 1000,
      unit: 'g',
      color: '#06B6D4',
      icon: AlertTriangle,
      impact: 'Low',
      description: 'Hydrocarbons - ozone precursor'
    },
    {
      pollutant: 'PMx',
      value: kpis.total_pmx || 0,
      perKm: (kpis.total_pmx || 0) / Math.max(kpis.total_distance_traveled || 1, 1) * 1000,
      unit: 'g',
      color: '#84CC16',
      icon: AlertTriangle,
      impact: 'High',
      description: 'Particulate matter - respiratory health'
    }
  ];

  // Energy consumption data
  const energyData = [
    {
      type: 'Fuel Consumption',
      total: kpis.total_fuel_consumption || 0,
      perKm: kpis.avg_fuel_per_km || 0,
      unit: 'L',
      color: '#3B82F6',
      icon: Fuel
    },
    {
      type: 'Energy Consumption',
      total: kpis.total_energy_consumption || 0,
      perKm: (kpis.total_energy_consumption || 0) / Math.max(kpis.total_distance_traveled || 1, 1) * 1000,
      unit: 'kWh',
      color: '#10B981',
      icon: Zap
    }
  ];

  // Vehicle type emissions (mock data - would come from detailed analysis)
  const vehicleTypeEmissions = [
    { type: 'Cars', co2: 65, percentage: 70, color: '#3B82F6' },
    { type: 'Trucks', co2: 25, percentage: 15, color: '#EF4444' },
    { type: 'Buses', co2: 8, percentage: 10, color: '#F59E0B' },
    { type: 'Motorcycles', co2: 2, percentage: 5, color: '#10B981' }
  ];

  // Environmental impact categories
  const impactCategories = [
    {
      category: 'Air Quality',
      score: Math.max(0, 100 - (kpis.total_nox || 0) * 10),
      color: '#10B981',
      icon: TreePine
    },
    {
      category: 'Climate Impact',
      score: Math.max(0, 100 - (kpis.total_co2 || 0) / 10),
      color: '#3B82F6',
      icon: Leaf
    },
    {
      category: 'Energy Efficiency',
      score: Math.max(0, 100 - (kpis.total_fuel_consumption || 0) * 5),
      color: '#F59E0B',
      icon: Zap
    },
    {
      category: 'Sustainability',
      score: environmentalScore,
      color: '#8B5CF6',
      icon: Award
    }
  ];

  const viewConfigs = {
    overview: {
      title: 'Environmental Overview',
      description: 'Key environmental metrics and scores'
    },
    emissions: {
      title: 'Emissions Breakdown',
      description: 'Detailed pollutant analysis'
    },
    energy: {
      title: 'Energy Analysis',
      description: 'Fuel and energy consumption patterns'
    },
    comparison: {
      title: 'Impact Comparison',
      description: 'Environmental impact categories'
    }
  };



  const renderView = () => {
    switch (selectedView) {
      case 'overview':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Environmental Score */}
            <div className="card">
              <div className="card-header">
                <h4 className="card-title">Environmental Score</h4>
              </div>
              <div className="card-body text-center">
                <div className="text-4xl font-bold text-success mb-2">
                  {environmentalScore.toFixed(1)}/100
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-bar-fill progress-bar-success"
                    style={{ width: `${environmentalScore}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Total Emissions */}
            <div className="card">
              <div className="card-header">
                <h4 className="card-title">Total CO2 Emissions</h4>
              </div>
              <div className="card-body text-center">
                <div className="text-4xl font-bold text-error mb-2">
                  {(kpis.total_co2 || 0).toFixed(2)} kg
                </div>
                <div className="text-secondary">
                  {(kpis.avg_co2_per_km || 0).toFixed(3)} kg/km average
                </div>
              </div>
            </div>

            {/* Impact Categories Chart */}
            <div className="lg:col-span-2">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={impactCategories}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}/100`, 'Score']} />
                  <Bar dataKey="score" name="Environmental Score">
                    {impactCategories.map((category, index) => (
                      <Cell key={`cell-${index}`} fill={category.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'emissions':
        return (
          <div className="space-y-6">
            {/* Emissions Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {emissionsBreakdown.map((emission) => {
                const Icon = emission.icon;
                return (
                  <div key={emission.pollutant} className="card">
                    <div className="card-header">
                      <div className="flex items-center justify-between">
                        <h4 className="card-title">{emission.pollutant}</h4>
                        <Icon className="w-5 h-5" style={{ color: emission.color }} />
                      </div>
                    </div>
                    <div className="card-body">
                      <div className="text-2xl font-bold mb-1" style={{ color: emission.color }}>
                        {emission.value.toFixed(2)} {emission.unit}
                      </div>
                      <div className="text-secondary mb-2">
                        {emission.perKm.toFixed(3)} {emission.unit}/km
                      </div>
                      <div className="text-sm text-secondary">
                        {emission.description}
                      </div>
                      <div className={`inline-block px-2 py-1 rounded text-xs mt-2 ${
                        emission.impact === 'High' ? 'badge-error' :
                        emission.impact === 'Medium' ? 'badge-warning' :
                        'badge-success'
                      }`}>
                        {emission.impact} Impact
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Emissions Breakdown Chart */}
            <div className="card">
              <div className="card-header">
                <h4 className="card-title">Emissions by Type</h4>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={emissionsBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="pollutant" />
                    <YAxis />
                    <Tooltip formatter={(value, name, props) => [
                      `${value.toFixed(2)} ${props.payload.unit}`,
                      name
                    ]} />
                    <Bar dataKey="value" name="Total Emissions">
                      {emissionsBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        );

      case 'energy':
        return (
          <div className="space-y-6">
            {/* Energy Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {energyData.map((energy) => {
                const Icon = energy.icon;
                return (
                  <div key={energy.type} className="card">
                    <div className="card-header">
                      <div className="flex items-center space-x-3">
                        <Icon className="w-6 h-6" style={{ color: energy.color }} />
                        <h4 className="card-title">{energy.type}</h4>
                      </div>
                    </div>
                    <div className="card-body">
                      <div className="text-3xl font-bold mb-2" style={{ color: energy.color }}>
                        {energy.total.toFixed(2)} {energy.unit}
                      </div>
                      <div className="text-secondary">
                        {energy.perKm.toFixed(3)} {energy.unit}/km average
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Vehicle Type Emissions */}
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">CO2 by Vehicle Type</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={vehicleTypeEmissions}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="co2"
                    label={({ type, percentage }) => `${type}: ${percentage}%`}
                  >
                    {vehicleTypeEmissions.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value}%`, 'CO2 Share']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'comparison':
        return (
          <div className="space-y-6">
            {/* Impact Categories */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {impactCategories.map((category) => {
                const Icon = category.icon;
                return (
                  <div key={category.category} className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center space-x-3 mb-4">
                      <Icon className="w-6 h-6" style={{ color: category.color }} />
                      <h4 className="text-lg font-semibold text-gray-900">{category.category}</h4>
                    </div>
                    <div className="text-3xl font-bold mb-2" style={{ color: category.color }}>
                      {category.score.toFixed(1)}/100
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all duration-300"
                        style={{ 
                          backgroundColor: category.color,
                          width: `${category.score}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Environmental Recommendations</h4>
                <div className="space-y-3">
                  {recommendations.map((rec, index) => {
                    const Icon = rec.icon;
                    return (
                      <div key={index} className={`p-4 rounded-lg border-l-4 ${
                        rec.type === 'error' ? 'bg-red-50 border-red-500' :
                        rec.type === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                        'bg-blue-50 border-blue-500'
                      }`}>
                        <div className="flex items-start space-x-3">
                          <Icon className={`w-5 h-5 mt-1 ${
                            rec.type === 'error' ? 'text-red-500' :
                            rec.type === 'warning' ? 'text-yellow-500' :
                            'text-blue-500'
                          }`} />
                          <div>
                            <h5 className="font-semibold text-gray-900">{rec.title}</h5>
                            <p className="text-sm text-gray-700">{rec.message}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
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
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            {viewConfigs[selectedView].title}
          </h3>
        </div>
        <div className="card-body">
          <p className="text-secondary">
            {viewConfigs[selectedView].description}
          </p>
        </div>
      </div>

      {/* View Content */}
      {renderView()}
    </div>
  );
};

export default EmissionsAnalysis;