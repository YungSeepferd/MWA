<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { apiClient } from '$lib/services/api';
  import type { MarketIntelligenceContact } from '$lib/types/api';

  export let contact: MarketIntelligenceContact;
  export let isOpen = false;

  const dispatch = createEventDispatcher();

  let isLoading = false;
  let error: string | null = null;

  const closeModal = () => {
    dispatch('close');
  };

  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      closeModal();
    }
  };

  const getStatusColor = (contact: MarketIntelligenceContact) => {
    if (contact.is_approved) return 'bg-green-100 text-green-800 border-green-200';
    if (contact.is_rejected) return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  };

  const getStatusText = (contact: MarketIntelligenceContact) => {
    if (contact.is_approved) return 'Approved';
    if (contact.is_rejected) return 'Rejected';
    return 'Pending';
  };

  const getContactIcon = (contact: MarketIntelligenceContact) => {
    if (contact.email) return '📧';
    if (contact.phone) return '📱';
    return '👤';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const updateContactStatus = async (status: string) => {
    isLoading = true;
    error = null;

    try {
      await apiClient.updateContact(contact.id, { status });
      dispatch('contactUpdated', { contact: { ...contact, status } });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to update contact status';
    } finally {
      isLoading = false;
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success feedback (could be enhanced with a toast notification)
      console.log('Copied to clipboard:', text);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };
</script>

{#if isOpen}
  <div
    class="fixed inset-0 z-50 overflow-y-auto"
    role="dialog"
    aria-labelledby="modal-title"
    on:keydown={handleKeydown}
  >
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" on:click={closeModal}></div>

    <!-- Modal -->
    <div class="flex min-h-full items-end justify-center p-4 sm:items-center sm:p-0">
      <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-3">
            <span class="text-3xl">{getContactIcon(contact.type)}</span>
            <div>
              <h2 id="modal-title" class="text-lg font-semibold text-gray-900">
                Contact Details
              </h2>
              <p class="text-sm text-gray-500">{contact.position || 'Contact'}</p>
            </div>
          </div>
          
          <button
            on:click={closeModal}
            class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <span class="sr-only">Close</span>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Error Message -->
        {#if error}
          <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p class="text-sm text-red-600">{error}</p>
          </div>
        {/if}

        <!-- Contact Value -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Contact Value</label>
          <div class="flex items-center justify-between">
            <code class="text-sm bg-gray-100 px-2 py-1 rounded border">
              {contact.value}
            </code>
            <button
              on:click={() => copyToClipboard(contact.value)}
              class="text-blue-600 hover:text-blue-800 text-sm"
            >
              Copy
            </button>
          </div>
        </div>

        <!-- Status Section -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <div class="flex items-center space-x-2">
            <span class={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(contact.status)}`}>
              {contact.status}
            </span>
            
            {#if !isLoading}
              <select
                value={contact.status}
                on:change={(e) => updateContactStatus(e.target.value)}
                class="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="pending">Pending</option>
                <option value="verified">Verified</option>
                <option value="invalid">Invalid</option>
              </select>
            {:else}
              <span class="text-sm text-gray-500">Updating...</span>
            {/if}
          </div>
        </div>

        <!-- Confidence Score -->
        {#if contact.confidence !== undefined}
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Confidence Score: {Math.round(contact.confidence * 100)}%
            </label>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div 
                class="h-2 rounded-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-400 transition-all duration-300"
                style={`width: ${(contact.confidence * 100)}%`}
              ></div>
            </div>
          </div>
        {/if}

        <!-- Contact Information Grid -->
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Source</label>
            <p class="text-sm text-gray-900">{contact.source || 'Unknown'}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <p class="text-sm text-gray-900 capitalize">{contact.type}</p>
          </div>
        </div>

        <!-- Timestamps -->
        <div class="grid grid-cols-2 gap-4 mb-4">
          {#if contact.created_at}
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Created</label>
              <p class="text-sm text-gray-900">{formatDate(contact.created_at)}</p>
            </div>
          {/if}
          
          {#if contact.updated_at}
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Updated</label>
              <p class="text-sm text-gray-900">{formatDate(contact.updated_at)}</p>
            </div>
          {/if}
        </div>

        <!-- Metadata -->
        {#if contact.metadata && Object.keys(contact.metadata).length > 0}
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Metadata</label>
            <div class="bg-gray-50 rounded-md p-3 max-h-32 overflow-y-auto">
              <table class="w-full text-sm">
                <tbody>
                  {#each Object.entries(contact.metadata) as [key, value]}
                    <tr class="border-b border-gray-200 last:border-b-0">
                      <td class="py-1 pr-2 font-medium text-gray-600">{key}:</td>
                      <td class="py-1 text-gray-800">{value}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}

        <!-- Actions -->
        <div class="flex justify-end space-x-3 mt-6">
          <button
            on:click={closeModal}
            class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Close
          </button>
          
          <button
            on:click={() => dispatch('edit', { contact })}
            class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Edit Contact
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-enter {
    opacity: 0;
    transform: scale(0.95);
  }
  
  .modal-enter-active {
    opacity: 1;
    transform: scale(1);
    transition: opacity 300ms, transform 300ms;
  }
</style>