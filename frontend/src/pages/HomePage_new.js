/**
 * HomePage Component
 * 
 * Main landing page for the Traffic Simulator application.
 * Provides overview, features, and getting started information.
 * Follows responsive design principles and ISO 9241-110 guidelines.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Play, 
  Network, 
  BarChart3, 
  Settings, 
  CheckCircle, 
  AlertCircle,
  Info,
  ExternalLink,
  Book,
  Zap,
  Users,
  Globe,
  ArrowRight,
  Download,
  Server,
  Car,
  MapPin,
  Clock,
  TrendingUp,
  ChevronRight
} from 'lucide-react';
import { api } from '../utils/apiClient';

const HomePage = ({ onShowOnboarding, backendStatus, isConnected }) => {
  const [systemStatus, setSystemStatus] = useState({
    backend: 'unknown',
    sumo: 'unknown',
    loading: true
  });
  
  useEffect(() => {
    checkSystemStatus();
  }, []);
  
  const checkSystemStatus = async () => {
    try {
      const response = await api.getStatus();
      setSystemStatus({
        backend: response.data.backend_status,
        sumo: response.data.sumo_available ? 'available' : 'not_found',
        loading: false
      });
    } catch (error) {
      setSystemStatus({
        backend: 'error',
        sumo: 'unknown',
        loading: false
      });
    }
  };

  const StatusBadge = ({ status, label }) => {
    const getStatusColor = () => {
      switch (status) {
        case 'running':
        case 'available':
          return 'bg-green-100 text-green-800 border-green-200';
        case 'error':
        case 'not_found':
          return 'bg-red-100 text-red-800 border-red-200';
        case 'loading':
          return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        default:
          return 'bg-gray-100 text-gray-800 border-gray-200';
      }
    };

    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor()}`}>
        <div className={`w-2 h-2 rounded-full mr-2 ${
          status === 'running' || status === 'available' ? 'bg-green-500' :
          status === 'error' || status === 'not_found' ? 'bg-red-500' :
          'bg-yellow-500'
        }`} />
        {label}: {status === 'available' ? 'Ready' : status === 'not_found' ? 'Not Found' : status}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <section className="relative py-16 sm:py-20 lg:py-24 xl:py-28" role="banner">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Traffic Simulation
              <span className="block text-blue-600 mt-2">Made Simple</span>
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Create, analyze, and optimize traffic networks with our intuitive web-based SUMO integration platform.
            </p>
            
            {/* System Status */}
            <div className="flex flex-wrap justify-center gap-3 mb-8">
              <StatusBadge status={systemStatus.backend} label="Backend" />
              <StatusBadge status={systemStatus.sumo} label="SUMO" />
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                to="/network"
                className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl min-h-[48px] text-base font-medium"
                aria-label="Get started with network design"
              >
                Get Started
                <ChevronRight className="ml-2 w-5 h-5" aria-hidden="true" />
              </Link>
              <button
                onClick={onShowOnboarding}
                className="inline-flex items-center justify-center px-8 py-4 bg-white text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-all duration-200 shadow-md hover:shadow-lg min-h-[48px] text-base font-medium"
                aria-label="View interactive tutorial"
              >
                <Book className="mr-2 w-5 h-5" aria-hidden="true" />
                Take Tutorial
              </button>
              <Link
                to="/simulation"
                className="inline-flex items-center justify-center px-8 py-4 bg-gray-100 text-gray-700 border-2 border-gray-300 rounded-lg hover:bg-gray-200 transition-all duration-200 shadow-md hover:shadow-lg min-h-[48px] text-base font-medium"
                aria-label="View simulation demo"
              >
                <Play className="mr-2 w-5 h-5" aria-hidden="true" />
                View Demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-20 bg-white" role="main">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 lg:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to build and analyze traffic simulations
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
            {[
              {
                icon: MapPin,
                title: "Network Design",
                description: "Create complex road networks with an intuitive drag-and-drop interface",
                bgColor: "bg-blue-100",
                iconColor: "text-blue-600"
              },
              {
                icon: Car,
                title: "Vehicle Simulation",
                description: "Simulate realistic vehicle behavior with SUMO's advanced algorithms",
                bgColor: "bg-green-100",
                iconColor: "text-green-600"
              },
              {
                icon: BarChart3,
                title: "Real-time Analytics",
                description: "Monitor traffic flow, congestion, and performance metrics in real-time",
                bgColor: "bg-purple-100",
                iconColor: "text-purple-600"
              },
              {
                icon: Settings,
                title: "Advanced Configuration",
                description: "Fine-tune simulation parameters for accurate modeling",
                bgColor: "bg-orange-100",
                iconColor: "text-orange-600"
              },
              {
                icon: TrendingUp,
                title: "Export & Share",
                description: "Export results and share simulations with your team",
                bgColor: "bg-red-100",
                iconColor: "text-red-600"
              },
              {
                icon: Clock,
                title: "Batch Processing",
                description: "Run multiple simulations and compare results efficiently",
                bgColor: "bg-indigo-100",
                iconColor: "text-indigo-600"
              }
            ].map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={index}
                  className="p-6 lg:p-8 border border-gray-200 rounded-xl hover:shadow-xl transition-all duration-300 bg-white h-full"
                >
                  <div className={`w-12 h-12 lg:w-14 lg:h-14 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4 lg:mb-6`}>
                    <Icon className={`w-6 h-6 lg:w-7 lg:h-7 ${feature.iconColor}`} aria-hidden="true" />
                  </div>
                  <h3 className="text-lg lg:text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-16 lg:py-20 bg-gray-50">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12 lg:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
                Why Choose Our Platform?
              </h2>
              <p className="text-lg sm:text-xl text-gray-600">
                Built for researchers, urban planners, and traffic engineers
              </p>
            </div>
            
            <div className="space-y-8 lg:space-y-10">
              {[
                {
                  title: "Easy to Use",
                  description: "No complex setup required. Start simulating traffic within minutes with our intuitive interface.",
                  icon: Zap
                },
                {
                  title: "SUMO Integration",
                  description: "Powered by SUMO, the industry-standard traffic simulation software used worldwide.",
                  icon: Server
                },
                {
                  title: "Web-Based",
                  description: "Access your simulations from anywhere. No software installation needed.",
                  icon: Globe
                },
                {
                  title: "Collaborative",
                  description: "Share projects with team members and collaborate in real-time.",
                  icon: Users
                }
              ].map((benefit, index) => {
                const Icon = benefit.icon;
                return (
                  <div key={index} className="flex items-start space-x-4 lg:space-x-6">
                    <div className="w-12 h-12 lg:w-14 lg:h-14 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Icon className="w-6 h-6 lg:w-7 lg:h-7 text-green-600" aria-hidden="true" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg lg:text-xl font-semibold text-gray-900 mb-2 lg:mb-3">
                        {benefit.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">
                        {benefit.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Getting Started Section */}
      <section className="py-16 lg:py-20 bg-white">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Ready to Get Started?
            </h2>
            <p className="text-lg sm:text-xl text-gray-600 mb-12 lg:mb-16">
              Follow these simple steps to create your first traffic simulation
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12 mb-12 lg:mb-16">
              {[
                {
                  step: "1",
                  title: "Design Network",
                  description: "Create your road network using our visual editor",
                  icon: MapPin
                },
                {
                  step: "2",
                  title: "Configure Parameters",
                  description: "Set vehicle types, traffic patterns, and simulation settings",
                  icon: Settings
                },
                {
                  step: "3",
                  title: "Run & Analyze",
                  description: "Execute simulation and analyze results with built-in tools",
                  icon: BarChart3
                }
              ].map((step, index) => {
                const Icon = step.icon;
                return (
                  <div key={index} className="text-center">
                    <div className="w-16 h-16 lg:w-20 lg:h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 lg:mb-6">
                      <span className="text-xl lg:text-2xl font-bold text-blue-600">{step.step}</span>
                    </div>
                    <div className="mb-4">
                      <Icon className="w-8 h-8 lg:w-10 lg:h-10 text-blue-600 mx-auto" />
                    </div>
                    <h3 className="text-lg lg:text-xl font-semibold text-gray-900 mb-3">
                      {step.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>
            
            <Link
              to="/network"
              className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl text-lg font-medium min-h-[52px]"
              aria-label="Start building your traffic simulation"
            >
              Start Building
              <ChevronRight className="ml-2 w-5 h-5" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Actions Section */}
      <section className="py-16 lg:py-20 bg-gray-50">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12 lg:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
                Quick Actions
              </h2>
              <p className="text-lg sm:text-xl text-gray-600">
                Jump right into what you need
              </p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  title: "Network Designer",
                  description: "Create road networks",
                  icon: Network,
                  path: "/network",
                  color: "blue"
                },
                {
                  title: "Configuration",
                  description: "Set up parameters",
                  icon: Settings,
                  path: "/configuration",
                  color: "green"
                },
                {
                  title: "Run Simulation",
                  description: "Start simulation",
                  icon: Play,
                  path: "/simulation",
                  color: "purple"
                },
                {
                  title: "View Analytics",
                  description: "Analyze results",
                  icon: BarChart3,
                  path: "/analytics",
                  color: "orange"
                }
              ].map((action, index) => {
                const Icon = action.icon;
                const colorClasses = {
                  blue: "bg-blue-100 text-blue-600 hover:bg-blue-200",
                  green: "bg-green-100 text-green-600 hover:bg-green-200",
                  purple: "bg-purple-100 text-purple-600 hover:bg-purple-200",
                  orange: "bg-orange-100 text-orange-600 hover:bg-orange-200"
                };
                
                return (
                  <Link
                    key={index}
                    to={action.path}
                    className={`p-6 rounded-xl border border-gray-200 hover:shadow-lg transition-all duration-200 bg-white group`}
                  >
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors duration-200 ${colorClasses[action.color]}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {action.description}
                    </p>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
