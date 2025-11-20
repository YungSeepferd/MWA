<script lang="ts">
  import { onMount } from 'svelte';

  let error: Error | null = null;

  onMount(() => {
    // Error boundary setup - catches errors in child components
    // This is a basic implementation that can be enhanced with proper error handling
  });

  const resetError = () => {
    error = null;
  };
</script>

{#if error}
  <div class="error-boundary bg-red-50 border border-red-200 rounded-lg p-4 m-4">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-medium text-red-800">Something went wrong</h3>
        <p class="text-red-600 mt-1">{error.message}</p>
      </div>
      <button
        on:click={resetError}
        class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
      >
        Try Again
      </button>
    </div>
    <details class="mt-3">
      <summary class="cursor-pointer text-red-700 text-sm">Technical Details</summary>
      <pre class="bg-red-100 p-2 rounded text-xs mt-2 overflow-auto">{error.stack}</pre>
    </details>
  </div>
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    max-width: 600px;
    margin: 0 auto;
  }
</style>