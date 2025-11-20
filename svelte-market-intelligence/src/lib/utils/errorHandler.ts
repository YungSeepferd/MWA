/**
 * Global error handling utilities for the Market Intelligence app
 */

export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorCallbacks: ((error: AppError) => void)[] = [];

  private constructor() {}

  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  public handleError(error: any, context: string = 'unknown'): AppError {
    const appError: AppError = this.normalizeError(error, context);
    
    // Log to console in development
    if (import.meta.env.DEV) {
      console.error(`[${context}]`, appError);
    }
    
    // Notify subscribers
    this.errorCallbacks.forEach(callback => callback(appError));
    
    return appError;
  }

  public subscribe(callback: (error: AppError) => void): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    };
  }

  private normalizeError(error: any, context: string): AppError {
    if (error instanceof Error) {
      return {
        code: 'UNKNOWN_ERROR',
        message: error.message,
        details: { stack: error.stack, context },
        timestamp: new Date(),
        severity: 'medium'
      };
    }

    if (typeof error === 'string') {
      return {
        code: 'STRING_ERROR',
        message: error,
        details: { context },
        timestamp: new Date(),
        severity: 'low'
      };
    }

    if (error?.response) {
      // HTTP error
      const status = error.response.status;
      const statusText = error.response.statusText;
      const data = error.response.data;
      
      return {
        code: `HTTP_${status}`,
        message: data?.message || statusText || `HTTP Error ${status}`,
        details: { status, data, context },
        timestamp: new Date(),
        severity: this.getHttpErrorSeverity(status)
      };
    }

    if (error?.code) {
      // Already an AppError-like object
      return {
        code: error.code,
        message: error.message,
        details: { ...error.details, context },
        timestamp: new Date(),
        severity: error.severity || 'medium'
      };
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred',
      details: { originalError: error, context },
      timestamp: new Date(),
      severity: 'medium'
    };
  }

  private getHttpErrorSeverity(status: number): AppError['severity'] {
    if (status >= 500) return 'high';
    if (status >= 400) return 'medium';
    return 'low';
  }
}

// Common error codes
export const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  API_ERROR: 'API_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  AUTH_ERROR: 'AUTH_ERROR',
  WEBSOCKET_ERROR: 'WEBSOCKET_ERROR',
  DATA_ERROR: 'DATA_ERROR'
};

// Error messages for common scenarios
export const ERROR_MESSAGES = {
  NETWORK_OFFLINE: 'Network connection appears to be offline',
  API_UNAVAILABLE: 'API service is temporarily unavailable',
  INVALID_DATA: 'Invalid data received from server',
  AUTH_REQUIRED: 'Authentication required',
  WEBSOCKET_DISCONNECTED: 'WebSocket connection lost'
};

// Global error handler instance
export const errorHandler = ErrorHandler.getInstance();