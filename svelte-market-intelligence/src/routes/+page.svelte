<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import MobileNav from '../components/layout/MobileNav.svelte';
  import LoadingSkeleton from '../components/ui/LoadingSkeleton.svelte';
  import LineChart from '../components/visualization/LineChart.svelte';
  import { realTimeService, contactUpdates, systemStatus } from '$lib/services/websocket';
  
  // Get data from load function
  export let data;
  
  let isLoading = true;
  let wsConnected = false;
  let recentActivity = [];
  let systemStatusData = {
    scraper: { status: 'Unknown', state: 'unknown' },
    discovery: { status: 'Unknown', state: 'unknown' },
    notification: { status: 'Unknown', state: 'unknown' },
    database: { status: 'Unknown', state: 'unknown' }
  };
  let topSources = [];
  let performanceData = [];
  let lastUpdated = new Date();
  let autoRefreshInterval: NodeJS.Timeout | null = null;
  
  // Performance chart data
  let performanceChartData = {
    labels: [] as string[],
    contacts: [] as number[],
    successRates: [] as number[]
  };
  
  // Dashboard statistics
  let dashboardStats = {
    activeSearches: 0,
    newContacts: 0,
    pendingReview: 0,
    successRate: 0,
    trends: {
      searches: { direction: 'neutral', text: '0 changes' },
      contacts: { direction: 'neutral', text: '0 today' },
      pending: { direction: 'neutral', text: '0 changes' },
      success: { direction: 'neutral', text: '0% this month' }
    }
  };
  
  onMount(() => {
    initializeDashboard();
    startAutoRefresh();
    
    // Subscribe to WebSocket updates
    const unsubscribeActivity = contactUpdates.subscribe(updates => {
      recentActivity = updates.slice(0, 10);
    });
    
    const unsubscribeConnected = realTimeService.subscribe(connected => {
      wsConnected = connected;
    });
    
    const unsubscribeStatus = systemStatus.subscribe(status => {
      systemStatusData = status;
    });
    
    return () => {
      unsubscribeActivity();
      unsubscribeConnected();
      unsubscribeStatus();
      stopAutoRefresh();
    };
  });
  
  onDestroy(() => {
    stopAutoRefresh();
  });
  
  async function initializeDashboard() {
    try {
      await Promise.all([
        loadDashboardStats(),
        loadRecentActivity(),
        loadTopSources(),
        loadSystemStatus(),
        loadPerformanceData()
      ]);
      
      lastUpdated = new Date();
      isLoading = false;
    } catch (error) {
      console.error('Error initializing dashboard:', error);
      isLoading = false;
    }
  }
  
  async function loadDashboardStats() {
    try {
      // Simulate API call - replace with actual API
      dashboardStats = {
        activeSearches: data?.stats?.active_searches || 5,
        newContacts: data?.stats?.new_contacts_today || 12,
        pendingReview: data?.stats?.pending_review || 8,
        successRate: data?.stats?.success_rate || 75,
        trends: {
          searches: { direction: 'up', text: '+2 this week' },
          contacts: { direction: 'up', text: '+5 today' },
          pending: { direction: 'neutral', text: '0 changes' },
          success: { direction: 'up', text: '+5% this month' }
        }
      };
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  }
  
  async function loadRecentActivity() {
    try {
      // Use WebSocket data or fallback to mock data
      if (recentActivity.length === 0) {
        recentActivity = [
          {
            type: 'contact_created',
            title: 'New Contact Added',
            description: 'Max Mustermann - Property Manager',
            timestamp: new Date(Date.now() - 300000),
            icon: 'user-plus',
            icon_color: 'success'
          },
          {
            type: 'search_complete',
            title: 'Search Completed',
            description: 'Munchen Center Area',
            timestamp: new Date(Date.now() - 600000),
            icon: 'search',
            icon_color: 'primary'
          },
          {
            type: 'contact_approved',
            title: 'Contact Approved',
            description: 'Anna Schmidt - Real Estate Agent',
            timestamp: new Date(Date.now() - 900000),
            icon: 'check-circle',
            icon_color: 'success'
          }
        ];
      }
    } catch (error) {
      console.error('Error loading recent activity:', error);
    }
  }
  
  async function loadTopSources() {
    try {
      topSources = [
        { name: 'ImmobilienScout24', contacts_found: 45, success_rate: 82, score: 4.8 },
        { name: 'WG-Gesucht', contacts_found: 32, success_rate: 75, score: 4.5 },
        { name: 'ImmoWelt', contacts_found: 18, success_rate: 68, score: 4.2 },
        { name: 'Ebay Kleinanzeigen', contacts_found: 12, success_rate: 60, score: 3.9 }
      ];
    } catch (error) {
      console.error('Error loading top sources:', error);
    }
  }
  
  async function loadSystemStatus() {
    try {
      // Use WebSocket data or fallback to mock data
      systemStatusData = {
        scraper: { status: 'Active', state: 'active' },
        discovery: { status: 'Running', state: 'running' },
        notification: { status: 'Connected', state: 'connected' },
        database: { status: 'Syncing', state: 'syncing' }
      };
    } catch (error) {
      console.error('Error loading system status:', error);
    }
  }
  
  async function loadPerformanceData() {
    try {
      // Generate mock performance data for the chart
      const days = 7;
      const now = new Date();
      
      performanceChartData.labels = Array.from({ length: days }, (_, i) => {
        const date = new Date(now);
        date.setDate(date.getDate() - (days - i - 1));
        return date.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' });
      });
      
      performanceChartData.contacts = Array.from({ length: days }, () => 
        Math.floor(Math.random() * 20) + 5
      );
      
      performanceChartData.successRates = Array.from({ length: days }, () => 
        Math.floor(Math.random() * 30) + 60
      );
    } catch (error) {
      console.error('Error loading performance data:', error);
    }
  }
  
  function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
      if (!isLoading && wsConnected) {
        refreshDashboard();
      }
    }, 30000); // Refresh every 30 seconds
  }
  
  function stopAutoRefresh() {
    if (autoRefreshInterval) {
      clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;
    }
  }
  
  async function refreshDashboard() {
    isLoading = true;
    try {
      await Promise.all([
        loadDashboardStats(),
        loadRecentActivity(),
        loadTopSources(),
        loadSystemStatus(),
        loadPerformanceData()
      ]);
      
      lastUpdated = new Date();
    } catch (error) {
      console.error('Error refreshing dashboard:', error);
    } finally {
      isLoading = false;
    }
  }
  
  function getStatusClass(state: string) {
    switch (state) {
      case 'active':
      case 'running':
      case 'connected':
        return 'text-success-600';
      case 'warning':
      case 'syncing':
        return 'text-warning-600';
      case 'error':
      case 'failed':
        return 'text-error-600';
      default:
        return 'text-gray-500';
    }
  }
  
  function getStatusDotClass(state: string) {
    switch (state) {
      case 'active':
      case 'running':
      case 'connected':
        return 'bg-success-500';
      case 'warning':
      case 'syncing':
        return 'bg-warning-500';
      case 'error':
      case 'failed':
        return 'bg-error-500';
      default:
        return 'bg-gray-400';
    }
  }
  
  function formatRelativeTime(timestamp: Date) {
    const now = new Date();
    const diffMs = now.getTime() - timestamp.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  }
  
  // Quick action handlers
  function startNewSearch() {
    goto('/search/new');
  }
  
  function reviewContacts() {
    goto('/contacts?filter=pending');
  }
  
  function exportData() {
    // Implement export functionality
    console.log('Export data functionality');
  }
  
  function openSettings() {
    goto('/settings');
  }
</script>

<div class="min-h-screen bg-gray-50 pb-20">
  <div class="container mx-auto px-4 py-6">
    <!-- Header with welcome message and refresh -->
    <header class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p class="text-gray-600">Welcome back! Here's your apartment search overview.</p>
        </div>
        <div class="flex items-center gap-3">
          <div class={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span class="status-dot"></span>
            <span class="text-xs">
              {wsConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          <button on:click={refreshDashboard} class="btn btn-secondary" disabled={isLoading}>
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      <p class="text-sm text-gray-500">
        <i class="fas fa-clock me-1"></i>
        Last updated: {lastUpdated.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
      </p>
    </header>

    {#if isLoading}
      <!-- Loading state -->
      <div class="space-y-6">
        <LoadingSkeleton type="card" height="120px" />
        <LoadingSkeleton type="card" height="200px" />
        <LoadingSkeleton type="card" height="150px" />
        <LoadingSkeleton type="card" height="180px" />
      </div>
    {:else}
      <!-- Real-time Status Cards -->
      <div class="grid gap-4 mb-6 md:grid-cols-2 lg:grid-cols-4">
        <!-- Active Searches -->
        <div class="card text-center">
          <div class="text-3xl font-bold text-primary-600 mb-1">
            {dashboardStats.activeSearches}
          </div>
          <div class="text-sm text-gray-600">Active Searches</div>
          <div class="text-xs {dashboardStats.trends.searches.direction === 'up' ? 'text-success-600' : dashboardStats.trends.searches.direction === 'down' ? 'text-error-600' : 'text-gray-500'}">
            {dashboardStats.trends.searches.text}
          </div>
        </div>
        
        <!-- New Contacts -->
        <div class="card text-center">
          <div class="text-3xl font-bold text-success-600 mb-1">
            {dashboardStats.newContacts}
          </div>
          <div class="text-sm text-gray-600">New Contacts</div>
          <div class="text-xs {dashboardStats.trends.contacts.direction === 'up' ? 'text-success-600' : dashboardStats.trends.contacts.direction === 'down' ? 'text-error-600' : 'text-gray-500'}">
            {dashboardStats.trends.contacts.text}
          </div>
        </div>
        
        <!-- Pending Review -->
        <div class="card text-center">
          <div class="text-3xl font-bold text-warning-600 mb-1">
            {dashboardStats.pendingReview}
          </div>
          <div class="text-sm text-gray-600">Pending Review</div>
          <div class="text-xs {dashboardStats.trends.pending.direction === 'up' ? 'text-success-600' : dashboardStats.trends.pending.direction === 'down' ? 'text-error-600' : 'text-gray-500'}">
            {dashboardStats.trends.pending.text}
          </div>
        </div>
        
        <!-- Success Rate -->
        <div class="card text-center">
          <div class="text-3xl font-bold text-info-600 mb-1">
            {dashboardStats.successRate}%
          </div>
          <div class="text-sm text-gray-600">Success Rate</div>
          <div class="text-xs {dashboardStats.trends.success.direction === 'up' ? 'text-success-600' : dashboardStats.trends.success.direction === 'down' ? 'text-error-600' : 'text-gray-500'}">
            {dashboardStats.trends.success.text}
          </div>
        </div>
      </div>

      <!-- Main Dashboard Content -->
      <div class="grid gap-6 lg:grid-cols-3">
        <!-- Left Column - Charts and Activity -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Search Performance Chart -->
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Search Performance</h2>
            {#if performanceChartData.labels.length > 0}
              <LineChart
                data={performanceChartData.labels.map((label, index) => ({
                  label,
                  value: performanceChartData.contacts[index]
                }))}
                title="Contacts Found"
                size="medium"
                showGrid={true}
                showPoints={true}
              />
            {:else}
              <div class="text-center text-gray-500 py-8">
                <p>No performance data available</p>
              </div>
            {/if}
          </div>

          <!-- Recent Activity -->
          <div class="card">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-xl font-semibold">Recent Activity</h2>
              <a href="/activity" class="text-sm text-primary-600 hover:underline">View All</a>
            </div>
            
            {#if recentActivity.length > 0}
              <div class="space-y-3">
                {#each recentActivity as activity}
                  <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div class={`w-8 h-8 rounded-full flex items-center justify-center ${
                      activity.icon_color === 'success' ? 'bg-success-100 text-success-600' :
                      activity.icon_color === 'primary' ? 'bg-primary-100 text-primary-600' :
                      activity.icon_color === 'warning' ? 'bg-warning-100 text-warning-600' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      <i class="fas {activity.icon} text-sm"></i>
                    </div>
                    <div class="flex-1">
                      <div class="text-sm font-medium text-gray-900">{activity.title}</div>
                      <div class="text-xs text-gray-500">{activity.description}</div>
                    </div>
                    <div class="text-xs text-gray-400">
                      {formatRelativeTime(activity.timestamp)}
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-center text-gray-500 py-8">
                <p>No recent activity yet</p>
                <p class="text-sm">Start by adding your first contact</p>
              </div>
            {/if}
          </div>
        </div>

        <!-- Right Column - Quick Actions and Status -->
        <div class="space-y-6">
          <!-- Quick Actions -->
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
            <div class="grid gap-3">
              <button on:click={startNewSearch} class="btn btn-primary w-full text-left">
                <i class="fas fa-search me-2"></i>New Search
              </button>
              <button on:click={reviewContacts} class="btn btn-secondary w-full text-left">
                <i class="fas fa-check-circle me-2"></i>Review Contacts
              </button>
              <button on:click={exportData} class="btn btn-secondary w-full text-left">
                <i class="fas fa-download me-2"></i>Export Data
              </button>
              <button on:click={openSettings} class="btn btn-secondary w-full text-left">
                <i class="fas fa-cog me-2"></i>Settings
              </button>
            </div>
          </div>

          <!-- System Status -->
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">System Status</h2>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-700">Scraper Service</span>
                <span class="text-sm {getStatusClass(systemStatusData.scraper.state)}">
                  {systemStatusData.scraper.status}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-700">Contact Discovery</span>
                <span class="text-sm {getStatusClass(systemStatusData.discovery.state)}">
                  {systemStatusData.discovery.status}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-700">Notifications</span>
                <span class="text-sm {getStatusClass(systemStatusData.notification.state)}">
                  {systemStatusData.notification.status}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-700">Database</span>
                <span class="text-sm {getStatusClass(systemStatusData.database.state)}">
                  {systemStatusData.database.status}
                </span>
              </div>
            </div>
          </div>

          <!-- Top Sources -->
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Top Sources</h2>
            {#if topSources.length > 0}
              <div class="space-y-3">
                {#each topSources as source}
                  <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <p class="text-sm font-medium">{source.name}</p>
                      <p class="text-xs text-gray-500">
                        {source.contacts_found} contacts • {source.success_rate}% success
                      </p>
                    </div>
                    <div class="text-sm font-medium text-warning-600">
                      <i class="fas fa-star"></i> {source.score}
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-center text-gray-500 py-4">
                <p>No sources data available</p>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Mobile Navigation -->
  <MobileNav />
</div>

<style>
  .bg-gray-50 { background: var(--gray-50); }
  .bg-primary-100 { background: var(--primary-100); }
  .bg-success-100 { background: var(--success-100); }
  .bg-warning-100 { background: var(--warning-100); }
  .bg-gray-100 { background: var(--gray-100); }
  
  .text-gray-900 { color: var(--gray-900); }
  .text-gray-600 { color: var(--gray-600); }
  .text-gray-500 { color: var(--gray-500); }
  .text-gray-700 { color: var(--gray-700); }
  .text-primary-600 { color: var(--primary-600); }
  .text-success-600 { color: var(--success-600); }
  .text-warning-600 { color: var(--warning-600); }
  .text-error-600 { color: var(--error-600); }
  .text-info-600 { color: var(--info-600); }
  
  .text-3xl { font-size: var(--font-size-3xl); }
  .text-2xl { font-size: var(--font-size-2xl); }
  .text-xl { font-size: var(--font-size-xl); }
  .text-sm { font-size: var(--font-size-sm); }
  .text-xs { font-size: var(--font-size-xs); }
  
  .font-bold { font-weight: 600; }
  .font-semibold { font-weight: 500; }
  .font-medium { font-weight: 500; }
  
  .mb-1 { margin-bottom: var(--space-1); }
  .mb-2 { margin-bottom: var(--space-2); }
  .mb-4 { margin-bottom: var(--space-4); }
  .mb-6 { margin-bottom: var(--space-6); }
  
  .py-6 { padding-top: var(--space-6); padding-bottom: var(--space-6); }
  .py-4 { padding-top: var(--space-4); padding-bottom: var(--space-4); }
  .py-8 { padding-top: var(--space-8); padding-bottom: var(--space-8); }
  .px-4 { padding-left: var(--space-4); padding-right: var(--space-4); }
  .p-2 { padding: var(--space-2); }
  .p-3 { padding: var(--space-3); }
  .p-4 { padding: var(--space-4); }
  
  .pb-20 { padding-bottom: 5rem; }
  
  .rounded-lg { border-radius: var(--radius-lg); }
  .rounded { border-radius: var(--radius); }
  .rounded-full { border-radius: 9999px; }
  
  .space-y-3 > * + * { margin-top: var(--space-3); }
  .space-y-6 > * + * { margin-top: var(--space-6); }
  .gap-3 { gap: var(--space-3); }
  .gap-4 { gap: var(--space-4); }
  .gap-6 { gap: var(--space-6); }
  
  .flex { display: flex; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .justify-center { justify-content: center; }
  
  .w-full { width: 100%; }
  .w-8 { width: 2rem; }
  .h-8 { height: 2rem; }
  
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  
  .min-h-screen { min-height: 100vh; }
  
  .container {
    width: 100%;
    margin: 0 auto;
    padding: 0 var(--space-4);
  }
  
  .mx-auto { margin-left: auto; margin-right: auto; }
  
  .grid { display: grid; }
  .grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
  .lg\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
  .lg\:col-span-2 { grid-column: span 2; }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .status-indicator.connected {
    background: #dcfce7;
    color: #166534;
  }
  
  .status-indicator.disconnected {
    background: #fef2f2;
    color: #dc2626;
  }
  
  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  
  .status-indicator.connected .status-dot {
    background: #16a34a;
  }
  
  .status-indicator.disconnected .status-dot {
    background: #dc2626;
  }
  
  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  }
  
  @media (min-width: 768px) {
    .md\:grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  }
  
  @media (min-width: 1024px) {
    .lg\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
    .lg\:grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
    .lg\:col-span-2 { grid-column: span 2; }
  }
</style>