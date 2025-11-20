/**
 * Enhanced Dashboard JavaScript
 * Modern, interactive functionality for the MAFA dashboard
 */

class EnhancedDashboard {
    constructor() {
        this.isLoading = false;
        this.autoRefreshInterval = null;
        this.performanceChart = null;
        this.lastUpdate = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.startAutoRefresh();
        this.initializeCharts();
        this.initializeRealTimeUpdates();
        this.updateWelcomeMessage();
    }

    setupEventListeners() {
        // Performance timeframe selector
        const timeframeSelector = document.getElementById('performance-timeframe');
        if (timeframeSelector) {
            timeframeSelector.addEventListener('change', () => this.updatePerformanceChart());
        }

        // Auto-refresh toggle
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }

        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });
    }

    async loadDashboardData() {
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.loadDashboardStats(),
                this.loadRecentActivity(),
                this.loadTopSources(),
                this.loadSystemStatus()
            ]);
            
            this.lastUpdate = new Date();
            this.updateLastUpdatedDisplay();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/v1/dashboard/stats');
            if (!response.ok) throw new Error('Failed to fetch dashboard stats');
            
            const stats = await response.json();
            
            // Update status cards
            this.updateStatusCard('active-searches', stats.active_searches || 0);
            this.updateStatusCard('new-contacts', stats.new_contacts_today || 0);
            this.updateStatusCard('pending-review', stats.pending_review || 0);
            this.updateStatusCard('success-rate', `${stats.success_rate || 0}%`);
            
            // Update trends
            this.updateTrend('searches-trend', stats.searches_trend);
            this.updateTrend('contacts-trend', stats.contacts_trend);
            this.updateTrend('pending-trend', stats.pending_trend);
            this.updateTrend('success-trend', stats.success_trend);
            
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
            this.setDefaultStats();
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/api/v1/dashboard/activity?limit=10');
            if (!response.ok) throw new Error('Failed to fetch activity');
            
            const activities = await response.json();
            this.renderActivityFeed(activities);
            
        } catch (error) {
            console.error('Error loading activity:', error);
            this.renderDefaultActivity();
        }
    }

    async loadTopSources() {
        try {
            const response = await fetch('/api/v1/dashboard/sources?limit=5');
            if (!response.ok) throw new Error('Failed to fetch sources');
            
            const sources = await response.json();
            this.renderTopSources(sources);
            
        } catch (error) {
            console.error('Error loading sources:', error);
            this.renderDefaultSources();
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/v1/system/status');
            if (!response.ok) throw new Error('Failed to fetch system status');
            
            const status = await response.json();
            this.updateSystemStatus(status);
            
        } catch (error) {
            console.error('Error loading system status:', error);
            this.setDefaultSystemStatus();
        }
    }

    updateStatusCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            // Animate number change
            this.animateNumber(element, parseInt(element.textContent) || 0, value);
        }
    }

    animateNumber(element, start, end) {
        const duration = 1000;
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * easeOutCubic);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }

    updateTrend(elementId, trend) {
        const element = document.getElementById(elementId);
        if (element && trend) {
            const icon = trend.direction === 'up' ? 'fa-arrow-up' : 
                        trend.direction === 'down' ? 'fa-arrow-down' : 'fa-minus';
            const colorClass = trend.direction === 'up' ? 'text-success' : 
                              trend.direction === 'down' ? 'text-danger' : 'text-muted';
            
            element.innerHTML = `<i class="fas ${icon}"></i> ${trend.text}`;
            element.className = `status-trend ${colorClass}`;
        }
    }

    renderActivityFeed(activities) {
        const container = document.getElementById('activity-feed');
        if (!container) return;
        
        if (activities.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-3"></i>
                    <p>No recent activity</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon bg-${activity.icon_color || 'primary'}">
                    <i class="fas ${activity.icon} text-white"></i>
                </div>
                <div class="activity-content">
                    <h6 class="activity-title">${activity.title}</h6>
                    <p class="activity-description">${activity.description}</p>
                    <small class="activity-time">${this.formatRelativeTime(activity.timestamp)}</small>
                </div>
            </div>
        `).join('');
    }

    renderTopSources(sources) {
        const container = document.getElementById('top-sources');
        if (!container) return;
        
        if (sources.length === 0) {
            container.innerHTML = `
                <p class="text-muted text-center py-3">No data available</p>
            `;
            return;
        }
        
        container.innerHTML = sources.map(source => `
            <div class="source-item">
                <div class="source-info">
                    <p class="source-name">${source.name}</p>
                    <small class="source-stats">${source.contacts_found} contacts • ${source.success_rate}% success</small>
                </div>
                <div class="source-score">
                    <i class="fas fa-star text-warning"></i> ${source.score}
                </div>
            </div>
        `).join('');
    }

    updateSystemStatus(status) {
        const statusMap = {
            'scraper': { element: 'scraper-status', text: status.scraper || 'Unknown', class: this.getStatusClass(status.scraper_state) },
            'discovery': { element: 'discovery-status', text: status.discovery || 'Unknown', class: this.getStatusClass(status.discovery_state) },
            'notification': { element: 'notification-status', text: status.notification || 'Unknown', class: this.getStatusClass(status.notification_state) },
            'database': { element: 'database-status', text: status.database || 'Unknown', class: this.getStatusClass(status.database_state) }
        };
        
        Object.values(statusMap).forEach(({ element, text, class: className }) => {
            const statusElement = document.getElementById(element);
            if (statusElement) {
                statusElement.textContent = text;
                statusElement.className = `status-text ${className}`;
            }
        });
    }

    getStatusClass(state) {
        switch (state) {
            case 'active':
            case 'running':
            case 'connected':
                return 'text-success';
            case 'warning':
            case 'syncing':
                return 'text-warning';
            case 'error':
            case 'failed':
                return 'text-danger';
            default:
                return 'text-muted';
        }
    }

    initializeCharts() {
        this.setupPerformanceChart();
    }

    setupPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx || typeof Chart === 'undefined') return;
        
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Contacts Found',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Success Rate',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        position: 'left'
                    },
                    y1: {
                        beginAtZero: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        
        this.updatePerformanceChart();
    }

    async updatePerformanceChart() {
        const timeframe = document.getElementById('performance-timeframe')?.value || 7;
        
        try {
            const response = await fetch(`/api/v1/dashboard/performance?days=${timeframe}`);
            if (!response.ok) throw new Error('Failed to fetch performance data');
            
            const data = await response.json();
            
            if (this.performanceChart) {
                this.performanceChart.data.labels = data.labels;
                this.performanceChart.data.datasets[0].data = data.contacts;
                this.performanceChart.data.datasets[1].data = data.success_rates;
                this.performanceChart.update('active');
            }
            
        } catch (error) {
            console.error('Error updating performance chart:', error);
            this.setDefaultChartData();
        }
    }

    initializeRealTimeUpdates() {
        if (typeof WebSocketClient !== 'undefined') {
            // Set up WebSocket handlers for real-time updates
            if (window.realtimeDashboard) {
                window.realtimeDashboard.onMessage = (data) => {
                    this.handleRealtimeUpdate(data);
                };
            }
        }
    }

    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'new_contacts':
                this.updateStatusCard('new-contacts', data.count);
                this.loadRecentActivity(); // Refresh activity feed
                this.showNotification(`${data.count} new contacts found!`, 'success');
                break;
                
            case 'search_complete':
                this.loadDashboardStats();
                this.showNotification('Search completed', 'info');
                break;
                
            case 'system_status_change':
                this.loadSystemStatus();
                break;
                
            case 'contact_approved':
                this.loadDashboardStats();
                this.loadRecentActivity();
                break;
        }
    }

    updateWelcomeMessage() {
        const now = new Date();
        const hour = now.getHours();
        let greeting = 'Welcome back!';
        
        if (hour < 12) {
            greeting = 'Good morning!';
        } else if (hour < 18) {
            greeting = 'Good afternoon!';
        } else {
            greeting = 'Good evening!';
        }
        
        const welcomeElement = document.getElementId('welcome-message');
        if (welcomeElement) {
            welcomeElement.textContent = `${greeting} Here's your apartment search overview.`;
        }
    }

    updateLastUpdatedDisplay() {
        const element = document.getElementById('last-updated');
        if (element && this.lastUpdate) {
            element.textContent = this.lastUpdate.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            if (!this.isLoading && !document.hidden) {
                this.loadDashboardData();
            }
        }, 30000); // Refresh every 30 seconds
    }

    pauseAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    resumeAutoRefresh() {
        if (!this.autoRefreshInterval) {
            this.startAutoRefresh();
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            if (show) {
                overlay.classList.add('active');
            } else {
                overlay.classList.remove('active');
            }
        }
        this.isLoading = show;
    }

    showNotification(message, type = 'info') {
        const container = document.querySelector('.toast-container');
        if (!container) return;
        
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    formatRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }

    setDefaultStats() {
        const defaults = {
            'active-searches': 0,
            'new-contacts': 0,
            'pending-review': 0,
            'success-rate': '0%'
        };
        
        Object.entries(defaults).forEach(([id, value]) => {
            this.updateStatusCard(id, value);
        });
    }

    setDefaultChartData() {
        if (this.performanceChart) {
            this.performanceChart.data.labels = [];
            this.performanceChart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            this.performanceChart.update();
        }
    }

    renderDefaultActivity() {
        const container = document.getElementById('activity-feed');
        if (container) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-3"></i>
                    <p>No activity data available</p>
                </div>
            `;
        }
    }

    renderDefaultSources() {
        const container = document.getElementById('top-sources');
        if (container) {
            container.innerHTML = `
                <p class="text-muted text-center py-3">No sources data available</p>
            `;
        }
    }

    setDefaultSystemStatus() {
        const defaults = [
            { id: 'scraper-status', text: 'Unknown', class: 'text-muted' },
            { id: 'discovery-status', text: 'Unknown', class: 'text-muted' },
            { id: 'notification-status', text: 'Unknown', class: 'text-muted' },
            { id: 'database-status', text: 'Unknown', class: 'text-muted' }
        ];
        
        defaults.forEach(({ id, text, class: className }) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = text;
                element.className = `status-text ${className}`;
            }
        });
    }

    // Public API methods for external calls
    refreshDashboard() {
        this.loadDashboardData();
        this.updatePerformanceChart();
        this.showNotification('Dashboard refreshed', 'success');
    }
}

// Global functions for HTML onclick handlers
function refreshDashboard() {
    if (window.enhancedDashboard) {
        window.enhancedDashboard.refreshDashboard();
    }
}

function startNewSearch() {
    window.location.href = '/dashboard/search/new';
}

function reviewContacts() {
    window.location.href = '/dashboard/contacts?filter=pending';
}

function exportData() {
    window.location.href = '/dashboard/contacts/export';
}

function openSettings() {
    window.location.href = '/dashboard/settings';
}

function viewAllActivity() {
    window.location.href = '/dashboard/activity';
}

function updatePerformanceChart() {
    if (window.enhancedDashboard) {
        window.enhancedDashboard.updatePerformanceChart();
    }
}

function showQuickSetup() {
    window.location.href = '/dashboard/setup';
}

// Initialize enhanced dashboard when DOM is loaded
let enhancedDashboard;

document.addEventListener('DOMContentLoaded', function() {
    enhancedDashboard = new EnhancedDashboard();
    window.enhancedDashboard = enhancedDashboard;
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (enhancedDashboard) {
        enhancedDashboard.pauseAutoRefresh();
    }
});