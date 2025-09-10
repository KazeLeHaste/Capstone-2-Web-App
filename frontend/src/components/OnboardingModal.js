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
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Network className="w-8 h-8 text-blue-600" />
          </div>
          <p className="text-gray-600 mb-4">
            Welcome to the Traffic Simulator web application! This tool allows you to create, 
            configure, and analyze traffic simulations using SUMO (Simulation of Urban MObility).
          </p>
          <p className="text-gray-600">
            Let's take a quick tour to get you started with traffic simulation.
          </p>
        </div>
      )
    },
    {
      title: "Home Page",
      content: (
        <div>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <Home className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold">Project Introduction</h3>
          </div>
          <p className="text-gray-600 mb-4">
            The home page provides an overview of the traffic simulation project, 
            explaining the integration between SUMO and this web application.
          </p>
          <ul className="text-gray-600 space-y-2">
            <li>• Learn about traffic simulation benefits</li>
            <li>• Understand the SUMO integration</li>
            <li>• Access quick start guides</li>
            <li>• Check system requirements</li>
          </ul>
        </div>
      )
    },
    {
      title: "Network Selection",
      content: (
        <div>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <Network className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold">Choose Your Network</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Select from predefined traffic networks or upload your own SUMO network files.
          </p>
          <ul className="text-gray-600 space-y-2">
            <li>• Browse available network templates</li>
            <li>• View network previews and details</li>
            <li>• Upload custom network files</li>
            <li>• Validate network compatibility</li>
          </ul>
        </div>
      )
    },
    {
      title: "Configuration",
      content: (
        <div>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center mr-3">
              <Settings className="w-5 h-5 text-yellow-600" />
            </div>
            <h3 className="text-lg font-semibold">Simulation Setup</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Configure simulation parameters to customize your traffic scenario.
          </p>
          <ul className="text-gray-600 space-y-2">
            <li>• Set simulation duration and time step</li>
            <li>• Configure vehicle types and flows</li>
            <li>• Adjust traffic generation parameters</li>
            <li>• Define measurement areas</li>
          </ul>
        </div>
      )
    },
    {
      title: "Simulation Control",
      content: (
        <div>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
              <Play className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold">Run Your Simulation</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Launch and monitor your traffic simulation in real-time with live visualization.
          </p>
          <ul className="text-gray-600 space-y-2">
            <li>• Start/stop simulation control</li>
            <li>• Real-time 2D map visualization</li>
            <li>• Live vehicle position tracking</li>
            <li>• Interactive simulation monitoring</li>
          </ul>
        </div>
      )
    },
    {
      title: "Analytics & Results",
      content: (
        <div>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center mr-3">
              <BarChart3 className="w-5 h-5 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold">Analyze Results</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Review simulation results with comprehensive analytics and visualizations.
          </p>
          <ul className="text-gray-600 space-y-2">
            <li>• Traffic flow statistics</li>
            <li>• Vehicle density metrics</li>
            <li>• Performance charts and graphs</li>
            <li>• Export data for further analysis</li>
          </ul>
        </div>
      )
    },
    {
      title: "Getting Started",
      content: (
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold mb-4">You're Ready to Start!</h3>
          <p className="text-gray-600 mb-4">
            You now know the basics of using the Traffic Simulator. Here are some tips to get started:
          </p>
          <div className="bg-blue-50 p-4 rounded-lg text-left">
            <h4 className="font-medium text-blue-900 mb-2">Quick Start Tips:</h4>
            <ul className="text-blue-800 text-sm space-y-1">
              <li>• Start with a sample network to familiarize yourself</li>
              <li>• Use default configuration settings for your first simulation</li>
              <li>• Monitor the real-time visualization during simulation</li>
              <li>• Check the analytics page for detailed results</li>
              <li>• Make sure SUMO is installed on your system</li>
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-primary rounded-xl max-w-2xl w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-gray-900">
              {currentStepData.title}
            </h2>
            <span className="text-sm text-gray-500">
              Step {currentStep + 1} of {onboardingSteps.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Progress bar */}
        <div className="px-6 pt-4">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill"
              style={{ width: `${((currentStep + 1) / onboardingSteps.length) * 100}%` }}
            ></div>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          {currentStepData.content}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="flex space-x-2">
            <button
              onClick={handleSkip}
              className="text-gray-600 hover:text-gray-800 transition-colors"
            >
              Skip Tour
            </button>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="flex items-center space-x-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>
            
            <button
              onClick={handleNext}
              className="flex items-center space-x-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <span>
                {currentStep === onboardingSteps.length - 1 ? 'Get Started' : 'Next'}
              </span>
              {currentStep !== onboardingSteps.length - 1 && (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingModal;
