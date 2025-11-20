<script lang="ts">
  export let type: 'spinner' | 'dots' | 'skeleton' = 'spinner';
  export let message = 'Loading...';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-6 w-6',
    large: 'h-8 w-8'
  };
</script>

<div class="loading-state flex flex-col items-center justify-center p-4">
  {#if type === 'spinner'}
    <div class={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}></div>
  {:else if type === 'dots'}
    <div class="flex space-x-1">
      <div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full"></div>
      <div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full" style="animation-delay: 0.1s"></div>
      <div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full" style="animation-delay: 0.2s"></div>
    </div>
  {:else if type === 'skeleton'}
    <div class="space-y-2">
      <div class="animate-pulse bg-gray-200 rounded h-4 w-32"></div>
      <div class="animate-pulse bg-gray-200 rounded h-4 w-24"></div>
    </div>
  {/if}
  
  {#if message}
    <p class="text-sm text-gray-600 mt-2">{message}</p>
  {/if}
</div>

<style>
  .loading-state {
    min-height: 100px;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  .animate-bounce {
    animation: bounce 1s infinite;
  }
  
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>