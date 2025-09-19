/**
 * Report Export Utilities
 * 
 * Utilities for exporting analytics reports as PDF or other formats
 * including chart rendering and data formatting.
 * 
 * Author: Traffic Simulator Team
 * Date: September 2025
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import JSZip from 'jszip';

/**
 * Export analytics report as PDF
 */
export const exportAnalyticsAsPDF = async (analyticsData, sessionId) => {
  try {
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;
    
    // Title page
    pdf.setFontSize(24);
    pdf.text('Traffic Simulation Analytics Report', margin, 30);
    
    pdf.setFontSize(14);
    pdf.text(`Session ID: ${sessionId}`, margin, 45);
    pdf.text(`Generated: ${new Date().toLocaleString()}`, margin, 55);
    
    if (analyticsData.analysis_timestamp) {
      pdf.text(`Analysis Date: ${new Date(analyticsData.analysis_timestamp).toLocaleString()}`, margin, 65);
    }
    
    // Executive Summary
    pdf.setFontSize(18);
    pdf.text('Executive Summary', margin, 85);
    
    pdf.setFontSize(11);
    let yPos = 100;
    
    const kpis = analyticsData.kpis || {};
    const summaryLines = [
      `Total Vehicles Completed: ${kpis.total_vehicles_completed || 0}`,
      `Average Speed: ${((kpis.avg_speed || 0) * 3.6).toFixed(1)} km/h`,
      `Average Travel Time: ${((kpis.avg_travel_time || 0) / 60).toFixed(1)} minutes`,
      `Average Waiting Time: ${(kpis.avg_waiting_time || 0).toFixed(1)} seconds`,
      `Throughput: ${(kpis.throughput || 0).toFixed(0)} vehicles/hour`,
      `Total Distance Traveled: ${((kpis.total_distance_traveled || 0) / 1000).toFixed(1)} km`
    ];
    
    summaryLines.forEach(line => {
      pdf.text(line, margin, yPos);
      yPos += 8;
    });
    
    // Recommendations Section
    yPos += 10;
    pdf.setFontSize(16);
    pdf.text('Key Recommendations', margin, yPos);
    yPos += 10;
    
    pdf.setFontSize(10);
    const recommendations = analyticsData.recommendations || [];
    const highPriorityRecs = recommendations.filter(r => r.priority === 'high').slice(0, 5);
    
    if (highPriorityRecs.length > 0) {
      highPriorityRecs.forEach((rec, index) => {
        if (yPos > pageHeight - 30) {
          pdf.addPage();
          yPos = margin;
        }
        
        pdf.setFontSize(11);
        pdf.text(`${index + 1}. ${rec.category.toUpperCase()}`, margin, yPos);
        yPos += 8;
        
        pdf.setFontSize(9);
        const lines = pdf.splitTextToSize(rec.message, pageWidth - 2 * margin);
        lines.forEach(line => {
          pdf.text(line, margin + 5, yPos);
          yPos += 6;
        });
        yPos += 4;
      });
    } else {
      pdf.text('No high-priority recommendations at this time.', margin, yPos);
      yPos += 10;
    }
    
    // KPI Details Page
    pdf.addPage();
    yPos = margin;
    
    pdf.setFontSize(18);
    pdf.text('Detailed KPI Analysis', margin, yPos);
    yPos += 15;
    
    // Create KPI table
    const kpiDetails = [
      ['Metric', 'Value', 'Status'],
      ['Average Speed', `${((kpis.avg_speed || 0) * 3.6).toFixed(1)} km/h`, getSpeedStatus(kpis.avg_speed * 3.6)],
      ['Average Travel Time', `${((kpis.avg_travel_time || 0) / 60).toFixed(1)} min`, getTravelTimeStatus(kpis.avg_travel_time / 60)],
      ['Average Waiting Time', `${(kpis.avg_waiting_time || 0).toFixed(1)} s`, getWaitingTimeStatus(kpis.avg_waiting_time)],
      ['Throughput', `${(kpis.throughput || 0).toFixed(0)} veh/h`, getThroughputStatus(kpis.throughput)],
      ['Time Loss', `${((kpis.avg_time_loss || 0) / 60).toFixed(1)} min`, getTimeLossStatus(kpis.avg_time_loss / 60)],
      ['Total Teleports', `${kpis.total_teleports || 0}`, getTeleportStatus(kpis.total_teleports)],
      ['Total Collisions', `${kpis.total_collisions || 0}`, getCollisionStatus(kpis.total_collisions)]
    ];
    
    // Draw table
    const cellHeight = 8;
    const colWidths = [60, 40, 30];
    
    kpiDetails.forEach((row, rowIndex) => {
      let xPos = margin;
      
      row.forEach((cell, colIndex) => {
        // Draw cell border
        pdf.rect(xPos, yPos, colWidths[colIndex], cellHeight);
        
        // Set font style for header
        if (rowIndex === 0) {
          pdf.setFontSize(10);
          pdf.setFont(undefined, 'bold');
        } else {
          pdf.setFontSize(9);
          pdf.setFont(undefined, 'normal');
        }
        
        // Add text
        pdf.text(cell, xPos + 2, yPos + 5);
        xPos += colWidths[colIndex];
      });
      
      yPos += cellHeight;
    });
    
    // Emissions Analysis Section
    if (kpis.total_co2_emissions || kpis.total_fuel_consumption || kpis.total_noise_emissions) {
      yPos += 20;
      if (yPos > pageHeight - 50) {
        pdf.addPage();
        yPos = margin;
      }
      
      pdf.setFontSize(16);
      pdf.text('Environmental Impact Analysis', margin, yPos);
      yPos += 15;
      
      pdf.setFontSize(10);
      const emissionsData = [
        ['Environmental Metric', 'Value', 'Unit', 'Status'],
        ['Total CO2 Emissions', (kpis.total_co2_emissions || 0).toFixed(2), 'kg', getCO2Status(kpis.total_co2_emissions)],
        ['Total Fuel Consumption', (kpis.total_fuel_consumption || 0).toFixed(2), 'L', getFuelStatus(kpis.total_fuel_consumption)],
        ['Average Noise Level', (kpis.avg_noise_emissions || 0).toFixed(1), 'dB', getNoiseStatus(kpis.avg_noise_emissions)],
        ['Emissions per Vehicle', ((kpis.total_co2_emissions || 0) / Math.max(kpis.total_vehicles_completed || 1, 1)).toFixed(3), 'kg/veh', 'Info'],
        ['Fuel Efficiency', ((kpis.total_distance_traveled || 0) / Math.max(kpis.total_fuel_consumption || 1, 1)).toFixed(1), 'm/L', 'Info']
      ];
      
      // Draw emissions table
      const emissionsCellHeight = 8;
      const emissionsColWidths = [45, 30, 20, 25];
      
      emissionsData.forEach((row, rowIndex) => {
        let xPos = margin;
        
        if (yPos > pageHeight - 30) {
          pdf.addPage();
          yPos = margin;
        }
        
        row.forEach((cell, colIndex) => {
          pdf.rect(xPos, yPos, emissionsColWidths[colIndex], emissionsCellHeight);
          
          if (rowIndex === 0) {
            pdf.setFontSize(9);
            pdf.setFont(undefined, 'bold');
          } else {
            pdf.setFontSize(8);
            pdf.setFont(undefined, 'normal');
          }
          
          pdf.text(cell.toString(), xPos + 1, yPos + 5);
          xPos += emissionsColWidths[colIndex];
        });
        
        yPos += emissionsCellHeight;
      });
    }

    // Safety Analysis Section
    if (kpis.total_collisions !== undefined || kpis.total_teleports !== undefined || kpis.composite_safety_score !== undefined) {
      yPos += 20;
      if (yPos > pageHeight - 50) {
        pdf.addPage();
        yPos = margin;
      }
      
      pdf.setFontSize(16);
      pdf.text('Safety Analysis', margin, yPos);
      yPos += 15;
      
      pdf.setFontSize(10);
      const safetyData = [
        ['Safety Metric', 'Value', 'Unit', 'Status'],
        ['Safety Score', (kpis.composite_safety_score || 0).toFixed(1), '/100', getSafetyScoreStatus(kpis.composite_safety_score)],
        ['Total Collisions', kpis.total_collisions || 0, 'count', getCollisionStatus(kpis.total_collisions)],
        ['Total Teleports', kpis.total_teleports || 0, 'count', getTeleportStatus(kpis.total_teleports)],
        ['Collision Density', (kpis.collision_density || 0).toFixed(4), '/km', getCollisionDensityStatus(kpis.collision_density)],
        ['Emergency Stops', kpis.avg_emergency_stops || 0, 'avg/veh', getEmergencyStopStatus(kpis.avg_emergency_stops)]
      ];
      
      // Draw safety table
      const safetyCellHeight = 8;
      const safetyColWidths = [40, 25, 25, 30];
      
      safetyData.forEach((row, rowIndex) => {
        let xPos = margin;
        
        if (yPos > pageHeight - 30) {
          pdf.addPage();
          yPos = margin;
        }
        
        row.forEach((cell, colIndex) => {
          pdf.rect(xPos, yPos, safetyColWidths[colIndex], safetyCellHeight);
          
          if (rowIndex === 0) {
            pdf.setFontSize(9);
            pdf.setFont(undefined, 'bold');
          } else {
            pdf.setFontSize(8);
            pdf.setFont(undefined, 'normal');
          }
          
          pdf.text(cell.toString(), xPos + 1, yPos + 5);
          xPos += safetyColWidths[colIndex];
        });
        
        yPos += safetyCellHeight;
      });
    }

    // Network Performance Section  
    if (kpis.avg_density !== undefined || kpis.network_efficiency_index !== undefined) {
      yPos += 20;
      if (yPos > pageHeight - 50) {
        pdf.addPage();
        yPos = margin;
      }
      
      pdf.setFontSize(16);
      pdf.text('Network Performance Analysis', margin, yPos);
      yPos += 15;
      
      pdf.setFontSize(10);
      const networkData = [
        ['Network Metric', 'Value', 'Unit', 'Status'],
        ['Network Efficiency', (kpis.network_efficiency_index || 0).toFixed(3), 'index', getNetworkEfficiencyStatus(kpis.network_efficiency_index)],
        ['Average Density', (kpis.avg_density || 0).toFixed(2), 'veh/km', getDensityStatus(kpis.avg_density)],
        ['Edge Utilization Variance', (kpis.edge_utilization_variance || 0).toFixed(4), 'variance', getUtilizationVarianceStatus(kpis.edge_utilization_variance)],
        ['Max Edge Utilization', ((kpis.max_edge_utilization || 0) * 100).toFixed(1), '%', getMaxUtilizationStatus(kpis.max_edge_utilization)],
        ['Congestion Index', (kpis.congestion_index || 0).toFixed(2), 'index', getCongestionStatus(kpis.congestion_index)]
      ];
      
      // Draw network table
      const networkCellHeight = 8;
      const networkColWidths = [45, 25, 25, 25];
      
      networkData.forEach((row, rowIndex) => {
        let xPos = margin;
        
        if (yPos > pageHeight - 30) {
          pdf.addPage();
          yPos = margin;
        }
        
        row.forEach((cell, colIndex) => {
          pdf.rect(xPos, yPos, networkColWidths[colIndex], networkCellHeight);
          
          if (rowIndex === 0) {
            pdf.setFontSize(9);
            pdf.setFont(undefined, 'bold');
          } else {
            pdf.setFontSize(8);
            pdf.setFont(undefined, 'normal');
          }
          
          pdf.text(cell.toString(), xPos + 1, yPos + 5);
          xPos += networkColWidths[colIndex];
        });
        
        yPos += networkCellHeight;
      });
    }

    // Vehicle Type Analysis (if available)
    if (analyticsData.vehicle_type_breakdown && Object.keys(analyticsData.vehicle_type_breakdown).length > 0) {
      yPos += 20;
      if (yPos > pageHeight - 50) {
        pdf.addPage();
        yPos = margin;
      }
      
      pdf.setFontSize(16);
      pdf.text('Vehicle Type Breakdown', margin, yPos);
      yPos += 15;
      
      pdf.setFontSize(10);
      Object.entries(analyticsData.vehicle_type_breakdown).forEach(([type, stats]) => {
        pdf.text(`${type.toUpperCase()}:`, margin, yPos);
        pdf.text(`Count: ${stats.count}`, margin + 40, yPos);
        pdf.text(`Avg Speed: ${(stats.avg_speed * 3.6).toFixed(1)} km/h`, margin + 80, yPos);
        pdf.text(`Avg Distance: ${(stats.avg_distance / 1000).toFixed(1)} km`, margin + 130, yPos);
        yPos += 8;
      });
    }
    
    // Footer
    const totalPages = pdf.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.text(
        `Page ${i} of ${totalPages} | Traffic Simulation Analytics | ${new Date().toLocaleDateString()}`,
        margin,
        pageHeight - 10
      );
    }
    
    // Save the PDF
    pdf.save(`traffic_analytics_${sessionId}_${new Date().toISOString().split('T')[0]}.pdf`);
    
    return true;
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw new Error('Failed to generate PDF report');
  }
};

/**
 * Export chart as image
 */
export const exportChartAsImage = async (chartElementId, filename) => {
  try {
    const chartElement = document.getElementById(chartElementId);
    if (!chartElement) {
      throw new Error('Chart element not found');
    }
    
    const canvas = await html2canvas(chartElement, {
      backgroundColor: '#ffffff',
      scale: 2
    });
    
    // Create download link
    const link = document.createElement('a');
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    
    return true;
  } catch (error) {
    console.error('Error exporting chart:', error);
    throw new Error('Failed to export chart as image');
  }
};

/**
 * Export data as CSV
 */
export const exportDataAsCSV = (data, filename, headers = null) => {
  try {
    let csvContent = '';
    
    // Add headers if provided
    if (headers) {
      csvContent += headers.join(',') + '\n';
    }
    
    // Add data rows
    data.forEach(row => {
      const values = typeof row === 'object' ? Object.values(row) : [row];
      csvContent += values.map(val => 
        typeof val === 'string' ? `"${val}"` : val
      ).join(',') + '\n';
    });
    
    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
    
    return true;
  } catch (error) {
    console.error('Error exporting CSV:', error);
    throw new Error('Failed to export CSV file');
  }
};

/**
 * Create comprehensive analytics package
 */
export const createAnalyticsPackage = async (analyticsData, sessionId) => {
  try {
    const zip = new JSZip();
    
    // Add analytics JSON
    zip.file('analytics_data.json', JSON.stringify(analyticsData, null, 2));
    
    // Add KPI summary CSV
    if (analyticsData.kpis) {
      const kpiCsv = convertKPIsToCSV(analyticsData.kpis);
      zip.file('kpi_summary.csv', kpiCsv);
    }
    
    // Add recommendations CSV
    if (analyticsData.recommendations && analyticsData.recommendations.length > 0) {
      const recCsv = convertRecommendationsToCSV(analyticsData.recommendations);
      zip.file('recommendations.csv', recCsv);
    }
    
    // Add time series data CSV
    if (analyticsData.time_series && analyticsData.time_series.length > 0) {
      const timeSeriesCsv = convertTimeSeriestoCSV(analyticsData.time_series);
      zip.file('time_series.csv', timeSeriesCsv);
    }
    
    // Generate and save the zip
    const content = await zip.generateAsync({ type: 'blob' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(content);
    link.download = `analytics_package_${sessionId}_${new Date().toISOString().split('T')[0]}.zip`;
    link.click();
    
    return true;
  } catch (error) {
    console.error('Error creating analytics package:', error);
    throw new Error('Failed to create analytics package');
  }
};

// Helper functions for status determination
const getSpeedStatus = (speed) => {
  if (speed > 25) return 'Good';
  if (speed > 15) return 'Fair';
  return 'Poor';
};

const getTravelTimeStatus = (time) => {
  if (time < 15) return 'Good';
  if (time < 30) return 'Fair';
  return 'Poor';
};

const getWaitingTimeStatus = (time) => {
  if (time < 30) return 'Good';
  if (time < 60) return 'Fair';
  return 'Poor';
};

const getThroughputStatus = (throughput) => {
  if (throughput > 800) return 'Good';
  if (throughput > 400) return 'Fair';
  return 'Poor';
};

const getTimeLossStatus = (timeLoss) => {
  if (timeLoss < 2) return 'Good';
  if (timeLoss < 5) return 'Fair';
  return 'Poor';
};

const getTeleportStatus = (teleports) => {
  if (teleports === 0) return 'Good';
  if (teleports < 5) return 'Fair';
  return 'Poor';
};

const getCollisionStatus = (collisions) => {
  if (collisions === 0) return 'Good';
  return 'Poor';
};

// Environmental status functions
const getCO2Status = (co2) => {
  if (!co2) return 'N/A';
  if (co2 < 50) return 'Good';
  if (co2 < 100) return 'Fair';
  return 'Poor';
};

const getFuelStatus = (fuel) => {
  if (!fuel) return 'N/A';
  if (fuel < 20) return 'Good';
  if (fuel < 40) return 'Fair';
  return 'Poor';
};

const getNoiseStatus = (noise) => {
  if (!noise) return 'N/A';
  if (noise < 60) return 'Good';
  if (noise < 70) return 'Fair';
  return 'Poor';
};

// Safety status functions
const getSafetyScoreStatus = (score) => {
  if (!score) return 'N/A';
  if (score >= 80) return 'Good';
  if (score >= 60) return 'Fair';
  return 'Poor';
};

const getCollisionDensityStatus = (density) => {
  if (!density) return 'Good';
  if (density < 0.001) return 'Good';
  if (density < 0.01) return 'Fair';
  return 'Poor';
};

const getEmergencyStopStatus = (stops) => {
  if (!stops) return 'Good';
  if (stops < 2) return 'Good';
  if (stops < 5) return 'Fair';
  return 'Poor';
};

// Network performance status functions
const getNetworkEfficiencyStatus = (efficiency) => {
  if (!efficiency) return 'N/A';
  if (efficiency >= 0.8) return 'Good';
  if (efficiency >= 0.6) return 'Fair';
  return 'Poor';
};

const getDensityStatus = (density) => {
  if (!density) return 'N/A';
  if (density < 20) return 'Good';
  if (density < 40) return 'Fair';
  return 'Poor';
};

const getUtilizationVarianceStatus = (variance) => {
  if (!variance) return 'Good';
  if (variance < 0.1) return 'Good';
  if (variance < 0.3) return 'Fair';
  return 'Poor';
};

const getMaxUtilizationStatus = (utilization) => {
  if (!utilization) return 'N/A';
  const percent = utilization * 100;
  if (percent < 80) return 'Good';
  if (percent < 95) return 'Fair';
  return 'Poor';
};

const getCongestionStatus = (congestion) => {
  if (!congestion) return 'Good';
  if (congestion < 1.5) return 'Good';
  if (congestion < 2.5) return 'Fair';
  return 'Poor';
};

// Helper functions for CSV conversion
const convertKPIsToCSV = (kpis) => {
  const headers = ['Category', 'Metric', 'Value', 'Unit'];
  let csv = headers.join(',') + '\n';
  
  const metrics = [
    // Basic Performance Metrics
    ['Performance', 'Total Vehicles Completed', kpis.total_vehicles_completed || 0, 'vehicles'],
    ['Performance', 'Average Speed', ((kpis.avg_speed || 0) * 3.6).toFixed(2), 'km/h'],
    ['Performance', 'Average Travel Time', ((kpis.avg_travel_time || 0) / 60).toFixed(2), 'minutes'],
    ['Performance', 'Average Waiting Time', (kpis.avg_waiting_time || 0).toFixed(2), 'seconds'],
    ['Performance', 'Throughput', (kpis.throughput || 0).toFixed(0), 'vehicles/hour'],
    ['Performance', 'Total Distance Traveled', ((kpis.total_distance_traveled || 0) / 1000).toFixed(2), 'km'],
    
    // Environmental Metrics
    ['Environmental', 'Total CO2 Emissions', (kpis.total_co2_emissions || 0).toFixed(2), 'kg'],
    ['Environmental', 'Total Fuel Consumption', (kpis.total_fuel_consumption || 0).toFixed(2), 'L'],
    ['Environmental', 'Average Noise Level', (kpis.avg_noise_emissions || 0).toFixed(1), 'dB'],
    ['Environmental', 'CO2 per Vehicle', ((kpis.total_co2_emissions || 0) / Math.max(kpis.total_vehicles_completed || 1, 1)).toFixed(3), 'kg/veh'],
    ['Environmental', 'Fuel Efficiency', ((kpis.total_distance_traveled || 0) / Math.max(kpis.total_fuel_consumption || 1, 1)).toFixed(1), 'm/L'],
    
    // Safety Metrics
    ['Safety', 'Safety Score', (kpis.composite_safety_score || 0).toFixed(1), '/100'],
    ['Safety', 'Total Collisions', kpis.total_collisions || 0, 'count'],
    ['Safety', 'Total Teleports', kpis.total_teleports || 0, 'count'],
    ['Safety', 'Collision Density', (kpis.collision_density || 0).toFixed(4), '/km'],
    ['Safety', 'Average Emergency Stops', (kpis.avg_emergency_stops || 0).toFixed(2), 'per vehicle'],
    
    // Network Performance Metrics
    ['Network', 'Network Efficiency Index', (kpis.network_efficiency_index || 0).toFixed(3), 'ratio'],
    ['Network', 'Average Density', (kpis.avg_density || 0).toFixed(2), 'veh/km'],
    ['Network', 'Edge Utilization Variance', (kpis.edge_utilization_variance || 0).toFixed(4), 'variance'],
    ['Network', 'Max Edge Utilization', ((kpis.max_edge_utilization || 0) * 100).toFixed(1), '%'],
    ['Network', 'Congestion Index', (kpis.congestion_index || 0).toFixed(2), 'ratio']
  ];
  
  metrics.forEach(metric => {
    csv += `"${metric[0]}","${metric[1]}",${metric[2]},"${metric[3]}"\n`;
  });
  
  return csv;
};

const convertRecommendationsToCSV = (recommendations) => {
  const headers = ['Priority', 'Category', 'Message', 'KPI', 'Actual Value', 'Threshold'];
  let csv = headers.join(',') + '\n';
  
  recommendations.forEach(rec => {
    csv += `"${rec.priority}","${rec.category}","${rec.message.replace(/"/g, '""')}","${rec.kpi || ''}",${rec.actual_value || ''},${rec.threshold || ''}\n`;
  });
  
  return csv;
};

const convertTimeSeriestoCSV = (timeSeries) => {
  const headers = ['Time', 'Running Vehicles', 'Halting Vehicles', 'Mean Speed (m/s)', 'Mean Waiting Time'];
  let csv = headers.join(',') + '\n';
  
  timeSeries.forEach(ts => {
    csv += `${ts.time},${ts.running_vehicles},${ts.halting_vehicles},${ts.mean_speed},${ts.mean_waiting_time}\n`;
  });
  
  return csv;
};

/**
 * Export emissions data as CSV
 */
export const exportEmissionsDataAsCSV = (analyticsData, filename) => {
  try {
    const headers = ['Time', 'CO2 (kg)', 'Fuel (L)', 'Noise (dB)', 'Vehicle Count'];
    const data = [];
    
    if (analyticsData.emissions_time_series) {
      analyticsData.emissions_time_series.forEach(point => {
        data.push([
          new Date(point.timestamp).toISOString(),
          (point.co2_emissions || 0).toFixed(3),
          (point.fuel_consumption || 0).toFixed(3),
          (point.noise_emissions || 0).toFixed(1),
          point.vehicle_count || 0
        ]);
      });
    }
    
    return exportDataAsCSV(data, filename, headers);
  } catch (error) {
    console.error('Error exporting emissions data:', error);
    throw new Error('Failed to export emissions data');
  }
};

/**
 * Export safety data as CSV
 */
export const exportSafetyDataAsCSV = (analyticsData, filename) => {
  try {
    const headers = ['Time', 'Collisions', 'Teleports', 'Emergency Stops', 'Safety Index'];
    const data = [];
    
    if (analyticsData.safety_time_series) {
      analyticsData.safety_time_series.forEach(point => {
        data.push([
          new Date(point.timestamp).toISOString(),
          point.collisions || 0,
          point.teleports || 0,
          point.emergency_stops || 0,
          (point.safety_index || 0).toFixed(2)
        ]);
      });
    }
    
    return exportDataAsCSV(data, filename, headers);
  } catch (error) {
    console.error('Error exporting safety data:', error);
    throw new Error('Failed to export safety data');
  }
};

/**
 * Export network performance data as CSV
 */
export const exportNetworkDataAsCSV = (analyticsData, filename) => {
  try {
    const headers = ['Edge ID', 'Utilization', 'Density', 'Speed', 'Flow', 'Occupancy'];
    const data = [];
    
    if (analyticsData.network_analysis) {
      Object.entries(analyticsData.network_analysis).forEach(([edgeId, edgeData]) => {
        data.push([
          edgeId,
          (edgeData.utilization || 0).toFixed(3),
          (edgeData.density || 0).toFixed(2),
          (edgeData.speed || 0).toFixed(2),
          (edgeData.flow || 0).toFixed(1),
          (edgeData.occupancy || 0).toFixed(3)
        ]);
      });
    }
    
    return exportDataAsCSV(data, filename, headers);
  } catch (error) {
    console.error('Error exporting network data:', error);
    throw new Error('Failed to export network data');
  }
};

/**
 * Export comprehensive analytics report as Excel-like format
 */
export const exportAdvancedAnalyticsAsCSV = (analyticsData, sessionId) => {
  try {
    const zip = new JSZip();
    
    // Add main KPI summary
    const kpiCsv = convertKPIsToCSV(analyticsData.kpis || {});
    zip.file('01_kpi_summary.csv', kpiCsv);
    
    // Add time series data
    if (analyticsData.time_series && analyticsData.time_series.length > 0) {
      const timeSeriesCsv = convertTimeSeriestoCSV(analyticsData.time_series);
      zip.file('02_time_series.csv', timeSeriesCsv);
    }
    
    // Add emissions data
    if (analyticsData.emissions_time_series) {
      const emissionsCsv = convertEmissionsToCSV(analyticsData.emissions_time_series);
      zip.file('03_emissions_data.csv', emissionsCsv);
    }
    
    // Add safety data
    if (analyticsData.safety_time_series) {
      const safetyCsv = convertSafetyToCSV(analyticsData.safety_time_series);
      zip.file('04_safety_data.csv', safetyCsv);
    }
    
    // Add network analysis
    if (analyticsData.network_analysis) {
      const networkCsv = convertNetworkToCSV(analyticsData.network_analysis);
      zip.file('05_network_analysis.csv', networkCsv);
    }
    
    // Add recommendations
    if (analyticsData.recommendations && analyticsData.recommendations.length > 0) {
      const recCsv = convertRecommendationsToCSV(analyticsData.recommendations);
      zip.file('06_recommendations.csv', recCsv);
    }
    
    // Add route analysis if available
    if (analyticsData.route_analysis) {
      const routeCsv = convertRouteAnalysisToCSV(analyticsData.route_analysis);
      zip.file('07_route_analysis.csv', routeCsv);
    }
    
    // Generate and download the zip
    return zip.generateAsync({ type: 'blob' }).then(content => {
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(content);
      link.download = `advanced_analytics_${sessionId}_${new Date().toISOString().split('T')[0]}.zip`;
      link.click();
      return true;
    });
    
  } catch (error) {
    console.error('Error creating advanced analytics package:', error);
    throw new Error('Failed to create advanced analytics package');
  }
};

// Additional CSV conversion helpers
const convertEmissionsToCSV = (emissionsData) => {
  const headers = ['Timestamp', 'CO2_Emissions_kg', 'Fuel_Consumption_L', 'Noise_Emissions_dB', 'Vehicle_Count'];
  let csv = headers.join(',') + '\n';
  
  emissionsData.forEach(point => {
    csv += `${point.timestamp},${point.co2_emissions || 0},${point.fuel_consumption || 0},${point.noise_emissions || 0},${point.vehicle_count || 0}\n`;
  });
  
  return csv;
};

const convertSafetyToCSV = (safetyData) => {
  const headers = ['Timestamp', 'Collisions', 'Teleports', 'Emergency_Stops', 'Safety_Index'];
  let csv = headers.join(',') + '\n';
  
  safetyData.forEach(point => {
    csv += `${point.timestamp},${point.collisions || 0},${point.teleports || 0},${point.emergency_stops || 0},${point.safety_index || 0}\n`;
  });
  
  return csv;
};

const convertNetworkToCSV = (networkData) => {
  const headers = ['Edge_ID', 'Utilization', 'Density', 'Speed_ms', 'Flow_veh_h', 'Occupancy'];
  let csv = headers.join(',') + '\n';
  
  Object.entries(networkData).forEach(([edgeId, data]) => {
    csv += `${edgeId},${data.utilization || 0},${data.density || 0},${data.speed || 0},${data.flow || 0},${data.occupancy || 0}\n`;
  });
  
  return csv;
};

const convertRouteAnalysisToCSV = (routeData) => {
  const headers = ['Route_ID', 'Vehicle_Count', 'Average_Speed', 'Average_Travel_Time', 'Total_Distance', 'Utilization_Rate'];
  let csv = headers.join(',') + '\n';
  
  Object.entries(routeData).forEach(([routeId, data]) => {
    csv += `${routeId},${data.vehicle_count || 0},${data.avg_speed || 0},${data.avg_travel_time || 0},${data.total_distance || 0},${data.utilization_rate || 0}\n`;
  });
  
  return csv;
};

// Note: JSZip is imported at the top for the analytics package functionality
