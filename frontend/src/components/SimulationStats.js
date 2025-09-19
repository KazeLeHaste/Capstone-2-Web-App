import React from 'react';
import { Car, Clock, Users, Activity } from 'lucide-react';

/**
 * SimulationStats Component
 * 
 * Displays real-time simulation statistics in a grid layout.
 * Shows vehicle count, simulation time, throughput, and other metrics.
 * 
 * Props:
 * - stats: Object containing simulation statistics
 * - isRunning: Boolean indicating if simulation is active
 */
const SimulationStats = ({ stats = {}, isRunning = false }) => {
  // Default values for stats if not provided
  const {
    vehicleCount = 0,
    simulationTime = 0,
    throughput = 0,
    avgSpeed = 0,
    totalDistance = 0,
    activeRoutes = 0
  } = stats;

  // Format simulation time to MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Format large numbers with commas
  const formatNumber = (num) => {
    return num.toLocaleString();
  };

  const statItems = [
    {
      icon: Car,
      label: 'Active Vehicles',
      value: formatNumber(vehicleCount),
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      icon: Clock,
      label: 'Simulation Time',
      value: formatTime(simulationTime),
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      icon: Activity,
      label: 'Throughput (veh/min)',
      value: formatNumber(throughput),
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      icon: Users,
      label: 'Avg Speed (km/h)',
      value: avgSpeed.toFixed(1),
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ];

  return (
    <div className="bg-primary rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Simulation Statistics
        </h3>
        <div className={`flex items-center space-x-2 ${isRunning ? 'text-green-600' : 'text-gray-500'}`}>
          <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className="text-sm font-medium">
            {isRunning ? 'Running' : 'Stopped'}
          </span>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statItems.map((item, index) => {
          const IconComponent = item.icon;
          return (
            <div key={index} className={`${item.bgColor} rounded-lg p-4 border border-opacity-20`}>
              <div className="flex items-center space-x-3">
                <div className={`${item.color} p-2 rounded-lg bg-white bg-opacity-50`}>
                  <IconComponent size={20} />
                </div>
                <div>
                  <p className="text-sm text-gray-600 font-medium">{item.label}</p>
                  <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total Distance Traveled:</span>
          <span className="font-semibold text-gray-800">{formatNumber(totalDistance)} km</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Active Routes:</span>
          <span className="font-semibold text-gray-800">{formatNumber(activeRoutes)}</span>
        </div>
      </div>

      {/* Progress indicator when running */}
      {isRunning && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Simulation Progress</span>
            <span className="text-sm text-gray-500">Real-time updates</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill progress-bar-fill-complete"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimulationStats;
