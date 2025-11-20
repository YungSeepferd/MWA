"""
Market Intelligence Pydantic schemas for MWA Core API.

Provides enhanced contact models with market intelligence capabilities
for the Market Intelligence dashboard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator, EmailStr, HttpUrl
from .common import (
    ContactType, ContactStatus, ConfidenceField, EmailField, PhoneField, UrlField
)
from .contacts import ContactResponse, ContactCreateRequest, ContactUpdateRequest


# Market Intelligence Enums
class AgencyType(str, Enum):
    """Enumeration for agency types."""
    PROPERTY_MANAGER = "property_manager"
    LANDLORD = "landlord"
    REAL_ESTATE_AGENT = "real_estate_agent"
    OTHER = "other"


class SourceProvider(str, Enum):
    """Enumeration for source providers."""
    IMMOSCOUT = "immoscout"
    WG_GESUCHT = "wg_gesucht"
    OTHER_CRAWLER = "other_crawler"
    MANUAL = "manual"


class ExtractionMethod(str, Enum):
    """Enumeration for extraction methods."""
    HTML_SCRAPE = "html_scrape"
    API = "api"
    OCR = "ocr"
    MANUAL_ENTRY = "manual_entry"


class LeadSource(str, Enum):
    """Enumeration for lead sources."""
    WEB_SCRAPING = "web_scraping"
    REFERRAL = "referral"
    PARTNER = "partner"
    MANUAL = "manual"


class ContactMethod(str, Enum):
    """Enumeration for preferred contact methods."""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class ValidationStatus(str, Enum):
    """Enumeration for validation status."""
    UNVERIFIED = "unverified"
    VALIDATED = "validated"
    INVALID = "invalid"


# Nested Models
class Address(BaseModel):
    """Address information for market intelligence contacts."""
    street: Optional[str] = Field(None, max_length=200, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=50, description="Country")
    
    class Config:
        schema_extra = {
            "example": {
                "street": "Marienplatz 1",
                "city": "Munich",
                "postal_code": "80331",
                "country": "Germany"
            }
        }


class OutreachHistoryEntry(BaseModel):
    """Entry in outreach history."""
    outreach_id: str = Field(..., description="Unique outreach identifier")
    method: ContactMethod = Field(..., description="Outreach method used")
    timestamp: datetime = Field(..., description="Outreach timestamp")
    status: str = Field(..., description="Outreach status (sent, delivered, opened, etc.)")
    response: Optional[str] = Field(None, description="Response received")
    notes: Optional[str] = Field(None, description="Outreach notes")
    
    class Config:
        schema_extra = {
            "example": {
                "outreach_id": "outreach_12345",
                "method": "email",
                "timestamp": "2025-11-19T10:30:00Z",
                "status": "sent",
                "response": "Positive response received",
                "notes": "Contact expressed interest in collaboration"
            }
        }


# Market Intelligence Contact Models
class MarketIntelligenceContact(ContactResponse):
    """
    Enhanced contact model with market intelligence capabilities.
    
    Extends the base ContactResponse with additional fields for market analysis,
    outreach tracking, and business intelligence.
    """
    
    # Market Intelligence Fields
    position: Optional[str] = Field(None, max_length=100, description="Job title")
    company_name: Optional[str] = Field(None, max_length=200, description="Agency or company name")
    agency_type: Optional[AgencyType] = Field(None, description="Type of agency")
    market_areas: List[str] = Field(default_factory=list, description="Neighborhoods or districts")
    outreach_history: List[Dict[str, Any]] = Field(default_factory=list, description="Outreach attempts")
    preferred_contact_method: Optional[ContactMethod] = Field(None, description="Preferred contact method")
    last_contacted: Optional[datetime] = Field(None, description="Last outreach timestamp")
    
    # Enhanced scoring
    confidence_score: Optional[ConfidenceField] = Field(None, description="Enhanced confidence score")
    quality_score: Optional[ConfidenceField] = Field(None, description="Overall data quality metric")
    
    # Market intelligence flags
    is_active: bool = Field(True, description="Indicates if lead is viable")
    is_blacklisted: bool = Field(False, description="Exclude from outreach")
    blacklist_reason: Optional[str] = Field(None, description="Reason for blacklisting")
    
    # Source and extraction information
    scraped_from_url: Optional[str] = Field(None, description="Source page URL")
    source_provider: Optional[str] = Field(None, description="Source provider")
    extraction_method: Optional[str] = Field(None, description="Extraction method")
    extraction_confidence: Optional[ConfidenceField] = Field(None, description="Extraction confidence")
    lead_source: Optional[LeadSource] = Field(None, description="Lead source")
    
    # Management fields
    tags: List[str] = Field(default_factory=list, description="Free-form tags for segmentation")
    notes: Optional[str] = Field(None, description="Analyst notes")
    
    @root_validator(pre=True)
    def validate_contact_requirements(cls, values):
        """Ensure at least one of email or phone is present and valid."""
        contact_type = values.get('type')
        value = values.get('value')
        
        if contact_type == ContactType.EMAIL:
            if value:
                EmailField.validate(value)
        elif contact_type == ContactType.PHONE:
            if value:
                PhoneField.validate(value)
        
        return values
    
    @validator('market_areas', 'tags', 'associated_listing_ids')
    def validate_list_fields(cls, v):
        """Validate list fields to ensure they are properly formatted."""
        if v is None:
            return []
        return v
    
    @validator('extraction_confidence', 'quality_score', pre=True)
    def validate_confidence_scores(cls, v):
        """Validate confidence and quality scores."""
        if v is not None:
            return ConfidenceField.validate(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "listing_id": 123,
                "type": "email",
                "value": "property.manager@example.com",
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
                "validation_history": [],
                # Market Intelligence Fields
                "position": "Property Manager",
                "company_name": "Munich Property Management GmbH",
                "agency_type": "property_manager",
                "market_areas": ["Munich Center", "Schwabing", "Maxvorstadt"],
                "outreach_history": [
                    {
                        "outreach_id": "outreach_12345",
                        "method": "email",
                        "timestamp": "2025-11-19T10:30:00Z",
                        "status": "sent",
                        "response": "Positive response received"
                    }
                ],
                "preferred_contact_method": "email",
                "last_contacted": "2025-11-19T10:30:00Z",
                "confidence_score": 0.95,
                "quality_score": 0.88,
                "is_active": True,
                "is_blacklisted": False,
                "blacklist_reason": None,
                "scraped_from_url": "https://immoscout24.de/listing/123",
                "source_provider": "immoscout",
                "extraction_method": "html_scrape",
                "extraction_confidence": 0.92,
                "lead_source": "web_scraping",
                "tags": ["high-priority", "property-manager", "munich-center"],
                "notes": "Responsive and professional contact"
            }
        }


class MarketIntelligenceContactCreateRequest(ContactCreateRequest):
    """
    Request model for creating a market intelligence contact.
    
    Extends the base ContactCreateRequest with market intelligence fields.
    """
    
    # Market Intelligence Fields
    full_name: Optional[str] = Field(None, max_length=200, description="Person's full name")
    position: Optional[str] = Field(None, max_length=100, description="Job title")
    company_name: Optional[str] = Field(None, max_length=200, description="Agency or company name")
    agency_type: Optional[AgencyType] = Field(None, description="Type of agency")
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    address: Optional[Address] = Field(None, description="Business address")
    
    # Source and Extraction Information
    scraped_from_url: Optional[HttpUrl] = Field(None, description="Source page URL")
    source_provider: Optional[SourceProvider] = Field(None, description="Source provider")
    extraction_method: Optional[ExtractionMethod] = Field(None, description="Extraction method")
    extraction_confidence: Optional[ConfidenceField] = Field(None, description="Extraction confidence")
    
    # Market Intelligence
    lead_source: Optional[LeadSource] = Field(None, description="Lead source")
    market_areas: List[str] = Field(default_factory=list, description="Neighborhoods or districts")
    associated_listing_ids: List[int] = Field(default_factory=list, description="Associated listing IDs")
    preferred_contact_method: Optional[ContactMethod] = Field(None, description="Preferred contact method")
    tags: List[str] = Field(default_factory=list, description="Free-form tags for segmentation")
    notes: Optional[str] = Field(None, description="Analyst notes")
    
    class Config:
        schema_extra = {
            "example": {
                "listing_id": 123,
                "type": "email",
                "value": "property.manager@example.com",
                "confidence": 0.95,
                "source": "email_extractor",
                "status": "unvalidated",
                "validation_metadata": {
                    "extraction_method": "regex_pattern"
                },
                "full_name": "Max Mustermann",
                "position": "Property Manager",
                "company_name": "Munich Property Management GmbH",
                "agency_type": "property_manager",
                "website": "https://munich-property.com",
                "address": {
                    "street": "Marienplatz 1",
                    "city": "Munich",
                    "postal_code": "80331",
                    "country": "Germany"
                },
                "scraped_from_url": "https://immoscout24.de/listing/123",
                "source_provider": "immoscout",
                "extraction_method": "html_scrape",
                "extraction_confidence": 0.92,
                "lead_source": "web_scraping",
                "market_areas": ["Munich Center", "Schwabing"],
                "associated_listing_ids": [123],
                "preferred_contact_method": "email",
                "tags": ["property-manager", "munich-center"],
                "notes": "Found on Immoscout24 listing"
            }
        }


class MarketIntelligenceContactUpdateRequest(ContactUpdateRequest):
    """
    Request model for updating a market intelligence contact.
    
    Extends the base ContactUpdateRequest with market intelligence fields.
    """
    
    # Market Intelligence Fields
    full_name: Optional[str] = Field(None, max_length=200, description="Person's full name")
    position: Optional[str] = Field(None, max_length=100, description="Job title")
    company_name: Optional[str] = Field(None, max_length=200, description="Agency or company name")
    agency_type: Optional[AgencyType] = Field(None, description="Type of agency")
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    address: Optional[Address] = Field(None, description="Business address")
    
    # Enhanced Validation
    validation_status: Optional[ValidationStatus] = Field(None, description="Enhanced validation status")
    quality_score: Optional[ConfidenceField] = Field(None, description="Overall data quality metric")
    
    # Market Intelligence
    market_areas: Optional[List[str]] = Field(None, description="Neighborhoods or districts")
    associated_listing_ids: Optional[List[int]] = Field(None, description="Associated listing IDs")
    preferred_contact_method: Optional[ContactMethod] = Field(None, description="Preferred contact method")
    last_contacted: Optional[datetime] = Field(None, description="Last outreach timestamp")
    
    # Management Fields
    tags: Optional[List[str]] = Field(None, description="Free-form tags for segmentation")
    notes: Optional[str] = Field(None, description="Analyst notes")
    is_active: Optional[bool] = Field(None, description="Indicates if lead is viable")
    is_blacklisted: Optional[bool] = Field(None, description="Exclude from outreach")
    blacklist_reason: Optional[str] = Field(None, description="Reason for blacklisting")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "valid",
                "confidence": 0.98,
                "validation_metadata": {
                    "validated_by": "manual_review",
                    "validation_notes": "Verified email format"
                },
                "full_name": "Max Mustermann",
                "position": "Senior Property Manager",
                "quality_score": 0.90,
                "market_areas": ["Munich Center", "Schwabing", "Maxvorstadt"],
                "preferred_contact_method": "email",
                "last_contacted": "2025-11-19T10:30:00Z",
                "tags": ["high-priority", "property-manager"],
                "notes": "Responsive and professional contact",
                "is_active": True
            }
        }


# Market Intelligence Search and Filter Models
class MarketIntelligenceContactFilter(BaseModel):
    """Filtering parameters for market intelligence contact queries."""
    
    # Enhanced filtering options
    agency_type: Optional[AgencyType] = Field(None, description="Filter by agency type")
    source_provider: Optional[SourceProvider] = Field(None, description="Filter by source provider")
    lead_source: Optional[LeadSource] = Field(None, description="Filter by lead source")
    market_areas: Optional[List[str]] = Field(None, description="Filter by market areas")
    preferred_contact_method: Optional[ContactMethod] = Field(None, description="Filter by contact method")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_blacklisted: Optional[bool] = Field(None, description="Filter by blacklist status")
    has_outreach_history: Optional[bool] = Field(None, description="Filter by outreach history")
    last_contacted_from: Optional[datetime] = Field(None, description="Filter by last contacted date")
    last_contacted_to: Optional[datetime] = Field(None, description="Filter by last contacted date")
    quality_score_min: Optional[ConfidenceField] = Field(None, description="Minimum quality score")
    quality_score_max: Optional[ConfidenceField] = Field(None, description="Maximum quality score")
    
    @root_validator
    def validate_quality_score_range(cls, values):
        """Validate quality score range."""
        qs_min = values.get('quality_score_min')
        qs_max = values.get('quality_score_max')
        if qs_min is not None and qs_max is not None and qs_min > qs_max:
            raise ValueError('quality_score_min cannot be greater than quality_score_max')
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "agency_type": "property_manager",
                "source_provider": "immoscout",
                "lead_source": "web_scraping",
                "market_areas": ["Munich Center"],
                "preferred_contact_method": "email",
                "is_active": True,
                "is_blacklisted": False,
                "has_outreach_history": True,
                "quality_score_min": 0.8
            }
        }


class MarketIntelligenceContactSearchRequest(BaseModel):
    """Request model for market intelligence contact search."""
    
    query: Optional[str] = Field(None, description="Search query for contact value, company name, or notes")
    filters: Optional[MarketIntelligenceContactFilter] = Field(None, description="Market intelligence filters")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination parameters")
    sort: Optional[Dict[str, str]] = Field(None, description="Sort parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "property manager Munich",
                "filters": {
                    "agency_type": "property_manager",
                    "market_areas": ["Munich Center"],
                    "is_active": True
                },
                "pagination": {
                    "limit": 25,
                    "offset": 0
                },
                "sort": {
                    "sort_by": "quality_score",
                    "sort_order": "desc"
                }
            }
        }


# Update forward references
MarketIntelligenceContact.model_rebuild()