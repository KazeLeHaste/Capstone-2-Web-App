/**
 * Recommendations Panel Component
 * 
 * Displays data-driven recommendations based on simulation results
 * with actionable insights and priority indicators.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState } from 'react';
import { 
  AlertTriangle,
  CheckCircle,
  Info,
  Lightbulb,
  TrendingUp,
  Filter,
  ChevronRight,
  AlertCircle,
  Target,
  Settings
} from 'lucide-react';

const RecommendationsPanel = ({ recommendations = [], loading = false }) => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [expandedRecommendation, setExpandedRecommendation] = useState(null);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg border p-6 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">All Good!</h3>
        <p className="mt-1 text-gray-500">
          No recommendations at this time. Your simulation performed well.
        </p>
      </div>
    );
  }

  // Get unique categories and priorities
  const categories = ['all', ...new Set(recommendations.map(r => r.category))];
  const priorities = ['all', ...new Set(recommendations.map(r => r.priority))];

  // Filter recommendations
  const filteredRecommendations = recommendations.filter(rec => {
    const categoryMatch = selectedCategory === 'all' || rec.category === selectedCategory;
    const priorityMatch = selectedPriority === 'all' || rec.priority === selectedPriority;
    return categoryMatch && priorityMatch;
  });

  // Priority configurations
  const priorityConfig = {
    high: {
      icon: AlertTriangle,
      color: 'red',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-800',
      iconColor: 'text-red-600'
    },
    medium: {
      icon: AlertCircle,
      color: 'yellow',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-800',
      iconColor: 'text-yellow-600'
    },
    low: {
      icon: Info,
      color: 'blue',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-600'
    }
  };

  // Category configurations
  const categoryConfig = {
    congestion: {
      icon: AlertTriangle,
      color: 'red',
      label: 'Congestion'
    },
    safety: {
      icon: AlertCircle,
      color: 'orange',
      label: 'Safety'
    },
    efficiency: {
      icon: TrendingUp,
      color: 'blue',
      label: 'Efficiency'
    },
    environmental: {
      icon: CheckCircle,
      color: 'green',
      label: 'Environmental'
    }
  };

  // Get detailed recommendations based on category
  const getDetailedRecommendations = (recommendation) => {
    const details = {
      congestion: [
        "Consider reducing traffic signal cycle times",
        "Implement adaptive traffic control systems",
        "Add additional lanes to bottleneck areas",
        "Encourage off-peak travel through pricing",
        "Improve public transportation alternatives"
      ],
      safety: [
        "Review intersection design and visibility",
        "Implement speed management measures",
        "Add safety barriers or medians",
        "Improve street lighting",
        "Consider roundabouts for high-conflict intersections"
      ],
      efficiency: [
        "Optimize route choice and guidance systems",
        "Implement intelligent transportation systems",
        "Improve traffic signal coordination",
        "Consider highway on-ramp metering",
        "Enhance incident management procedures"
      ],
      environmental: [
        "Promote electric vehicle adoption",
        "Encourage public transportation use",
        "Implement car-sharing programs",
        "Create low-emission zones",
        "Improve traffic flow to reduce idle time"
      ]
    };

    return details[recommendation.category] || [];
  };

  return (
    <div className="space-y-6">
      {/* Header and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Lightbulb className="w-5 h-5 mr-2 text-yellow-500" />
            Recommendations
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {filteredRecommendations.length} of {recommendations.length} recommendations
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-sm border rounded px-3 py-1"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : 
                   categoryConfig[category]?.label || category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>
          
          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="text-sm border rounded px-3 py-1"
          >
            {priorities.map(priority => (
              <option key={priority} value={priority}>
                {priority === 'all' ? 'All Priorities' : 
                 priority.charAt(0).toUpperCase() + priority.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Priority Summary */}
      {selectedCategory === 'all' && selectedPriority === 'all' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {['high', 'medium', 'low'].map(priority => {
            const count = recommendations.filter(r => r.priority === priority).length;
            const config = priorityConfig[priority];
            const Icon = config.icon;
            
            return (
              <div key={priority} className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Icon className={`w-5 h-5 mr-2 ${config.iconColor}`} />
                    <span className={`font-medium ${config.textColor}`}>
                      {priority.charAt(0).toUpperCase() + priority.slice(1)} Priority
                    </span>
                  </div>
                  <span className={`text-xl font-bold ${config.textColor}`}>
                    {count}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecommendations.map((recommendation, index) => {
          const config = priorityConfig[recommendation.priority] || priorityConfig.low;
          const categoryConf = categoryConfig[recommendation.category] || { icon: Info, color: 'gray', label: recommendation.category };
          const Icon = config.icon;
          const CategoryIcon = categoryConf.icon;
          const isExpanded = expandedRecommendation === recommendation.id;

          return (
            <div key={recommendation.id || index} className={`bg-white border rounded-lg ${config.borderColor}`}>
              {/* Main Recommendation */}
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <Icon className={`w-6 h-6 mt-1 ${config.iconColor}`} />
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
                          {recommendation.priority.charAt(0).toUpperCase() + recommendation.priority.slice(1)}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          <CategoryIcon className="w-3 h-3 mr-1" />
                          {categoryConf.label}
                        </span>
                      </div>
                      
                      <p className={`text-base ${config.textColor} font-medium mb-2`}>
                        {recommendation.message}
                      </p>
                      
                      {recommendation.kpi && recommendation.actual_value && (
                        <div className="text-sm text-gray-600">
                          <span className="font-medium">Current value:</span> {recommendation.actual_value.toFixed(2)} 
                          {recommendation.threshold && (
                            <span className="ml-2">
                              <span className="font-medium">Threshold:</span> {recommendation.threshold}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setExpandedRecommendation(isExpanded ? null : recommendation.id)}
                    className="ml-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <ChevronRight className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t bg-gray-50 px-6 py-4">
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                        <Target className="w-4 h-4 mr-2" />
                        Suggested Actions
                      </h4>
                      <ul className="space-y-2">
                        {getDetailedRecommendations(recommendation).map((action, i) => (
                          <li key={i} className="flex items-start">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-700">{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    {recommendation.kpi && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                          <Settings className="w-4 h-4 mr-2" />
                          Technical Details
                        </h4>
                        <div className="bg-white rounded border p-3 text-sm">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <span className="font-medium">Affected KPI:</span> {recommendation.kpi}
                            </div>
                            <div>
                              <span className="font-medium">Category:</span> {recommendation.category}
                            </div>
                            {recommendation.actual_value && (
                              <div>
                                <span className="font-medium">Measured Value:</span> {recommendation.actual_value.toFixed(2)}
                              </div>
                            )}
                            {recommendation.threshold && (
                              <div>
                                <span className="font-medium">Target Threshold:</span> {recommendation.threshold}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredRecommendations.length === 0 && (
        <div className="text-center py-8">
          <Filter className="mx-auto h-8 w-8 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No recommendations match your filters</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your category or priority filters</p>
        </div>
      )}

      {/* Summary Footer */}
      {filteredRecommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
            <div className="text-sm">
              <p className="text-blue-800 font-medium">Implementation Priority</p>
              <p className="text-blue-700 mt-1">
                Address high-priority recommendations first, focusing on safety and congestion issues. 
                Medium and low priority items can be implemented as part of long-term improvement plans.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendationsPanel;
