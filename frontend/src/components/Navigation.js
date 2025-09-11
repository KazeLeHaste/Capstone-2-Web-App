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

import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Network, 
  Settings, 
  BarChart3, 
  Menu, 
  X,
  Wifi,
  WifiOff,
  Circle,
  Moon,
  Sun
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Navigation = ({ isConnected, backendStatus, simulationStatus }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const mobileMenuRef = useRef(null);
  const { isDarkMode, toggleTheme } = useTheme();
  
  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target)) {
        setIsMobileMenuOpen(false);
      }
    };

    if (isMobileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isMobileMenuOpen]);
  
  const navigationItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/configuration', label: 'Start Simulating', icon: Settings },
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
    <nav className="nav-main" role="navigation" aria-label="Main navigation">
      <div className="nav-container">
        <div className="nav-content">
          {/* Logo and brand - Always visible */}
          <div className="nav-brand">
            <Link 
              to="/" 
              className="nav-brand-link"
              aria-label="Go to home page"
            >
              <div className="nav-brand-icon">
                <Network className="w-5 h-5 lg:w-6 lg:h-6 text-white" />
              </div>
              <span className="nav-brand-text">
                Traffic Simulator
              </span>
            </Link>
          </div>
          
          {/* Status indicators and menu button */}
          <div className="nav-status">
            {/* Status indicators - Always visible on desktop */}
            <div className="nav-status-desktop">
              {/* Backend connection status */}
              <div className="nav-status-item" aria-live="polite">
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-600" aria-hidden="true" />
                    <span className="nav-status-text text-green-600">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-600" aria-hidden="true" />
                    <span className="nav-status-text text-red-600">Disconnected</span>
                  </>
                )}
              </div>
            </div>
            
            {/* Navigation menu button - Always visible */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="nav-menu-button"
              aria-expanded={isMobileMenuOpen}
              aria-controls="navigation-menu"
              aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
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
      
      {/* Navigation dropdown menu - Desktop optimized */}
      {isMobileMenuOpen && (
        <div className="nav-dropdown" id="navigation-menu" ref={mobileMenuRef}>
          <div className="nav-dropdown-content">
            <div className="nav-dropdown-nav space-y-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = isActiveRoute(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-dropdown-link ${isActive ? 'nav-dropdown-link-active' : 'nav-dropdown-link-inactive'}`}
                    onClick={() => setIsMobileMenuOpen(false)}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
              
              {/* Dark Mode Toggle */}
              <div className="nav-dropdown-divider"></div>
              <button
                onClick={toggleTheme}
                className="nav-dropdown-toggle"
                aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDarkMode ? (
                  <Sun className="w-5 h-5 flex-shrink-0" />
                ) : (
                  <Moon className="w-5 h-5 flex-shrink-0" />
                )}
                <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>
              </button>
              
              {/* Mobile status section - Only show on smaller screens */}
              <div className="nav-dropdown-status">
                <div className="nav-dropdown-status-grid space-y-2">
                  <div className="nav-dropdown-status-item">
                    <span className="nav-dropdown-status-label">Connection Status</span>
                    <div className="nav-dropdown-status-value">
                      {isConnected ? (
                        <>
                          <Wifi className="w-4 h-4 text-green-600" />
                          <span className="nav-dropdown-status-text text-green-600">Connected</span>
                        </>
                      ) : (
                        <>
                          <WifiOff className="w-4 h-4 text-red-600" />
                          <span className="nav-dropdown-status-text text-red-600">Disconnected</span>
                        </>
                      )}
                    </div>
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
