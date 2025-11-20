<script lang="ts">
  import { onMount } from 'svelte';
  import { contactStore, loadContacts, applyFilters, sortContacts, goToPage, clearAllFilters, selectedCount } from '$lib/stores/contactStore';
  import { paginatedContacts, totalPages, hasNextPage, hasPrevPage } from '$lib/stores/contactStore';
  import ContactCard from '$lib/components/contacts/ContactCard.svelte';
  import ContactTable from '$lib/components/contacts/ContactTable.svelte';
  import ContactDetailModal from '$lib/components/contacts/ContactDetailModal.svelte';
  import BulkOperations from '$lib/components/contacts/BulkOperations.svelte';
  
  let viewMode: 'grid' | 'table' = 'grid';
  let showDetailModal = false;
  let selectedContact = null;
  let searchTerm = '';
  let filters = {
    status: '',
    confidence: '',
    agencyType: ''
  };

  let { contacts, filteredContacts, selectedContacts, currentPage, itemsPerPage, isLoading, error } = contactStore;
  
  $: $selectedCount = selectedCount;
  $: $paginatedContacts = paginatedContacts;
  $: $totalPages = totalPages;
  $: $hasNextPage = hasNextPage;
  $: $hasPrevPage = hasPrevPage;

  onMount(async () => {
    await loadContacts();
  });

  const handleSearch = (value: string) => {
    searchTerm = value;
    applyFilters({ search: value });
  };

  const handleFilterChange = (filterType: string, value: string) => {
    filters = { ...filters, [filterType]: value };
    applyFilters(filters);
  };

  const handleClearFilters = () => {
    searchTerm = '';
    filters = { status: '', confidence: '', agencyType: '' };
    clearAllFilters();
  };

  const handleSort = (event: { field: string; order: 'asc' | 'desc' }) => {
    sortContacts(event.field, event.order);
  };

  const handleViewDetails = (contact: any) => {
    selectedContact = contact;
    showDetailModal = true;
  };

  const handleEdit = (contact: any) => {
    // Implement edit functionality
    console.log('Edit contact:', contact);
  };

  const handleDelete = (contact: any) => {
    // Implement delete functionality
    console.log('Delete contact:', contact);
  };

  const handleContactUpdated = (event: { contact: any }) => {
    // Update contact in store
    console.log('Contact updated:', event.contact);
  };

  const handleBulkAction = (action: string) => {
    console.log('Bulk action:', action, 'on', $selectedCount, 'contacts');
  };
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <div class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Contact Management</h1>
          <p class="mt-1 text-sm text-gray-600">
            Manage and organize your discovered contacts
          </p>
        </div>
        
        <div class="flex items-center space-x-4">
          <!-- View Mode Toggle -->
          <div class="flex rounded-md shadow-sm">
            <button
              class={`px-3 py-2 text-sm font-medium rounded-l-md ${
                viewMode === 'grid'
                  ? 'bg-blue-100 text-blue-600 border border-blue-200'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
              on:click={() => (viewMode = 'grid')}
            >
              Grid
            </button>
            <button
              class={`px-3 py-2 text-sm font-medium rounded-r-md ${
                viewMode === 'table'
                  ? 'bg-blue-100 text-blue-600 border border-blue-200'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
              on:click={() => (viewMode = 'table')}
            >
              Table
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Filters and Search -->
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <!-- Search -->
            <div class="lg:col-span-2">
              <label for="search" class="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <div class="relative">
                <input
                  id="search"
                  type="text"
                  bind:value={searchTerm}
                  on:input={(e) => handleSearch(e.target.value)}
                  placeholder="Search contacts..."
                  class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Status Filter -->
            <div>
              <label for="status" class="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                id="status"
                bind:value={filters.status}
                on:change={(e) => handleFilterChange('status', e.target.value)}
                class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">All Status</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
                <option value="invalid">Invalid</option>
              </select>
            </div>

            <!-- Confidence Filter -->
            <div>
              <label for="confidence" class="block text-sm font-medium text-gray-700 mb-1">Confidence</label>
              <select
                id="confidence"
                bind:value={filters.confidence}
                on:change={(e) => handleFilterChange('confidence', e.target.value)}
                class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">All Confidence</option>
                <option value="high">High (≥90%)</option>
                <option value="medium">Medium (70-89%)</option>
                <option value="low">Low (&lt;70%)</option>
              </select>
            </div>

            <!-- Agency Type Filter -->
            <div>
              <label for="agencyType" class="block text-sm font-medium text-gray-700 mb-1">Agency Type</label>
              <select
                id="agencyType"
                bind:value={filters.agencyType}
                on:change={(e) => handleFilterChange('agencyType', e.target.value)}
                class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">All Types</option>
                <option value="property_manager">Property Manager</option>
                <option value="landlord">Landlord</option>
                <option value="real_estate_agent">Real Estate Agent</option>
                <option value="broker">Broker</option>
                <option value="developer">Developer</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <!-- Clear Filters -->
          <div class="mt-4 flex justify-between items-center">
            <div class="text-sm text-gray-600">
              Showing {filteredContacts.length} of {contacts.length} contacts
              {searchTerm && ` matching "${searchTerm}"`}
            </div>
            <button
              on:click={handleClearFilters}
              class="text-sm text-gray-600 hover:text-gray-900"
            >
              Clear all filters
            </button>
          </div>
        </div>

    <!-- Bulk Operations -->
    {#if $selectedCount > 0}
      <div class="mb-6">
        <BulkOperations
          selectedCount={$selectedCount}
          on:bulkAction={handleBulkAction}
        />
      </div>
    {/if}

    <!-- Error Message -->
    {#if error}
      <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
        <div class="flex">
          <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error loading contacts</h3>
            <p class="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Content -->
    {#if viewMode === 'grid'}
      <!-- Grid View -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {#each $paginatedContacts as contact}
          <ContactCard
            {contact}
            selected={selectedContacts.has(contact.id.toString())}
            on:viewDetails={handleViewDetails}
            on:edit={handleEdit}
            on:delete={handleDelete}
          />
        {/each}
      </div>
    {:else}
      <!-- Table View -->
      <ContactTable
        contacts={$paginatedContacts}
        selectedContacts={selectedContacts}
        {isLoading}
        on:sort={handleSort}
        on:viewDetails={handleViewDetails}
        on:edit={handleEdit}
        on:delete={handleDelete}
      />
    {/if}

    <!-- Pagination -->
    {#if $totalPages > 1}
      <div class="mt-6 flex items-center justify-between">
        <div class="text-sm text-gray-700">
          Page {currentPage} of {$totalPages}
        </div>
        
        <div class="flex space-x-2">
          <button
            on:click={() => goToPage(currentPage - 1)}
            disabled={!$hasPrevPage}
            class="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <button
            on:click={() => goToPage(currentPage + 1)}
            disabled={!$hasNextPage}
            class="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- Contact Detail Modal -->
{#if showDetailModal && selectedContact}
  <ContactDetailModal
    contact={selectedContact}
    isOpen={showDetailModal}
    on:close={() => (showDetailModal = false)}
    on:contactUpdated={handleContactUpdated}
    on:edit={handleEdit}
  />
{/if}