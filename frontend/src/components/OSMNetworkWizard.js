/**
 * OSM Network Creation Wizard
 * 
 * Main modal component that handles the complete flow from instructions 
 * to OSM Web Wizard launch to scenario import for creating new networks.
 * 
 * Author: Traffic Simulator Team
 * Date: October 2025
 */

import React, { useState, useEffect } from 'react';
import { 
  X, 
  ExternalLink, 
  ChevronRight, 
  ChevronLeft,
  AlertCircle,
  CheckCircle2,
  Info
} from 'lucide-react';
import OSMInstructions from './OSMInstructions';
import OSMScenarioScanner from './OSMScenarioScanner';
import { osmApi } from '../utils/apiClient';

const OSMNetworkWizard = ({ isOpen, onClose, onNetworkAdded }) => {
  console.log('OSMNetworkWizard render - isOpen:', isOpen);
  
  const [currentStep, setCurrentStep] = useState('instructions');
  const [wizardStatus, setWizardStatus] = useState({
    running: false,
    url: null,
    port: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [launchResult, setLaunchResult] = useState(null);

  // Steps: 'instructions' → 'wizard-launched' → 'scan-import'
  const steps = [
    { key: 'instructions', title: 'Instructions', subtitle: 'Learn how to use OSM Web Wizard' },
    { key: 'wizard-launched', title: 'Create Scenario', subtitle: 'Use OSM Web Wizard to generate scenario' },
    { key: 'scan-import', title: 'Import Network', subtitle: 'Scan and import your generated scenario' }
  ];

  // Check wizard status on mount and when step changes
  useEffect(() => {
    if (isOpen) {
      checkWizardStatus();
      
      // Check status periodically when on wizard-launched step
      if (currentStep === 'wizard-launched') {
        const interval = setInterval(checkWizardStatus, 5000);
        return () => clearInterval(interval);
      }
    }
  }, [isOpen, currentStep]);

  const checkWizardStatus = async () => {
    try {
      const response = await osmApi.getWizardStatus();
      if (response.data.success) {
        setWizardStatus(response.data.status);
      }
    } catch (error) {
      console.error('Failed to check wizard status:', error);
    }
  };

  const handleLaunchWizard = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await osmApi.launchWizard();
      
      if (response.data.success) {
        setLaunchResult(response.data);
        setWizardStatus({
          running: true,
          url: response.data.url,
          port: response.data.port
        });
        
        // Open wizard in new tab/window
        if (response.data.url) {
          window.open(response.data.url, '_blank', 'width=1200,height=800');
        }
        
        // Move to next step
        setCurrentStep('wizard-launched');
      } else {
        setError(response.data.error || 'Failed to launch OSM Web Wizard');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to launch OSM Web Wizard');
      console.error('Launch wizard error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopWizard = async () => {
    setLoading(true);
    
    try {
      await osmApi.stopWizard();
      setWizardStatus({ running: false, url: null, port: null });
      setLaunchResult(null);
    } catch (error) {
      console.error('Failed to stop wizard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNetworkImported = (networkInfo) => {
    // Close the wizard and notify parent
    onClose();
    if (onNetworkAdded) {
      onNetworkAdded(networkInfo);
    }
  };

  const handleBack = () => {
    const currentIndex = steps.findIndex(step => step.key === currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1].key);
    }
  };

  const handleNext = () => {
    const currentIndex = steps.findIndex(step => step.key === currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1].key);
    }
  };

  const getCurrentStepIndex = () => {
    return steps.findIndex(step => step.key === currentStep);
  };

  const renderStepIndicator = () => {
    const currentIndex = getCurrentStepIndex();
    
    return (
      <div className="osm-step-indicator-list">
        {steps.map((step, index) => (
          <div 
            key={step.key}
            className={`osm-step-indicator-item ${
              index === currentIndex ? 'active' : 
              index < currentIndex ? 'completed' : ''
            }`}
          >
            <div className="osm-step-number">
              {index < currentIndex ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                index + 1
              )}
            </div>
            <div className="osm-step-title">{step.title}</div>
            <div className="osm-step-subtitle">{step.subtitle}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'instructions':
        return (
          <OSMInstructions 
            onLaunchWizard={handleLaunchWizard}
            loading={loading}
            error={error}
            wizardStatus={wizardStatus}
          />
        );
        
      case 'wizard-launched':
        return (
          <div className="osm-status-section">
            <div className="osm-status-header">
              <div className="osm-modal-icon-container">
                <ExternalLink className="osm-status-icon" />
              </div>
              <div>
                <h3 className="osm-status-title">
                  OSM Web Wizard Launched
                </h3>
                <p className="osm-status-description">
                  The OSM Web Wizard is now running and should have opened in a new browser tab.
                </p>
              </div>
            </div>

            {launchResult && (
              <div className="osm-success-alert">
                <div className="osm-success-content">
                  <CheckCircle2 className="osm-success-icon" />
                  <div>
                    <p className="osm-success-text">
                      <strong>Success!</strong> OSM Web Wizard is running at{' '}
                      <a 
                        href={launchResult.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="osm-success-link"
                      >
                        {launchResult.url}
                      </a>
                    </p>
                    {launchResult.working_directory && (
                      <p className="osm-success-directory">
                        Working directory: {launchResult.working_directory}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="osm-info-alert">
              <div className="osm-info-content">
                <Info className="osm-info-icon" />
                <div>
                  <h4 className="osm-info-title">Next Steps:</h4>
                  <ol className="osm-info-list">
                    <li>Use the opened browser tab to create your scenario</li>
                    <li>Follow the instructions from the previous step</li>
                    <li>After generating your scenario, return here</li>
                    <li><strong>Click the "Continue" button below to import your scenario</strong></li>
                  </ol>
                </div>
              </div>
            </div>

            <div className="osm-warning-alert">
              <div className="osm-warning-content">
                <AlertCircle className="osm-warning-icon" />
                <div>
                  <h4 className="osm-warning-title">Important:</h4>
                  <p className="osm-warning-text">
                    After you generate your scenario in OSM Web Wizard, click the <strong>"Continue"</strong> button 
                    below to scan for and import your new network.
                  </p>
                </div>
              </div>
            </div>

            <div className="osm-wizard-status">
              <div className={`osm-status-indicator ${wizardStatus.running ? 'running' : 'stopped'}`}>
                <div className={`osm-status-dot ${wizardStatus.running ? 'running' : 'stopped'}`} />
                <span className="osm-status-text">
                  {wizardStatus.running ? 'Wizard Running' : 'Wizard Stopped'}
                </span>
              </div>
              
              {wizardStatus.running && wizardStatus.url && (
                <button
                  onClick={() => window.open(wizardStatus.url, '_blank')}
                  className="osm-button open-wizard"
                >
                  Open OSM Wizard
                </button>
              )}
            </div>
          </div>
        );
        
      case 'scan-import':
        return (
          <OSMScenarioScanner 
            onScenarioImported={handleNetworkImported}
          />
        );
        
      default:
        return null;
    }
  };

  if (!isOpen) {
    console.log('OSMNetworkWizard - isOpen is false, returning null');
    return null;
  }

  console.log('OSMNetworkWizard - isOpen is true, rendering modal');

  return (
    <div className="osm-modal-backdrop">
      <div className="osm-modal-container">
        {/* Header */}
        <div className="osm-modal-header">
          <div className="osm-modal-header-content">
            <div className="osm-modal-icon-container">
              <ExternalLink className="osm-modal-icon" />
            </div>
            <div>
              <h2 className="osm-modal-title">
                Create New Network with OSM
              </h2>
              <p className="osm-modal-subtitle">
                Generate traffic networks from real-world map data
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="osm-modal-close-button"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="osm-step-indicator">
          {renderStepIndicator()}
        </div>

        {/* Content */}
        <div className="osm-modal-content">
          {error && (
            <div className="osm-error-alert">
              <div className="osm-error-content">
                <AlertCircle className="osm-error-icon" />
                <p className="osm-error-text">{error}</p>
              </div>
            </div>
          )}
          
          {renderStepContent()}
        </div>

        {/* Footer */}
        <div className="osm-modal-footer">
          <div className="osm-footer-left">
            <button
              onClick={handleBack}
              disabled={getCurrentStepIndex() === 0}
              className={`osm-button back ${getCurrentStepIndex() === 0 ? 'disabled' : ''}`}
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          </div>

          <div className="osm-footer-right">
            {wizardStatus.running && currentStep !== 'scan-import' && (
              <button
                onClick={handleStopWizard}
                disabled={loading}
                className="osm-button danger"
              >
                Stop Wizard
              </button>
            )}
            
            {currentStep === 'wizard-launched' && (
              <button
                onClick={handleNext}
                className="osm-button success"
              >
                <span>Continue to Import Scenario</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            )}
            
            {currentStep === 'scan-import' && (
              <button
                onClick={onClose}
                className="osm-button secondary"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OSMNetworkWizard;