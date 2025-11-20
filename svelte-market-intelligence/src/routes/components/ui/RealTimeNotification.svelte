<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { wsService } from '$lib/services/api';
  import type { WebSocketMessage, WebSocketMessageType } from '$lib/types/api';

  let notifications: Array<{ id: number; message: string; type: string; timestamp: Date }> = [];
  let nextId = 1;
  let isConnected = false;

  onMount(async () => {
    try {
      await wsService.connect();
      isConnected = true;
      
      // Listen for real-time updates
      wsService.on('contact_created', handleContactCreated);
      wsService.on('contact_updated', handleContactUpdated);
      wsService.on('contact_deleted', handleContactDeleted);
      wsService.on('analytics_updated', handleAnalyticsUpdated);
      wsService.on('system_notification', handleSystemNotification);
      
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      addNotification('Failed to connect to real-time updates', 'error');
    }
  });

  onDestroy(() => {
    // Clean up WebSocket listeners
    wsService.off('contact_created', handleContactCreated);
    wsService.off('contact_updated', handleContactUpdated);
    wsService.off('contact_deleted', handleContactDeleted);
    wsService.off('analytics_updated', handleAnalyticsUpdated);
    wsService.off('system_notification', handleSystemNotification);
    
    wsService.disconnect();
  });

  const handleContactCreated = (data: any) => {
    addNotification(`New contact created: ${data.name}`, 'success');
  };

  const handleContactUpdated = (data: any) => {
    addNotification(`Contact updated: ${data.name}`, 'info');
  };

  const handleContactDeleted = (data: any) => {
    addNotification(`Contact deleted: ${data.name}`, 'warning');
  };

  const handleAnalyticsUpdated = (data: any) => {
    addNotification('Analytics data updated', 'info');
  };

  const handleSystemNotification = (data: any) => {
    addNotification(data.message, data.type || 'info');
  };

  const addNotification = (message: string, type: string = 'info') => {
    const id = nextId++;
    notifications.push({
      id,
      message,
      type,
      timestamp: new Date()
    });

    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 5000);
  };

  const removeNotification = (id: number) => {
    notifications = notifications.filter(n => n.id !== id);
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-50 border-green-200 text-green-800';
      case 'error': return 'bg-red-50 border-red-200 text-red-800';
      case 'warning': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info': return 'bg-blue-50 border-blue-200 text-blue-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✗';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return '•';
    }
  };
</script>

<div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
  {#each notifications as notification (notification.id)}
    <div 
      class={`p-3 rounded-lg border shadow-sm transition-all duration-300 ${getNotificationColor(notification.type)}`}
      role="alert"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium">{getNotificationIcon(notification.type)}</span>
          <span class="text-sm">{notification.message}</span>
        </div>
        <button
          on:click={() => removeNotification(notification.id)}
          class="text-gray-500 hover:text-gray-700 text-sm"
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
      <div class="text-xs text-gray-600 mt-1">
        {notification.timestamp.toLocaleTimeString('de-DE')}
      </div>
    </div>
  {/each}

  <!-- Connection Status Indicator -->
  <div class={`p-2 rounded-lg border text-xs ${isConnected ? 'bg-green-50 border-green-200 text-green-800' : 'bg-yellow-50 border-yellow-200 text-yellow-800'}`}>
    {isConnected ? '🟢 Connected' : '🟡 Connecting...'}
  </div>
</div>

<style>
  .notification-enter {
    opacity: 0;
    transform: translateX(100%);
  }
  
  .notification-enter-active {
    opacity: 1;
    transform: translateX(0);
    transition: opacity 300ms, transform 300ms;
  }
  
  .notification-exit {
    opacity: 1;
    transform: translateX(0);
  }
  
  .notification-exit-active {
    opacity: 0;
    transform: translateX(100%);
    transition: opacity 300ms, transform 300ms;
  }
</style>