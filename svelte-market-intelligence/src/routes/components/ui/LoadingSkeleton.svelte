<script lang="ts">
  export let type: 'card' | 'text' | 'circle' | 'line' = 'card';
  export let height = 'auto';
  export let width = '100%';
  export let count = 1;
</script>

{#if type === 'card'}
  <div class="loading-skeleton-card bg-gray-200 rounded-lg animate-pulse" style={`height: ${height}; width: ${width};`}>
    <div class="p-4">
      <div class="h-4 bg-gray-300 rounded mb-3 w-3/4"></div>
      <div class="h-3 bg-gray-300 rounded mb-2 w-1/2"></div>
      <div class="h-3 bg-gray-300 rounded w-2/3"></div>
    </div>
  </div>
{:else if type === 'text'}
  <div class="loading-skeleton-text space-y-2" style={`width: ${width};`}>
    {#each Array(count) as _, i}
      <div class="h-4 bg-gray-200 rounded animate-pulse" style={`width: ${i % 2 === 0 ? '100%' : '80%'};`}></div>
    {/each}
  </div>
{:else if type === 'circle'}
  <div class="loading-skeleton-circle bg-gray-200 rounded-full animate-pulse" style={`height: ${height}; width: ${width};`}></div>
{:else if type === 'line'}
  <div class="loading-skeleton-line bg-gray-200 rounded animate-pulse" style={`height: ${height}; width: ${width};`}></div>
{/if}

<style>
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .loading-skeleton-card {
    min-height: 80px;
  }

  .loading-skeleton-text {
    min-height: 20px;
  }

  .loading-skeleton-circle {
    min-height: 40px;
    min-width: 40px;
  }

  .loading-skeleton-line {
    min-height: 16px;
  }
</style>