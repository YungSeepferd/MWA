<script lang="ts">
  export let type: 'spinner' | 'skeleton' | 'progress' = 'spinner';
  export let message: string = 'Loading...';
  export let progress: number = 0;
  export let size: 'small' | 'medium' | 'large' = 'medium';
</script>

<div class="loading-state {type} {size}">
  {#if type === 'spinner'}
    <div class="spinner">
      <div class="spinner-circle"></div>
    </div>
    <p class="loading-message">{message}</p>
  {:else if type === 'progress'}
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
      </div>
      <p class="loading-message">{message} ({progress}%)</p>
    </div>
  {:else if type === 'skeleton'}
    <div class="skeleton-container">
      <div class="skeleton-line skeleton-title"></div>
      <div class="skeleton-line skeleton-text"></div>
      <div class="skeleton-line skeleton-text"></div>
      <div class="skeleton-line skeleton-short"></div>
    </div>
  {/if}
</div>

<style>
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
  }

  .loading-state.small {
    padding: 1rem;
  }

  .loading-state.large {
    padding: 3rem;
  }

  /* Spinner styles */
  .spinner {
    display: inline-block;
    position: relative;
  }

  .spinner-circle {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f4f6;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-state.small .spinner-circle {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }

  .loading-state.large .spinner-circle {
    width: 60px;
    height: 60px;
    border-width: 6px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Progress bar styles */
  .progress-container {
    width: 100%;
    max-width: 300px;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: #f3f4f6;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 1rem;
  }

  .progress-fill {
    height: 100%;
    background: #3b82f6;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .loading-state.small .progress-bar {
    height: 4px;
  }

  .loading-state.large .progress-bar {
    height: 12px;
  }

  /* Skeleton styles */
  .skeleton-container {
    width: 100%;
    max-width: 400px;
  }

  .skeleton-line {
    height: 16px;
    background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
    background-size: 200% 100%;
    border-radius: 4px;
    margin-bottom: 1rem;
    animation: skeleton-loading 1.5s infinite;
  }

  .skeleton-title {
    height: 24px;
    width: 60%;
  }

  .skeleton-text {
    width: 100%;
  }

  .skeleton-short {
    width: 40%;
  }

  .loading-state.small .skeleton-line {
    height: 12px;
  }

  .loading-state.small .skeleton-title {
    height: 18px;
  }

  .loading-state.large .skeleton-line {
    height: 20px;
  }

  .loading-state.large .skeleton-title {
    height: 28px;
  }

  @keyframes skeleton-loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }

  /* Message styles */
  .loading-message {
    margin-top: 1rem;
    color: #6b7280;
    font-size: 0.875rem;
  }

  .loading-state.small .loading-message {
    font-size: 0.75rem;
    margin-top: 0.5rem;
  }

  .loading-state.large .loading-message {
    font-size: 1rem;
    margin-top: 1.5rem;
  }

  /* Mobile responsive */
  @media (max-width: 640px) {
    .loading-state {
      padding: 1rem;
    }

    .progress-container {
      max-width: 250px;
    }

    .skeleton-container {
      max-width: 300px;
    }
  }
</style>