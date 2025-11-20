<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { errorHandler, type AppError } from '$lib/utils/errorHandler';
  
  export let fallback: (error: AppError) => string = (error) => `
    <div class="error-boundary">
      <div class="error-content">
        <h2>Something went wrong</h2>
        <p>${error.message}</p>
        <button onclick="window.location.reload()">Reload Page</button>
      </div>
    </div>
  `;
  
  let error: AppError | null = null;
  let unsubscribe: () => void;
  
  onMount(() => {
    unsubscribe = errorHandler.subscribe((appError: AppError) => {
      error = appError;
    });
  });
  
  onDestroy(() => {
    if (unsubscribe) {
      unsubscribe();
    }
  });
</script>

{#if error}
  <div class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        {#if error.severity === 'critical'}
          🚨
        {:else if error.severity === 'high'}
          ⚠️
        {:else if error.severity === 'medium'}
          ℹ️
        {:else}
          💡
        {/if}
      </div>
      
      <div class="error-details">
        <h3 class="error-title">
          {error.severity === 'critical' ? 'Critical Error' :
           error.severity === 'high' ? 'High Priority Error' :
           error.severity === 'medium' ? 'Error' : 'Notice'}
        </h3>
        <p class="error-message">{error.message}</p>
        <p class="error-code">Error Code: {error.code}</p>
        <p class="error-time">{error.timestamp.toLocaleString()}</p>
      </div>
      
      <div class="error-actions">
        <button class="btn btn-primary" on:click={() => error = null}>
          Dismiss
        </button>
        <button class="btn btn-secondary" on:click={() => window.location.reload()}>
          Reload Page
        </button>
      </div>
    </div>
  </div>
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }
  
  .error-content {
    background: white;
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    text-align: center;
  }
  
  .error-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .error-details {
    margin-bottom: 1.5rem;
  }
  
  .error-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #1f2937;
  }
  
  .error-message {
    color: #6b7280;
    margin-bottom: 0.5rem;
    line-height: 1.4;
  }
  
  .error-code {
    font-size: 0.875rem;
    color: #9ca3af;
    margin-bottom: 0.25rem;
  }
  
  .error-time {
    font-size: 0.75rem;
    color: #d1d5db;
  }
  
  .error-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background: #3b82f6;
    color: white;
  }
  
  .btn-primary:hover {
    background: #2563eb;
  }
  
  .btn-secondary {
    background: #6b7280;
    color: white;
  }
  
  .btn-secondary:hover {
    background: #4b5563;
  }
  
  /* Mobile responsive */
  @media (max-width: 640px) {
    .error-boundary {
      padding: 0.5rem;
    }
    
    .error-content {
      padding: 1rem;
    }
    
    .error-actions {
      flex-direction: column;
    }
    
    .btn {
      width: 100%;
    }
  }
</style>