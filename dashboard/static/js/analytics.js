/**
 * MAFA Analytics Dashboard JavaScript
 * 
 * This file contains the client-side functionality for the analytics dashboard with charts integration.
 */

// Global variables
let analyticsCharts = {};
let currentTimeframe = '30';
const API_BASE_URL = '/api/v1';

// Chart.js configurations
const chartColors = {
    primary: '#007bff',
    success: '#28a745',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#17a2b8',
    secondary: '#6c757d',
    light: '#f8f9fa',
    dark: '#343a40'
};

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                usePointStyle: true,
                padding: 20
            }
        },
        tooltip: {
            mode: 'index',
            intersect: false
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: 'rgba(0,0,0,0.1)'
            }
        },
        x: {
            grid: {
                color: 'rgba(0,0,0,0.1)'
            }
        }
    }
};

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat('de-DE').format(num);
}

function formatPercentage(num) {
    return `${num.toFixed(1)}%`;
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

// Analytics data loading functions
async function loadAnalyticsData(timeframe = '30') {
    try {
        currentTimeframe = timeframe;
        
        // Show loading states
        showLoading('discovery-chart');
        showLoading('provider-chart');
        showLoading('confidence-chart');
        showLoading('methods-chart');
        
        // Load analytics data
        const response = await fetch(`${API_BASE_URL}/system/analytics/data?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch analytics data');
        
        const data = await response.json();
        
        // Update metrics
        updateMetrics(data);
        
        // Render charts
        renderDiscoveryChart(data.contact_discovery_trend);
        renderProviderChart(data.provider_performance);
        renderConfidenceChart(data.confidence_distribution);
        renderMethodsChart(data.contact_methods);
        
        // Load insights
        await loadInsights(timeframe);
        
    } catch (error) {
        console.error('Error loading analytics data:', error);
        showError('analytics-error', 'Failed to load analytics data. Please try again.');
        
        // Hide loading states and show error states
        ['discovery-chart', 'provider-chart', 'confidence-chart', 'methods-chart'].forEach(chartId => {
            showError(chartId, 'Failed to load chart data');
        });
    }
}

function updateMetrics(data) {
    // Calculate metrics from the data
    const totalContacts = data.contact_discovery_trend.reduce((sum, day) => sum + day.count, 0);
    const avgDaily = totalContacts / data.contact_discovery_trend.length;
    
    // Update key metrics
    const metrics = {
        'total-searches-metric': '247', // Mock data for searches
        'contacts-found-metric': formatNumber(totalContacts),
        'success-rate-metric': '87.3%', // Mock success rate
        'avg-response-metric': `${Math.round(avgDaily)}h`
    };
    
    // Update trend indicators
    const trends = {
        'searches-change': '+12%',
        'contacts-change': '+8%',
        'success-change': '+3%',
        'response-change': '-5%'
    };
    
    Object.entries(metrics).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
    
    Object.entries(trends).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            const isPositive = value.startsWith('+');
            const isNegative = value.startsWith('-');
            
            element.className = `metric-change ${isPositive ? 'positive' : isNegative ? 'negative' : 'neutral'}`;
            element.textContent = value;
        }
    });
}

// Chart rendering functions
function renderDiscoveryChart(trendData) {
    const ctx = document.getElementById('discovery-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (analyticsCharts.discovery) {
        analyticsCharts.discovery.destroy();
    }
    
    const labels = trendData.map(item => item.date);
    const counts = trendData.map(item => item.count);
    const quality = trendData.map(item => item.quality * 100);
    
    analyticsCharts.discovery = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Contacts Found',
                    data: counts,
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Quality Score',
                    data: quality,
                    borderColor: chartColors.success,
                    backgroundColor: chartColors.success + '20',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

function renderProviderChart(providerData) {
    const ctx = document.getElementById('provider-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (analyticsCharts.provider) {
        analyticsCharts.provider.destroy();
    }
    
    const labels = providerData.map(item => item.provider);
    const listings = providerData.map(item => item.listings_found);
    const successRates = providerData.map(item => item.success_rate);
    
    analyticsCharts.provider = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: listings,
                backgroundColor: [
                    chartColors.primary,
                    chartColors.success,
                    chartColors.warning,
                    chartColors.info
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const successRate = successRates[index];
                            return `${context.label}: ${context.parsed} listings (${successRate}% success)`;
                        }
                    }
                }
            }
        }
    });
}

function renderConfidenceChart(confidenceData) {
    const ctx = document.getElementById('confidence-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (analyticsCharts.confidence) {
        analyticsCharts.confidence.destroy();
    }
    
    const labels = confidenceData.map(item => item.range);
    const counts = confidenceData.map(item => item.count);
    
    analyticsCharts.confidence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Contacts',
                data: counts,
                backgroundColor: [
                    chartColors.success,
                    chartColors.success,
                    chartColors.warning,
                    chartColors.warning,
                    chartColors.danger
                ],
                borderColor: [
                    chartColors.success,
                    chartColors.success,
                    chartColors.warning,
                    chartColors.warning,
                    chartColors.danger
                ],
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderMethodsChart(methodsData) {
    const ctx = document.getElementById('methods-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (analyticsCharts.methods) {
        analyticsCharts.methods.destroy();
    }
    
    const labels = methodsData.map(item => item.method);
    const counts = methodsData.map(item => item.count);
    
    analyticsCharts.methods = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    chartColors.primary,
                    chartColors.info,
                    chartColors.warning,
                    chartColors.secondary
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const percentage = methodsData[context.dataIndex].percentage;
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Insights functions
async function loadInsights(timeframe = '30') {
    try {
        const response = await fetch(`${API_BASE_URL}/system/analytics/insights?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch insights');
        
        const data = await response.json();
        
        renderInsights(data.insights);
    } catch (error) {
        console.error('Error loading insights:', error);
        showError('insights-error', 'Failed to load insights');
    }
}

function renderInsights(insights) {
    const container = document.getElementById('insights-content');
    if (!container) return;
    
    container.innerHTML = insights.map(insight => `
        <div class="insight-item mb-3 p-3 border-start border-4 border-${getInsightColor(insight.type)}">
            <div class="d-flex align-items-start">
                <div class="insight-icon me-3 mt-1">
                    <i class="fas fa-${getInsightIcon(insight.type)} text-${getInsightColor(insight.type)}"></i>
                </div>
                <div class="insight-content flex-grow-1">
                    <h6 class="insight-title fw-bold mb-1">${insight.title}</h6>
                    <p class="insight-description text-muted mb-2">${insight.description}</p>
                    <div class="insight-actions">
                        <span class="badge bg-${getInsightColor(insight.type)} me-2">
                            ${Math.round(insight.confidence * 100)}% confidence
                        </span>
                        <small class="text-muted">${insight.action}</small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function getInsightIcon(type) {
    switch (type) {
        case 'recommendation': return 'lightbulb';
        case 'trend': return 'chart-line';
        case 'alert': return 'exclamation-triangle';
        case 'opportunity': return 'star';
        default: return 'info-circle';
    }
}

function getInsightColor(type) {
    switch (type) {
        case 'recommendation': return 'info';
        case 'trend': return 'success';
        case 'alert': return 'warning';
        case 'opportunity': return 'primary';
        default: return 'secondary';
    }
}

// Control functions
function updateAnalytics() {
    const timeframe = document.getElementById('time-range').value;
    loadAnalyticsData(timeframe);
}

function updateDiscoveryChart() {
    // This would update the discovery chart with different metrics
    const metric = document.getElementById('discovery-metric').value;
    console.log('Updating discovery chart with metric:', metric);
    
    // Re-render the discovery chart with new metric
    loadAnalyticsData(currentTimeframe);
}

async function exportAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/export/analytics`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timeframe: currentTimeframe,
                format: 'json'
            })
        });
        
        if (!response.ok) throw new Error('Failed to export analytics');
        
        const data = await response.json();
        
        // Create download link
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_${currentTimeframe}_days_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('Analytics data exported successfully', 'success');
        
    } catch (error) {
        console.error('Error exporting analytics:', error);
        showAlert('Failed to export analytics data', 'danger');
    }
}

function refreshInsights() {
    loadInsights(currentTimeframe);
    showAlert('Insights refreshed', 'success');
}

// Chart update functions for different timeframes
function updatePerformanceChart() {
    const timeframe = document.getElementById('performance-timeframe').value;
    // This would update the performance chart based on selected timeframe
    console.log('Updating performance chart for timeframe:', timeframe);
}

// Alert notification function
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertContainer.style.zIndex = '9999';
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.parentNode.removeChild(alertContainer);
        }
    }, 5000);
}

// Real-time updates integration
function setupRealtimeUpdates() {
    // Listen for real-time updates via WebSocket
    if (typeof wsClient !== 'undefined') {
        wsClient.onMessage = (data) => {
            if (data.type === 'analytics_update') {
                loadAnalyticsData(currentTimeframe);
            }
        };
    }
}

// Performance monitoring
function monitorChartPerformance() {
    const startTime = performance.now();
    
    // Monitor chart rendering performance
    setTimeout(() => {
        const endTime = performance.now();
        const renderTime = endTime - startTime;
        
        if (renderTime > 1000) {
            console.warn('Chart rendering took longer than expected:', renderTime + 'ms');
        }
    }, 0);
}

// Initialize analytics dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    const timeRangeSelect = document.getElementById('time-range');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', updateAnalytics);
    }
    
    const discoveryMetricSelect = document.getElementById('discovery-metric');
    if (discoveryMetricSelect) {
        discoveryMetricSelect.addEventListener('change', updateDiscoveryChart);
    }
    
    // Load initial data
    loadAnalyticsData('30');
    
    // Set up real-time updates
    setupRealtimeUpdates();
    
    // Monitor performance
    monitorChartPerformance();
    
    console.log('Analytics dashboard initialized');
});

// Export for use in other scripts
window.AnalyticsDashboard = {
    loadAnalyticsData,
    updateAnalytics,
    exportAnalytics,
    refreshInsights
};