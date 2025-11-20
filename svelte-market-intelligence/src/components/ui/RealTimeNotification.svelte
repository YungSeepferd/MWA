<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { realTimeService, contactUpdates, isConnected } from '$lib/services/websocket';
  
  let isVisible = false;
  let currentUpdate = null;
  let notificationTimeout;
  
  // Subscribe to contact updates
  let updates = [];
  let connected = false;
  
  const unsubscribeUpdates = contactUpdates.subscribe(value => {
    updates = value;
    // Show notification for new updates
    if (value.length > 0 && value[0] !== currentUpdate) {
      showNotification(value[0]);
    }
  });
  
  const unsubscribeConnected = isConnected.subscribe(value => {
    connected = value;
  });
  
  function showNotification(update) {
    currentUpdate = update;
    isVisible = true;
    
    // Auto-hide after 5 seconds
    clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(() => {
      isVisible = false;
    }, 5000);
  }
  
  function hideNotification() {
    isVisible = false;
    clearTimeout(notificationTimeout);
  }
  
  function getNotificationIcon(type) {
    switch (type) {
      case 'contact_created':
        return '👤';
      case 'contact_updated':
        return '✏️';
      case 'contact_deleted':
        return '🗑️';
      case 'contact_approved':
        return '✅';
      case 'contact_rejected':
        return '❌';
      default:
        return '📢';
    }
  }
  
  function getNotificationColor(type) {
    switch (type) {
      case 'contact_created':
        return 'bg-success-100 border-success-200 text-success-800';
      case 'contact_updated':
        return 'bg-warning-100 border-warning-200 text-warning-800';
      case 'contact_deleted':
        return 'bg-error-100 border-error-200 text-error-800';
      case 'contact_approved':
        return 'bg-success-100 border-success-200 text-success-800';
      case 'contact_rejected':
        return 'bg-error-100 border-error-200 text-error-800';
      default:
        return 'bg-primary-100 border-primary-200 text-primary-800';
    }
  }
  
  function getNotificationTitle(type) {
    switch (type) {
      case 'contact_created':
        return 'New Contact';
      case 'contact_updated':
        return 'Contact Updated';
      case 'contact_deleted':
        return 'Contact Deleted';
      case 'contact_approved':
        return 'Contact Approved';
      case 'contact_rejected':
        return 'Contact Rejected';
      default:
        return 'System Update';
    }
  }
  
  onDestroy(() => {
    unsubscribeUpdates();
    unsubscribeConnected();
    clearTimeout(notificationTimeout);
  });
</script>

<div class="real-time-notification">
  <!-- Connection Status Indicator -->
  <div class="connection-status">
    <div class={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
      <span class="status-dot"></span>
      <span class="status-text">
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  </div>
  
  <!-- Notification -->
  {#if isVisible && currentUpdate}
    <div class={`notification ${getNotificationColor(currentUpdate.type)}`}>
      <div class="notification-content">
        <div class="notification-icon">
          {getNotificationIcon(currentUpdate.type)}
        </div>
        <div class="notification-body">
          <div class="notification-title">
            {getNotificationTitle(currentUpdate.type)}
          </div>
          <div class="notification-message">
            {#if currentUpdate.data?.contact?.name}
              {currentUpdate.data.contact.name}
            {:else if currentUpdate.data?.contact_id}
              Contact ID: {currentUpdate.data.contact_id}
            {:else}
              System update received
            {/if}
          </div>
          <div class="notification-time">
            {new Date(currentUpdate.timestamp).toLocaleTimeString()}
          </div>
        </div>
        <button
          on:click={hideNotification}
          class="notification-close"
          aria-label="Close notification"
        >
          ✕
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .real-time-notification {
    position: fixed;
    top: var(--space-4);
    right: var(--space-4);
    z-index: 1001;
    max-width: 300px;
  }
  
  .connection-status {
    margin-bottom: var(--space-2);
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: 500;
  }
  
  .status-indicator.connected {
    background: var(--success-100);
    color: var(--success-800);
    border: 1px solid var(--success-200);
  }
  
  .status-indicator.disconnected {
    background: var(--error-100);
    color: var(--error-800);
    border: 1px solid var(--error-200);
  }
  
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }
  
  .status-indicator.connected .status-dot {
    background: var(--success-500);
  }
  
  .status-indicator.disconnected .status-dot {
    background: var(--error-500);
  }
  
  .notification {
    border: 1px solid;
    border-radius: var(--radius-lg);
    padding: var(--space-3);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    animation: slideIn 0.3s ease-out;
  }
  
  .notification-content {
    display: flex;
    align-items: flex-start;
    gap: var(--space-3);
  }
  
  .notification-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
  }
  
  .notification-body {
    flex: 1;
    min-width: 0;
  }
  
  .notification-title {
    font-weight: 600;
    font-size: var(--font-size-sm);
    margin-bottom: var(--space-1);
  }
  
  .notification-message {
    font-size: var(--font-size-sm);
    color: inherit;
    opacity: 0.9;
    margin-bottom: var(--space-1);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .notification-time {
    font-size: var(--font-size-xs);
    opacity: 0.7;
  }
  
  .notification-close {
    background: none;
    border: none;
    font-size: var(--font-size-sm);
    cursor: pointer;
    opacity: 0.7;
    padding: var(--space-1);
    border-radius: var(--radius-sm);
  }
  
  .notification-close:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.1);
  }
  
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  /* Mobile responsive */
  @media (max-width: 768px) {
    .real-time-notification {
      top: var(--space-2);
      right: var(--space-2);
      left: var(--space-2);
      max-width: none;
    }
    
    .notification {
      padding: var(--space-2);
    }
  }
</style>