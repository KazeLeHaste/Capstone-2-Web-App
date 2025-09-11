/**
 * HomePage Component
 * 
 * Minimalist landing page for the Traffic Simulator application.
 * Provides brief overview and getting started information.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChevronRight,
  Book
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
              A web-based platform for creating and analyzing traffic simulations using SUMO. 
              Configure parameters, run simulations, and visualize results - all in your browser.
            </p>
            
            {/* System Status */}
            <div className="status-badges-container">
              <StatusBadge status={systemStatus.backend} label="Backend" />
              <StatusBadge status={systemStatus.sumo} label="SUMO" />
            </div>
            
            <div className="hero-buttons">
              <button
                onClick={onShowOnboarding}
                className="btn-secondary"
                aria-label="View interactive tutorial"
              >
                <Book className="btn-icon-left" aria-hidden="true" />
                Tutorial
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Getting Started Section */}
      <section className="section section-white">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              How It Works
            </h2>
            <p className="section-subtitle">
              Three simple steps to get your simulation running
            </p>
          </div>
          
          <div className="steps-grid">
            <div className="step-item">
              <div className="step-number">1</div>
              <h3 className="step-title">Configure</h3>
              <p className="step-description">
                Set simulation parameters and traffic settings
              </p>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <h3 className="step-title">Simulate</h3>
              <p className="step-description">
                Run your simulation with real-time monitoring
              </p>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <h3 className="step-title">Analyze</h3>
              <p className="step-description">
                Review results and traffic analytics
              </p>
            </div>
          </div>
          
          <div className="text-center">
            <Link
              to="/configuration"
              className="btn-primary btn-large"
              aria-label="Start building your traffic simulation"
            >
              Start Simulating
              <ChevronRight className="btn-icon" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
