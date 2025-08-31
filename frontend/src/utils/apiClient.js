/**
 * API Client Utility
 * 
 * Handles HTTP requests to the Flask backend with proper error handling
 * and request/response interceptors for the Traffic Simulator application.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import axios from 'axios';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor for debugging and token handling
apiClient.interceptors.request.use(
  (config) => {
    // Log requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    // Add any authentication tokens here if needed in the future
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and logging
apiClient.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      
      console.error(`API Error ${status}:`, data?.error || data?.message || 'Unknown error');
      
      // Handle specific status codes
      switch (status) {
        case 400:
          console.error('Bad Request:', data?.error);
          break;
        case 401:
          console.error('Unauthorized access');
          // Handle authentication errors if needed
          break;
        case 403:
          console.error('Forbidden access');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Internal server error');
          break;
        default:
          console.error('Unexpected error:', data?.error);
      }
    } else if (error.request) {
      // Network error or server not responding
      console.error('Network Error: Could not connect to server');
    } else {
      // Request configuration error
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * API service methods for Traffic Simulator endpoints
 */
export const api = {
  // Health and status endpoints
  getHealth: () => apiClient.get('/'),
  getStatus: () => apiClient.get('/api/status'),
  
  // Network management
  getNetworks: () => apiClient.get('/api/networks'),
  
  // Scenario management
  getScenarios: () => apiClient.get('/api/scenarios'),
  
  // Simulation control
  startSimulation: (config) => apiClient.post('/api/simulation/start', config),
  stopSimulation: () => apiClient.post('/api/simulation/stop'),
  getSimulationData: () => apiClient.get('/api/simulation/data'),
  
  // Generic request methods
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data = {}, config = {}) => apiClient.post(url, data, config),
  put: (url, data = {}, config = {}) => apiClient.put(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),
  patch: (url, data = {}, config = {}) => apiClient.patch(url, data, config)
};

/**
 * Error handling utilities
 */
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    return {
      message: error.response.data?.error || error.response.data?.message || 'Server error occurred',
      status: error.response.status,
      type: 'server_error'
    };
  } else if (error.request) {
    // Network error
    return {
      message: 'Unable to connect to server. Please check your connection.',
      status: null,
      type: 'network_error'
    };
  } else {
    // Request configuration error
    return {
      message: error.message || 'An unexpected error occurred',
      status: null,
      type: 'client_error'
    };
  }
};

/**
 * Check if backend is reachable
 */
export const checkBackendConnection = async () => {
  try {
    const response = await api.getHealth();
    return {
      connected: true,
      status: response.data
    };
  } catch (error) {
    return {
      connected: false,
      error: handleApiError(error)
    };
  }
};

/**
 * Utility function to format API responses consistently
 */
export const formatApiResponse = (response) => {
  return {
    success: true,
    data: response.data,
    status: response.status,
    timestamp: new Date().toISOString()
  };
};

/**
 * Utility function to format API errors consistently
 */
export const formatApiError = (error) => {
  const errorInfo = handleApiError(error);
  return {
    success: false,
    error: errorInfo,
    timestamp: new Date().toISOString()
  };
};

// Export the configured axios instance as default
export { apiClient };
export default api;
