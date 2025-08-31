/**
 * Navigation Component
 * 
 * Responsive navigation bar for the Traffic Simulator application.
 * Provides navigation between different sections and displays connection status.
 * Follows ISO 9241-110 accessibility guidelines and WCAG 2.1 AA standards.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Network, 
  Settings, 
  Play, 
  BarChart3, 
  Menu, 
  X,
  Wifi,
  WifiOff,
  Circle
} from 'lucide-react';

const Navigation = ({ isConnected, backendStatus, simulationStatus }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  
  const navigationItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/network', label: 'Network', icon: Network },
    { path: '/configuration', label: 'Configuration', icon: Settings },
    { path: '/simulation', label: 'Simulation', icon: Play },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 }
  ];
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'text-green-600';
      case 'stopped':
        return 'text-gray-600';
      case 'error':
        return 'text-red-600';
      case 'initializing':
        return 'text-yellow-600';
      default:
        return 'text-gray-400';
    }
  };
  
  const getStatusText = (status) => {
    switch (status) {
      case 'running':
        return 'Running';
      case 'stopped':
        return 'Stopped';
      case 'error':
        return 'Error';
      case 'initializing':
        return 'Starting';
      case 'finished':
        return 'Finished';
      default:
        return 'Unknown';
    }
  };
  
  const isActiveRoute = (path) => {
    return location.pathname === path;
  };
  
  return (
    <nav className="bg-white shadow-lg fixed top-0 left-0 right-0 z-50" role="navigation" aria-label="Main navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 lg:h-20">
          {/* Logo and brand - Always visible */}
          <div className="flex items-center flex-shrink-0">
            <Link 
              to="/" 
              className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-1"
              aria-label="Go to home page"
            >
              <div className="w-8 h-8 lg:w-10 lg:h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Network className="w-5 h-5 lg:w-6 lg:h-6 text-white" />
              </div>
              <span className="text-lg lg:text-xl font-bold text-gray-900 hidden sm:block">
                Traffic Simulator
              </span>
            </Link>
          </div>
          
          {/* Desktop navigation - Hidden on mobile */}
          <div className="hidden lg:flex items-center space-x-6 xl:space-x-8">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = isActiveRoute(item.path);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm xl:text-base font-medium transition-all duration-200 min-h-[44px] ${
                    isActive
                      ? 'text-blue-600 bg-blue-50 border-2 border-blue-200 shadow-sm'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50 border-2 border-transparent hover:border-gray-200'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className="w-4 h-4 xl:w-5 xl:h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
          
          {/* Status indicators and mobile menu button */}
          <div className="flex items-center space-x-2 lg:space-x-4">
            {/* Status indicators - Responsive visibility */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              {/* Backend connection status */}
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-50" aria-live="polite">
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-600" aria-hidden="true" />
                    <span className="text-sm font-medium text-green-600 hidden lg:inline">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-600" aria-hidden="true" />
                    <span className="text-sm font-medium text-red-600 hidden lg:inline">Disconnected</span>
                  </>
                )}
              </div>
              
              {/* Simulation status */}
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-50" aria-live="polite">
                <Circle 
                  className={`w-3 h-3 ${getStatusColor(simulationStatus)} ${simulationStatus === 'running' ? 'animate-pulse' : ''}`}
                  fill="currentColor"
                  aria-hidden="true"
                />
                <span className={`text-sm font-medium ${getStatusColor(simulationStatus)} hidden xl:inline`}>
                  {getStatusText(simulationStatus)}
                </span>
              </div>
            </div>
            
            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={isMobileMenuOpen ? 'Close main menu' : 'Open main menu'}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" aria-hidden="true" />
              ) : (
                <Menu className="w-6 h-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu - Responsive overlay */}
      {isMobileMenuOpen && (
        <div className="lg:hidden" id="mobile-menu">
          <div className="px-4 pt-2 pb-3 space-y-1 bg-white border-t shadow-lg">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = isActiveRoute(item.path);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-base font-medium transition-all duration-200 min-h-[48px] ${
                    isActive
                      ? 'text-blue-600 bg-blue-50 border-l-4 border-blue-600'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`}
                  onClick={() => setIsMobileMenuOpen(false)}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            
            {/* Mobile status section */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="px-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Connection Status</span>
                  <div className="flex items-center space-x-2">
                    {isConnected ? (
                      <>
                        <Wifi className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-green-600">Connected</span>
                      </>
                    ) : (
                      <>
                        <WifiOff className="w-4 h-4 text-red-600" />
                        <span className="text-sm text-red-600">Disconnected</span>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Simulation</span>
                  <div className="flex items-center space-x-2">
                    <Circle 
                      className={`w-3 h-3 ${getStatusColor(simulationStatus)} ${simulationStatus === 'running' ? 'animate-pulse' : ''}`}
                      fill="currentColor"
                    />
                    <span className={`text-sm ${getStatusColor(simulationStatus)}`}>
                      {getStatusText(simulationStatus)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
