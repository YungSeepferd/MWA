<script lang="ts">
  import { apiClient } from '$lib/services/api';
  import { goto } from '$app/navigation';
  
  export let filters: any = {};
  
  let isOpen = false;
  let isLoading = false;
  
  // Filter state
  let selectedAgencyType = '';
  let selectedMarketArea = '';
  let minConfidenceScore = '';
  let minQualityScore = '';
  let approvalStatus = '';
  let leadSource = '';
  let dateRange = {
    start: '',
    end: ''
  };
  
  // Available options
  const agencyTypes = [
    { value: '', label: 'All Agency Types' },
    { value: 'property_manager', label: 'Property Manager' },
    { value: 'landlord', label: 'Landlord' },
    { value: 'real_estate_agent', label: 'Real Estate Agent' },
    { value: 'broker', label: 'Broker' },
    { value: 'developer', label: 'Developer' },
    { value: 'other', label: 'Other' }
  ];
  
  const approvalStatuses = [
    { value: '', label: 'All Status' },
    { value: 'approved', label: 'Approved' },
    { value: 'pending', label: 'Pending' },
    { value: 'rejected', label: 'Rejected' }
  ];
  
  const leadSources = [
    { value: '', label: 'All Sources' },
    { value: 'web_crawler', label: 'Web Crawler' },
    { value: 'manual_entry', label: 'Manual Entry' },
    { value: 'import', label: 'Import' },
    { value: 'api', label: 'API' }
  ];
  
  // Apply filters
  async function applyFilters() {
    isLoading = true;
    
    try {
      const params = new URLSearchParams();
      
      // Add filters to URL parameters
      if (selectedAgencyType) params.set('agency_type', selectedAgencyType);
      if (selectedMarketArea) params.set('market_area', selectedMarketArea);
      if (minConfidenceScore) params.set('min_confidence', minConfidenceScore);
      if (minQualityScore) params.set('min_quality', minQualityScore);
      if (approvalStatus) params.set('status', approvalStatus);
      if (leadSource) params.set('lead_source', leadSource);
      if (dateRange.start) params.set('date_start', dateRange.start);
      if (dateRange.end) params.set('date_end', dateRange.end);
      
      // Navigate with filters
      await goto(`/contacts?${params.toString()}`, { replaceState: true });
      
      // Close filter panel
      isOpen = false;
    } catch (error) {
      console.error('Error applying filters:', error);
    } finally {
      isLoading = false;
    }
  }
  
  // Reset filters
  function resetFilters() {
    selectedAgencyType = '';
    selectedMarketArea = '';
    minConfidenceScore = '';
    minQualityScore = '';
    approvalStatus = '';
    leadSource = '';
    dateRange = { start: '', end: '' };
  }
  
  // Clear all filters
  async function clearAllFilters() {
    resetFilters();
    await goto('/contacts', { replaceState: true });
    isOpen = false;
  }
</script>

<div class="contact-filter">
  <!-- Filter Toggle Button -->
  <button
    class="btn btn-secondary"
    on:click={() => isOpen = !isOpen}
    aria-expanded={isOpen}
    aria-controls="filter-panel"
  >
    <span class="mr-2">Filter</span>
    {#if isOpen}
      <span>▲</span>
    {:else}
      <span>▼</span>
    {/if}
  </button>
  
  <!-- Filter Panel -->
  {#if isOpen}
    <div id="filter-panel" class="filter-panel">
      <div class="filter-header">
        <h3 class="text-lg font-semibold">Filter Contacts</h3>
        <button
          on:click={() => isOpen = false}
          class="text-gray-400 hover:text-gray-600"
          aria-label="Close filters"
        >
          ✕
        </button>
      </div>
      
      <div class="filter-content">
        <!-- Agency Type -->
        <div class="filter-group">
          <label for="agency-type" class="filter-label">Agency Type</label>
          <select
            id="agency-type"
            bind:value={selectedAgencyType}
            class="filter-input"
          >
            {#each agencyTypes as type}
              <option value={type.value}>{type.label}</option>
            {/each}
          </select>
        </div>
        
        <!-- Market Area -->
        <div class="filter-group">
          <label for="market-area" class="filter-label">Market Area</label>
          <input
            id="market-area"
            type="text"
            bind:value={selectedMarketArea}
            placeholder="Enter market area..."
            class="filter-input"
          />
        </div>
        
        <!-- Confidence Score -->
        <div class="filter-group">
          <label for="confidence-score" class="filter-label">Min Confidence</label>
          <div class="flex items-center gap-2">
            <input
              id="confidence-score"
              type="range"
              min="0"
              max="100"
              bind:value={minConfidenceScore}
              class="flex-1"
            />
            <span class="text-sm text-gray-600 w-12">{minConfidenceScore || 0}%</span>
          </div>
        </div>
        
        <!-- Quality Score -->
        <div class="filter-group">
          <label for="quality-score" class="filter-label">Min Quality</label>
          <div class="flex items-center gap-2">
            <input
              id="quality-score"
              type="range"
              min="0"
              max="100"
              bind:value={minQualityScore}
              class="flex-1"
            />
            <span class="text-sm text-gray-600 w-12">{minQualityScore || 0}%</span>
          </div>
        </div>
        
        <!-- Approval Status -->
        <div class="filter-group">
          <label for="approval-status" class="filter-label">Status</label>
          <select
            id="approval-status"
            bind:value={approvalStatus}
            class="filter-input"
          >
            {#each approvalStatuses as status}
              <option value={status.value}>{status.label}</option>
            {/each}
          </select>
        </div>
        
        <!-- Lead Source -->
        <div class="filter-group">
          <label for="lead-source" class="filter-label">Lead Source</label>
          <select
            id="lead-source"
            bind:value={leadSource}
            class="filter-input"
          >
            {#each leadSources as source}
              <option value={source.value}>{source.label}</option>
            {/each}
          </select>
        </div>
        
        <!-- Date Range -->
        <div class="filter-group">
          <label class="filter-label">Date Range</label>
          <div class="grid gap-2 grid-cols-2">
            <input
              type="date"
              bind:value={dateRange.start}
              placeholder="Start date"
              class="filter-input text-sm"
            />
            <input
              type="date"
              bind:value={dateRange.end}
              placeholder="End date"
              class="filter-input text-sm"
            />
          </div>
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div class="filter-actions">
        <button
          on:click={clearAllFilters}
          class="btn btn-secondary"
          disabled={isLoading}
        >
          Clear All
        </button>
        <button
          on:click={applyFilters}
          class="btn btn-primary"
          disabled={isLoading}
        >
          {#if isLoading}
            <span class="animate-pulse">Applying...</span>
          {:else}
            Apply Filters
          {/if}
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .contact-filter {
    position: relative;
    display: inline-block;
  }
  
  .filter-panel {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    min-width: 300px;
    margin-top: var(--space-2);
  }
  
  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    border-bottom: 1px solid var(--gray-200);
  }
  
  .filter-content {
    padding: var(--space-4);
    max-height: 400px;
    overflow-y: auto;
  }
  
  .filter-group {
    margin-bottom: var(--space-4);
  }
  
  .filter-label {
    display: block;
    margin-bottom: var(--space-1);
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--gray-700);
  }
  
  .filter-input {
    width: 100%;
    padding: var(--space-2);
    border: 1px solid var(--gray-300);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
  }
  
  .filter-input:focus {
    outline: none;
    border-color: var(--primary-500);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }
  
  .filter-actions {
    display: flex;
    justify-content: space-between;
    padding: var(--space-4);
    border-top: 1px solid var(--gray-200);
    gap: var(--space-2);
  }
  
  .mr-2 {
    margin-right: var(--space-2);
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .filter-panel {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      margin: 0;
      border-radius: 0;
      z-index: 1001;
    }
    
    .filter-content {
      max-height: calc(100vh - 120px);
    }
  }
</style>