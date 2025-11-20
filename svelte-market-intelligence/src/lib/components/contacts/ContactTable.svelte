<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { toggleContactSelection, toggleSelectAll } from '$lib/stores/contactStore';
  import type { MarketIntelligenceContact } from '$lib/types/api';

  export let contacts: MarketIntelligenceContact[] = [];
  export let selectedContacts: Set<string> = new Set();
  export let isLoading = false;
  export let sortField = 'created_at';
  export let sortOrder: 'asc' | 'desc' = 'desc';

  const dispatch = createEventDispatcher();

  const handleSelect = (contactId: string) => {
    toggleContactSelection(contactId);
  };

  const handleSelectAll = () => {
    toggleSelectAll();
  };

  const handleSort = (field: string) => {
    const newOrder = sortField === field && sortOrder === 'desc' ? 'asc' : 'desc';
    dispatch('sort', { field, order: newOrder });
  };

  const handleEdit = (contact: MarketIntelligenceContact) => {
    dispatch('edit', { contact });
  };

  const handleDelete = (contact: MarketIntelligenceContact) => {
    dispatch('delete', { contact });
  };

  const handleViewDetails = (contact: MarketIntelligenceContact) => {
    dispatch('viewDetails', { contact });
  };

  const getSortIcon = (field: string) => {
    if (sortField !== field) return '↕️';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'invalid': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getContactIcon = (type: string) => {
    switch (type) {
      case 'email': return '📧';
      case 'phone': return '📱';
      case 'website': return '🌐';
      case 'address': return '🏠';
      default: return '📋';
    }
  };
</script>

<div class="bg-white shadow-sm rounded-lg border border-gray-200">
  <!-- Table -->
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <!-- Select All Checkbox -->
          <th class="w-12 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <input
              type="checkbox"
              checked={contacts.length > 0 && contacts.every(c => selectedContacts.has(c.id.toString()))}
              on:change={handleSelectAll}
              class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
          </th>

          <!-- Contact Value -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('value')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Contact</span>
              <span class="text-xs">{getSortIcon('value')}</span>
            </button>
          </th>

          <!-- Agency Type -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('agency_type')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Agency Type</span>
              <span class="text-xs">{getSortIcon('agency_type')}</span>
            </button>
          </th>

          <!-- Status -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('status')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Status</span>
              <span class="text-xs">{getSortIcon('status')}</span>
            </button>
          </th>

          <!-- Confidence -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('confidence')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Confidence</span>
              <span class="text-xs">{getSortIcon('confidence')}</span>
            </button>
          </th>

          <!-- Source -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('source')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Source</span>
              <span class="text-xs">{getSortIcon('source')}</span>
            </button>
          </th>

          <!-- Created Date -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <button
              on:click={() => handleSort('created_at')}
              class="flex items-center space-x-1 hover:text-gray-700"
            >
              <span>Created</span>
              <span class="text-xs">{getSortIcon('created_at')}</span>
            </button>
          </th>

          <!-- Actions -->
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>

      <tbody class="bg-white divide-y divide-gray-200">
        {#if isLoading}
          <!-- Loading State -->
          <tr>
            <td colspan="8" class="px-4 py-8 text-center">
              <div class="flex justify-center items-center space-x-2">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span class="text-sm text-gray-600">Loading contacts...</span>
              </div>
            </td>
          </tr>
        {:else if contacts.length === 0}
          <!-- Empty State -->
          <tr>
            <td colspan="8" class="px-4 py-8 text-center">
              <div class="text-gray-500">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No contacts found</h3>
                <p class="mt-1 text-sm text-gray-500">Try adjusting your search filters.</p>
              </div>
            </td>
          </tr>
        {:else}
          <!-- Contact Rows -->
          {#each contacts as contact}
            <tr class="hover:bg-gray-50 transition-colors duration-150">
              <!-- Checkbox -->
              <td class="px-4 py-3 whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={selectedContacts.has(contact.id.toString())}
                  on:change={() => handleSelect(contact.id.toString())}
                  class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
              </td>

              <!-- Contact Value -->
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="flex items-center space-x-2">
                  <span class="text-lg">{getContactIcon(contact.type)}</span>
                  <div>
                    <div class="text-sm font-medium text-gray-900 truncate max-w-[200px]">
                      {contact.value}
                    </div>
                  </div>
                </div>
              </td>

              <!-- Type -->
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">
                {contact.type}
              </td>

              <!-- Status -->
              <td class="px-4 py-3 whitespace-nowrap">
                <span class={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(contact.status)}`}>
                  {contact.status}
                </span>
              </td>

              <!-- Confidence -->
              <td class="px-4 py-3 whitespace-nowrap">
                {#if contact.confidence !== undefined}
                  <div class="flex items-center space-x-2">
                    <div class="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        class="h-2 rounded-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-400"
                        style={`width: ${(contact.confidence * 100)}%`}
                      ></div>
                    </div>
                    <span class={`text-xs font-medium ${getConfidenceColor(contact.confidence)}`}>
                      {Math.round(contact.confidence * 100)}%
                    </span>
                  </div>
                {:else}
                  <span class="text-xs text-gray-400">N/A</span>
                {/if}
              </td>

              <!-- Source -->
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 truncate max-w-[120px]">
                {contact.source || 'Unknown'}
              </td>

              <!-- Created Date -->
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {formatDate(contact.created_at)}
              </td>

              <!-- Actions -->
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center space-x-2">
                  <button
                    on:click={() => handleViewDetails(contact)}
                    class="text-blue-600 hover:text-blue-900 text-xs"
                    title="View Details"
                  >
                    Details
                  </button>
                  
                  <button
                    on:click={() => handleEdit(contact)}
                    class="text-gray-600 hover:text-gray-900 text-xs"
                    title="Edit Contact"
                  >
                    Edit
                  </button>
                  
                  <button
                    on:click={() => handleDelete(contact)}
                    class="text-red-600 hover:text-red-900 text-xs"
                    title="Delete Contact"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

<style>
  table {
    border-collapse: separate;
    border-spacing: 0;
  }
  
  th, td {
    border-right: 1px solid #e5e7eb;
  }
  
  th:last-child, td:last-child {
    border-right: none;
  }
</style>