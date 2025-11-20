"""
Listing management Pydantic schemas for MWA Core API.

Provides request/response models for apartment listing management including
retrieval, creation, updates, search, filtering, and export operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal

from pydantic import BaseModel, Field, validator, HttpUrl
from .common import (
    PaginationParams, SortParams, DateRange, SearchParams, 
    PaginatedResponse, ExportRequest, ListingStatus,
    StatisticsResponse, SuccessResponse
)


# Listing Response Models
class ListingResponse(BaseModel):
    """Response model for listing data."""
    id: int = Field(..., description="Unique listing identifier")
    provider: str = Field(..., description="Source provider")
    external_id: Optional[str] = Field(None, description="External provider ID")
    title: str = Field(..., description="Listing title")
    url: str = Field(..., description="Listing URL")
    price: Optional[str] = Field(None, description="Price string")
    size: Optional[str] = Field(None, description="Apartment size")
    rooms: Optional[str] = Field(None, description="Number of rooms")
    address: Optional[str] = Field(None, description="Property address")
    description: Optional[str] = Field(None, description="Listing description")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    scraped_at: datetime = Field(..., description="When listing was scraped")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: ListingStatus = Field(..., description="Listing status")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Provider-specific raw data")
    
    # Enhanced fields from PR C
    hash_signature: Optional[str] = Field(None, description="Deduplication hash signature")
    deduplication_status: Optional[str] = Field(None, description="Deduplication status")
    duplicate_of_id: Optional[int] = Field(None, description="ID of original if duplicate")
    first_seen_at: datetime = Field(..., description="First time listing was seen")
    last_seen_at: datetime = Field(..., description="Last time listing was seen")
    view_count: int = Field(..., description="Number of times viewed")
    
    # Contacts relationship
    contacts: List['ContactSummary'] = Field(default_factory=list, description="Associated contacts")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "provider": "immoscout",
                "external_id": "123456",
                "title": "Beautiful 3-room apartment in Munich",
                "url": "https://www.immoscout24.de/immobilien/123456",
                "price": "1800€",
                "size": "85 m²",
                "rooms": "3 Zimmer",
                "address": "Musterstraße 123, 80331 München",
                "description": "Beautiful apartment in city center...",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg"
                ],
                "scraped_at": "2025-11-19T11:19:26Z",
                "updated_at": "2025-11-19T11:19:26Z",
                "status": "active",
                "raw_data": {
                    "scraped_at": "2025-11-19T10:00:00Z",
                    "provider_data": "original provider data"
                },
                "hash_signature": "abc123def456...",
                "deduplication_status": "original",
                "duplicate_of_id": None,
                "first_seen_at": "2025-11-18T10:00:00Z",
                "last_seen_at": "2025-11-19T11:19:26Z",
                "view_count": 5,
                "contacts": []
            }
        }


class ContactSummary(BaseModel):
    """Summary of contact information for listings."""
    id: int = Field(..., description="Contact ID")
    type: str = Field(..., description="Contact type")
    value: str = Field(..., description="Contact value")
    confidence: Optional[float] = Field(None, description="Confidence score")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "type": "email",
                "value": "landlord@example.com",
                "confidence": 0.95
            }
        }


class ListingSearchResponse(BaseModel):
    """Response model for listing search results."""
    listings: List[ListingResponse] = Field(..., description="List of listings")
    total: int = Field(..., description="Total number of matching listings")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    sort: Dict[str, str] = Field(default_factory=dict, description="Sort parameters")


# Listing Request Models
class ListingCreateRequest(BaseModel):
    """Request model for creating a new listing."""
    provider: str = Field(..., min_length=1, max_length=50, description="Source provider")
    external_id: Optional[str] = Field(None, max_length=100, description="External provider ID")
    title: str = Field(..., min_length=1, max_length=500, description="Listing title")
    url: HttpUrl = Field(..., description="Listing URL")
    price: Optional[str] = Field(None, max_length=50, description="Price string")
    size: Optional[str] = Field(None, max_length=50, description="Apartment size")
    rooms: Optional[str] = Field(None, max_length=20, description="Number of rooms")
    address: Optional[str] = Field(None, max_length=500, description="Property address")
    description: Optional[str] = Field(None, description="Listing description")
    images: List[HttpUrl] = Field(default_factory=list, description="Image URLs")
    status: ListingStatus = Field(ListingStatus.ACTIVE, description="Listing status")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Provider-specific raw data")
    
    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ['immoscout', 'wg_gesucht', 'manual']
        if v not in valid_providers:
            raise ValueError(f'Provider must be one of: {valid_providers}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "immoscout",
                "external_id": "123456",
                "title": "Beautiful 3-room apartment in Munich",
                "url": "https://www.immoscout24.de/immobilien/123456",
                "price": "1800€",
                "size": "85 m²",
                "rooms": "3 Zimmer",
                "address": "Musterstraße 123, 80331 München",
                "description": "Beautiful apartment in city center...",
                "images": [
                    "https://example.com/image1.jpg"
                ],
                "status": "active",
                "raw_data": {
                    "original_url": "https://immoscout24.de/123456",
                    "crawl_metadata": "data from scraping"
                }
            }
        }


class ListingUpdateRequest(BaseModel):
    """Request model for updating a listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Listing title")
    price: Optional[str] = Field(None, max_length=50, description="Price string")
    size: Optional[str] = Field(None, max_length=50, description="Apartment size")
    rooms: Optional[str] = Field(None, max_length=20, description="Number of rooms")
    address: Optional[str] = Field(None, max_length=500, description="Property address")
    description: Optional[str] = Field(None, description="Listing description")
    images: Optional[List[HttpUrl]] = Field(None, description="Image URLs")
    status: Optional[ListingStatus] = Field(None, description="Listing status")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Provider-specific raw data")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated title",
                "price": "1900€",
                "description": "Updated description",
                "status": "active",
                "raw_data": {
                    "last_crawled": "2025-11-19T11:19:26Z"
                }
            }
        }


class ListingFilter(BaseModel):
    """Filtering parameters for listing queries."""
    provider: Optional[str] = Field(None, description="Filter by provider")
    status: Optional[ListingStatus] = Field(None, description="Filter by status")
    price_min: Optional[Union[str, float, int]] = Field(None, description="Minimum price filter")
    price_max: Optional[Union[str, float, int]] = Field(None, description="Maximum price filter")
    rooms_min: Optional[str] = Field(None, description="Minimum rooms")
    rooms_max: Optional[str] = Field(None, description="Maximum rooms")
    size_min: Optional[str] = Field(None, description="Minimum size")
    size_max: Optional[str] = Field(None, description="Maximum size")
    has_images: Optional[bool] = Field(None, description="Filter listings with/without images")
    has_contacts: Optional[bool] = Field(None, description="Filter listings with/without contacts")
    duplicate_status: Optional[str] = Field(None, description="Filter by deduplication status")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "immoscout",
                "status": "active",
                "price_min": "1000",
                "price_max": "2000",
                "rooms_min": "2",
                "rooms_max": "4",
                "has_images": True,
                "has_contacts": True,
                "duplicate_status": "original"
            }
        }


class ListingSearchRequest(BaseModel):
    """Request model for listing search."""
    query: Optional[str] = Field(None, description="Search query for title/description/address")
    filters: Optional[ListingFilter] = Field(None, description="Search filters")
    pagination: PaginationParams = Field(default_factory=PaginationParams, description="Pagination parameters")
    sort: SortParams = Field(default_factory=lambda: SortParams(sort_by="scraped_at", sort_order="desc"), description="Sort parameters")
    date_range: Optional[DateRange] = Field(None, description="Date range filter")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "München apartment 2 Zimmer",
                "filters": {
                    "provider": "immoscout",
                    "status": "active",
                    "price_min": "1000",
                    "price_max": "2000"
                },
                "pagination": {
                    "limit": 20,
                    "offset": 0
                },
                "sort": {
                    "sort_by": "scraped_at",
                    "sort_order": "desc"
                },
                "date_range": {
                    "date_from": "2025-11-01T00:00:00Z",
                    "date_to": "2025-11-30T23:59:59Z"
                }
            }
        }


# Listing Statistics Models
class ListingStatisticsResponse(BaseModel):
    """Response model for listing statistics."""
    total_listings: int = Field(..., description="Total number of listings")
    listings_by_status: Dict[str, int] = Field(default_factory=dict, description="Listings by status")
    listings_by_provider: Dict[str, int] = Field(default_factory=dict, description="Listings by provider")
    average_price: Optional[float] = Field(None, description="Average price")
    price_range: Dict[str, Optional[float]] = Field(default_factory=dict, description="Price range (min/max)")
    recent_listings_7_days: int = Field(..., description="Listings added in last 7 days")
    recent_listings_30_days: int = Field(..., description="Listings added in last 30 days")
    most_active_providers: List[Dict[str, Any]] = Field(default_factory=list, description="Most active providers")
    listings_with_images: int = Field(..., description="Listings with images")
    listings_with_contacts: int = Field(..., description="Listings with contacts")
    duplicate_count: int = Field(..., description="Number of duplicate listings")
    unique_listings: int = Field(..., description="Number of unique listings")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_listings": 1250,
                "listings_by_status": {
                    "active": 1000,
                    "inactive": 200,
                    "rented": 50
                },
                "listings_by_provider": {
                    "immoscout": 800,
                    "wg_gesucht": 450
                },
                "average_price": 1750.5,
                "price_range": {
                    "min": 800.0,
                    "max": 3000.0
                },
                "recent_listings_7_days": 75,
                "recent_listings_30_days": 280,
                "most_active_providers": [
                    {"provider": "immoscout", "count": 800},
                    {"provider": "wg_gesucht", "count": 450}
                ],
                "listings_with_images": 1100,
                "listings_with_contacts": 950,
                "duplicate_count": 125,
                "unique_listings": 1125,
                "timestamp": "2025-11-19T11:19:26Z"
            }
        }


class PriceStatistics(BaseModel):
    """Price statistics for listings."""
    average: Optional[float] = Field(None, description="Average price")
    median: Optional[float] = Field(None, description="Median price")
    min: Optional[float] = Field(None, description="Minimum price")
    max: Optional[float] = Field(None, description="Maximum price")
    standard_deviation: Optional[float] = Field(None, description="Price standard deviation")
    price_ranges: Dict[str, int] = Field(default_factory=dict, description="Count by price ranges")
    
    class Config:
        schema_extra = {
            "example": {
                "average": 1750.5,
                "median": 1700.0,
                "min": 800.0,
                "max": 3000.0,
                "standard_deviation": 450.2,
                "price_ranges": {
                    "800-1200": 200,
                    "1200-1600": 350,
                    "1600-2000": 450,
                    "2000-3000": 250
                }
            }
        }


class ProviderStatistics(BaseModel):
    """Statistics for a specific provider."""
    name: str = Field(..., description="Provider name")
    total_listings: int = Field(..., description="Total listings from provider")
    success_rate: float = Field(..., description="Success rate for scraping")
    average_response_time: Optional[float] = Field(None, description="Average response time")
    last_successful_run: Optional[datetime] = Field(None, description="Last successful scraping run")
    error_count: int = Field(..., description="Number of errors")
    listing_quality_score: Optional[float] = Field(None, description="Quality score")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "immoscout",
                "total_listings": 800,
                "success_rate": 95.5,
                "average_response_time": 2.3,
                "last_successful_run": "2025-11-19T10:00:00Z",
                "error_count": 5,
                "listing_quality_score": 0.87
            }
        }


# Listing Export Models
class ListingExportRequest(BaseModel):
    """Request model for listing export."""
    format: str = Field("json", pattern="^(json|csv|xlsx)$", description="Export format")
    filters: Optional[ListingSearchRequest] = Field(None, description="Export filters")
    include_metadata: bool = Field(True, description="Include metadata")
    include_contacts: bool = Field(False, description="Include associated contacts")
    include_images: bool = Field(False, description="Include image URLs")
    deduplicated_only: bool = Field(False, description="Export only deduplicated listings")
    
    class Config:
        schema_extra = {
            "example": {
                "format": "csv",
                "filters": {
                    "query": "München",
                    "filters": {
                        "status": "active",
                        "provider": "immoscout"
                    }
                },
                "include_metadata": True,
                "include_contacts": False,
                "include_images": True,
                "deduplicated_only": True
            }
        }


class ListingExportResponse(BaseModel):
    """Response model for listing export."""
    export_id: str = Field(..., description="Unique export identifier")
    format: str = Field(..., description="Export format")
    total_listings: int = Field(..., description="Number of listings exported")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[datetime] = Field(None, description="Download URL expiration")
    created_at: datetime = Field(default_factory=datetime.now, description="Export creation time")
    
    class Config:
        schema_extra = {
            "example": {
                "export_id": "export_12345",
                "format": "csv",
                "total_listings": 850,
                "file_size": 204800,
                "download_url": "https://api.example.com/exports/export_12345/download",
                "expires_at": "2025-11-26T11:19:26Z",
                "created_at": "2025-11-19T11:19:26Z"
            }
        }


# Listing Deduplication Models
class ListingDuplicateGroup(BaseModel):
    """Group of duplicate listings."""
    group_id: str = Field(..., description="Unique group identifier")
    original_listing: ListingResponse = Field(..., description="Original/first listing")
    duplicates: List[ListingResponse] = Field(default_factory=list, description="Duplicate listings")
    similarity_score: float = Field(..., description="Similarity score between listings")
    merge_suggested: bool = Field(..., description="Whether automatic merge is suggested")
    
    class Config:
        schema_extra = {
            "example": {
                "group_id": "dup_group_123",
                "original_listing": {
                    "id": 123,
                    "title": "Beautiful apartment Munich",
                    "provider": "immoscout"
                },
                "duplicates": [
                    {
                        "id": 124,
                        "title": "Schöne Wohnung München",
                        "provider": "wg_gesucht"
                    }
                ],
                "similarity_score": 0.95,
                "merge_suggested": True
            }
        }


class ListingDeduplicationRequest(BaseModel):
    """Request model for deduplication operations."""
    action: str = Field(..., pattern="^(analyze|merge|unmerge|ignore)$", description="Deduplication action")
    listing_ids: List[int] = Field(..., min_items=2, description="List of listing IDs to process")
    keep_original: Optional[bool] = Field(True, description="Keep first listing as original")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "merge",
                "listing_ids": [123, 124, 125],
                "keep_original": True
            }
        }


class ListingDeduplicationResponse(BaseModel):
    """Response model for deduplication operation."""
    success: bool = Field(..., description="Operation success status")
    original_listing_id: Optional[int] = Field(None, description="Original listing ID")
    merged_listing_ids: List[int] = Field(default_factory=list, description="Merged listing IDs")
    removed_listing_ids: List[int] = Field(default_factory=list, description="Removed listing IDs")
    similarity_scores: List[float] = Field(default_factory=list, description="Similarity scores")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "original_listing_id": 123,
                "merged_listing_ids": [123, 124, 125],
                "removed_listing_ids": [124, 125],
                "similarity_scores": [0.95, 0.87]
            }
        }


# Listing Bulk Operations
class ListingBulkUpdateRequest(BaseModel):
    """Request model for bulk listing operations."""
    listing_ids: List[int] = Field(..., min_items=1, description="List of listing IDs to update")
    operation: str = Field(..., pattern="^(update_status|add_contacts|update_metadata|delete)$", description="Bulk operation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "listing_ids": [123, 124, 125],
                "operation": "update_status",
                "parameters": {
                    "status": "inactive",
                    "reason": "No longer available"
                }
            }
        }


class ListingBulkOperationResponse(BaseModel):
    """Response model for bulk operation."""
    success: bool = Field(..., description="Operation success status")
    processed_count: int = Field(..., description="Number of listings processed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of errors")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    operation: str = Field(..., description="Performed operation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "processed_count": 3,
                "success_count": 2,
                "error_count": 1,
                "errors": [
                    {
                        "listing_id": 125,
                        "error": "Listing not found"
                    }
                ],
                "operation": "update_status",
                "timestamp": "2025-11-19T11:19:26Z"
            }
        }


# Listing Quality Assessment
class ListingQualityMetrics(BaseModel):
    """Quality metrics for a listing."""
    completeness_score: float = Field(..., description="Data completeness score (0-1)")
    image_quality_score: Optional[float] = Field(None, description="Image quality score (0-1)")
    description_quality_score: Optional[float] = Field(None, description="Description quality score (0-1)")
    contact_availability_score: Optional[float] = Field(None, description="Contact availability score (0-1)")
    price_consistency_score: Optional[float] = Field(None, description="Price consistency score (0-1)")
    overall_score: float = Field(..., description="Overall quality score (0-1)")
    quality_issues: List[str] = Field(default_factory=list, description="Identified quality issues")
    
    class Config:
        schema_extra = {
            "example": {
                "completeness_score": 0.85,
                "image_quality_score": 0.90,
                "description_quality_score": 0.75,
                "contact_availability_score": 1.0,
                "price_consistency_score": 0.95,
                "overall_score": 0.89,
                "quality_issues": [
                    "Description could be more detailed",
                    "Missing floor information"
                ]
            }
        }


class ListingQualityReport(BaseModel):
    """Comprehensive quality report for listings."""
    listing_id: int = Field(..., description="Listing ID")
    metrics: ListingQualityMetrics = Field(..., description="Quality metrics")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    last_assessed: datetime = Field(default_factory=datetime.now, description="Last assessment time")
    
    class Config:
        schema_extra = {
            "example": {
                "listing_id": 123,
                "metrics": {
                    "completeness_score": 0.85,
                    "image_quality_score": 0.90,
                    "description_quality_score": 0.75,
                    "contact_availability_score": 1.0,
                    "price_consistency_score": 0.95,
                    "overall_score": 0.89,
                    "quality_issues": [
                        "Description could be more detailed"
                    ]
                },
                "recommendations": [
                    "Add more detailed description",
                    "Include floor number if available"
                ],
                "last_assessed": "2025-11-19T11:19:26Z"
            }
        }


# Update forward references
ListingResponse.model_rebuild()
ContactSummary.model_rebuild()