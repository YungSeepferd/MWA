<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { apiClient } from '$lib/services/api';

  export let selectedCount = 0;

  const dispatch = createEventDispatcher();

  let isLoading = false;
  let error: string | null = null;

  const handleBulkAction = async (action: string) => {
    isLoading = true;
    error = null;

    try {
      switch (action) {
        case 'verify':
          // Implement bulk verification
          console.log('Bulk verify', selectedCount, 'contacts');
          break;
        
        case 'delete':
          // Implement bulk deletion
          console.log('Bulk delete', selectedCount, 'contacts');
          break;
        
        case 'export':
          // Implement bulk export
          console.log('Bulk export', selectedCount, 'contacts');
          break;
        
        default:
          console.log('Unknown bulk action:', action);
      }

      dispatch('bulkAction', { action });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to perform bulk action';
    } finally {
      isLoading = false;
    }
  };
</script>

<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="flex-shrink-0">
        <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </div>
      
      <div>
        <h3 class="text-sm font-medium text-blue-800">
          {selectedCount} contact{selectedCount !== 1 ? 's' : ''} selected
        </h3>
        <p class="text-sm text-blue-600">
          Choose an action to perform on all selected contacts
        </p>
      </div>
    </div>

    <div class="flex items-center space-x-2">
      <!-- Bulk Actions -->
      <button
        on:click={() => handleBulkAction('verify')}
        disabled={isLoading}
        class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {#if isLoading}
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {/if}
        Verify Selected
      </button>

      <button
        on:click={() => handleBulkAction('export')}
        disabled={isLoading}
        class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg class="-ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Export Selected
      </button>

      <button
        on:click={() => handleBulkAction('delete')}
        disabled={isLoading}
        class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg class="-ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Delete Selected
      </button>
    </div>
  </div>

  <!-- Error Message -->
  {#if error}
    <div class="mt-3 p-2 bg-red-50 border border-red-200 rounded-md">
      <p class="text-sm text-red-600">{error}</p>
    </div>
  {/if}
</div>