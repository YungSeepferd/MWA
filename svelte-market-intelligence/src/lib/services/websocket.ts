import { wsService } from './api';
import { writable } from 'svelte/store';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface RealTimeUpdate {
  type: 'contact_created' | 'contact_updated' | 'contact_deleted' | 'contact_approved' | 'contact_rejected';
  data: any;
  timestamp: string;
}

export interface SystemStatus {
  crawler: {
    status: 'running' | 'stopped' | 'error';
    lastRun: string;
    nextRun: string;
  };
  database: {
    status: 'healthy' | 'degraded' | 'error';
    size: number;
    connections: number;
  };
  notifications: {
    status: 'active' | 'paused' | 'error';
    sentToday: number;
  };
  uptime: string;
  timestamp: string;
}

export interface DashboardStats {
  total_contacts: number;
  approved_contacts: number;
  pending_contacts: number;
  rejected_contacts: number;
  average_confidence_score: number;
  average_quality_score: number;
  outreach_success_rate: number;
  contacts_by_status: Record<string, number>;
  top_sources: Array<{ source: string; count: number }>;
  monthly_trends: Array<{
    month: string;
    contacts_added: number;
    contacts_approved: number;
    average_score: number;
  }>;
  timestamp: string;
}

export interface ScraperStatus {
  status: 'running' | 'stopped' | 'error' | 'paused';
  current_job?: {
    provider: string;
    status: string;
    progress: number;
    estimated_completion?: string;
  };
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  timestamp: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  request_rate: number;
  error_rate: number;
  timestamp: string;
}

export interface ContactDiscoveryUpdate {
  new_contacts: number;
  source: string;
  confidence: 'high' | 'medium' | 'low';
  timestamp: string;
}

export interface SearchStatusUpdate {
  search_id: string;
  status: 'running' | 'completed' | 'error' | 'paused';
  results_count: number;
  progress: number;
  estimated_completion?: string;
  timestamp: string;
}

export interface JobProgressUpdate {
  job_id: string;
  job_type: string;
  status: string;
  progress: number;
  current_step: number;
  total_steps: number;
  estimated_completion?: string;
  results?: Record<string, any>;
  error?: string;
  timestamp: string;
}

class RealTimeService {
  private isConnected = writable(false);
  private messages = writable<WebSocketMessage[]>([]);
  private contactUpdates = writable<RealTimeUpdate[]>([]);
  private systemStatus = writable<SystemStatus>({
    crawler: { status: 'stopped', lastRun: '', nextRun: '' },
    database: { status: 'healthy', size: 0, connections: 0 },
    notifications: { status: 'active', sentToday: 0 },
    uptime: '',
    timestamp: ''
  });
  
  // New real-time stores
  private dashboardStats = writable<DashboardStats>({
    total_contacts: 0,
    approved_contacts: 0,
    pending_contacts: 0,
    rejected_contacts: 0,
    average_confidence_score: 0,
    average_quality_score: 0,
    outreach_success_rate: 0,
    contacts_by_status: {},
    top_sources: [],
    monthly_trends: [],
    timestamp: ''
  });
  
  private scraperStatus = writable<ScraperStatus>({
    status: 'stopped',
    active_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    timestamp: ''
  });
  
  private systemMetrics = writable<SystemMetrics>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    active_connections: 0,
    request_rate: 0,
    error_rate: 0,
    timestamp: ''
  });
  
  private contactDiscoveryUpdates = writable<ContactDiscoveryUpdate[]>([]);
  private searchStatusUpdates = writable<SearchStatusUpdate[]>([]);
  private jobProgressUpdates = writable<JobProgressUpdate[]>([]);
  
  constructor() {
    this.initialize();
  }
  
  private async initialize() {
    try {
      await wsService.connect();
      this.setupEventListeners();
      this.isConnected.set(true);
      console.log('WebSocket connected successfully');
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.isConnected.set(false);
    }
  }
  
  private setupEventListeners() {
    // Contact events
    wsService.on('contact_created', this.handleContactCreated.bind(this));
    wsService.on('contact_updated', this.handleContactUpdated.bind(this));
    wsService.on('contact_deleted', this.handleContactDeleted.bind(this));
    wsService.on('contact_approved', this.handleContactApproved.bind(this));
    wsService.on('contact_rejected', this.handleContactRejected.bind(this));
    
    // Analytics updates
    wsService.on('analytics_updated', this.handleAnalyticsUpdated.bind(this));
    
    // System notifications
    wsService.on('system_notification', this.handleSystemNotification.bind(this));
    
    // System status updates
    wsService.on('system_status', this.handleSystemStatus.bind(this));
    
    // New real-time event listeners
    wsService.on('dashboard_update', this.handleDashboardUpdate.bind(this));
    wsService.on('scraper_update', this.handleScraperUpdate.bind(this));
    wsService.on('contact_discovery', this.handleContactDiscovery.bind(this));
    wsService.on('search_status', this.handleSearchStatus.bind(this));
    wsService.on('job_progress', this.handleJobProgress.bind(this));
    wsService.on('system_metrics', this.handleSystemMetrics.bind(this));
  }
  
  private handleContactCreated(data: any) {
    console.log('Contact created:', data);
    this.addMessage({
      type: 'contact_created',
      data,
      timestamp: new Date().toISOString()
    });
    
    // Update contact updates store
    this.contactUpdates.update(updates => [
      {
        type: 'contact_created',
        data,
        timestamp: new Date().toISOString()
      },
      ...updates.slice(0, 9) // Keep only last 10 updates
    ]);
  }
  
  private handleContactUpdated(data: any) {
    console.log('Contact updated:', data);
    this.addMessage({
      type: 'contact_updated',
      data,
      timestamp: new Date().toISOString()
    });
    
    this.contactUpdates.update(updates => [
      {
        type: 'contact_updated',
        data,
        timestamp: new Date().toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  
  private handleContactDeleted(data: any) {
    console.log('Contact deleted:', data);
    this.addMessage({
      type: 'contact_deleted',
      data,
      timestamp: new Date().toISOString()
    });
    
    this.contactUpdates.update(updates => [
      {
        type: 'contact_deleted',
        data,
        timestamp: new Date().toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  
  private handleContactApproved(data: any) {
    console.log('Contact approved:', data);
    this.addMessage({
      type: 'contact_approved',
      data,
      timestamp: new Date().toISOString()
    });
    
    this.contactUpdates.update(updates => [
      {
        type: 'contact_approved',
        data,
        timestamp: new Date().toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  
  private handleContactRejected(data: any) {
    console.log('Contact rejected:', data);
    this.addMessage({
      type: 'contact_rejected',
      data,
      timestamp: new Date().toISOString()
    });
    
    this.contactUpdates.update(updates => [
      {
        type: 'contact_rejected',
        data,
        timestamp: new Date().toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  
  private handleAnalyticsUpdated(data: any) {
    console.log('Analytics updated:', data);
    this.addMessage({
      type: 'analytics_updated',
      data,
      timestamp: new Date().toISOString()
    });
    
    // Emit custom event for analytics updates
    window.dispatchEvent(new CustomEvent('analytics-update', { detail: data }));
  }
  
  private handleSystemNotification(data: any) {
    console.log('System notification:', data);
    this.addMessage({
      type: 'system_notification',
      data,
      timestamp: new Date().toISOString()
    });
    
    // Show browser notification if permitted
    if (Notification.permission === 'granted') {
      new Notification(data.title || 'System Notification', {
        body: data.message,
        icon: '/favicon.ico'
      });
    }
  }
  
  private handleSystemStatus(data: any) {
    console.log('System status updated:', data);
    this.systemStatus.set({
      ...data,
      timestamp: new Date().toISOString()
    });
  }
  
  // New real-time event handlers
  private handleDashboardUpdate(data: any) {
    console.log('Dashboard update received:', data);
    this.dashboardStats.set({
      ...data,
      timestamp: new Date().toISOString()
    });
    
    // Emit custom event for dashboard updates
    window.dispatchEvent(new CustomEvent('dashboard-update', { detail: data }));
  }
  
  private handleScraperUpdate(data: any) {
    console.log('Scraper update received:', data);
    this.scraperStatus.set({
      ...data,
      timestamp: new Date().toISOString()
    });
    
    // Show notification for scraper status changes
    if (data.status === 'running' || data.status === 'error') {
      this.showNotification(`Scraper status: ${data.status}`, data.status === 'error' ? 'error' : 'info');
    }
  }
  
  private handleContactDiscovery(data: any) {
    console.log('Contact discovery update:', data);
    
    const update: ContactDiscoveryUpdate = {
      new_contacts: data.new_contacts || 0,
      source: data.source || 'unknown',
      confidence: data.confidence || 'medium',
      timestamp: new Date().toISOString()
    };
    
    // Add to contact discovery updates
    this.contactDiscoveryUpdates.update(updates => [update, ...updates.slice(0, 9)]);
    
    // Show notification
    this.showNotification(`New ${update.new_contacts} contacts discovered from ${update.source}`, 'info');
  }
  
  private handleSearchStatus(data: any) {
    console.log('Search status update:', data);
    
    const update: SearchStatusUpdate = {
      search_id: data.search_id,
      status: data.status || 'running',
      results_count: data.results_count || 0,
      progress: data.progress || 0,
      estimated_completion: data.estimated_completion,
      timestamp: new Date().toISOString()
    };
    
    // Add to search status updates
    this.searchStatusUpdates.update(updates => [update, ...updates.slice(0, 9)]);
    
    // Show notification for completed searches
    if (update.status === 'completed') {
      this.showNotification(`Search completed: ${update.results_count} results`, 'success');
    }
  }
  
  private handleJobProgress(data: any) {
    console.log('Job progress update:', data);
    
    const update: JobProgressUpdate = {
      job_id: data.job_id,
      job_type: data.job_type,
      status: data.status,
      progress: data.progress || 0,
      current_step: data.current_step || 0,
      total_steps: data.total_steps || 1,
      estimated_completion: data.estimated_completion,
      results: data.results,
      error: data.error,
      timestamp: new Date().toISOString()
    };
    
    // Add to job progress updates
    this.jobProgressUpdates.update(updates => [update, ...updates.slice(0, 9)]);
    
    // Show notification for completed jobs
    if (update.status === 'completed') {
      this.showNotification(`Job ${update.job_id} completed`, 'success');
    } else if (update.status === 'error') {
      this.showNotification(`Job ${update.job_id} failed: ${update.error}`, 'error');
    }
  }
  
  private handleSystemMetrics(data: any) {
    console.log('System metrics update:', data);
    this.systemMetrics.set({
      ...data,
      timestamp: new Date().toISOString()
    });
    
    // Emit custom event for system metrics updates
    window.dispatchEvent(new CustomEvent('system-metrics-update', { detail: data }));
  }
  
  private showNotification(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
    // Emit custom event for notifications
    window.dispatchEvent(new CustomEvent('system-notification', {
      detail: { message, type, timestamp: new Date().toISOString() }
    }));
    
    // Show browser notification if permitted
    if (Notification.permission === 'granted') {
      new Notification('MWA System Notification', {
        body: message,
        icon: '/favicon.ico'
      });
    }
  }
  
  private addMessage(message: WebSocketMessage) {
    this.messages.update(messages => [message, ...messages]);
  }
  
  // Public methods
  subscribe(callback: (value: boolean) => void) {
    return this.isConnected.subscribe(callback);
  }
  
  subscribeMessages(callback: (value: WebSocketMessage[]) => void) {
    return this.messages.subscribe(callback);
  }
  
  subscribeContactUpdates(callback: (value: RealTimeUpdate[]) => void) {
    return this.contactUpdates.subscribe(callback);
  }
  
  subscribeSystemStatus(callback: (value: SystemStatus) => void) {
    return this.systemStatus.subscribe(callback);
  }
  
  // New subscription methods for real-time stores
  subscribeDashboardStats(callback: (value: DashboardStats) => void) {
    return this.dashboardStats.subscribe(callback);
  }
  
  subscribeScraperStatus(callback: (value: ScraperStatus) => void) {
    return this.scraperStatus.subscribe(callback);
  }
  
  subscribeSystemMetrics(callback: (value: SystemMetrics) => void) {
    return this.systemMetrics.subscribe(callback);
  }
  
  subscribeContactDiscoveryUpdates(callback: (value: ContactDiscoveryUpdate[]) => void) {
    return this.contactDiscoveryUpdates.subscribe(callback);
  }
  
  subscribeSearchStatusUpdates(callback: (value: SearchStatusUpdate[]) => void) {
    return this.searchStatusUpdates.subscribe(callback);
  }
  
  subscribeJobProgressUpdates(callback: (value: JobProgressUpdate[]) => void) {
    return this.jobProgressUpdates.subscribe(callback);
  }
  
  getConnectionStatus() {
    let status = false;
    this.isConnected.subscribe(value => { status = value; })();
    return status;
  }
  
  async reconnect() {
    try {
      await wsService.connect();
      this.isConnected.set(true);
      return true;
    } catch (error) {
      console.error('Reconnection failed:', error);
      this.isConnected.set(false);
      return false;
    }
  }
  
  disconnect() {
    wsService.disconnect();
    this.isConnected.set(false);
  }
  
  // Send message through WebSocket
  sendMessage(type: string, data: any) {
    if (this.getConnectionStatus()) {
      wsService.send({ type, data, timestamp: new Date().toISOString() });
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }
  
  // Request analytics refresh
  refreshAnalytics() {
    this.sendMessage('refresh_analytics', {});
  }
  
  // Request contact list refresh
  refreshContacts() {
    this.sendMessage('refresh_contacts', {});
  }
  
  // Clear message history
  clearMessages() {
    this.messages.set([]);
  }
  
  // Clear contact updates
  clearContactUpdates() {
    this.contactUpdates.set([]);
  }
}

// Create singleton instance
export const realTimeService = new RealTimeService();

// Export stores for Svelte components
export const isConnected = realTimeService.isConnected;
export const messages = realTimeService.messages;
export const contactUpdates = realTimeService.contactUpdates;
export const systemStatus = realTimeService.systemStatus;

// Export new real-time stores
export const dashboardStats = realTimeService.dashboardStats;
export const scraperStatus = realTimeService.scraperStatus;
export const systemMetrics = realTimeService.systemMetrics;
export const contactDiscoveryUpdates = realTimeService.contactDiscoveryUpdates;
export const searchStatusUpdates = realTimeService.searchStatusUpdates;
export const jobProgressUpdates = realTimeService.jobProgressUpdates;

// Browser notification permission
export async function requestNotificationPermission() {
  if ('Notification' in window) {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  return false;
}

// Custom event for real-time updates
export function onAnalyticsUpdate(callback: (data: any) => void) {
  const handler = (event: CustomEvent) => callback(event.detail);
  window.addEventListener('analytics-update', handler as EventListener);
  
  return () => {
    window.removeEventListener('analytics-update', handler as EventListener);
  };
}