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

// Helper functions for CSV conversion
const convertKPIsToCSV = (kpis) => {
  const headers = ['Metric', 'Value', 'Unit'];
  let csv = headers.join(',') + '\n';
  
  const metrics = [
    ['Total Vehicles Completed', kpis.total_vehicles_completed || 0, 'vehicles'],
    ['Average Speed', ((kpis.avg_speed || 0) * 3.6).toFixed(2), 'km/h'],
    ['Average Travel Time', ((kpis.avg_travel_time || 0) / 60).toFixed(2), 'minutes'],
    ['Average Waiting Time', (kpis.avg_waiting_time || 0).toFixed(2), 'seconds'],
    ['Throughput', (kpis.throughput || 0).toFixed(0), 'vehicles/hour'],
    ['Total Distance Traveled', ((kpis.total_distance_traveled || 0) / 1000).toFixed(2), 'km']
  ];
  
  metrics.forEach(metric => {
    csv += `"${metric[0]}",${metric[1]},"${metric[2]}"\n`;
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

// Note: JSZip would need to be imported for the analytics package functionality
// For now, we'll provide the individual export functions
