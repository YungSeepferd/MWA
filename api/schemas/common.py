"""
Common Pydantic schemas shared across all API modules.

This module contains reusable schemas for pagination, filtering, error handling,
and other common patterns used throughout the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl
import re


# Enums for common choices
class SortOrder(str, Enum):
    """Enumeration for sort order."""
    ASC = "asc"
    DESC = "desc"


class ContactType(str, Enum):
    """Enumeration for contact types."""
    EMAIL = "email"
    PHONE = "phone"
    FORM = "form"
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class ContactStatus(str, Enum):
    """Enumeration for contact validation status."""
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"


class ListingStatus(str, Enum):
    """Enumeration for listing statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RENTED = "rented"
    UNAVAILABLE = "unavailable"
    EXPIRED = "expired"


class JobStatus(str, Enum):
    """Enumeration for job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationLevel(str, Enum):
    """Enumeration for validation levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


# Common Request/Response Models
class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    limit: int = Field(50, ge=1, le=1000, description="Maximum number of items to return")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    
    class Config:
        schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0
            }
        }


class SortParams(BaseModel):
    """Standard sorting parameters."""
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order (asc/desc)")
    
    class Config:
        schema_extra = {
            "example": {
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


class DateRange(BaseModel):
    """Date range filtering parameters."""
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from'] and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "date_from": "2025-01-01T00:00:00Z",
                "date_to": "2025-12-31T23:59:59Z"
            }
        }


class SearchParams(BaseModel):
    """Standard search parameters."""
    query: Optional[str] = Field(None, min_length=1, max_length=500, description="Search query")


class PaginatedResponse(BaseModel):
    """Standard paginated response structure."""
    items: List[Dict[str, Any]] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    has_more: bool = Field(..., description="Whether there are more items")


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "invalid_email"
                    }
                ],
                "timestamp": "2025-11-19T11:17:16Z"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = Field(True, description="Success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "id": 123,
                    "status": "active"
                },
                "timestamp": "2025-11-19T11:17:16Z"
            }
        }


# Validation Helpers
class EmailField(str):
    """Email validation field."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('Email must be a string')
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        if len(v) > 320:  # RFC 5321 limit
            raise ValueError('Email too long')
        
        return v


class PhoneField(str):
    """Phone number validation field."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('Phone must be a string')
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+]', '', v)
        
        # Basic phone validation (allows international format)
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, cleaned):
            raise ValueError('Invalid phone number format')
        
        return v


class UrlField(str):
    """URL validation field."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('URL must be a string')
        
        try:
            # Use HttpUrl for validation
            HttpUrl.validate(v)
        except ValueError:
            raise ValueError('Invalid URL format')
        
        return v


class ConfidenceField(float):
    """Confidence score validation field (0.0 to 1.0)."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        try:
            confidence = float(v)
            if not (0.0 <= confidence <= 1.0):
                raise ValueError('Confidence must be between 0.0 and 1.0')
            return confidence
        except (ValueError, TypeError):
            raise ValueError('Confidence must be a valid number')


# Filter Models
class BaseFilter(BaseModel):
    """Base filter model with common fields."""
    status: Optional[str] = Field(None, description="Status filter")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")


class ContactFilter(BaseFilter):
    """Contact-specific filter parameters."""
    contact_type: Optional[ContactType] = Field(None, description="Contact type filter")
    confidence_min: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum confidence")
    listing_id: Optional[int] = Field(None, gt=0, description="Filter by listing ID")


class ListingFilter(BaseFilter):
    """Listing-specific filter parameters."""
    provider: Optional[str] = Field(None, description="Provider filter")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")


# Export/Import Models
class ExportRequest(BaseModel):
    """Standard export request parameters."""
    format: str = Field("json", pattern="^(json|csv|xlsx)$", description="Export format")
    include_metadata: bool = Field(True, description="Include metadata in export")
    filters: Optional[Dict[str, Any]] = Field(None, description="Export filters")


class ImportRequest(BaseModel):
    """Standard import request parameters."""
    merge_strategy: str = Field("replace", pattern="^(replace|merge)$", description="How to handle existing data")
    validate_before_import: bool = Field(True, description="Validate data before importing")
    backup_current: bool = Field(True, description="Create backup before importing")


# Statistics Models
class StatValue(BaseModel):
    """Single statistic value."""
    count: int = Field(..., description="Count of items")
    percentage: Optional[float] = Field(None, description="Percentage of total")


class StatisticsResponse(BaseModel):
    """Standard statistics response."""
    total: int = Field(..., description="Total count")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Counts by category")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")


# Health Check Models
class ComponentHealth(BaseModel):
    """Health status of a system component."""
    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status (healthy/degraded/unhealthy)")
    last_check: datetime = Field(..., description="Last health check time")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthCheckResponse(BaseModel):
    """Standard health check response."""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    components: List[ComponentHealth] = Field(default_factory=list, description="Component statuses")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")
    version: str = Field("1.0.0", description="Application version")


# Utility Models
class ApiInfo(BaseModel):
    """API information response."""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: Optional[str] = Field(None, description="API description")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Requests remaining")
    reset_time: Optional[datetime] = Field(None, description="Rate limit reset time")


# Common field descriptions for reuse
FIELD_DESCRIPTIONS = {
    "id": "Unique identifier",
    "created_at": "Creation timestamp",
    "updated_at": "Last update timestamp", 
    "title": "Title or name",
    "description": "Description or details",
    "status": "Status or state",
    "provider": "Source provider",
    "url": "URL or link",
    "value": "Primary value",
    "confidence": "Confidence score (0.0-1.0)",
    "metadata": "Additional metadata as key-value pairs",
    "pagination": "Pagination information",
    "sorting": "Sorting parameters",
    "filtering": "Filtering parameters"
}