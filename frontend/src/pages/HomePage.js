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
    const getStatusClasses = () => {
      switch (status) {
        case 'running':
        case 'available':
          return 'status-badge status-badge-green';
        case 'error':
        case 'not_found':
          return 'status-badge status-badge-red';
        case 'loading':
          return 'status-badge status-badge-yellow';
        default:
          return 'status-badge status-badge-gray';
      }
    };

    const getDotClasses = () => {
      switch (status) {
        case 'running':
        case 'available':
          return 'status-badge-dot';
        case 'error':
        case 'not_found':
          return 'status-badge-dot';
        case 'loading':
          return 'status-badge-dot';
        default:
          return 'status-badge-dot';
      }
    };

    return (
      <div className={getStatusClasses()}>
        <div className={getDotClasses()} />
        {label}: {status === 'available' ? 'Ready' : status === 'not_found' ? 'Not Found' : status}
      </div>
    );
  };

  return (
    <div className="page-layout">
      {/* Hero Section */}
      <section className="hero-section" role="banner">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              Traffic Simulation
              <span className="hero-title-accent">Made Simple</span>
            </h1>
            <p className="hero-description">
              Create, analyze, and optimize traffic networks with our intuitive web-based SUMO integration platform.
            </p>
            
            {/* System Status */}
            <div className="status-badges-container">
              <StatusBadge status={systemStatus.backend} label="Backend" />
              <StatusBadge status={systemStatus.sumo} label="SUMO" />
            </div>
            
            <div className="hero-buttons">
              <Link
                to="/simulation-setup"
                className="btn-primary"
                aria-label="Start simulation configuration"
              >
                Get Started
                <ChevronRight className="btn-icon" aria-hidden="true" />
              </Link>
              <button
                onClick={onShowOnboarding}
                className="btn-secondary"
                aria-label="View interactive tutorial"
              >
                <Book className="btn-icon-left" aria-hidden="true" />
                Take Tutorial
              </button>
              <Link
                to="/simulation-launch"
                className="btn-success"
                aria-label="View simulation demo"
              >
                <Play className="btn-icon-left" aria-hidden="true" />
                Launch Demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section section-white" role="main">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              Powerful Features
            </h2>
            <p className="section-subtitle">
              Everything you need to build and analyze traffic simulations
            </p>
          </div>
          
          <div className="features-grid">
            {[
              {
                icon: MapPin,
                title: "Network Design",
                description: "Create complex road networks with an intuitive drag-and-drop interface",
                iconClass: "feature-icon feature-icon-blue",
                iconColor: "icon-blue"
              },
              {
                icon: Car,
                title: "Vehicle Simulation",
                description: "Simulate realistic vehicle behavior with SUMO's advanced algorithms",
                iconClass: "feature-icon feature-icon-green",
                iconColor: "icon-green"
              },
              {
                icon: BarChart3,
                title: "Real-time Analytics",
                description: "Monitor traffic flow, congestion, and performance metrics in real-time",
                iconClass: "feature-icon feature-icon-purple",
                iconColor: "icon-purple"
              },
              {
                icon: Settings,
                title: "Advanced Configuration",
                description: "Fine-tune simulation parameters for accurate modeling",
                iconClass: "feature-icon feature-icon-orange",
                iconColor: "icon-orange"
              },
              {
                icon: TrendingUp,
                title: "Export & Share",
                description: "Export results and share simulations with your team",
                iconClass: "feature-icon feature-icon-red",
                iconColor: "icon-red"
              },
              {
                icon: Clock,
                title: "Batch Processing",
                description: "Run multiple simulations and compare results efficiently",
                iconClass: "feature-icon feature-icon-indigo",
                iconColor: "icon-indigo"
              }
            ].map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="feature-card">
                  <div className={feature.iconClass}>
                    <Icon className={feature.iconColor} aria-hidden="true" />
                  </div>
                  <h3 className="feature-title">
                    {feature.title}
                  </h3>
                  <p className="feature-description">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="section section-gray">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              Why Choose Our Platform?
            </h2>
            <p className="section-subtitle">
              Built for researchers, urban planners, and traffic engineers
            </p>
          </div>
          
          <div className="benefits-list">
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
                <div key={index} className="benefit-item">
                  <div className="benefit-icon">
                    <Icon className="icon-green" aria-hidden="true" />
                  </div>
                  <div className="benefit-content">
                    <h3 className="benefit-title">
                      {benefit.title}
                    </h3>
                    <p className="benefit-description">
                      {benefit.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Getting Started Section */}
      <section className="section section-white">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              Ready to Get Started?
            </h2>
            <p className="section-subtitle">
              Follow these simple steps to create your first traffic simulation
            </p>
          </div>
          
          <div className="steps-grid">
            {[
              {
                step: "1",
                title: "Configure Simulation",
                description: "Set simulation parameters and network modifications",
                icon: Settings
              },
              {
                step: "2",
                title: "Select Network",
                description: "Choose from available SUMO networks",
                icon: Network
              },
              {
                step: "3",
                title: "Launch & Monitor",
                description: "Start simulation and view live results",
                icon: BarChart3
              }
            ].map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={index} className="step-item">
                  <div className="step-number">
                    {step.step}
                  </div>
                  <div>
                    <Icon className="step-icon" />
                  </div>
                  <h3 className="step-title">
                    {step.title}
                  </h3>
                  <p className="step-description">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
          
          <div className="text-center">
            <Link
              to="/simulation-setup"
              className="btn-primary btn-large"
              aria-label="Start building your traffic simulation"
            >
              Start Building
              <ChevronRight className="btn-icon" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Actions Section */}
      <section className="section section-gray">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              Quick Actions
            </h2>
            <p className="section-subtitle">
              Jump right into what you need
            </p>
          </div>
          
          <div className="actions-grid">
            {[
              {
                title: "Configuration Setup",
                description: "Configure simulation parameters",
                icon: Settings,
                path: "/simulation-setup",
                color: "blue"
              },
              {
                title: "Network Selection",
                description: "Choose your network",
                icon: Network,
                path: "/network-selection-enhanced",
                color: "green"
              },
              {
                title: "Launch Simulation",
                description: "Start SUMO simulation",
                icon: Play,
                path: "/simulation-launch",
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
              const iconClass = `action-icon action-icon-${action.color}`;
              
              return (
                <Link
                  key={index}
                  to={action.path}
                  className="action-card"
                >
                  <div className={iconClass}>
                    <Icon className="action-icon-svg" />
                  </div>
                  <h3 className="action-title">
                    {action.title}
                  </h3>
                  <p className="action-description">
                    {action.description}
                  </p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
