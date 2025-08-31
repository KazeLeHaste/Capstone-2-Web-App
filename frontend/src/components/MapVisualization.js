/**
 * Map Visualization Component
 * 
 * Renders a 2D map view of the traffic simulation using a simple canvas-based approach.
 * Displays vehicles, roads, and real-time traffic flow.
 * 
 * Author: Traffic Simulator Team
 * Date: August 2025
 */

import React, { useRef, useEffect, useState } from 'react';
import { AlertCircle, Zap, Eye } from 'lucide-react';

const MapVisualization = ({ simulationData, isRunning, config, isFullscreen = false }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [canvasDimensions, setCanvasDimensions] = useState({ width: 800, height: 600 });
  const [viewMode, setViewMode] = useState('vehicles'); // 'vehicles', 'traffic', 'network'
  const [showGrid, setShowGrid] = useState(true);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Set canvas dimensions
    const container = canvas.parentElement;
    const containerRect = container.getBoundingClientRect();
    const width = containerRect.width - 32; // Account for padding
    const height = isFullscreen ? window.innerHeight - 200 : 400;
    
    canvas.width = width;
    canvas.height = height;
    setCanvasDimensions({ width, height });
    
    // Start animation loop
    animationRef.current = requestAnimationFrame(drawMap);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [simulationData, isRunning, viewMode, showGrid, isFullscreen]);
  
  const drawMap = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const { width, height } = canvasDimensions;
    
    // Clear canvas
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid if enabled
    if (showGrid) {
      drawGrid(ctx, width, height);
    }
    
    // Draw network (roads and junctions)
    if (simulationData && simulationData.junctions) {
      drawNetwork(ctx, width, height);
    }
    
    // Draw vehicles
    if (simulationData && simulationData.vehicles && viewMode === 'vehicles') {
      drawVehicles(ctx, width, height);
    }
    
    // Draw traffic density overlay
    if (simulationData && simulationData.edges && viewMode === 'traffic') {
      drawTrafficDensity(ctx, width, height);
    }
    
    // Draw legend
    drawLegend(ctx, width, height);
    
    // Continue animation if running
    if (isRunning) {
      animationRef.current = requestAnimationFrame(drawMap);
    }
  };
  
  const drawGrid = (ctx, width, height) => {
    const gridSize = 50;
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    
    // Vertical lines
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    // Horizontal lines
    for (let y = 0; y <= height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };
  
  const drawNetwork = (ctx, width, height) => {
    const { junctions = [], edges = [] } = simulationData;
    
    // Scale factors to fit network in canvas
    const padding = 50;
    const scale = calculateScale(junctions, width - 2 * padding, height - 2 * padding);
    const offset = { x: padding, y: padding };
    
    // Draw edges (roads)
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 3;
    
    edges.forEach(edge => {
      // For demo purposes, create a simple road network
      // In a real implementation, this would use actual edge geometry
      const startJunction = junctions.find(j => j.id.includes('1')) || junctions[0];
      const endJunction = junctions.find(j => j.id.includes('2')) || junctions[1];
      
      if (startJunction && endJunction) {
        const start = scalePosition(startJunction.position, scale, offset);
        const end = scalePosition(endJunction.position, scale, offset);
        
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
      }
    });
    
    // Draw junctions
    ctx.fillStyle = '#475569';
    junctions.forEach(junction => {
      const pos = scalePosition(junction.position, scale, offset);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
      ctx.fill();
    });
  };
  
  const drawVehicles = (ctx, width, height) => {
    const { vehicles = [], junctions = [] } = simulationData;
    
    if (junctions.length === 0) return;
    
    const padding = 50;
    const scale = calculateScale(junctions, width - 2 * padding, height - 2 * padding);
    const offset = { x: padding, y: padding };
    
    vehicles.forEach(vehicle => {
      const pos = scalePosition(vehicle.position, scale, offset);
      
      // Vehicle color based on type
      let color = '#3b82f6'; // Blue for cars
      if (vehicle.type === 'truck') {
        color = '#ef4444'; // Red for trucks
      }
      
      // Draw vehicle as a circle with speed indicator
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, 2 * Math.PI);
      ctx.fill();
      
      // Draw speed indicator (line)
      if (vehicle.speed > 0) {
        const speedLength = Math.min(vehicle.speed * 2, 20);
        const angle = (vehicle.angle || 0) * Math.PI / 180;
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(
          pos.x + Math.cos(angle) * speedLength,
          pos.y + Math.sin(angle) * speedLength
        );
        ctx.stroke();
      }
    });
  };
  
  const drawTrafficDensity = (ctx, width, height) => {
    const { edges = [], junctions = [] } = simulationData;
    
    if (junctions.length === 0) return;
    
    const padding = 50;
    const scale = calculateScale(junctions, width - 2 * padding, height - 2 * padding);
    const offset = { x: padding, y: padding };
    
    edges.forEach(edge => {
      // Get density color based on vehicle count
      const density = edge.vehicle_count || 0;
      let color = '#22c55e'; // Green for low density
      
      if (density > 5) {
        color = '#eab308'; // Yellow for medium density
      }
      if (density > 10) {
        color = '#ef4444'; // Red for high density
      }
      
      // Draw density overlay (simplified)
      const startJunction = junctions[0] || { position: { x: 100, y: 100 } };
      const endJunction = junctions[1] || { position: { x: 400, y: 100 } };
      
      const start = scalePosition(startJunction.position, scale, offset);
      const end = scalePosition(endJunction.position, scale, offset);
      
      ctx.strokeStyle = color;
      ctx.lineWidth = 8;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    });
  };
  
  const drawLegend = (ctx, width, height) => {
    const legendX = width - 150;
    const legendY = 20;
    
    // Legend background
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillRect(legendX, legendY, 140, 100);
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY, 140, 100);
    
    // Legend title
    ctx.fillStyle = '#1f2937';
    ctx.font = '12px Arial';
    ctx.fontWeight = 'bold';
    ctx.fillText('Legend', legendX + 10, legendY + 20);
    
    // Legend items
    let y = legendY + 40;
    
    if (viewMode === 'vehicles') {
      // Cars
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(legendX + 15, y, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = '#374151';
      ctx.font = '10px Arial';
      ctx.fillText('Cars', legendX + 25, y + 3);
      
      y += 20;
      
      // Trucks
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(legendX + 15, y, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = '#374151';
      ctx.fillText('Trucks', legendX + 25, y + 3);
    } else if (viewMode === 'traffic') {
      // Traffic density
      const densityColors = [
        { color: '#22c55e', label: 'Low' },
        { color: '#eab308', label: 'Medium' },
        { color: '#ef4444', label: 'High' }
      ];
      
      densityColors.forEach((item, index) => {
        ctx.strokeStyle = item.color;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(legendX + 10, y + index * 15);
        ctx.lineTo(legendX + 20, y + index * 15);
        ctx.stroke();
        
        ctx.fillStyle = '#374151';
        ctx.font = '10px Arial';
        ctx.fillText(item.label, legendX + 25, y + index * 15 + 3);
      });
    }
  };
  
  const calculateScale = (junctions, maxWidth, maxHeight) => {
    if (junctions.length === 0) return 1;
    
    const positions = junctions.map(j => j.position);
    const minX = Math.min(...positions.map(p => p.x));
    const maxX = Math.max(...positions.map(p => p.x));
    const minY = Math.min(...positions.map(p => p.y));
    const maxY = Math.max(...positions.map(p => p.y));
    
    const networkWidth = maxX - minX || 500;
    const networkHeight = maxY - minY || 500;
    
    return Math.min(maxWidth / networkWidth, maxHeight / networkHeight) * 0.8;
  };
  
  const scalePosition = (position, scale, offset) => {
    return {
      x: position.x * scale + offset.x,
      y: position.y * scale + offset.y
    };
  };
  
  const getVehicleCount = () => {
    return simulationData?.vehicles?.length || 0;
  };
  
  const getActiveVehicleCount = () => {
    return simulationData?.vehicles?.filter(v => v.speed > 0).length || 0;
  };
  
  return (
    <div className="relative w-full h-full">
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 bg-white rounded-lg shadow-lg p-3 space-y-2">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">View:</label>
          <select
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="vehicles">Vehicles</option>
            <option value="traffic">Traffic Density</option>
            <option value="network">Network Only</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="showGrid"
            checked={showGrid}
            onChange={(e) => setShowGrid(e.target.checked)}
            className="text-sm"
          />
          <label htmlFor="showGrid" className="text-sm text-gray-700">Grid</label>
        </div>
        
        <div className="text-xs text-gray-600 border-t pt-2">
          <div>Vehicles: {getVehicleCount()}</div>
          <div>Active: {getActiveVehicleCount()}</div>
        </div>
      </div>
      
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full border border-gray-200 rounded-lg"
        style={{ minHeight: '400px' }}
      />
      
      {/* No data overlay */}
      {(!simulationData || !isRunning) && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-90">
          <div className="text-center">
            {!simulationData ? (
              <>
                <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Simulation Data
                </h3>
                <p className="text-gray-600">
                  Start the simulation to see live traffic visualization
                </p>
              </>
            ) : (
              <>
                <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Simulation Stopped
                </h3>
                <p className="text-gray-600">
                  Click "Start Simulation" to begin traffic monitoring
                </p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapVisualization;
