/**
 * OSM Instructions Component
 * 
 * Displays detailed step-by-step instructions for using OSM Web Wizard
 * to create traffic scenarios, including best practices and tips.
 * 
 * Author: Traffic Simulator Team
 * Date: October 2025
 */

import React from 'react';
import { 
  MapPin, 
  Car, 
  Settings, 
  Target, 
  ExternalLink,
  AlertTriangle,
  Info,
  CheckCircle2,
  Loader2
} from 'lucide-react';

const OSMInstructions = ({ onLaunchWizard, loading, error, wizardStatus }) => {
  const instructionSteps = [
    {
      icon: MapPin,
      title: 'Select Area',
      description: 'Choose your geographic region',
      details: [
        'Use the map to navigate to your desired location',
        'Click "Select Area" and drag to define simulation boundaries',
        'Keep the area reasonably sized for good performance',
        'Avoid very large areas as they may cause slow simulations'
      ],
      colorClass: 'step-2'
    },
    {
      icon: Car,
      title: 'Configure Traffic',
      description: 'Set up vehicle types and density',
      details: [
        'Choose vehicle types: Cars, Buses, Trucks, Motorcycles',
        'Set traffic density (start with default values)',
        'Adjust "Through Traffic Factor" if needed',
        'Higher density = more vehicles, but may impact performance'
      ],
      colorClass: 'step-3'
    },
    {
      icon: Settings,
      title: 'Network Options',
      description: 'Configure road and visual settings',
      details: [
        'Keep "Add Polygons" checked for visual elements',
        'Choose road types (default: all roads recommended)',
        'Enable "Import Public Transport" if desired',
        'Car-only networks are simpler but less realistic'
      ],
      colorClass: 'step-4'
    },
    {
      icon: Target,
      title: 'Generate & Return',
      description: 'Create scenario and come back here',
      details: [
        'Click "Generate Scenario" button in OSM Web Wizard',
        'Wait for generation to complete (may take a few minutes)',
        'SUMO GUI will open - you can close it safely',
        'Return to this application and click "Continue"'
      ],
      colorClass: 'step-1'
    }
  ];

  return (
    <div className="osm-instructions-container">
      {/* Introduction */}
      <div className="osm-instructions-header">
        <h3 className="osm-instructions-title">
          Create New Network with OSM Web Wizard
        </h3>
        <p className="osm-instructions-description">
          Follow these steps to create a new traffic network from real-world map data
        </p>
      </div>

      {/* Current Status */}
      {wizardStatus.running && (
        <div className="osm-wizard-status-alert">
          <div className="osm-wizard-status-content">
            <CheckCircle2 className="osm-wizard-status-icon" />
            <div>
              <p className="osm-wizard-status-text">
                OSM Web Wizard is already running
              </p>
              <p className="osm-wizard-status-subtext">
                You can proceed directly to the wizard or launch a new instance
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="osm-instructions-grid">
        {instructionSteps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={index} className="osm-instruction-card">
              <div className="osm-instruction-content">
                <div className={`osm-instruction-icon-container ${step.colorClass}`}>
                  <Icon className="osm-instruction-icon" />
                </div>
                <div className="osm-instruction-details">
                  <h4 className="osm-instruction-title">
                    Step {index + 1}: {step.title}
                  </h4>
                  <p className="osm-instruction-description">
                    {step.description}
                  </p>
                  <ul className="osm-instruction-list">
                    {step.details.map((detail, detailIndex) => (
                      <li key={detailIndex} className="osm-instruction-list-item">
                        <span className="osm-instruction-bullet" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Important Notes */}
      <div className="osm-tips-grid">
        <div className="osm-warning-alert">
          <div className="osm-warning-content">
            <AlertTriangle className="osm-warning-icon" />
            <div>
              <h4 className="osm-warning-title">Important:</h4>
              <ul className="osm-instruction-list">
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Keep this window open while using OSM Web Wizard
                </li>
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Don't close the wizard until generation is complete
                </li>
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Large areas may take several minutes to process
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="osm-info-alert">
          <div className="osm-info-content">
            <Info className="osm-info-icon" />
            <div>
              <h4 className="osm-info-title">Tips:</h4>
              <ul className="osm-instruction-list">
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Start with smaller areas for faster generation
                </li>
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Use default traffic settings initially
                </li>
                <li className="osm-instruction-list-item">
                  <span className="osm-instruction-bullet" />
                  Include polygons for better visualization
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Launch Button */}
      <div className="osm-launch-section">
        <button
          onClick={onLaunchWizard}
          disabled={loading}
          className="osm-launch-button"
        >
          {loading ? (
            <>
              <div className="osm-loading-spinner" />
              <span>Launching OSM Web Wizard...</span>
            </>
          ) : (
            <>
              <ExternalLink className="osm-launch-icon" />
              <span>Launch OSM Web Wizard</span>
            </>
          )}
        </button>
        
        {wizardStatus.running && (
          <p className="osm-instructions-description osm-wizard-note">
            Note: This will launch a new wizard instance. You can also{' '}
            <button
              onClick={() => window.open(wizardStatus.url, '_blank')}
              className="osm-success-link osm-link-button"
            >
              reopen the existing one
            </button>
          </p>
        )}
      </div>
    </div>
  );
};

export default OSMInstructions;