<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { toggleContactSelection } from '$lib/stores/contactStore';
  import type { MarketIntelligenceContact } from '$lib/types/api';

  export let contact: MarketIntelligenceContact;
  export let selected = false;
  export let showActions = true;

  const dispatch = createEventDispatcher();

  const handleSelect = () => {
    toggleContactSelection(contact.id.toString());
  };

  const handleEdit = () => {
    dispatch('edit', { contact });
  };

  const handleDelete = () => {
    dispatch('delete', { contact });
  };

  const handleViewDetails = () => {
    dispatch('viewDetails', { contact });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusColor = (contact: MarketIntelligenceContact) => {
    if (contact.is_approved) return 'bg-green-100 text-green-800';
    if (contact.is_rejected) return 'bg-red-100 text-red-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  const getStatusText = (contact: MarketIntelligenceContact) => {
    if (contact.is_approved) return 'Approved';
    if (contact.is_rejected) return 'Rejected';
    return 'Pending';
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

<div class="contact-card bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
  <!-- Header -->
  <div class="flex items-center justify-between p-4 border-b border-gray-100">
    <div class="flex items-center space-x-3">
      <input
        type="checkbox"
        checked={selected}
        on:change={handleSelect}
        class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
      />
      
      <span class="text-2xl">{getContactIcon(contact.type)}</span>
      
      <div>
        <h3 class="text-sm font-medium text-gray-900 truncate max-w-[200px]">
          {contact.name}
        </h3>
        <p class="text-xs text-gray-500">{contact.position || 'Contact'}</p>
      </div>
    </div>

    <div class="flex items-center space-x-2">
      <span class={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(contact)}`}>
        {getStatusText(contact)}
      </span>
    </div>
  </div>

  <!-- Content -->
  <div class="p-4 space-y-3">
    <!-- Confidence Score -->
    {#if contact.confidence_score !== undefined}
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-600">Confidence:</span>
        <div class="flex items-center space-x-2">
          <div class="w-16 bg-gray-200 rounded-full h-2">
            <div
              class="h-2 rounded-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-400"
              style={`width: ${(contact.confidence_score * 100)}%`}
            ></div>
          </div>
          <span class={`text-xs font-medium ${getConfidenceColor(contact.confidence_score)}`}>
            {Math.round(contact.confidence_score * 100)}%
          </span>
        </div>
      </div>
    {/if}

    <!-- Contact Information -->
    <div class="space-y-1 text-xs">
      {#if contact.email}
        <div class="flex justify-between">
          <span class="text-gray-600">Email:</span>
          <span class="text-gray-900 truncate max-w-[120px]">{contact.email}</span>
        </div>
      {/if}
      
      {#if contact.phone}
        <div class="flex justify-between">
          <span class="text-gray-600">Phone:</span>
          <span class="text-gray-900">{contact.phone}</span>
        </div>
      {/if}
      
      {#if contact.company_name}
        <div class="flex justify-between">
          <span class="text-gray-600">Company:</span>
          <span class="text-gray-900 truncate max-w-[120px]">{contact.company_name}</span>
        </div>
      {/if}
    </div>

    <!-- Metadata -->
    <div class="grid grid-cols-2 gap-2 text-xs">
      {#if contact.created_at}
        <div>
          <span class="text-gray-600">Created:</span>
          <div class="text-gray-900">{formatDate(contact.created_at)}</div>
        </div>
      {/if}
      
      {#if contact.updated_at}
        <div>
          <span class="text-gray-600">Updated:</span>
          <div class="text-gray-900">{formatDate(contact.updated_at)}</div>
        </div>
      {/if}
    </div>

    <!-- Additional Fields -->
    {#if contact.metadata && Object.keys(contact.metadata).length > 0}
      <div class="border-t border-gray-100 pt-2">
        <div class="text-xs text-gray-600 mb-1">Metadata:</div>
        <div class="grid grid-cols-2 gap-1 text-xs">
          {#each Object.entries(contact.metadata).slice(0, 4) as [key, value]}
            <div class="truncate">
              <span class="text-gray-500">{key}:</span>
              <span class="text-gray-900 ml-1 truncate">{value}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <!-- Actions -->
  {#if showActions}
    <div class="flex border-t border-gray-100 divide-x divide-gray-100">
      <button
        on:click={handleViewDetails}
        class="flex-1 py-2 px-3 text-xs text-blue-600 hover:bg-blue-50 transition-colors duration-150"
        title="View Details"
      >
        Details
      </button>
      
      <button
        on:click={handleEdit}
        class="flex-1 py-2 px-3 text-xs text-gray-600 hover:bg-gray-50 transition-colors duration-150"
        title="Edit Contact"
      >
        Edit
      </button>
      
      <button
        on:click={handleDelete}
        class="flex-1 py-2 px-3 text-xs text-red-600 hover:bg-red-50 transition-colors duration-150"
        title="Delete Contact"
      >
        Delete
      </button>
    </div>
  {/if}
</div>

<style>
  .contact-card {
    min-height: 200px;
  }
  
  .contact-card:hover {
    transform: translateY(-1px);
    transition: transform 0.2s ease-in-out;
  }
</style>