<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { realTimeService } from '$lib/services/websocket';
  import { createEventDispatcher } from 'svelte';

  export let data;

  let configurations = data.configurations || [];
  let statistics = data.statistics || {};
  let isLoading = false;
  let activeTab = 'active';
  let searchStats = {
    total_searches: 0,
    running_searches: 0,
    results_today: 0,
    success_rate: 0
  };

  const dispatch = createEventDispatcher();

  // Munich districts data
  const munichDistricts = [
    { id: 1, name: 'Altstadt-Lehel', code: '01' },
    { id: 2, name: 'Ludwigsvorstadt-Isarvorstadt', code: '02' },
    { id: 3, name: 'Maxvorstadt', code: '03' },
    { id: 4, name: 'Schwabing-West', code: '04' },
    { id: 5, name: 'Au-Haidhausen', code: '05' },
    { id: 6, name: 'Schwabing-Freimann', code: '06' },
    { id: 7, name: 'Neuhausen-Nymphenburg', code: '07' },
    { id: 8, name: 'Moosach', code: '08' },
    { id: 9, name: 'Milbertshofen-Am Hart', code: '09' },
    { id: 10, name: 'Schwanthalerhöhe', code: '10' },
    { id: 11, name: 'Laim', code: '11' },
    { id: 12, name: 'Thalkirchen-Obersendling-Forstenried', code: '12' },
    { id: 13, name: 'Hadern', code: '13' },
    { id: 14, name: 'Pasing-Obermenzing', code: '14' },
    { id: 15, name: 'Aubing-Lochhausen-Langwied', code: '15' },
    { id: 16, name: 'Ramersdorf-Perlach', code: '16' },
    { id: 17, name: 'Trudering-Riem', code: '17' },
    { id: 18, name: 'Berg am Laim', code: '18' },
    { id: 19, name: 'Bogenhausen', code: '19' },
    { id: 20, name: 'Untergiesing-Harlaching', code: '20' },
    { id: 21, name: 'Thalkirchen-Obersendling-Forstenried-Fürstenried', code: '21' },
    { id: 22, name: 'Laim', code: '22' },
    { id: 23, name: 'Lohhof', code: '23' },
    { id: 24, name: 'Taufkirchen', code: '24' },
    { id: 25, name: 'Unterhaching', code: '25' }
  ];

  onMount(() => {
    // Initialize statistics
    searchStats = { ...statistics };
    
    // Subscribe to real-time updates
    const unsubscribe = realTimeService.subscribeSystemStatus((status) => {
      // Update search statistics from system status
      if (status.search_stats) {
        searchStats = { ...searchStats, ...status.search_stats };
      }
    });

    return () => unsubscribe();
  });

  // Format number with commas
  const formatNumber = (num) => {
    return new Intl.NumberFormat('de-DE').format(num);
  };

  // Get status badge color
  const getStatusBadgeColor = (status) => {
    const colors = {
      'running': 'success',
      'paused': 'warning',
      'completed': 'info',
      'error': 'error',
      'idle': 'secondary'
    };
    return colors[status] || 'secondary';
  };

  // Format relative time
  const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'Never';
    
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
  };

  // Create new search
  const createNewSearch = () => {
    dispatch('navigate', { url: '/search/new' });
  };

  // Edit search
  const editSearch = (searchId) => {
    dispatch('navigate', { url: `/search/edit/${searchId}` });
  };

  // Toggle search status
  const toggleSearch = async (searchId) => {
    try {
      isLoading = true;
      const response = await fetch(`/api/v1/search/${searchId}/toggle`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh configurations
        const updatedConfigs = await fetch('/api/v1/search/configurations');
        if (updatedConfigs.ok) {
          configurations = await updatedConfigs.json();
        }
      }
    } catch (error) {
      console.error('Error toggling search:', error);
    } finally {
      isLoading = false;
    }
  };

  // Delete search
  const deleteSearch = async (searchId) => {
    if (confirm('Are you sure you want to delete this search?')) {
      try {
        const response = await fetch(`/api/v1/search/${searchId}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          configurations = configurations.filter(config => config.id !== searchId);
        }
      } catch (error) {
        console.error('Error deleting search:', error);
      }
    }
  };
</script>

<div class="search-management">
  <div class="container mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Search Management</h1>
      <p class="text-gray-600">Manage your apartment search configurations and monitor search performance</p>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-blue-100 text-blue-600">
            <span class="text-xl">🔍</span>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Total Searches</p>
            <p class="text-2xl font-bold text-gray-900">{formatNumber(searchStats.total_searches)}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-green-100 text-green-600">
            <span class="text-xl">▶️</span>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Running</p>
            <p class="text-2xl font-bold text-gray-900">{formatNumber(searchStats.running_searches)}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-purple-100 text-purple-600">
            <span class="text-xl">📈</span>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Results Today</p>
            <p class="text-2xl font-bold text-gray-900">{formatNumber(searchStats.results_today)}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
            <span class="text-xl">🎯</span>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Success Rate</p>
            <p class="text-2xl font-bold text-gray-900">{searchStats.success_rate}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Bar -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex space-x-4">
        <button
          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          on:click={createNewSearch}
        >
          + New Search
        </button>
        <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Import Search
        </button>
      </div>
      
      <div class="flex space-x-2">
        <button
          class:active={activeTab === 'active'}
          class="px-4 py-2 rounded-lg transition-colors"
          on:click={() => activeTab = 'active'}
        >
          Active ({configurations.filter(c => c.status === 'running').length})
        </button>
        <button
          class:active={activeTab === 'all'}
          class="px-4 py-2 rounded-lg transition-colors"
          on:click={() => activeTab = 'all'}
        >
          All ({configurations.length})
        </button>
      </div>
    </div>

    <!-- Search Configurations Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each configurations.filter(config => activeTab === 'all' || config.status === 'running') as config}
        <div
          transition:fade
          class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div class="p-4 border-b border-gray-100">
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900">{config.name}</h3>
              <span class="badge badge-{getStatusBadgeColor(config.status)}">
                {config.status}
              </span>
            </div>
            
            <div class="mt-2 space-y-1 text-sm text-gray-600">
              <div class="flex justify-between">
                <span>Price:</span>
                <span>€{formatNumber(config.min_price)} - €{formatNumber(config.max_price)}</span>
              </div>
              <div class="flex justify-between">
                <span>Rooms:</span>
                <span>{config.min_rooms}+</span>
              </div>
              <div class="flex justify-between">
                <span>Districts:</span>
                <span>{config.districts?.length || 0}</span>
              </div>
            </div>
          </div>

          <div class="p-4 border-b border-gray-100">
            <div class="flex justify-between text-sm">
              <span>Last Run:</span>
              <span class="text-gray-600">{formatRelativeTime(config.last_run)}</span>
            </div>
            <div class="flex justify-between text-sm mt-1">
              <span>Results:</span>
              <span class="text-gray-600">{config.results_count || 0}</span>
            </div>
          </div>

          <div class="p-3 flex justify-end space-x-2">
            <button
              class="p-2 text-gray-400 hover:text-blue-600 transition-colors"
              on:click={() => editSearch(config.id)}
              title="Edit Search"
            >
              <span class="text-sm">✏️</span>
            </button>
            <button
              class="p-2 text-gray-400 hover:text-green-600 transition-colors"
              on:click={() => toggleSearch(config.id)}
              disabled={isLoading}
              title={config.status === 'running' ? 'Pause Search' : 'Start Search'}
            >
              <span class="text-sm">{config.status === 'running' ? '⏸️' : '▶️'}</span>
            </button>
            <button
              class="p-2 text-gray-400 hover:text-red-600 transition-colors"
              on:click={() => deleteSearch(config.id)}
              title="Delete Search"
            >
              <span class="text-sm">🗑️</span>
            </button>
          </div>
        </div>
      {:else}
        <div class="col-span-full text-center py-12">
          <div class="text-6xl mb-4">🔍</div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No Active Searches</h3>
          <p class="text-gray-600 mb-4">Create your first search to start finding apartments</p>
          <button
            class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            on:click={createNewSearch}
          >
            Create Search
          </button>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .search-management {
    min-height: calc(100vh - 200px);
  }

  .badge {
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .badge-success {
    background-color: var(--green-100);
    color: var(--green-800);
  }

  .badge-warning {
    background-color: var(--yellow-100);
    color: var(--yellow-800);
  }

  .badge-info {
    background-color: var(--blue-100);
    color: var(--blue-800);
  }

  .badge-error {
    background-color: var(--red-100);
    color: var(--red-800);
  }

  .badge-secondary {
    background-color: var(--gray-100);
    color: var(--gray-800);
  }

  button.active {
    background-color: var(--primary-600);
    color: white;
  }
</style>