/**
 * Main React Application Component
 * 
 * Entry point for the Traffic Simulator web application.
 * Handles routing, global state, and WebSocket connections.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import io from 'socket.io-client';

// Import pages
import HomePage from './pages/HomePage';
import NetworkSelectionPage from './pages/NetworkSelectionPage';
import ConfigurationPage from './pages/ConfigurationPage';
import SimulationPage from './pages/SimulationPage';
import AnalyticsPage from './pages/AnalyticsPage';

// Import components
import Navigation from './components/Navigation';
import OnboardingModal from './components/OnboardingModal';
import LoadingOverlay from './components/LoadingOverlay';
import ErrorBoundary from './components/ErrorBoundary';

// Import utilities
import { apiClient } from './utils/apiClient';

// Import CSS
import './App.css';

function App() {
  // Application state
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [loading, setLoading] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [simulationStatus, setSimulationStatus] = useState('stopped');
  const [backendStatus, setBackendStatus] = useState('unknown');
  
  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    
    newSocket.on('connect', () => {
      console.log('Connected to backend');
      setIsConnected(true);
      setSocket(newSocket);
    });
    
    newSocket.on('disconnect', () => {
      console.log('Disconnected from backend');
      setIsConnected(false);
    });
    
    newSocket.on('simulation_data', (data) => {
      setSimulationData(data.data);
    });
    
    newSocket.on('simulation_status', (data) => {
      setSimulationStatus(data.status);
    });
    
    newSocket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
    
    newSocket.on('welcome', (data) => {
      console.log('Welcome message:', data.message);
    });
    
    return () => {
      newSocket.close();
    };
  }, []);
  
  // Check backend status on mount
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        const response = await apiClient.get('/api/status');
        setBackendStatus(response.data.backend_status);
      } catch (error) {
        console.error('Failed to check backend status:', error);
        setBackendStatus('offline');
      }
    };
    
    checkBackendStatus();
    
    // Check status periodically
    const interval = setInterval(checkBackendStatus, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);
  
  // Check if user should see onboarding
  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem('traffic_simulator_onboarding_seen');
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);
  
  const handleOnboardingComplete = () => {
    localStorage.setItem('traffic_simulator_onboarding_seen', 'true');
    setShowOnboarding(false);
  };
  
  const handleLoadingChange = (isLoading) => {
    setLoading(isLoading);
  };
  
  return (
    <ErrorBoundary>
      <Router>
        <div className="App">
          {/* Navigation */}
          <Navigation 
            isConnected={isConnected}
            backendStatus={backendStatus}
            simulationStatus={simulationStatus}
          />
          
          {/* Main content */}
          <main className="main-content">
            <Routes>
              <Route 
                path="/" 
                element={
                  <HomePage 
                    onShowOnboarding={() => setShowOnboarding(true)}
                    backendStatus={backendStatus}
                    isConnected={isConnected}
                  />
                } 
              />
              
              {/* Configuration-first workflow */}
              <Route 
                path="/configuration" 
                element={
                  <ConfigurationPage 
                    socket={socket}
                  />
                } 
              />
              <Route 
                path="/network-selection" 
                element={
                  <NetworkSelectionPage 
                    socket={socket}
                    onLoadingChange={handleLoadingChange}
                  />
                } 
              />
              <Route 
                path="/simulation" 
                element={
                  <SimulationPage 
                    socket={socket}
                  />
                } 
              />
              <Route 
                path="/analytics" 
                element={
                  <AnalyticsPage 
                    socket={socket}
                    simulationData={simulationData}
                    simulationStatus={simulationStatus}
                  />
                } 
              />
            </Routes>
          </main>
          
          {/* Onboarding Modal */}
          {showOnboarding && (
            <OnboardingModal 
              onComplete={handleOnboardingComplete}
              onClose={() => setShowOnboarding(false)}
            />
          )}
          
          {/* Loading Overlay */}
          {loading && <LoadingOverlay />}
          
          {/* Connection Status Indicator */}
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-indicator"></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
