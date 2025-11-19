"""
Custom exception classes for MAFA application.

Provides specific exception types for different failure scenarios to enable
proper error handling and recovery mechanisms.
"""

from typing import Optional, Dict, Any


class MAFAError(Exception):
    """Base exception class for all MAFA-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(MAFAError):
    """Raised when configuration validation or loading fails."""
    pass


class ScrapingError(MAFAError):
    """Raised when web scraping operations fail."""
    pass


class DatabaseError(MAFAError):
    """Raised when database operations fail."""
    pass


class NotificationError(MAFAError):
    """Raised when notification delivery fails."""
    pass


class ProviderError(MAFAError):
    """Raised when provider-specific operations fail."""
    
    def __init__(self, provider_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['provider_name'] = provider_name
        super().__init__(f"[{provider_name}] {message}", details)
        self.provider_name = provider_name


class SchedulerError(MAFAError):
    """Raised when scheduler operations fail."""
    pass


class TemplateError(MAFAError):
    """Raised when template rendering fails."""
    pass


class ValidationError(MAFAError):
    """Raised when contact validation fails."""
    pass