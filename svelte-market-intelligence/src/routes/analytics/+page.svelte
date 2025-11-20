<script lang="ts">
  import { onMount } from 'svelte';
  import LoadingSkeleton from '../components/ui/LoadingSkeleton.svelte';
  import MobileNav from '../../components/layout/MobileNav.svelte';
  import PieChart from '../../components/visualization/PieChart.svelte';
  import LineChart from '../../components/visualization/LineChart.svelte';
  import ScoringChart from '../../components/visualization/ScoringChart.svelte';
  
  // Get data from load function
  export let data;
  
  let isLoading = true;
  let currentTimeframe = '30';
  let searchAnalytics = null;
  let insights = [];
  
  onMount(async () => {
    // Load search analytics data
    await loadSearchAnalytics();
    
    // Simulate loading for charts
    setTimeout(() => {
      isLoading = false;
    }, 1000);
  });
  
  async function loadSearchAnalytics() {
    try {
      const response = await fetch(`/api/v1/system/analytics/data?timeframe=${currentTimeframe}`);
      if (response.ok) {
        searchAnalytics = await response.json();
        await loadInsights();
      }
    } catch (error) {
      console.error('Error loading search analytics:', error);
    }
  }
  
  async function loadInsights() {
    try {
      const response = await fetch(`/api/v1/system/analytics/insights?timeframe=${currentTimeframe}`);
      if (response.ok) {
        const data = await response.json();
        insights = data.insights || [];
      }
    } catch (error) {
      console.error('Error loading insights:', error);
    }
  }
  
  function updateTimeframe(timeframe) {
    currentTimeframe = timeframe;
    loadSearchAnalytics();
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

  async function exportAnalytics() {
    try {
      const response = await fetch(`/api/v1/system/analytics/export?timeframe=${currentTimeframe}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `analytics-${currentTimeframe}d-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Export failed:', response.statusText);
        alert('Failed to export analytics data');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Error exporting analytics data');
    }
  }

  // Prepare data for charts
  $: agencyTypeData = data?.analytics?.agency_type_distribution || {};
  $: totalContacts = data?.analytics?.total_contacts || 0;
  
  $: monthlyTrendsData = data?.analytics?.monthly_trends?.map(trend => ({
    month: trend.month,
    value: trend.contacts_added
  })) || [];
  
  $: averageScoresData = data?.analytics?.monthly_trends?.map(trend => ({
    month: trend.month,
    value: Math.round(trend.average_score * 100)
  })) || [];
</script>

<div class="min-h-screen bg-gray-50 pb-20">
  <div class="container mx-auto px-4 py-6">
    <!-- Header -->
    <header class="mb-6">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">Market Intelligence Analytics</h1>
          <p class="text-gray-600">Comprehensive insights into your contact database and market trends</p>
        </div>
        <div class="flex gap-3">
          <!-- Timeframe Selector -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">Timeframe:</label>
            <select
              class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
              value={currentTimeframe}
              on:change={(e) => updateTimeframe(e.target.value)}
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="365">Last year</option>
              <option value="all">All time</option>
            </select>
          </div>
          
          <!-- Export Button -->
          <button
            class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"
            on:click={exportAnalytics}
          >
            Export Data
          </button>
        </div>
      </div>
    </header>

    {#if isLoading}
      <!-- Loading state -->
      <div class="space-y-6">
        <LoadingSkeleton type="card" height="120px" />
        <LoadingSkeleton type="card" height="200px" />
        <LoadingSkeleton type="card" height="250px" />
        <LoadingSkeleton type="card" height="180px" />
      </div>
    {:else}
      <!-- Key Metrics -->
      <div class="grid gap-4 mb-6 md:grid-cols-2 lg:grid-cols-4">
        <div class="card text-center">
          <div class="text-3xl font-bold text-primary-600 mb-1">
            {data?.stats?.total_contacts || 0}
          </div>
          <div class="text-sm text-gray-600">Total Contacts</div>
        </div>
        
        <div class="card text-center">
          <div class="text-3xl font-bold text-success-600 mb-1">
            {data?.analytics?.approved_contacts || 0}
          </div>
          <div class="text-sm text-gray-600">Approved</div>
        </div>
        
        <div class="card text-center">
          <div class="text-3xl font-bold text-warning-600 mb-1">
            {Math.round((data?.analytics?.average_confidence_score || 0) * 100)}%
          </div>
          <div class="text-sm text-gray-600">Avg Confidence</div>
        </div>
        
        <div class="card text-center">
          <div class="text-3xl font-bold text-error-600 mb-1">
            {Math.round((data?.analytics?.outreach_success_rate || 0) * 100)}%
          </div>
          <div class="text-sm text-gray-600">Success Rate</div>
        </div>
      </div>

      <!-- Search Performance Charts -->
      {#if searchAnalytics}
        <div class="card mb-6">
          <h2 class="text-xl font-semibold mb-4">Search Performance</h2>
          <div class="grid gap-6 md:grid-cols-2">
            <!-- Contact Discovery Trend -->
            <div>
              <h3 class="text-lg font-medium mb-3">Contact Discovery Trend</h3>
              <div class="bg-gray-100 rounded-lg p-8 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl mb-2">📈</div>
                  <p class="text-gray-600">Contact discovery chart would appear here</p>
                  <p class="text-sm text-gray-500">(Showing trends over selected timeframe)</p>
                </div>
              </div>
            </div>
            
            <!-- Provider Performance -->
            <div>
              <h3 class="text-lg font-medium mb-3">Provider Performance</h3>
              <div class="bg-gray-100 rounded-lg p-8 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl mb-2">🥧</div>
                  <p class="text-gray-600">Provider performance chart would appear here</p>
                  <p class="text-sm text-gray-500">(Showing distribution by provider)</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Additional Search Charts -->
        <div class="card mb-6">
          <h2 class="text-xl font-semibold mb-4">Search Analytics</h2>
          <div class="grid gap-6 md:grid-cols-2">
            <!-- Confidence Distribution -->
            <div>
              <h3 class="text-lg font-medium mb-3">Confidence Distribution</h3>
              <div class="bg-gray-100 rounded-lg p-8 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl mb-2">📊</div>
                  <p class="text-gray-600">Confidence distribution chart would appear here</p>
                  <p class="text-sm text-gray-500">(Showing contact confidence levels)</p>
                </div>
              </div>
            </div>
            
            <!-- Contact Methods -->
            <div>
              <h3 class="text-lg font-medium mb-3">Contact Methods</h3>
              <div class="bg-gray-100 rounded-lg p-8 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl mb-2">📋</div>
                  <p class="text-gray-600">Contact methods chart would appear here</p>
                  <p class="text-sm text-gray-500">(Showing distribution by contact method)</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- AI-Generated Insights -->
        {#if insights.length > 0}
          <div class="card mb-6">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-xl font-semibold">AI-Generated Insights</h2>
              <button class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">
                Refresh Insights
              </button>
            </div>
            <div class="space-y-4">
              {#each insights as insight}
                <div class="p-4 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg">
                  <div class="flex items-start">
                    <div class="text-blue-600 mr-3 mt-1">
                      <span class="text-lg">💡</span>
                    </div>
                    <div class="flex-1">
                      <h4 class="font-semibold text-gray-900 mb-1">{insight.title}</h4>
                      <p class="text-gray-600 text-sm mb-2">{insight.description}</p>
                      <div class="flex items-center text-xs text-gray-500">
                        <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-2">
                          {Math.round(insight.confidence * 100)}% confidence
                        </span>
                        <span>{insight.action}</span>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      {/if}

      <!-- Agency Type Distribution -->
      <div class="card mb-6">
        <h2 class="text-xl font-semibold mb-4">Agency Type Distribution</h2>
        <div class="grid gap-6 md:grid-cols-2">
          {#if data?.analytics?.agency_type_distribution}
            <div class="space-y-3">
              {#each Object.entries(data.analytics.agency_type_distribution) as [type, count]}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="text-sm font-medium text-gray-700 capitalize">
                    {type.replace('_', ' ')}
                  </span>
                  <div class="flex items-center gap-3">
                    <span class="text-sm text-gray-500">
                      {Math.round((count / totalContacts) * 100)}%
                    </span>
                    <span class="text-sm font-medium text-gray-900">
                      {count}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
            
            <!-- Pie Chart -->
            <div class="flex justify-center">
              <PieChart
                data={agencyTypeData}
                total={totalContacts}
                size="medium"
                showLabels={true}
                showPercentages={true}
              />
            </div>
          {:else}
            <div class="col-span-2 text-center py-8 text-gray-500">
              No agency type data available
            </div>
          {/if}
        </div>
      </div>

      <!-- Market Area Analysis -->
      <div class="card mb-6">
        <h2 class="text-xl font-semibold mb-4">Market Area Analysis</h2>
        {#if data?.analytics?.market_area_distribution}
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-3">
              {#each Object.entries(data.analytics.market_area_distribution).slice(0, 5) as [area, count]}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="text-sm font-medium text-gray-700">{area}</span>
                  <span class="text-sm font-medium text-gray-900">{count}</span>
                </div>
              {/each}
            </div>
            
            <!-- Placeholder for map visualization -->
            <div class="bg-gray-100 rounded-lg p-8 flex items-center justify-center">
              <div class="text-center">
                <div class="text-4xl mb-2">🗺️</div>
                <p class="text-gray-600">Geographic map would appear here</p>
                <p class="text-sm text-gray-500">(Showing market area distribution)</p>
              </div>
            </div>
          </div>
        {:else}
          <div class="text-center py-8 text-gray-500">
            No market area data available
          </div>
        {/if}
      </div>

      <!-- Monthly Trends -->
      <div class="card mb-6">
        <h2 class="text-xl font-semibold mb-4">Monthly Trends</h2>
        {#if data?.analytics?.monthly_trends?.length > 0}
          <div class="grid gap-6 md:grid-cols-2">
            <!-- Contacts Added Trend -->
            <div>
              <h3 class="text-lg font-medium mb-3">Contacts Added</h3>
              <LineChart
                data={monthlyTrendsData}
                title="Contacts Added"
                size="medium"
                showGrid={true}
                showPoints={true}
              />
            </div>
            
            <!-- Average Score Trend -->
            <div>
              <h3 class="text-lg font-medium mb-3">Average Score</h3>
              <LineChart
                data={averageScoresData}
                title="Average Score (%)"
                size="medium"
                showGrid={true}
                showPoints={true}
              />
            </div>
          </div>
          
          <!-- Data Table -->
          <div class="mt-6 overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200">
                  <th class="text-left py-3 font-medium text-gray-700">Month</th>
                  <th class="text-right py-3 font-medium text-gray-700">Contacts Added</th>
                  <th class="text-right py-3 font-medium text-gray-700">Approved</th>
                  <th class="text-right py-3 font-medium text-gray-700">Avg Score</th>
                </tr>
              </thead>
              <tbody>
                {#each data.analytics.monthly_trends as trend}
                  <tr class="border-b border-gray-100">
                    <td class="py-3 text-gray-900">{trend.month}</td>
                    <td class="py-3 text-right text-gray-900">{trend.contacts_added}</td>
                    <td class="py-3 text-right text-gray-900">{trend.contacts_approved}</td>
                    <td class="py-3 text-right text-gray-900">
                      {Math.round(trend.average_score * 100)}%
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <div class="text-center py-8 text-gray-500">
            No trend data available
          </div>
        {/if}
      </div>

      <!-- Quality Metrics -->
      <div class="card">
        <h2 class="text-xl font-semibold mb-4">Data Quality Metrics</h2>
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div class="text-center p-4 bg-primary-50 rounded-lg">
            <div class="text-2xl font-bold text-primary-600 mb-1">
              {Math.round((data?.analytics?.average_quality_score || 0) * 100)}%
            </div>
            <div class="text-sm text-gray-600">Data Quality Score</div>
          </div>
          
          <div class="text-center p-4 bg-success-50 rounded-lg">
            <div class="text-2xl font-bold text-success-600 mb-1">
              {data?.analytics?.pending_contacts || 0}
            </div>
            <div class="text-sm text-gray-600">Pending Review</div>
          </div>
          
          <div class="text-center p-4 bg-warning-50 rounded-lg">
            <div class="text-2xl font-bold text-warning-600 mb-1">
              {data?.analytics?.rejected_contacts || 0}
            </div>
            <div class="text-sm text-gray-600">Rejected</div>
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
  .bg-primary-50 { background: var(--primary-50); }
  .bg-success-50 { background: color-mix(in srgb, var(--success-500) 10%, transparent); }
  .bg-warning-50 { background: color-mix(in srgb, var(--warning-500) 10%, transparent); }
  
  .text-gray-900 { color: var(--gray-900); }
  .text-gray-600 { color: var(--gray-600); }
  .text-gray-500 { color: var(--gray-500); }
  .text-gray-700 { color: var(--gray-700); }
  .text-primary-600 { color: var(--primary-600); }
  .text-success-600 { color: var(--success-600); }
  .text-warning-600 { color: var(--warning-600); }
  .text-error-600 { color: var(--error-600); }
  
  .text-2xl { font-size: var(--font-size-2xl); }
  .text-xl { font-size: var(--font-size-xl); }
  .text-sm { font-size: var(--font-size-sm); }
  .text-3xl { font-size: var(--font-size-3xl); }
  .text-4xl { font-size: 2.25rem; }
  
  .font-bold { font-weight: 600; }
  .font-semibold { font-weight: 500; }
  .font-medium { font-weight: 500; }
  
  .mb-1 { margin-bottom: var(--space-1); }
  .mb-2 { margin-bottom: var(--space-2); }
  .mb-4 { margin-bottom: var(--space-4); }
  .mb-6 { margin-bottom: var(--space-6); }
  
  .py-6 { padding-top: var(--space-6); padding-bottom: var(--space-6); }
  .py-8 { padding-top: var(--space-8); padding-bottom: var(--space-8); }
  .px-4 { padding-left: var(--space-4); padding-right: var(--space-4); }
  .p-3 { padding: var(--space-3); }
  .p-4 { padding: var(--space-4); }
  .p-8 { padding: var(--space-8); }
  
  .pb-20 { padding-bottom: 5rem; }
  
  .rounded-lg { border-radius: var(--radius-lg); }
  
  .space-y-3 > * + * { margin-top: var(--space-3); }
  .gap-3 { gap: var(--space-3); }
  .gap-4 { gap: var(--space-4); }
  .gap-6 { gap: var(--space-6); }
  
  .flex { display: flex; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .justify-center { justify-content: center; }
  
  .w-full { width: 100%; }
  
  
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  .text-right { text-align: right; }
  
  .min-h-screen { min-height: 100vh; }
  
  .container {
    width: 100%;
    margin: 0 auto;
    padding: 0 var(--space-4);
  }
  
  .mx-auto { margin-left: auto; margin-right: auto; }
  
  .grid { display: grid; }
  
  .border-b { border-bottom-width: 1px; }
  .border-gray-200 { border-color: var(--gray-200); }
  .border-gray-100 { border-color: var(--gray-100); }
  
  .overflow-x-auto { overflow-x: auto; }
  
  table { border-collapse: collapse; }
  
  th, td { padding: var(--space-3); }
  
  .capitalize { text-transform: capitalize; }
  
  @media (min-width: 768px) {
    .md\:grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  }
  
  @media (min-width: 1024px) {
    .lg\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
    .lg\:grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
  }
</style>