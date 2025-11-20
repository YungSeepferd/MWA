"""
Contact management Pydantic schemas for MWA Core API.

Provides request/response models for contact management including
retrieval, creation, updates, validation, search, and export operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel, Field, validator, EmailStr, root_validator
from .common import (
    PaginationParams, SortParams, DateRange, SearchParams, 
    PaginatedResponse, ExportRequest, ContactType, ContactStatus,
    StatisticsResponse, SuccessResponse, EmailField, PhoneField, ConfidenceField
)


# Contact Response Models
class ContactResponse(BaseModel):
    """Response model for contact data."""
    id: int = Field(..., description="Unique contact identifier")
    listing_id: Optional[int] = Field(None, description="Associated listing ID")
    type: ContactType = Field(..., description="Contact type")
    value: str = Field(..., description="Contact value")
    confidence: Optional[ConfidenceField] = Field(None, description="Confidence score")
    source: Optional[str] = Field(None, description="Source of contact discovery")
    status: ContactStatus = Field(..., description="Contact validation status")
    validated_at: Optional[datetime] = Field(None, description="Validation timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    validation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Validation metadata")
    
    # Enhanced fields from PR C
    hash_signature: Optional[str] = Field(None, description="Deduplication hash signature")
    usage_count: int = Field(..., description="Number of times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    # Relationships
    listing: Optional['ListingSummary'] = Field(None, description="Associated listing summary")
    validation_history: List['ValidationHistoryEntry'] = Field(default_factory=list, description="Validation history")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "listing_id": 123,
                "type": "email",
                "value": "landlord@example.com",
                "confidence": 0.95,
                "source": "email_extractor",
                "status": "valid",
                "validated_at": "2025-11-19T11:20:53Z",
                "created_at": "2025-11-18T10:00:00Z",
                "updated_at": "2025-11-19T11:20:53Z",
                "validation_metadata": {
                    "validation_method": "smtp_check",
                    "validation_details": "Email exists and accepts mail"
                },
                "hash_signature": "def789abc123...",
                "usage_count": 3,
                "last_used_at": "2025-11-19T10:30:00Z",
                "listing": {
                    "id": 123,
                    "title": "Beautiful apartment Munich"
                },
                "validation_history": []
            }
        }


class ListingSummary(BaseModel):
    """Summary of listing information for contacts."""
    id: int = Field(..., description="Listing ID")
    title: str = Field(..., description="Listing title")
    provider: str = Field(..., description="Source provider")
    status: str = Field(..., description="Listing status")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "title": "Beautiful apartment Munich",
                "provider": "immoscout",
                "status": "active"
            }
        }


class ValidationHistoryEntry(BaseModel):
    """Entry in contact validation history."""
    id: int = Field(..., description="Validation entry ID")
    validation_method: str = Field(..., description="Validation method used")
    validation_result: ContactStatus = Field(..., description="Validation result")
    confidence_score: Optional[ConfidenceField] = Field(None, description="Confidence score")
    validation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Validation metadata")
    validated_at: datetime = Field(..., description="Validation timestamp")
    validator_version: Optional[str] = Field(None, description="Validator version used")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "validation_method": "smtp_check",
                "validation_result": "valid",
                "confidence_score": 0.95,
                "validation_metadata": {
                    "smtp_response": "250 OK",
                    "response_time_ms": 150
                },
                "validated_at": "2025-11-19T11:20:53Z",
                "validator_version": "1.2.0"
            }
        }


class ContactSearchResponse(BaseModel):
    """Response model for contact search results."""
    contacts: List[ContactResponse] = Field(..., description="List of contacts")
    total: int = Field(..., description="Total number of matching contacts")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    sort: Dict[str, str] = Field(default_factory=dict, description="Sort parameters")


# Contact Request Models
class ContactCreateRequest(BaseModel):
    """Request model for creating a new contact."""
    listing_id: Optional[int] = Field(None, gt=0, description="Associated listing ID")
    type: ContactType = Field(..., description="Contact type")
    value: str = Field(..., min_length=1, max_length=500, description="Contact value")
    confidence: Optional[ConfidenceField] = Field(None, description="Confidence score")
    source: Optional[str] = Field(None, max_length=50, description="Source of discovery")
    status: ContactStatus = Field(ContactStatus.UNVALIDATED, description="Initial status")
    validation_metadata: Optional[Dict[str, Any]] = Field(None, description="Validation metadata")
    
    @validator('value')
    def validate_contact_value(cls, v, values):
        contact_type = values.get('type')
        if contact_type == ContactType.EMAIL:
            EmailField.validate(v)
        elif contact_type == ContactType.PHONE:
            PhoneField.validate(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "listing_id": 123,
                "type": "email",
                "value": "landlord@example.com",
                "confidence": 0.95,
                "source": "email_extractor",
                "status": "unvalidated",
                "validation_metadata": {
                    "extraction_method": "regex_pattern"
                }
            }
        }


class ContactUpdateRequest(BaseModel):
    """Request model for updating a contact."""
    type: Optional[ContactType] = Field(None, description="Contact type")
    value: Optional[str] = Field(None, min_length=1, max_length=500, description="Contact value")
    confidence: Optional[ConfidenceField] = Field(None, description="Confidence score")
    status: Optional[ContactStatus] = Field(None, description="Contact status")
    validation_metadata: Optional[Dict[str, Any]] = Field(None, description="Validation metadata")
    
    @validator('value')
    def validate_contact_value(cls, v, values):
        if v is not None:
            contact_type = values.get('type')
            if contact_type == ContactType.EMAIL:
                EmailField.validate(v)
            elif contact_type == ContactType.PHONE:
                PhoneField.validate(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "valid",
                "confidence": 0.98,
                "validation_metadata": {
                    "validated_by": "manual_review",
                    "validation_notes": "Verified email format"
                }
            }
        }


class ContactFilter(BaseModel):
    """Filtering parameters for contact queries."""
    contact_type: Optional[ContactType] = Field(None, description="Filter by contact type")
    status: Optional[ContactStatus] = Field(None, description="Filter by status")
    confidence_min: Optional[ConfidenceField] = Field(None, description="Minimum confidence")
    confidence_max: Optional[ConfidenceField] = Field(None, description="Maximum confidence")
    listing_id: Optional[int] = Field(None, gt=0, description="Filter by listing ID")
    source: Optional[str] = Field(None, description="Filter by source")
    has_validation_history: Optional[bool] = Field(None, description="Filter by validation history")
    validated_only: Optional[bool] = Field(None, description="Only validated contacts")
    
    @root_validator
    def validate_confidence_range(cls, values):
        conf_min = values.get('confidence_min')
        conf_max = values.get('confidence_max')
        if conf_min is not None and conf_max is not None and conf_min > conf_max:
            raise ValueError('confidence_min cannot be greater than confidence_max')
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "contact_type": "email",
                "status": "valid",
                "confidence_min": 0.8,
                "confidence_max": 1.0,
                "listing_id": 123,
                "source": "email_extractor",
                "validated_only": True
            }
        }


class ContactSearchRequest(BaseModel):
    """Request model for contact search."""
    query: Optional[str] = Field(None, description="Search query for contact value/source")
    filters: Optional[ContactFilter] = Field(None, description="Search filters")
    pagination: PaginationParams = Field(default_factory=PaginationParams, description="Pagination parameters")
    sort: SortParams = Field(default_factory=lambda: SortParams(sort_by="confidence", sort_order="desc"), description="Sort parameters")
    date_range: Optional[DateRange] = Field(None, description="Date range filter")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "example.com email",
                "filters": {
                    "contact_type": "email",
                    "status": "valid",
                    "confidence_min": 0.8
                },
                "pagination": {
                    "limit": 25,
                    "offset": 0
                },
                "sort": {
                    "sort_by": "confidence",
                    "sort_order": "desc"
                },
                "date_range": {
                    "date_from": "2025-11-01T00:00:00Z",
                    "date_to": "2025-11-30T23:59:59Z"
                }
            }
        }


# Contact Validation Models
class ContactValidationRequest(BaseModel):
    """Request model for contact validation."""
    validation_level: str = Field("standard", pattern="^(basic|standard|comprehensive)$", description="Validation level")
    methods: Optional[List[str]] = Field(None, description="Specific validation methods")
    async_validation: bool = Field(False, description="Run validation asynchronously")
    
    class Config:
        schema_extra = {
            "example": {
                "validation_level": "comprehensive",
                "methods": ["smtp_check", "dns_verification", "format_check"],
                "async_validation": False
            }
        }


class ContactValidationResult(BaseModel):
    """Result of contact validation."""
    contact_id: int = Field(..., description="Contact ID")
    is_valid: bool = Field(..., description="Whether contact is valid")
    validation_method: str = Field(..., description="Primary validation method used")
    confidence_score: Optional[ConfidenceField] = Field(None, description="Updated confidence score")
    validation_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed validation results")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    duration_ms: Optional[float] = Field(None, description="Validation duration")
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "contact_id": 456,
                "is_valid": True,
                "validation_method": "smtp_check",
                "confidence_score": 0.95,
                "validation_details": {
                    "smtp_response": "250 OK",
                    "server_reachable": True,
                    "response_time_ms": 120
                },
                "warnings": [],
                "errors": [],
                "duration_ms": 150.5,
                "validated_at": "2025-11-19T11:20:53Z"
            }
        }


class ContactValidationResponse(BaseModel):
    """Response model for contact validation."""
    success: bool = Field(..., description="Validation success status")
    contact_id: int = Field(..., description="Contact ID")
    validation_result: ContactValidationResult = Field(..., description="Validation result details")
    new_status: Optional[ContactStatus] = Field(None, description="Updated contact status")
    validation_record_id: Optional[int] = Field(None, description="Validation record ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "contact_id": 456,
                "validation_result": {
                    "contact_id": 456,
                    "is_valid": True,
                    "validation_method": "smtp_check",
                    "confidence_score": 0.95,
                    "validation_details": {
                        "smtp_response": "250 OK"
                    },
                    "warnings": [],
                    "errors": [],
                    "duration_ms": 150.5,
                    "validated_at": "2025-11-19T11:20:53Z"
                },
                "new_status": "valid",
                "validation_record_id": 789
            }
        }


# Contact Statistics Models
class ContactStatisticsResponse(BaseModel):
    """Response model for contact statistics."""
    total_contacts: int = Field(..., description="Total number of contacts")
    contacts_by_type: Dict[str, int] = Field(default_factory=dict, description="Contacts by type")
    contacts_by_status: Dict[str, int] = Field(default_factory=dict, description="Contacts by status")
    contacts_by_confidence: Dict[str, int] = Field(default_factory=dict, description="Contacts by confidence ranges")
    recent_contacts_7_days: int = Field(..., description="Contacts added in last 7 days")
    recent_contacts_30_days: int = Field(..., description="Contacts added in last 30 days")
    high_confidence_contacts: int = Field(..., description="High confidence contacts (>=0.8)")
    validated_contacts: int = Field(..., description="Number of validated contacts")
    validation_rate: float = Field(..., description="Validation rate percentage")
    average_confidence: float = Field(..., description="Average confidence score")
    top_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Top contact sources")
    validation_failures_7_days: int = Field(..., description="Validation failures in last 7 days")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_contacts": 2500,
                "contacts_by_type": {
                    "email": 1800,
                    "phone": 600,
                    "form": 100
                },
                "contacts_by_status": {
                    "unvalidated": 1500,
                    "valid": 800,
                    "invalid": 150,
                    "suspicious": 50
                },
                "contacts_by_confidence": {
                    "high_0.8_1.0": 1200,
                    "medium_0.5_0.8": 800,
                    "low_0.0_0.5": 500
                },
                "recent_contacts_7_days": 120,
                "recent_contacts_30_days": 450,
                "high_confidence_contacts": 1200,
                "validated_contacts": 800,
                "validation_rate": 34.8,
                "average_confidence": 0.72,
                "top_sources": [
                    {"source": "email_extractor", "count": 1200},
                    {"source": "phone_extractor", "count": 600}
                ],
                "validation_failures_7_days": 25,
                "timestamp": "2025-11-19T11:20:53Z"
            }
        }


class ValidationMethodStatistics(BaseModel):
    """Statistics for validation methods."""
    method: str = Field(..., description="Validation method name")
    total_validations: int = Field(..., description="Total validations performed")
    success_rate: float = Field(..., description="Success rate percentage")
    average_duration_ms: float = Field(..., description="Average validation duration")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    success_count: int = Field(..., description="Number of successful validations")
    failure_count: int = Field(..., description="Number of failed validations")
    
    class Config:
        schema_extra = {
            "example": {
                "method": "smtp_check",
                "total_validations": 1500,
                "success_rate": 85.2,
                "average_duration_ms": 200.5,
                "last_used": "2025-11-19T11:20:53Z",
                "success_count": 1278,
                "failure_count": 222
            }
        }


# Contact Review Models
class ContactReviewRequest(BaseModel):
    """Request model for contact review operations."""
    contact_ids: List[int] = Field(..., min_items=1, description="List of contact IDs to review")
    action: str = Field(..., pattern="^(approve|reject|flag|validate)$", description="Review action")
    reason: Optional[str] = Field(None, max_length=500, description="Review reason")
    confidence_level: Optional[str] = Field(None, pattern="^(high|medium|low)$", description="Confidence level")
    
    class Config:
        schema_extra = {
            "example": {
                "contact_ids": [456, 457, 458],
                "action": "approve",
                "reason": "Manually verified contact information",
                "confidence_level": "high"
            }
        }


class ContactReviewResult(BaseModel):
    """Result of contact review operation."""
    contact_id: int = Field(..., description="Contact ID")
    success: bool = Field(..., description="Review success status")
    new_status: Optional[ContactStatus] = Field(None, description="New contact status")
    action: str = Field(..., description="Action performed")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "contact_id": 456,
                "success": True,
                "new_status": "valid",
                "action": "approve",
                "error": None
            }
        }


class ContactReviewResponse(BaseModel):
    """Response model for contact review operation."""
    success: bool = Field(..., description="Overall operation success")
    total_processed: int = Field(..., description="Number of contacts processed")
    results: List[ContactReviewResult] = Field(default_factory=list, description="Individual results")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "total_processed": 3,
                "results": [
                    {
                        "contact_id": 456,
                        "success": True,
                        "new_status": "valid",
                        "action": "approve",
                        "error": None
                    }
                ],
                "timestamp": "2025-11-19T11:20:53Z"
            }
        }


# Contact Export Models
class ContactExportRequest(BaseModel):
    """Request model for contact export."""
    format: str = Field("csv", pattern="^(csv|json|xlsx)$", description="Export format")
    filters: Optional[ContactSearchRequest] = Field(None, description="Export filters")
    include_metadata: bool = Field(True, description="Include validation metadata")
    include_validation_history: bool = Field(False, description="Include validation history")
    include_listing_info: bool = Field(True, description="Include associated listing info")
    
    class Config:
        schema_extra = {
            "example": {
                "format": "csv",
                "filters": {
                    "query": "example.com",
                    "filters": {
                        "contact_type": "email",
                        "status": "valid"
                    }
                },
                "include_metadata": True,
                "include_validation_history": False,
                "include_listing_info": True
            }
        }


class ContactExportResponse(BaseModel):
    """Response model for contact export."""
    export_id: str = Field(..., description="Unique export identifier")
    format: str = Field(..., description="Export format")
    total_contacts: int = Field(..., description="Number of contacts exported")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[datetime] = Field(None, description="Download URL expiration")
    created_at: datetime = Field(default_factory=datetime.now, description="Export creation time")
    
    class Config:
        schema_extra = {
            "example": {
                "export_id": "export_12345",
                "format": "csv",
                "total_contacts": 1500,
                "file_size": 512000,
                "download_url": "https://api.example.com/exports/export_12345/download",
                "expires_at": "2025-11-26T11:20:53Z",
                "created_at": "2025-11-19T11:20:53Z"
            }
        }


# Contact Bulk Operations
class ContactBulkOperationRequest(BaseModel):
    """Request model for bulk contact operations."""
    contact_ids: List[int] = Field(..., min_items=1, description="List of contact IDs to process")
    operation: str = Field(..., pattern="^(validate|export|delete|merge|update_status)$", description="Bulk operation")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operation parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "contact_ids": [456, 457, 458, 459],
                "operation": "validate",
                "parameters": {
                    "validation_level": "standard",
                    "async": False
                }
            }
        }


class ContactBulkOperationResponse(BaseModel):
    """Response model for bulk operation."""
    success: bool = Field(..., description="Operation success status")
    total_processed: int = Field(..., description="Number of contacts processed")
    operation: str = Field(..., description="Performed operation")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Operation results")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "total_processed": 4,
                "operation": "validate",
                "results": [
                    {
                        "contact_id": 456,
                        "status": "success",
                        "validation_result": "valid"
                    }
                ],
                "errors": [
                    {
                        "contact_id": 459,
                        "error": "Contact not found"
                    }
                ],
                "timestamp": "2025-11-19T11:20:53Z"
            }
        }


# Contact Discovery Models
class ContactDiscoveryRequest(BaseModel):
    """Request model for contact discovery."""
    listing_id: int = Field(..., gt=0, description="Listing ID to discover contacts for")
    enable_crawling: bool = Field(True, description="Enable web crawling for contact discovery")
    enable_validation: bool = Field(True, description="Enable contact validation")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum crawling depth")
    timeout_seconds: int = Field(60, ge=10, le=300, description="Discovery timeout")
    
    class Config:
        schema_extra = {
            "example": {
                "listing_id": 123,
                "enable_crawling": True,
                "enable_validation": True,
                "max_depth": 3,
                "timeout_seconds": 120
            }
        }


class ContactDiscoveryResult(BaseModel):
    """Result of contact discovery operation."""
    listing_id: int = Field(..., description="Listing ID")
    contacts_found: int = Field(..., description="Number of contacts found")
    forms_found: int = Field(..., description="Number of forms found")
    contacts: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered contacts")
    forms: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered forms")
    discovery_duration_ms: Optional[float] = Field(None, description="Discovery duration")
    discovery_methods: List[str] = Field(default_factory=list, description="Methods used for discovery")
    
    class Config:
        schema_extra = {
            "example": {
                "listing_id": 123,
                "contacts_found": 3,
                "forms_found": 1,
                "contacts": [
                    {
                        "type": "email",
                        "value": "landlord@example.com",
                        "confidence": 0.95,
                        "source": "page_text"
                    }
                ],
                "forms": [
                    {
                        "form_type": "contact_form",
                        "url": "https://example.com/contact",
                        "fields": ["name", "email", "message"]
                    }
                ],
                "discovery_duration_ms": 2500.5,
                "discovery_methods": ["page_text_analysis", "form_detection"]
            }
        }


# Contact Quality Assessment
class ContactQualityMetrics(BaseModel):
    """Quality metrics for a contact."""
    format_validity: bool = Field(..., description="Whether contact format is valid")
    reachability_score: Optional[float] = Field(None, description="Reachability score (0-1)")
    spam_score: Optional[float] = Field(None, description="Spam likelihood score (0-1)")
    uniqueness_score: float = Field(..., description="Uniqueness score (0-1)")
    overall_quality: float = Field(..., description="Overall quality score (0-1)")
    quality_issues: List[str] = Field(default_factory=list, description="Identified quality issues")
    
    class Config:
        schema_extra = {
            "example": {
                "format_validity": True,
                "reachability_score": 0.90,
                "spam_score": 0.05,
                "uniqueness_score": 0.95,
                "overall_quality": 0.88,
                "quality_issues": []
            }
        }


# Update forward references
ContactResponse.model_rebuild()