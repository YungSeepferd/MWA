/**
 * MWA Core Dashboard Real-Time Features
 * 
 * This file enhances the dashboard with WebSocket-based real-time functionality:
 * - Real-time dashboard statistics
 * - Live scraper status monitoring
 * - System status updates
 * - WebSocket connection management
 * - Real-time notifications
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.isConnecting = false;
        this.connectionStatus = 'disconnected';
        
        // WebSocket event handlers
        this.onOpen = null;
        this.onClose = null;
        this.onMessage = null;
        this.onError = null;
        
        // Auto-connect on initialization
        this.connect();
    }
    
    connect(token = null) {
        if (this.isConnecting || this.ws?.readyState === WebSocket.CONNECTING) {
            return;
        }
        
        this.isConnecting = true;
        this.connectionStatus = 'connecting';
        this.updateConnectionStatus();
        
        try {
            // Build WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const baseUrl = `${protocol}//${host}/api/v1/websocket/connect`;
            
            const url = token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl;
            
            this.ws = new WebSocket(url);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.connectionStatus = 'connected';
                this.reconnectAttempts = 0;
                this.updateConnectionStatus();
                this.startHeartbeat();
                
                if (this.onOpen) this.onOpen(event);
                
                // Join dashboard room for real-time updates
                this.sendMessage({
                    type: 'join_room',
                    data: { room: 'dashboard' }
                });
                
                // Join scraper room for scraper updates
                this.sendMessage({
                    type: 'join_room', 
                    data: { room: 'scraper' }
                });
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    
                    if (this.onMessage) this.onMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.isConnecting = false;
                this.connectionStatus = 'disconnected';
                this.updateConnectionStatus();
                this.stopHeartbeat();
                
                if (this.onClose) this.onClose(event);
                
                // Attempt to reconnect unless it was a clean close
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                        this.connect(token);
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.connectionStatus = 'error';
                this.updateConnectionStatus();
                
                if (this.onError) this.onError(error);
            };
            
        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
            this.isConnecting = false;
            this.connectionStatus = 'error';
            this.updateConnectionStatus();
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Manual disconnect');
            this.ws = null;
        }
        this.stopHeartbeat();
        this.connectionStatus = 'disconnected';
        this.updateConnectionStatus();
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('WebSocket is not connected');
            return false;
        }
    }
    
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            this.sendMessage({
                type: 'heartbeat',
                data: { timestamp: new Date().toISOString() }
            });
        }, 30000); // Send heartbeat every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    updateConnectionStatus() {
        const statusElement = document.getElementById('websocket-status');
        if (statusElement) {
            const statusMap = {
                'connected': { class: 'bg-success', text: 'Connected' },
                'connecting': { class: 'bg-warning', text: 'Connecting...' },
                'disconnected': { class: 'bg-secondary', text: 'Disconnected' },
                'error': { class: 'bg-danger', text: 'Error' }
            };
            
            const status = statusMap[this.connectionStatus] || statusMap['disconnected'];
            statusElement.className = `badge ${status.class}`;
            statusElement.textContent = status.text;
        }
    }
}

// Global WebSocket client instance
let wsClient = null;

// Real-time dashboard functionality
class RealtimeDashboard {
    constructor() {
        this.statsUpdateInterval = null;
        this.lastStatsUpdate = null;
        this.isAutoRefreshEnabled = true;
        this.scraperStatus = null;
        this.systemStatus = null;
        
        // Initialize WebSocket client
        this.initializeWebSocket();
        
        // Set up periodic stats updates
        this.startPeriodicUpdates();
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }
    
    initializeWebSocket() {
        // Get authentication token if available
        const token = this.getAuthToken();
        
        wsClient = new WebSocketClient();
        
        // Set up WebSocket event handlers
        wsClient.onOpen = () => {
            console.log('Real-time dashboard WebSocket connected');
            this.showNotification('Connected to real-time updates', 'success');
            this.resumeUpdates();
        };
        
        wsClient.onMessage = (data) => {
            this.handleWebSocketMessage(data);
        };
        
        wsClient.onClose = () => {
            console.log('Real-time dashboard WebSocket disconnected');
            this.showNotification('Disconnected from real-time updates', 'warning');
            this.pauseUpdates();
        };
        
        wsClient.onError = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('WebSocket connection error', 'danger');
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'dashboard_update':
                this.handleDashboardUpdate(data.data);
                break;
            case 'system_status':
                this.handleSystemStatus(data.data);
                break;
            case 'scraper_update':
                this.handleScraperUpdate(data.data);
                break;
            case 'contact_discovery':
                this.handleContactDiscovery(data.data);
                break;
            case 'heartbeat':
                // Handle heartbeat response
                break;
            case 'notification':
                this.handleNotification(data.data);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    handleDashboardUpdate(data) {
        console.log('Dashboard update received:', data);
        
        if (data.action === 'refresh_stats') {
            this.loadDashboardStats();
        } else if (data.stats) {
            this.updateStats(data.stats);
        }
    }
    
    handleSystemStatus(data) {
        console.log('System status update:', data);
        this.systemStatus = data;
        this.updateSystemStatusDisplay(data);
    }
    
    handleScraperUpdate(data) {
        console.log('Scraper update:', data);
        this.scraperStatus = data;
        this.updateScraperStatusDisplay(data);
    }
    
    handleContactDiscovery(data) {
        console.log('Contact discovery update:', data);
        this.showNotification(`New contacts discovered: ${data.count || 0}`, 'info');
        this.loadDashboardStats(); // Refresh stats
        this.loadRecentContacts(); // Refresh recent contacts
    }
    
    handleNotification(data) {
        console.log('Notification received:', data);
        this.showNotification(data.message, data.type || 'info');
    }
    
    updateStats(stats) {
        // Update total contacts
        const totalContactsElement = document.getElementById('total-contacts');
        if (totalContactsElement) {
            totalContactsElement.textContent = stats.total_contacts || 0;
        }
        
        // Update status-specific counts
        if (stats.contacts_by_status) {
            Object.keys(stats.contacts_by_status).forEach(status => {
                const element = document.getElementById(`${status}-contacts`);
                if (element) {
                    element.textContent = stats.contacts_by_status[status] || 0;
                }
            });
        }
        
        // Update top sources
        if (stats.top_sources) {
            this.updateTopSources(stats.top_sources);
        }
        
        // Update last updated time
        this.updateLastUpdated();
    }
    
    updateSystemStatusDisplay(data) {
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            const statusClass = data.healthy ? 'bg-success' : 'bg-danger';
            statusElement.className = `badge ${statusClass}`;
            statusElement.textContent = data.healthy ? 'Healthy' : 'Issues Detected';
        }
        
        // Update system metrics
        if (data.metrics) {
            this.updateSystemMetrics(data.metrics);
        }
    }
    
    updateScraperStatusDisplay(data) {
        const statusElement = document.getElementById('scraper-status');
        if (statusElement) {
            const statusMap = {
                'running': 'bg-success',
                'stopped': 'bg-secondary',
                'error': 'bg-danger',
                'paused': 'bg-warning'
            };
            
            const statusClass = statusMap[data.status] || 'bg-secondary';
            statusElement.className = `badge ${statusClass}`;
            statusElement.textContent = data.status || 'unknown';
        }
        
        // Update scraper details
        if (data.current_job) {
            this.updateCurrentJobDisplay(data.current_job);
        }
    }
    
    updateSystemMetrics(metrics) {
        // Update CPU usage
        const cpuElement = document.getElementById('cpu-usage');
        if (cpuElement && metrics.cpu_usage !== undefined) {
            cpuElement.textContent = `${metrics.cpu_usage.toFixed(1)}%`;
            
            // Color coding
            const cpuProgress = cpuElement.parentElement.querySelector('.progress-bar');
            if (cpuProgress) {
                let colorClass = 'bg-success';
                if (metrics.cpu_usage > 80) colorClass = 'bg-danger';
                else if (metrics.cpu_usage > 60) colorClass = 'bg-warning';
                
                cpuProgress.className = `progress-bar ${colorClass}`;
                cpuProgress.style.width = `${metrics.cpu_usage}%`;
            }
        }
        
        // Update memory usage
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement && metrics.memory_usage !== undefined) {
            memoryElement.textContent = `${metrics.memory_usage.toFixed(1)}%`;
            
            // Color coding
            const memoryProgress = memoryElement.parentElement.querySelector('.progress-bar');
            if (memoryProgress) {
                let colorClass = 'bg-success';
                if (metrics.memory_usage > 85) colorClass = 'bg-danger';
                else if (metrics.memory_usage > 70) colorClass = 'bg-warning';
                
                memoryProgress.className = `progress-bar ${colorClass}`;
                memoryProgress.style.width = `${metrics.memory_usage}%`;
            }
        }
        
        // Update active connections
        const connectionsElement = document.getElementById('active-connections');
        if (connectionsElement && metrics.active_connections !== undefined) {
            connectionsElement.textContent = metrics.active_connections;
        }
    }
    
    updateCurrentJobDisplay(jobData) {
        const jobElement = document.getElementById('current-scraper-job');
        if (jobElement) {
            // Sanitize user input to prevent XSS
            const provider = this.escapeHtml(jobData.provider || 'Unknown');
            const status = this.escapeHtml(jobData.status || 'Unknown status');
            const progress = jobData.progress ? this.escapeHtml(jobData.progress.toString()) : null;
            
            jobElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${provider}</strong>
                        <br>
                        <small class="text-muted">${status}</small>
                    </div>
                    <div class="text-end">
                        ${progress ? `
                            <div class="progress" style="width: 100px; height: 6px;">
                                <div class="progress-bar" style="width: ${progress}%"></div>
                            </div>
                            <small class="text-muted">${progress}%</small>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    }
    
    updateTopSources(sources) {
        const topSourcesList = document.getElementById('top-sources-list');
        if (topSourcesList) {
            topSourcesList.innerHTML = sources.slice(0, 5).map(source => {
                // Sanitize user input to prevent XSS
                const sourceName = this.escapeHtml(source.source);
                const count = this.escapeHtml(source.count.toString());
                return `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-truncate" style="max-width: 200px;" title="${sourceName}">
                            ${sourceName}
                        </span>
                        <span class="badge bg-primary">${count}</span>
                    </div>
                `;
            }).join('');
        }
    }
    
    startPeriodicUpdates() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }
        
        // Update stats every 30 seconds when tab is visible
        this.statsUpdateInterval = setInterval(() => {
            if (this.isAutoRefreshEnabled && !document.hidden) {
                this.loadDashboardStats();
            }
        }, 30000);
    }
    
    pauseUpdates() {
        this.isAutoRefreshEnabled = false;
    }
    
    resumeUpdates() {
        this.isAutoRefreshEnabled = true;
        // Immediately update stats when resuming
        this.loadDashboardStats();
    }
    
    getAuthToken() {
        // Try to get token from localStorage or other sources
        return localStorage.getItem('access_token') || null;
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        // Sanitize message to prevent XSS
        const sanitizedMessage = this.escapeHtml(message);
        
        notification.innerHTML = `
            ${sanitizedMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-dismiss
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    // Enhanced API calls with real-time updates
    async loadDashboardStats() {
        try {
            const response = await fetch('/api/v1/system/metrics');
            if (!response.ok) throw new Error('Failed to fetch stats');
            
            const stats = await response.json();
            this.updateStats(stats);
            this.lastStatsUpdate = new Date();
            
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }
    
    async loadRecentContacts() {
        try {
            const response = await fetch('/api/v1/contacts?limit=10&offset=0');
            if (!response.ok) throw new Error('Failed to fetch recent contacts');
            
            const contacts = await response.json();
            this.updateRecentContactsDisplay(contacts);
            
        } catch (error) {
            console.error('Error loading recent contacts:', error);
        }
    }
    
    updateRecentContactsDisplay(contacts) {
        const recentContactsBody = document.getElementById('recent-contacts-body');
        if (recentContactsBody) {
            recentContactsBody.innerHTML = contacts.map(contact => {
                // Sanitize all user input to prevent XSS
                const source = this.escapeHtml(contact.source);
                const method = this.escapeHtml(contact.method);
                const value = this.escapeHtml(contact.value);
                const confidence = this.escapeHtml(contact.confidence);
                const status = this.escapeHtml(contact.status);
                const id = this.escapeHtml(contact.id.toString());
                
                return `
                    <tr>
                        <td>
                            <span class="text-truncate" style="max-width: 200px;" title="${source}">
                                ${source}
                            </span>
                        </td>
                        <td>
                            <i class="fas fa-${contact.method === 'email' ? 'envelope' : contact.method === 'phone' ? 'phone' : 'file-alt'}"></i>
                            ${method}
                        </td>
                        <td>
                            <span class="text-truncate" style="max-width: 200px;" title="${value}">
                                ${value}
                            </span>
                        </td>
                        <td>
                            <span class="badge bg-${contact.confidence === 'high' ? 'success' : contact.confidence === 'medium' ? 'warning' : 'danger'}">
                                ${confidence}
                            </span>
                        </td>
                        <td>
                            <span class="badge bg-${contact.status === 'approved' ? 'success' : contact.status === 'rejected' ? 'danger' : 'warning'}">
                                ${status}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewContactDetails(${id})">
                                <i class="fas fa-eye"></i> View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }
    
    // Control functions
    toggleAutoRefresh() {
        this.isAutoRefreshEnabled = !this.isAutoRefreshEnabled;
        const toggleElement = document.getElementById('auto-refresh-toggle');
        if (toggleElement) {
            toggleElement.innerHTML = this.isAutoRefreshEnabled ? 
                '<i class="fas fa-pause"></i> Pause Auto-Refresh' : 
                '<i class="fas fa-play"></i> Resume Auto-Refresh';
        }
        
        this.showNotification(
            this.isAutoRefreshEnabled ? 'Auto-refresh enabled' : 'Auto-refresh disabled',
            'info'
        );
    }
    
    requestManualUpdate() {
        // Send WebSocket message to request server-side update
        if (wsClient) {
            wsClient.sendMessage({
                type: 'dashboard_update',
                data: { action: 'refresh_all' }
            });
        }
        
        // Also update locally
        this.loadDashboardStats();
        this.loadRecentContacts();
        
        this.showNotification('Manual update requested', 'success');
    }

    /**
     * Escape HTML special characters to prevent XSS attacks
     */
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return text;
        }
        
        const map = {
            '&': '&',
            '<': '<',
            '>': '>',
            '"': '"',
            "'": '&#x27;',
            '/': '&#x2F;'
        };
        
        return text.replace(/[&<>"'/]/g, (char) => map[char]);
    }
}

// Real-time monitoring functions
class SystemMonitor {
    constructor() {
        this.performanceData = [];
        this.maxDataPoints = 50;
        this.chart = null;
        
        this.initializeMonitoring();
    }
    
    initializeMonitoring() {
        // Initialize performance monitoring
        this.startPerformanceMonitoring();
        
        // Set up real-time charts if Chart.js is available
        this.initializeCharts();
    }
    
    startPerformanceMonitoring() {
        setInterval(() => {
            this.collectPerformanceData();
        }, 5000); // Collect data every 5 seconds
    }
    
    async collectPerformanceData() {
        try {
            const response = await fetch('/api/v1/system/performance');
            if (response.ok) {
                const data = await response.json();
                this.performanceData.push({
                    timestamp: new Date(),
                    cpu: data.cpu_usage || 0,
                    memory: data.memory_usage || 0,
                    requests: data.request_rate || 0
                });
                
                // Keep only recent data
                if (this.performanceData.length > this.maxDataPoints) {
                    this.performanceData = this.performanceData.slice(-this.maxDataPoints);
                }
                
                this.updatePerformanceDisplay();
            }
        } catch (error) {
            console.error('Error collecting performance data:', error);
        }
    }
    
    updatePerformanceDisplay() {
        // Update CPU usage display
        const cpuElement = document.getElementById('cpu-usage');
        if (cpuElement && this.performanceData.length > 0) {
            const latest = this.performanceData[this.performanceData.length - 1];
            cpuElement.textContent = `${latest.cpu.toFixed(1)}%`;
        }
        
        // Update memory usage display
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement && this.performanceData.length > 0) {
            const latest = this.performanceData[this.performanceData.length - 1];
            memoryElement.textContent = `${latest.memory.toFixed(1)}%`;
        }
    }
    
    initializeCharts() {
        // This would initialize Chart.js charts if available
        // For now, we'll just prepare the data structure
        if (typeof Chart !== 'undefined') {
            this.setupPerformanceChart();
        }
    }
    
    setupPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (ctx) {
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }, {
                        label: 'Memory Usage (%)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    }
}

// Initialize real-time dashboard when DOM is loaded
let realtimeDashboard = null;
let systemMonitor = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize real-time dashboard
    realtimeDashboard = new RealtimeDashboard();
    
    // Initialize system monitor
    systemMonitor = new SystemMonitor();
    
    // Set up control buttons
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('click', () => {
            realtimeDashboard.toggleAutoRefresh();
        });
    }
    
    const manualUpdateButton = document.getElementById('manual-update-button');
    if (manualUpdateButton) {
        manualUpdateButton.addEventListener('click', () => {
            realtimeDashboard.requestManualUpdate();
        });
    }
    
    // Add WebSocket status indicator to the page
    addWebSocketStatusIndicator();
    
    console.log('Real-time dashboard initialized');
});

function addWebSocketStatusIndicator() {
    // Add connection status indicator to the navigation or header
    const nav = document.querySelector('.navbar-nav.ms-auto');
    if (nav) {
        const statusLi = document.createElement('li');
        statusLi.className = 'nav-item me-3';
        
        // Use textContent instead of innerHTML for static content
        const statusSpan = document.createElement('span');
        statusSpan.className = 'navbar-text';
        statusSpan.innerHTML = `
            <i class="fas fa-wifi"></i>
            <span id="websocket-status" class="badge bg-secondary">Disconnected</span>
        `;
        statusLi.appendChild(statusSpan);
        nav.insertBefore(statusLi, nav.firstChild);
    }
}

// Export for use in other scripts
window.WebSocketClient = WebSocketClient;
window.RealtimeDashboard = RealtimeDashboard;
window.SystemMonitor = SystemMonitor;