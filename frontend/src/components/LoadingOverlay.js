/**
 * Loading Overlay Component
 * 
 * Displays a loading spinner overlay when operations are in progress.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React from 'react';

const LoadingOverlay = ({ message = 'Loading...', isVisible = true }) => {
  if (!isVisible) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-primary rounded-lg p-6 flex flex-col items-center space-y-4 max-w-sm mx-4">
        {/* Spinner */}
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        
        {/* Message */}
        <p className="text-gray-700 text-center">{message}</p>
      </div>
    </div>
  );
};

export default LoadingOverlay;
