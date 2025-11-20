import type {
  MarketIntelligenceContact,
  ContactListResponse,
  ContactCreateRequest,
  ContactUpdateRequest,
  ContactScoringResponse,
  MarketIntelligenceAnalytics,
  ApiResponse,
  ApiError,
  ContactSearchRequest,
  ExportRequest,
  ExportResponse
} from '../types/api';
import { errorHandler, ERROR_CODES, ERROR_MESSAGES } from '../utils/errorHandler';

class ApiClient {
  private baseURL: string;
  private defaultHeaders: HeadersInit;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    attempt: number = 1
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          code: 'NETWORK_ERROR',
          message: 'Failed to parse error response',
          timestamp: new Date().toISOString(),
        }));

        // Retry on 5xx errors
        if (response.status >= 500 && attempt < 3) {
          await this.delay(1000 * attempt);
          return this.request<T>(endpoint, options, attempt + 1);
        }

        throw new Error(`API Error: ${errorData.message} (${errorData.code})`);
      }

      return await response.json();
    } catch (error) {
      const appError = errorHandler.handleError(error, `API:${endpoint}`);
      
      // Check for network connectivity
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw errorHandler.handleError({
          code: ERROR_CODES.NETWORK_ERROR,
          message: ERROR_MESSAGES.NETWORK_OFFLINE
        }, `API:${endpoint}`);
      }
      
      throw appError;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Contact Management
  async getContacts(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
  }): Promise<ContactListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params?.search) queryParams.append('search', params.search);

    const endpoint = `/contacts${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request<ContactListResponse>(endpoint);
  }

  async searchContacts(request: ContactSearchRequest): Promise<ContactListResponse> {
    return this.request<ContactListResponse>('/contacts/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getContact(id: string): Promise<ApiResponse<MarketIntelligenceContact>> {
    return this.request<ApiResponse<MarketIntelligenceContact>>(`/contacts/${id}`);
  }

  async createContact(contact: ContactCreateRequest): Promise<ApiResponse<MarketIntelligenceContact>> {
    return this.request<ApiResponse<MarketIntelligenceContact>>('/contacts', {
      method: 'POST',
      body: JSON.stringify(contact),
    });
  }

  async updateContact(id: string, updates: ContactUpdateRequest): Promise<ApiResponse<MarketIntelligenceContact>> {
    return this.request<ApiResponse<MarketIntelligenceContact>>(`/contacts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteContact(id: string): Promise<ApiResponse<void>> {
    return this.request<ApiResponse<void>>(`/contacts/${id}`, {
      method: 'DELETE',
    });
  }

  async approveContact(id: string): Promise<ApiResponse<MarketIntelligenceContact>> {
    return this.request<ApiResponse<MarketIntelligenceContact>>(`/contacts/${id}/approve`, {
      method: 'POST',
    });
  }

  async rejectContact(id: string, reason?: string): Promise<ApiResponse<MarketIntelligenceContact>> {
    return this.request<ApiResponse<MarketIntelligenceContact>>(`/contacts/${id}/reject`, {
      method: 'POST',
      body: reason ? JSON.stringify({ rejection_reason: reason }) : undefined,
    });
  }

  // Scoring and Analytics
  async getContactScoring(id: string): Promise<ApiResponse<ContactScoringResponse>> {
    return this.request<ApiResponse<ContactScoringResponse>>(`/contacts/${id}/scoring`);
  }

  async getAnalytics(): Promise<ApiResponse<MarketIntelligenceAnalytics>> {
    return this.request<ApiResponse<MarketIntelligenceAnalytics>>('/analytics');
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: this.defaultHeaders
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Export
  async exportContacts(request: ExportRequest): Promise<ApiResponse<ExportResponse>> {
    return this.request<ApiResponse<ExportResponse>>('/export', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getExportStatus(exportId: string): Promise<ApiResponse<ExportResponse>> {
    return this.request<ApiResponse<ExportResponse>>(`/export/${exportId}`);
  }

  // Bulk Operations
  async bulkApproveContacts(ids: string[]): Promise<ApiResponse<{ approved: number; failed: number }>> {
    return this.request<ApiResponse<{ approved: number; failed: number }>>('/contacts/bulk/approve', {
      method: 'POST',
      body: JSON.stringify({ contact_ids: ids }),
    });
  }

  async bulkRejectContacts(ids: string[], reason?: string): Promise<ApiResponse<{ rejected: number; failed: number }>> {
    return this.request<ApiResponse<{ rejected: number; failed: number }>>('/contacts/bulk/reject', {
      method: 'POST',
      body: JSON.stringify({ contact_ids: ids, rejection_reason: reason }),
    });
  }
}

// Create a singleton instance
export const apiClient = new ApiClient();

// WebSocket Service
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, Function[]> = new Map();

  constructor(private baseURL: string = '/ws') {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${this.baseURL}`;
        
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(() => this.handleReconnect());
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private handleMessage(message: any) {
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message.data));
  }

  on(messageType: string, handler: Function) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  off(messageType: string, handler: Function) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }
}

export const wsService = new WebSocketService();