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
          <div key={i} className="bg-primary rounded-lg border p-6 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-tertiary rounded"></div>
              <div className="flex-1">
                <div className="h-4 bg-tertiary rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-tertiary rounded w-1/2"></div>
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
      bgColor: 'bg-error',
      borderColor: 'border-error',
      textColor: 'text-error',
      iconColor: 'text-error'
    },
    medium: {
      icon: AlertCircle,
      color: 'yellow',
      bgColor: 'bg-warning',
      borderColor: 'border-warning',
      textColor: 'text-warning',
      iconColor: 'text-warning'
    },
    low: {
      icon: Info,
      color: 'blue',
      bgColor: 'bg-info',
      borderColor: 'border-info',
      textColor: 'text-info',
      iconColor: 'text-info'
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
            <Filter className="w-4 h-4 text-theme-muted" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="form-control text-sm recommendations-category-select"
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
            className="form-control text-sm recommendations-priority-select"
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

      {/* Recommendations Grid */}
      <div className="analytics-recommendations-grid">
        {filteredRecommendations.map((recommendation, index) => {
          const config = priorityConfig[recommendation.priority] || priorityConfig.low;
          const categoryConf = categoryConfig[recommendation.category] || { icon: Info, color: 'gray', label: recommendation.category };
          const Icon = config.icon;
          const CategoryIcon = categoryConf.icon;
          const isExpanded = expandedRecommendation === recommendation.id;

          return (
            <div 
              key={recommendation.id || index} 
              className={`analytics-recommendation-tile ${recommendation.priority}-priority`}
            >
              {/* Recommendation Header */}
              <div className="analytics-recommendation-header">
                <div className="analytics-recommendation-priority">
                  <div className={`analytics-recommendation-icon ${config.bgColor}`}>
                    <Icon className={`w-5 h-5 ${config.iconColor}`} />
                  </div>
                  <span className={`analytics-recommendation-badge ${config.bgColor} ${config.textColor}`}>
                    {recommendation.priority} priority
                  </span>
                </div>
                <CategoryIcon className="analytics-recommendation-category-icon" />
              </div>

              {/* Recommendation Content */}
              <div className="analytics-recommendation-content">
                <div className="analytics-recommendation-main">
                  <p className="analytics-recommendation-title">
                    {recommendation.category.charAt(0).toUpperCase() + recommendation.category.slice(1)}
                  </p>
                  <p className="analytics-recommendation-message">
                    {recommendation.message}
                  </p>
                </div>

                {recommendation.kpi && (
                  <div className="analytics-recommendation-details">
                    <div className="analytics-recommendation-kpi-grid">
                      <div>
                        <span className="analytics-recommendation-label">KPI:</span>
                        <p className="analytics-recommendation-value">{recommendation.kpi}</p>
                      </div>
                      {recommendation.actual_value && (
                        <div>
                          <span className="analytics-recommendation-label">Value:</span>
                          <p className="analytics-recommendation-value">{recommendation.actual_value.toFixed(2)}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Button */}
                <button
                  onClick={() => setExpandedRecommendation(isExpanded ? null : recommendation.id)}
                  className="analytics-recommendation-toggle"
                >
                  {isExpanded ? 'Less details' : 'More details'}
                  <ChevronRight className={`analytics-recommendation-chevron ${isExpanded ? 'expanded' : ''}`} />
                </button>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="analytics-recommendation-expanded">
                  <div className="analytics-recommendation-actions">
                    <h4 className="analytics-recommendation-actions-title">
                      <Target className="w-4 h-4 mr-2" />
                      Suggested Actions
                    </h4>
                    <ul className="analytics-recommendation-actions-list">
                      {getDetailedRecommendations(recommendation).map((detail, idx) => (
                        <li key={idx} className="analytics-recommendation-action-item">
                          <span className="analytics-recommendation-bullet">•</span>
                          {detail}
                        </li>
                      ))}
                    </ul>
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
        <div className="bg-info border border-info rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-info mr-3 mt-0.5" />
            <div className="text-sm">
              <p className="text-info font-medium">Implementation Priority</p>
              <p className="text-info mt-1">
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
