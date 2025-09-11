/**
 * Onboarding Modal Component
 * 
 * Provides a guided tour and introduction for first-time users
 * of the Traffic Simulator application.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState } from 'react';
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Home, 
  Network, 
  Settings, 
  Play, 
  BarChart3,
  CheckCircle
} from 'lucide-react';

const OnboardingModal = ({ onComplete, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  
  const onboardingSteps = [
    {
      title: "Welcome to Traffic Simulator",
      content: (
        <div className="onboarding-welcome-content">
          <div className="onboarding-icon-blue onboarding-icon-large">
            <Network className="onboarding-icon-svg-large" />
          </div>
          <p className="onboarding-text-primary onboarding-text-mb">
            Welcome to the Traffic Simulator web application! This tool integrates with SUMO 
            (Simulation of Urban MObility) to provide a complete traffic simulation experience 
            with real-time monitoring and comprehensive analytics.
          </p>
          <p className="onboarding-text-primary">
            Let's walk through the simulation workflow to get you started with traffic analysis.
          </p>
        </div>
      )
    },
    {
      title: "Configuration Setup",
      content: (
        <div className="onboarding-step-content">
          <div className="onboarding-step-header">
            <div className="onboarding-icon-blue onboarding-icon-small">
              <Settings className="onboarding-icon-svg-small" />
            </div>
            <h3 className="onboarding-step-title">Start Simulating - Configuration First</h3>
          </div>
          <p className="onboarding-text-primary onboarding-text-mb">
            Begin your simulation by configuring essential SUMO parameters. This configuration-first 
            approach ensures your settings are applied correctly to your chosen network.
          </p>
          <ul className="onboarding-list">
            <li>Set simulation duration (begin/end time)</li>
            <li>Configure time step and teleport settings</li>
            <li>Choose vehicle types (passenger, bus, truck, motorcycle)</li>
            <li>Set traffic control (fixed timing or adaptive signals)</li>
            <li>Adjust traffic intensity and volume</li>
          </ul>
        </div>
      )
    },
    {
      title: "Network Selection",
      content: (
        <div className="onboarding-step-content">
          <div className="onboarding-step-header">
            <div className="onboarding-icon-green onboarding-icon-small">
              <Network className="onboarding-icon-svg-small" />
            </div>
            <h3 className="onboarding-step-title">Choose Your Traffic Network</h3>
          </div>
          <p className="onboarding-text-primary onboarding-text-mb">
            Select from available Filipino traffic networks. Your configuration will be applied 
            to the selected network automatically.
          </p>
          <ul className="onboarding-list">
            <li>Browse predefined networks (Jollibee Molino, SM Bacoor, etc.)</li>
            <li>View network details and metadata</li>
            <li>Networks are copied to your session folder</li>
            <li>Configuration parameters are applied automatically</li>
          </ul>
        </div>
      )
    },
    {
      title: "Live Simulation",
      content: (
        <div className="onboarding-step-content">
          <div className="onboarding-step-header">
            <div className="onboarding-icon-purple onboarding-icon-small">
              <Play className="onboarding-icon-svg-small" />
            </div>
            <h3 className="onboarding-step-title">Run & Monitor Simulation</h3>
          </div>
          <p className="onboarding-text-primary onboarding-text-mb">
            Launch SUMO with your configured parameters and monitor the simulation in real-time 
            through the web interface.
          </p>
          <ul className="onboarding-list">
            <li>Start/pause/stop simulation controls</li>
            <li>Real-time vehicle statistics and metrics</li>
            <li>Live SUMO GUI integration with zoom controls</li>
            <li>WebSocket connection for instant data updates</li>
            <li>Session management and auto-save functionality</li>
          </ul>
        </div>
      )
    },
    {
      title: "Analytics & Insights",
      content: (
        <div className="onboarding-step-content">
          <div className="onboarding-step-header">
            <div className="onboarding-icon-red onboarding-icon-small">
              <BarChart3 className="onboarding-icon-svg-small" />
            </div>
            <h3 className="onboarding-step-title">Comprehensive Analytics</h3>
          </div>
          <p className="onboarding-text-primary onboarding-text-mb">
            Analyze simulation results with detailed dashboards, charts, and comparison tools 
            for traffic optimization insights.
          </p>
          <ul className="onboarding-list">
            <li>KPI dashboard with key traffic metrics</li>
            <li>Interactive charts and visualizations</li>
            <li>Session comparison and trend analysis</li>
            <li>Traffic recommendations and optimization suggestions</li>
            <li>PDF report export functionality</li>
          </ul>
        </div>
      )
    },
    {
      title: "Getting Started",
      content: (
        <div className="onboarding-welcome-content">
          <div className="onboarding-icon-green onboarding-icon-large">
            <CheckCircle className="onboarding-icon-svg-large" />
          </div>
          <h3 className="onboarding-final-title">Ready to Simulate Traffic!</h3>
          <p className="onboarding-text-primary onboarding-text-mb">
            You're now ready to start creating traffic simulations. Follow the configuration-first 
            workflow for best results.
          </p>
          <div className="onboarding-tips-box">
            <h4 className="onboarding-tips-title">Quick Start Tips:</h4>
            <ul className="onboarding-tips-list">
              <li>Always start with "Start Simulating" to configure parameters first</li>
              <li>Use default settings for your first simulation</li>
              <li>Monitor the real-time statistics during simulation</li>
              <li>Check Analytics after completion for detailed insights</li>
              <li>Ensure SUMO is installed and WebSocket connection is active</li>
            </ul>
          </div>
        </div>
      )
    }
  ];
  
  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };
  
  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleSkip = () => {
    onComplete();
  };
  
  const currentStepData = onboardingSteps[currentStep];
  
  return (
    <div className="onboarding-modal-backdrop">
      <div className="onboarding-modal-container">
        <div className="onboarding-modal-content">
          {/* Header */}
          <div className="onboarding-modal-header">
            <div className="onboarding-header-content">
              <h2 className="onboarding-modal-title">
                {currentStepData.title}
              </h2>
              <span className="onboarding-step-counter">
                Step {currentStep + 1} of {onboardingSteps.length}
              </span>
            </div>
            <button
              onClick={onClose}
              className="onboarding-close-btn"
            >
              <X className="onboarding-close-icon" />
            </button>
          </div>
          
          {/* Progress bar */}
          <div className="onboarding-progress-container">
            <div className="progress-bar">
              <div 
                className="progress-bar-fill onboarding-progress-fill"
                data-progress={((currentStep + 1) / onboardingSteps.length) * 100}
              ></div>
            </div>
          </div>
          
          {/* Content */}
          <div className="onboarding-content">
            {currentStepData.content}
          </div>
          
          {/* Footer */}
          <div className="onboarding-modal-footer">
            <div className="onboarding-footer-left">
              <button
                onClick={handleSkip}
                className="onboarding-skip-btn"
              >
                Skip Tour
              </button>
            </div>
            
            <div className="onboarding-footer-right">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className="onboarding-btn-secondary"
              >
                <ChevronLeft className="onboarding-btn-icon" />
                <span>Previous</span>
              </button>
              
              <button
                onClick={handleNext}
                className="onboarding-btn-primary"
              >
                <span>
                  {currentStep === onboardingSteps.length - 1 ? 'Get Started' : 'Next'}
                </span>
                {currentStep !== onboardingSteps.length - 1 && (
                  <ChevronRight className="onboarding-btn-icon" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingModal;
