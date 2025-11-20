<script lang="ts">
  import { onMount } from 'svelte';
  import { mockDataService } from '$lib/services/mockData';
  import LoadingState from '../components/ui/LoadingState.svelte';
  import { errorHandler } from '$lib/utils/errorHandler';
  
  let isLoading = true;
  let testResults = {
    contacts: null,
    analytics: null,
    scoring: null,
    errors: []
  };
  
  onMount(async () => {
    try {
      // Test contacts API
      const contactsResponse = await mockDataService.getContacts();
      testResults.contacts = contactsResponse;
      
      // Test analytics API
      const analyticsResponse = await mockDataService.getAnalytics();
      testResults.analytics = analyticsResponse;
      
      // Test scoring API
      const scoringResponse = await mockDataService.getContactScoring('1');
      testResults.scoring = scoringResponse;
      
    } catch (error) {
      const appError = errorHandler.handleError(error, 'TestPage');
      testResults.errors.push(appError);
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="test-page">
  <div class="container mx-auto px-4 py-6">
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">API Integration Test</h1>
      <p class="text-gray-600">Testing the Market Intelligence API integration with mock data</p>
    </header>

    {#if isLoading}
      <div class="flex justify-center py-12">
        <LoadingState type="spinner" message="Running API tests..." size="large" />
      </div>
    {:else}
      <div class="space-y-6">
        <!-- Contacts Test -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Contacts API Test</h2>
          {#if testResults.contacts}
            <div class="bg-success-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">✅</span>
                <span class="font-medium">Success</span>
              </div>
              <p class="text-sm text-gray-600 mt-2">
                Retrieved {testResults.contacts.data.contacts.length} contacts
                (Total: {testResults.contacts.data.total_count})
              </p>
              <div class="mt-3 space-y-2">
                {#each testResults.contacts.data.contacts as contact}
                  <div class="flex items-center gap-3 p-2 bg-white rounded">
                    <span class="text-lg">
                      {contact.agency_type === 'property_manager' ? '🏢' :
                       contact.agency_type === 'real_estate_agent' ? '👔' :
                       contact.agency_type === 'landlord' ? '🏠' : '📊'}
                    </span>
                    <div class="flex-1">
                      <div class="text-sm font-medium">{contact.name}</div>
                      <div class="text-xs text-gray-500">{contact.company_name}</div>
                    </div>
                    <div class="text-xs text-gray-400">
                      Score: {Math.round(contact.confidence_score * 100)}%
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {:else}
            <div class="bg-error-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">❌</span>
                <span class="font-medium">Failed</span>
              </div>
            </div>
          {/if}
        </div>

        <!-- Analytics Test -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Analytics API Test</h2>
          {#if testResults.analytics}
            <div class="bg-success-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">✅</span>
                <span class="font-medium">Success</span>
              </div>
              <div class="grid grid-cols-2 gap-4 mt-3">
                <div class="text-center">
                  <div class="text-2xl font-bold">{testResults.analytics.data.total_contacts}</div>
                  <div class="text-sm text-gray-600">Total Contacts</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold">{Math.round(testResults.analytics.data.average_confidence_score * 100)}%</div>
                  <div class="text-sm text-gray-600">Avg Confidence</div>
                </div>
              </div>
            </div>
          {:else}
            <div class="bg-error-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">❌</span>
                <span class="font-medium">Failed</span>
              </div>
            </div>
          {/if}
        </div>

        <!-- Scoring Test -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Scoring API Test</h2>
          {#if testResults.scoring}
            <div class="bg-success-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">✅</span>
                <span class="font-medium">Success</span>
              </div>
              <div class="mt-3">
                <div class="text-center mb-4">
                  <div class="text-3xl font-bold">{Math.round(testResults.scoring.data.overall_score * 100)}%</div>
                  <div class="text-sm text-gray-600">Overall Score</div>
                </div>
                <div class="space-y-2">
                  {#each Object.entries(testResults.scoring.data.breakdown) as [category, data]}
                    <div class="flex justify-between items-center">
                      <span class="text-sm capitalize">{category.replace('_', ' ')}</span>
                      <span class="text-sm font-medium">{Math.round(data.score * 100)}%</span>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          {:else}
            <div class="bg-error-50 p-4 rounded-lg">
              <div class="flex items-center gap-2">
                <span class="text-2xl">❌</span>
                <span class="font-medium">Failed</span>
              </div>
            </div>
          {/if}
        </div>

        <!-- Errors -->
        {#if testResults.errors.length > 0}
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Errors</h2>
            <div class="space-y-3">
              {#each testResults.errors as error}
                <div class="bg-error-50 p-4 rounded-lg">
                  <div class="flex items-center gap-2">
                    <span class="text-2xl">⚠️</span>
                    <span class="font-medium">{error.code}</span>
                  </div>
                  <p class="text-sm text-gray-600 mt-1">{error.message}</p>
                  <p class="text-xs text-gray-500 mt-1">{error.timestamp.toLocaleString()}</p>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Summary -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Test Summary</h2>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-4 bg-primary-50 rounded-lg">
              <div class="text-2xl font-bold text-primary-600">
                {[testResults.contacts, testResults.analytics, testResults.scoring].filter(Boolean).length}
              </div>
              <div class="text-sm text-gray-600">Tests Passed</div>
            </div>
            <div class="p-4 bg-warning-50 rounded-lg">
              <div class="text-2xl font-bold text-warning-600">
                {testResults.errors.length}
              </div>
              <div class="text-sm text-gray-600">Errors</div>
            </div>
            <div class="p-4 bg-success-50 rounded-lg">
              <div class="text-2xl font-bold text-success-600">
                {testResults.errors.length === 0 ? '✅' : '❌'}
              </div>
              <div class="text-sm text-gray-600">Overall Status</div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .test-page {
    min-height: 100vh;
    background: var(--gray-50);
  }
  
  .card {
    background: white;
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }
  
  .bg-success-50 { background: color-mix(in srgb, var(--success-500) 10%, transparent); }
  .bg-error-50 { background: color-mix(in srgb, var(--error-500) 10%, transparent); }
  .bg-warning-50 { background: color-mix(in srgb, var(--warning-500) 10%, transparent); }
  .bg-primary-50 { background: color-mix(in srgb, var(--primary-500) 10%, transparent); }
  
  .text-primary-600 { color: var(--primary-600); }
  .text-success-600 { color: var(--success-600); }
  .text-warning-600 { color: var(--warning-600); }
  
  .text-3xl { font-size: var(--font-size-3xl); }
  .text-2xl { font-size: var(--font-size-2xl); }
  .text-xl { font-size: var(--font-size-xl); }
  .text-sm { font-size: var(--font-size-sm); }
  
  .font-bold { font-weight: 600; }
  .font-semibold { font-weight: 500; }
  
  .mb-2 { margin-bottom: var(--space-2); }
  .mb-4 { margin-bottom: var(--space-4); }
  .mb-8 { margin-bottom: var(--space-8); }
  
  .py-6 { padding-top: var(--space-6); padding-bottom: var(--space-6); }
  .px-4 { padding-left: var(--space-4); padding-right: var(--space-4); }
  
  .space-y-6 > * + * { margin-top: var(--space-6); }
  .gap-4 { gap: var(--space-4); }
  
  .grid { display: grid; }
  .grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
  
  
  .text-center { text-align: center; }
  
  
  .container {
    width: 100%;
    margin: 0 auto;
    padding: 0 var(--space-4);
  }
  
  .mx-auto { margin-left: auto; margin-right: auto; }
</style>