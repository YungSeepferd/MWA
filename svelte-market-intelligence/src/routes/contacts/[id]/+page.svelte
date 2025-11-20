<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import LoadingSkeleton from '../../components/ui/LoadingSkeleton.svelte';
  import MobileNav from '../../../components/layout/MobileNav.svelte';
  import ScoringChart from '../../../components/visualization/ScoringChart.svelte';
  
  // Get data from load function
  export let data;
  
  let isLoading = false;
  
  // Navigate back to contact list
  function goBack() {
    goto('/contacts');
  }
  
  // Handle contact approval
  async function approveContact() {
    isLoading = true;
    try {
      // TODO: Implement approval API call
      console.log('Approving contact:', data.contact.id);
      // await apiClient.approveContact(data.contact.id);
    } catch (error) {
      console.error('Error approving contact:', error);
    } finally {
      isLoading = false;
    }
  }
  
  // Handle contact rejection
  async function rejectContact() {
    isLoading = true;
    try {
      // TODO: Implement rejection API call
      console.log('Rejecting contact:', data.contact.id);
      // await apiClient.rejectContact(data.contact.id);
    } catch (error) {
      console.error('Error rejecting contact:', error);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="min-h-screen bg-gray-50 pb-20">
  <div class="container mx-auto px-4 py-6">
    <!-- Header with back button -->
    <header class="mb-6">
      <div class="flex items-center gap-4 mb-2">
        <button on:click={goBack} class="btn btn-secondary">
          ← Back to Contacts
        </button>
        <h1 class="text-2xl font-bold text-gray-900">Contact Details</h1>
      </div>
    </header>

    {#if isLoading}
      <!-- Loading state -->
      <div class="space-y-6">
        <LoadingSkeleton type="card" height="200px" />
        <LoadingSkeleton type="card" height="150px" />
        <LoadingSkeleton type="card" height="120px" />
      </div>
    {:else if data?.contact}
      <!-- Contact Information -->
      <div class="grid gap-6">
        <!-- Basic Contact Info -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Contact Information</h2>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <h3 class="font-medium text-gray-900">{data.contact.name}</h3>
              {#if data.contact.position}
                <p class="text-gray-600">{data.contact.position}</p>
              {/if}
              {#if data.contact.company_name}
                <p class="text-gray-600">{data.contact.company_name}</p>
              {/if}
            </div>
            
            <div class="space-y-2">
              {#if data.contact.email}
                <div>
                  <span class="text-sm font-medium text-gray-500">Email:</span>
                  <p class="text-gray-900">{data.contact.email}</p>
                </div>
              {/if}
              {#if data.contact.phone}
                <div>
                  <span class="text-sm font-medium text-gray-500">Phone:</span>
                  <p class="text-gray-900">{data.contact.phone}</p>
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Market Intelligence -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Market Intelligence</h2>
          
          <!-- Agency Type and Scoring -->
          <div class="grid gap-4 md:grid-cols-2 mb-4">
            {#if data.contact.agency_type}
              <div>
                <span class="text-sm font-medium text-gray-500">Agency Type:</span>
                <div class="mt-1">
                  <span class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm capitalize">
                    {data.contact.agency_type.replace('_', ' ')}
                  </span>
                </div>
              </div>
            {/if}
            
            {#if data.contact.confidence_score}
              <div>
                <span class="text-sm font-medium text-gray-500">Confidence Score:</span>
                <div class="mt-1 flex items-center gap-2">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      class="bg-success-500 h-2 rounded-full transition-all duration-300"
                      style={`width: ${data.contact.confidence_score * 100}%`}
                    ></div>
                  </div>
                  <span class="text-sm font-medium text-gray-900">
                    {Math.round(data.contact.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            {/if}
          </div>

          <!-- Market Areas -->
          {#if data.contact.market_areas?.length > 0}
            <div class="mb-4">
              <span class="text-sm font-medium text-gray-500">Market Areas:</span>
              <div class="mt-2 flex flex-wrap gap-2">
                {#each data.contact.market_areas as area}
                  <span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {area.name}
                    {#if area.relevance_score}
                      <span class="text-xs text-gray-500 ml-1">
                        ({Math.round(area.relevance_score * 100)}%)
                      </span>
                    {/if}
                  </span>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Business Context -->
          {#if data.contact.business_context}
            <div>
              <span class="text-sm font-medium text-gray-500">Business Context:</span>
              <div class="mt-2 grid gap-2 md:grid-cols-2">
                {#if data.contact.business_context.company_size}
                  <div>
                    <span class="text-xs text-gray-500">Company Size:</span>
                    <p class="text-sm capitalize">{data.contact.business_context.company_size}</p>
                  </div>
                {/if}
                {#if data.contact.business_context.portfolio_size}
                  <div>
                    <span class="text-xs text-gray-500">Portfolio Size:</span>
                    <p class="text-sm">{data.contact.business_context.portfolio_size} properties</p>
                  </div>
                {/if}
                {#if data.contact.business_context.specialization}
                  <div>
                    <span class="text-xs text-gray-500">Specialization:</span>
                    <p class="text-sm">{data.contact.business_context.specialization}</p>
                  </div>
                {/if}
                {#if data.contact.business_context.years_in_business}
                  <div>
                    <span class="text-xs text-gray-500">Years in Business:</span>
                    <p class="text-sm">{data.contact.business_context.years_in_business} years</p>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>

        <!-- Scoring Breakdown -->
        {#if data.scoring}
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Scoring Breakdown</h2>
            <div class="grid gap-6 md:grid-cols-2">
              <!-- Chart Visualization -->
              <div class="flex justify-center">
                <ScoringChart
                  scores={data.scoring.breakdown}
                  overallScore={data.scoring.overall_score}
                  size="medium"
                  showLabels={true}
                  showValues={true}
                />
              </div>
              
              <!-- Detailed Breakdown -->
              <div class="space-y-3">
                {#each Object.entries(data.scoring.breakdown) as [category, score]}
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-700 capitalize">
                      {category.replace('_', ' ')}:
                    </span>
                    <div class="flex items-center gap-2">
                      <div class="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          class="bg-primary-500 h-2 rounded-full"
                          style={`width: ${score * 100}%`}
                        ></div>
                      </div>
                      <span class="text-sm font-medium text-gray-900 w-8">
                        {Math.round(score * 100)}%
                      </span>
                    </div>
                  </div>
                {/each}
                
                <!-- Overall Score -->
                <div class="pt-3 border-t border-gray-200">
                  <div class="flex items-center justify-between">
                    <span class="text-lg font-semibold text-gray-900">Overall Score:</span>
                    <span class="text-lg font-bold text-primary-600">
                      {Math.round(data.scoring.overall_score * 100)}%
                    </span>
                  </div>
                </div>
                
                <!-- Recommendations -->
                {#if data.scoring.recommendations?.length > 0}
                  <div class="pt-3 border-t border-gray-200">
                    <h3 class="text-sm font-medium text-gray-700 mb-2">Recommendations:</h3>
                    <ul class="space-y-1">
                      {#each data.scoring.recommendations as recommendation}
                        <li class="text-sm text-gray-600 flex items-start gap-2">
                          <span class="text-primary-500 mt-1">•</span>
                          {recommendation}
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <!-- Outreach History -->
        {#if data.contact.outreach_history?.length > 0}
          <div class="card">
            <h2 class="text-xl font-semibold mb-4">Outreach History</h2>
            <div class="space-y-3">
              {#each data.contact.outreach_history as outreach}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span class="font-medium text-gray-900 capitalize">
                      {outreach.method.replace('_', ' ')}
                    </span>
                    <span class="text-sm text-gray-500 ml-2">
                      {new Date(outreach.date).toLocaleDateString()}
                    </span>
                  </div>
                  <span class={`px-2 py-1 text-xs rounded-full capitalize ${
                    outreach.outcome === 'successful' ? 'bg-success-100 text-success-800' :
                    outreach.outcome === 'no_response' ? 'bg-warning-100 text-warning-800' :
                    'bg-error-100 text-error-800'
                  }`}>
                    {outreach.outcome.replace('_', ' ')}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Action Buttons -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Actions</h2>
          <div class="flex gap-3">
            <button on:click={approveContact} class="btn btn-primary flex-1">
              Approve Contact
            </button>
            <button on:click={rejectContact} class="btn btn-secondary flex-1">
              Reject Contact
            </button>
          </div>
        </div>
      </div>
    {:else}
      <!-- Error state -->
      <div class="card text-center py-12">
        <div class="text-6xl mb-4">❌</div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Contact not found</h3>
        <p class="text-gray-600 mb-4">The contact you're looking for doesn't exist.</p>
        <button on:click={goBack} class="btn btn-primary">Back to Contacts</button>
      </div>
    {/if}
  </div>

  <!-- Mobile Navigation -->
  <MobileNav />
</div>

<style>
  .bg-gray-50 { background: var(--gray-50); }
  .bg-primary-100 { background: var(--primary-100); }
  .bg-gray-100 { background: var(--gray-100); }
  .bg-gray-200 { background: var(--gray-200); }
  .bg-primary-500 { background: var(--primary-500); }
  .bg-success-500 { background: var(--success-500); }
  .bg-warning-100 { background: var(--warning-100); }
  .bg-error-100 { background: var(--error-100); }
  .bg-success-100 { background: color-mix(in srgb, var(--success-500) 20%, transparent); }
  
  .text-gray-900 { color: var(--gray-900); }
  .text-gray-600 { color: var(--gray-600); }
  .text-gray-500 { color: var(--gray-500); }
  .text-gray-700 { color: var(--gray-700); }
  .text-primary-800 { color: var(--primary-800); }
  .text-primary-600 { color: var(--primary-600); }
  .text-success-800 { color: var(--success-800); }
  .text-warning-800 { color: var(--warning-800); }
  .text-error-800 { color: var(--error-800); }
  
  .text-2xl { font-size: var(--font-size-2xl); }
  .text-xl { font-size: var(--font-size-xl); }
  .text-lg { font-size: var(--font-size-lg); }
  .text-sm { font-size: var(--font-size-sm); }
  .text-xs { font-size: var(--font-size-xs); }
  .text-6xl { font-size: 3.75rem; }
  
  .font-bold { font-weight: 600; }
  .font-semibold { font-weight: 500; }
  .font-medium { font-weight: 500; }
  
  .mb-2 { margin-bottom: var(--space-2); }
  .mb-4 { margin-bottom: var(--space-4); }
  .mb-6 { margin-bottom: var(--space-6); }
  
  .py-6 { padding-top: var(--space-6); padding-bottom: var(--space-6); }
  .py-12 { padding-top: 3rem; padding-bottom: 3rem; }
  .px-4 { padding-left: var(--space-4); padding-right: var(--space-4); }
  .p-3 { padding: var(--space-3); }
  .p-4 { padding: var(--space-4); }
  
  .pb-20 { padding-bottom: 5rem; }
  
  .rounded-lg { border-radius: var(--radius-lg); }
  .rounded-full { border-radius: 9999px; }
  
  .space-y-2 > * + * { margin-top: var(--space-2); }
  .space-y-3 > * + * { margin-top: var(--space-3); }
  .gap-2 { gap: var(--space-2); }
  .gap-3 { gap: var(--space-3); }
  .gap-4 { gap: var(--space-4); }
  .gap-6 { gap: var(--space-6); }
  
  .flex { display: flex; }
  .flex-col { flex-direction: column; }
  .flex-1 { flex: 1; }
  .flex-wrap { flex-wrap: wrap; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .justify-center { justify-content: center; }
  
  .w-full { width: 100%; }
  .w-20 { width: 5rem; }
  .w-8 { width: 2rem; }
  
  .h-2 { height: 0.5rem; }
  
  .text-center { text-align: center; }
  
  .min-h-screen { min-height: 100vh; }
  
  .container {
    width: 100%;
    margin: 0 auto;
    padding: 0 var(--space-4);
  }
  
  .mx-auto { margin-left: auto; margin-right: auto; }
  
  .grid { display: grid; }
  .grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  
  .border-t { border-top-width: 1px; }
  .border-gray-200 { border-color: var(--gray-200); }
  
  .ml-1 { margin-left: var(--space-1); }
  .ml-2 { margin-left: var(--space-2); }
  
  .pt-3 { padding-top: var(--space-3); }
  
  .transition-all { transition-property: all; }
  .duration-300 { transition-duration: 300ms; }
  
  .capitalize { text-transform: capitalize; }
  
  @media (min-width: 768px) {
    .md\:grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  }
</style>