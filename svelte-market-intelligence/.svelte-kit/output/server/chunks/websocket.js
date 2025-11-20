import { w as wsService } from "./api.js";
import { w as writable } from "./index2.js";
class RealTimeService {
  isConnected = writable(false);
  messages = writable([]);
  contactUpdates = writable([]);
  systemStatus = writable({
    crawler: { status: "stopped", lastRun: "", nextRun: "" },
    database: { status: "healthy", size: 0, connections: 0 },
    notifications: { status: "active", sentToday: 0 },
    uptime: "",
    timestamp: ""
  });
  // New real-time stores
  dashboardStats = writable({
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
    timestamp: ""
  });
  scraperStatus = writable({
    status: "stopped",
    active_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    timestamp: ""
  });
  systemMetrics = writable({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    active_connections: 0,
    request_rate: 0,
    error_rate: 0,
    timestamp: ""
  });
  contactDiscoveryUpdates = writable([]);
  searchStatusUpdates = writable([]);
  jobProgressUpdates = writable([]);
  constructor() {
    this.initialize();
  }
  async initialize() {
    try {
      await wsService.connect();
      this.setupEventListeners();
      this.isConnected.set(true);
      console.log("WebSocket connected successfully");
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      this.isConnected.set(false);
    }
  }
  setupEventListeners() {
    wsService.on("contact_created", this.handleContactCreated.bind(this));
    wsService.on("contact_updated", this.handleContactUpdated.bind(this));
    wsService.on("contact_deleted", this.handleContactDeleted.bind(this));
    wsService.on("contact_approved", this.handleContactApproved.bind(this));
    wsService.on("contact_rejected", this.handleContactRejected.bind(this));
    wsService.on("analytics_updated", this.handleAnalyticsUpdated.bind(this));
    wsService.on("system_notification", this.handleSystemNotification.bind(this));
    wsService.on("system_status", this.handleSystemStatus.bind(this));
    wsService.on("dashboard_update", this.handleDashboardUpdate.bind(this));
    wsService.on("scraper_update", this.handleScraperUpdate.bind(this));
    wsService.on("contact_discovery", this.handleContactDiscovery.bind(this));
    wsService.on("search_status", this.handleSearchStatus.bind(this));
    wsService.on("job_progress", this.handleJobProgress.bind(this));
    wsService.on("system_metrics", this.handleSystemMetrics.bind(this));
  }
  handleContactCreated(data) {
    console.log("Contact created:", data);
    this.addMessage({
      type: "contact_created",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.contactUpdates.update((updates) => [
      {
        type: "contact_created",
        data,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      },
      ...updates.slice(0, 9)
      // Keep only last 10 updates
    ]);
  }
  handleContactUpdated(data) {
    console.log("Contact updated:", data);
    this.addMessage({
      type: "contact_updated",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.contactUpdates.update((updates) => [
      {
        type: "contact_updated",
        data,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  handleContactDeleted(data) {
    console.log("Contact deleted:", data);
    this.addMessage({
      type: "contact_deleted",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.contactUpdates.update((updates) => [
      {
        type: "contact_deleted",
        data,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  handleContactApproved(data) {
    console.log("Contact approved:", data);
    this.addMessage({
      type: "contact_approved",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.contactUpdates.update((updates) => [
      {
        type: "contact_approved",
        data,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  handleContactRejected(data) {
    console.log("Contact rejected:", data);
    this.addMessage({
      type: "contact_rejected",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.contactUpdates.update((updates) => [
      {
        type: "contact_rejected",
        data,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      },
      ...updates.slice(0, 9)
    ]);
  }
  handleAnalyticsUpdated(data) {
    console.log("Analytics updated:", data);
    this.addMessage({
      type: "analytics_updated",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    window.dispatchEvent(new CustomEvent("analytics-update", { detail: data }));
  }
  handleSystemNotification(data) {
    console.log("System notification:", data);
    this.addMessage({
      type: "system_notification",
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    if (Notification.permission === "granted") {
      new Notification(data.title || "System Notification", {
        body: data.message,
        icon: "/favicon.ico"
      });
    }
  }
  handleSystemStatus(data) {
    console.log("System status updated:", data);
    this.systemStatus.set({
      ...data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
  }
  // New real-time event handlers
  handleDashboardUpdate(data) {
    console.log("Dashboard update received:", data);
    this.dashboardStats.set({
      ...data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    window.dispatchEvent(new CustomEvent("dashboard-update", { detail: data }));
  }
  handleScraperUpdate(data) {
    console.log("Scraper update received:", data);
    this.scraperStatus.set({
      ...data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    if (data.status === "running" || data.status === "error") {
      this.showNotification(`Scraper status: ${data.status}`, data.status === "error" ? "error" : "info");
    }
  }
  handleContactDiscovery(data) {
    console.log("Contact discovery update:", data);
    const update = {
      new_contacts: data.new_contacts || 0,
      source: data.source || "unknown",
      confidence: data.confidence || "medium",
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    this.contactDiscoveryUpdates.update((updates) => [update, ...updates.slice(0, 9)]);
    this.showNotification(`New ${update.new_contacts} contacts discovered from ${update.source}`, "info");
  }
  handleSearchStatus(data) {
    console.log("Search status update:", data);
    const update = {
      search_id: data.search_id,
      status: data.status || "running",
      results_count: data.results_count || 0,
      progress: data.progress || 0,
      estimated_completion: data.estimated_completion,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    this.searchStatusUpdates.update((updates) => [update, ...updates.slice(0, 9)]);
    if (update.status === "completed") {
      this.showNotification(`Search completed: ${update.results_count} results`, "success");
    }
  }
  handleJobProgress(data) {
    console.log("Job progress update:", data);
    const update = {
      job_id: data.job_id,
      job_type: data.job_type,
      status: data.status,
      progress: data.progress || 0,
      current_step: data.current_step || 0,
      total_steps: data.total_steps || 1,
      estimated_completion: data.estimated_completion,
      results: data.results,
      error: data.error,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    this.jobProgressUpdates.update((updates) => [update, ...updates.slice(0, 9)]);
    if (update.status === "completed") {
      this.showNotification(`Job ${update.job_id} completed`, "success");
    } else if (update.status === "error") {
      this.showNotification(`Job ${update.job_id} failed: ${update.error}`, "error");
    }
  }
  handleSystemMetrics(data) {
    console.log("System metrics update:", data);
    this.systemMetrics.set({
      ...data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    window.dispatchEvent(new CustomEvent("system-metrics-update", { detail: data }));
  }
  showNotification(message, type = "info") {
    window.dispatchEvent(new CustomEvent("system-notification", {
      detail: { message, type, timestamp: (/* @__PURE__ */ new Date()).toISOString() }
    }));
    if (Notification.permission === "granted") {
      new Notification("MWA System Notification", {
        body: message,
        icon: "/favicon.ico"
      });
    }
  }
  addMessage(message) {
    this.messages.update((messages2) => [message, ...messages2]);
  }
  // Public methods
  subscribe(callback) {
    return this.isConnected.subscribe(callback);
  }
  subscribeMessages(callback) {
    return this.messages.subscribe(callback);
  }
  subscribeContactUpdates(callback) {
    return this.contactUpdates.subscribe(callback);
  }
  subscribeSystemStatus(callback) {
    return this.systemStatus.subscribe(callback);
  }
  // New subscription methods for real-time stores
  subscribeDashboardStats(callback) {
    return this.dashboardStats.subscribe(callback);
  }
  subscribeScraperStatus(callback) {
    return this.scraperStatus.subscribe(callback);
  }
  subscribeSystemMetrics(callback) {
    return this.systemMetrics.subscribe(callback);
  }
  subscribeContactDiscoveryUpdates(callback) {
    return this.contactDiscoveryUpdates.subscribe(callback);
  }
  subscribeSearchStatusUpdates(callback) {
    return this.searchStatusUpdates.subscribe(callback);
  }
  subscribeJobProgressUpdates(callback) {
    return this.jobProgressUpdates.subscribe(callback);
  }
  getConnectionStatus() {
    let status = false;
    this.isConnected.subscribe((value) => {
      status = value;
    })();
    return status;
  }
  async reconnect() {
    try {
      await wsService.connect();
      this.isConnected.set(true);
      return true;
    } catch (error) {
      console.error("Reconnection failed:", error);
      this.isConnected.set(false);
      return false;
    }
  }
  disconnect() {
    wsService.disconnect();
    this.isConnected.set(false);
  }
  // Send message through WebSocket
  sendMessage(type, data) {
    if (this.getConnectionStatus()) {
      wsService.send({ type, data, timestamp: (/* @__PURE__ */ new Date()).toISOString() });
    } else {
      console.warn("Cannot send message: WebSocket not connected");
    }
  }
  // Request analytics refresh
  refreshAnalytics() {
    this.sendMessage("refresh_analytics", {});
  }
  // Request contact list refresh
  refreshContacts() {
    this.sendMessage("refresh_contacts", {});
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
const realTimeService = new RealTimeService();
realTimeService.isConnected;
realTimeService.messages;
realTimeService.contactUpdates;
realTimeService.systemStatus;
realTimeService.dashboardStats;
realTimeService.scraperStatus;
realTimeService.systemMetrics;
realTimeService.contactDiscoveryUpdates;
realTimeService.searchStatusUpdates;
realTimeService.jobProgressUpdates;
