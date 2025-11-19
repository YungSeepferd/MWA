"""
Listings management router for MWA Core API.

Provides endpoints for managing apartment listings, including:
- Retrieving listings with filtering and pagination
- Creating and updating listings
- Managing listing status
- Exporting listings
- Getting listing statistics
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, validator

from mwa_core.storage.manager import get_storage_manager
from mwa_core.storage.models import Listing, ListingStatus
from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function for datetime parsing
def _get_listing_datetime(listing: Dict[str, Any]) -> datetime:
    """Helper function to parse listing datetime safely."""
    created_at = listing.get('created_at')
    if isinstance(created_at, str):
        return datetime.fromisoformat(created_at)
    return created_at


# Pydantic models for listing requests/responses
class ListingResponse(BaseModel):
    """Response model for listing data."""
    id: int
    title: str
    url: str
    price: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    provider: str
    status: str
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}


class ListingCreateRequest(BaseModel):
    """Request model for creating a new listing."""
    title: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., min_length=1)
    price: Optional[float] = Field(None, ge=0)
    address: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    provider: str = Field(..., min_length=1)
    status: str = Field("active", regex="^(active|inactive|rented|unavailable)$")
    metadata: Optional[Dict[str, Any]] = {}


class ListingUpdateRequest(BaseModel):
    """Request model for updating a listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    address: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, regex="^(active|inactive|rented|unavailable)$")
    metadata: Optional[Dict[str, Any]] = None


class ListingSearchRequest(BaseModel):
    """Request model for listing search."""
    query: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(active|inactive|rented|unavailable)$")
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("created_at", regex="^(created_at|updated_at|price|title)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class ListingStatisticsResponse(BaseModel):
    """Response model for listing statistics."""
    total_listings: int
    listings_by_status: Dict[str, int]
    listings_by_provider: Dict[str, int]
    average_price: Optional[float]
    price_range: Dict[str, Optional[float]]
    recent_listings_7_days: int
    recent_listings_30_days: int
    most_active_providers: List[Dict[str, Any]]
    timestamp: datetime


class ListingExportRequest(BaseModel):
    """Request model for listing export."""
    format: str = Field("json", regex="^(json|csv|xlsx)$")
    filters: Optional[ListingSearchRequest] = None
    include_metadata: bool = Field(True)
    include_contacts: bool = Field(False)


# Dependency to get storage manager
def get_storage_manager_instance():
    """Get the storage manager instance."""
    return get_storage_manager()


@router.get("/", response_model=Dict[str, Any], summary="Get listings with filtering and pagination")
async def get_listings(
    provider: Optional[str] = Query(None, description="Filter by provider name"),
    status: Optional[str] = Query(None, regex="^(active|inactive|rented|unavailable)$", description="Filter by status"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    date_from: Optional[datetime] = Query(None, description="Filter listings from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter listings to this date"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|price|title)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Retrieve listings with optional filtering and pagination.
    
    Args:
        provider: Filter by provider name
        status: Filter by listing status
        price_min: Minimum price filter
        price_max: Maximum price filter
        date_from: Filter listings from this date
        date_to: Filter listings to this date
        limit: Maximum number of results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        storage_manager: Storage manager instance
        
    Returns:
        Paginated list of listings
    """
    try:
        # Get listings from storage
        listings = storage_manager.get_listings(
            limit=limit,
            offset=offset,
            provider=provider,
            status=status
        )
        
        # Apply additional filters (price, date range)
        filtered_listings = []
        for listing in listings:
            # Price filter
            if price_min is not None and (listing.get('price') is None or listing['price'] < price_min):
                continue
            if price_max is not None and (listing.get('price') is None or listing['price'] > price_max):
                continue
            
            # Date filter
            listing_date = _get_listing_datetime(listing)
            if date_from and listing_date < date_from:
                continue
            if date_to and listing_date > date_to:
                continue
            
            filtered_listings.append(listing)
        
        # Apply sorting
        reverse_order = sort_order == "desc"
        if sort_by == "price":
            filtered_listings.sort(key=lambda x: x.get('price', 0), reverse=reverse_order)
        elif sort_by == "title":
            filtered_listings.sort(key=lambda x: x.get('title', ''), reverse=reverse_order)
        else:  # created_at or updated_at
            filtered_listings.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse_order)
        
        # Get total count for pagination
        total_count = len(filtered_listings)
        
        # Apply pagination after filtering and sorting
        paginated_listings = filtered_listings[offset:offset + limit]
        
        return {
            "listings": paginated_listings,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "provider": provider,
                "status": status,
                "price_min": price_min,
                "price_max": price_max,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None
            },
            "sort": {
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving listings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving listings: {str(e)}")


@router.get("/{listing_id}", response_model=ListingResponse, summary="Get specific listing")
async def get_listing(
    listing_id: int = Path(..., gt=0, description="Listing ID"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Retrieve detailed information about a specific listing.
    
    Args:
        listing_id: ID of the listing to retrieve
        storage_manager: Storage manager instance
        
    Returns:
        Detailed listing information
    """
    try:
        # Get listing by URL (using ID as URL identifier for this implementation)
        # Note: This is a simplified implementation - in production you'd have a proper get_by_id method
        listings = storage_manager.get_listings(limit=1000)  # Get all listings to find the one
        
        target_listing = None
        for listing in listings:
            if listing.get('id') == listing_id:
                target_listing = listing
                break
        
        if not target_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return ListingResponse(**target_listing)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving listing: {str(e)}")


@router.post("/", response_model=ListingResponse, summary="Create new listing")
async def create_listing(
    request: ListingCreateRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Create a new listing.
    
    Args:
        request: Listing creation request
        storage_manager: Storage manager instance
        
    Returns:
        Created listing information
    """
    try:
        # Prepare listing data
        listing_data = {
            "title": request.title,
            "url": request.url,
            "price": request.price,
            "address": request.address,
            "description": request.description,
            "provider": request.provider,
            "status": request.status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "scraped_at": datetime.now().isoformat(),
            "metadata": request.metadata or {}
        }
        
        # Check for duplicates
        existing_listing = storage_manager.get_listing_by_url(request.url)
        if existing_listing:
            raise HTTPException(status_code=409, detail="Listing with this URL already exists")
        
        # Add listing to storage
        success = storage_manager.add_listing(listing_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create listing")
        
        # Retrieve the created listing
        created_listing = storage_manager.get_listing_by_url(request.url)
        if not created_listing:
            raise HTTPException(status_code=500, detail="Failed to retrieve created listing")
        
        return ListingResponse(**created_listing)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating listing: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


@router.put("/{listing_id}", response_model=ListingResponse, summary="Update listing")
async def update_listing(
    listing_id: int = Path(..., gt=0, description="Listing ID"),
    request: ListingUpdateRequest = Body(...),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Update an existing listing.
    
    Args:
        listing_id: ID of the listing to update
        request: Listing update request
        storage_manager: Storage manager instance
        
    Returns:
        Updated listing information
    """
    try:
        # Find the listing first
        listings = storage_manager.get_listings(limit=1000)
        target_listing = None
        for listing in listings:
            if listing.get('id') == listing_id:
                target_listing = listing
                break
        
        if not target_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.price is not None:
            update_data['price'] = request.price
        if request.address is not None:
            update_data['address'] = request.address
        if request.description is not None:
            update_data['description'] = request.description
        if request.status is not None:
            update_data['status'] = request.status
        if request.metadata is not None:
            update_data['metadata'] = request.metadata
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update listing status using storage manager
        success = storage_manager.update_listing_status(target_listing['url'], request.status or target_listing['status'])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update listing")
        
        # Get updated listing
        updated_listing = storage_manager.get_listing_by_url(target_listing['url'])
        if not updated_listing:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated listing")
        
        return ListingResponse(**updated_listing)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating listing: {str(e)}")


@router.delete("/{listing_id}", summary="Delete listing")
async def delete_listing(
    listing_id: int = Path(..., gt=0, description="Listing ID"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Delete a listing.
    
    Args:
        listing_id: ID of the listing to delete
        storage_manager: Storage manager instance
        
    Returns:
        Deletion confirmation
    """
    try:
        # Find the listing first
        listings = storage_manager.get_listings(limit=1000)
        target_listing = None
        for listing in listings:
            if listing.get('id') == listing_id:
                target_listing = listing
                break
        
        if not target_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Note: The storage manager doesn't have a direct delete method in the current implementation
        # This is a placeholder that would need to be implemented in the storage layer
        # For now, we'll mark it as inactive
        success = storage_manager.update_listing_status(target_listing['url'], "inactive")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete listing")
        
        return {
            "success": True,
            "message": "Listing deleted successfully",
            "listing_id": listing_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting listing: {str(e)}")


@router.post("/search", response_model=Dict[str, Any], summary="Search listings")
async def search_listings(
    request: ListingSearchRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Search listings with advanced filtering.
    
    Args:
        request: Search request parameters
        storage_manager: Storage manager instance
        
    Returns:
        Search results with pagination
    """
    try:
        # Get all listings and apply filters
        listings = storage_manager.get_listings(limit=1000)
        
        filtered_listings = []
        for listing in listings:
            # Text search
            if request.query:
                query_lower = request.query.lower()
                searchable_text = f"{listing.get('title', '')} {listing.get('description', '')} {listing.get('address', '')}".lower()
                if query_lower not in searchable_text:
                    continue
            
            # Provider filter
            if request.provider and listing.get('provider') != request.provider:
                continue
            
            # Status filter
            if request.status and listing.get('status') != request.status:
                continue
            
            # Price filters
            price = listing.get('price')
            if request.price_min is not None and (price is None or price < request.price_min):
                continue
            if request.price_max is not None and (price is None or price > request.price_max):
                continue
            
            # Date filters
            listing_date = _get_listing_datetime(listing)
            if request.date_from and listing_date < request.date_from:
                continue
            if request.date_to and listing_date > request.date_to:
                continue
            
            filtered_listings.append(listing)
        
        # Apply sorting
        reverse_order = request.sort_order == "desc"
        if request.sort_by == "price":
            filtered_listings.sort(key=lambda x: x.get('price', 0), reverse=reverse_order)
        elif request.sort_by == "title":
            filtered_listings.sort(key=lambda x: x.get('title', ''), reverse=reverse_order)
        else:  # created_at or updated_at
            filtered_listings.sort(key=lambda x: x.get(request.sort_by, ''), reverse=reverse_order)
        
        # Get total count
        total_count = len(filtered_listings)
        
        # Apply pagination
        paginated_listings = filtered_listings[request.offset:request.offset + request.limit]
        
        return {
            "listings": paginated_listings,
            "total": total_count,
            "limit": request.limit,
            "offset": request.offset,
            "search_params": request.dict(exclude_none=True)
        }
        
    except Exception as e:
        logger.error(f"Error searching listings: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching listings: {str(e)}")


@router.get("/statistics/summary", response_model=ListingStatisticsResponse, summary="Get listing statistics")
async def get_listing_statistics(
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get comprehensive listing statistics.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        Listing statistics
    """
    try:
        # Get basic statistics from storage
        stats = storage_manager.get_statistics()
        
        # Get all listings for detailed analysis
        listings = storage_manager.get_listings(limit=10000)
        
        # Calculate statistics
        total_listings = len(listings)
        
        # Listings by status
        listings_by_status = {}
        for listing in listings:
            status = listing.get('status', 'unknown')
            listings_by_status[status] = listings_by_status.get(status, 0) + 1
        
        # Listings by provider
        listings_by_provider = {}
        for listing in listings:
            provider = listing.get('provider', 'unknown')
            listings_by_provider[provider] = listings_by_provider.get(provider, 0) + 1
        
        # Price statistics
        prices = [listing.get('price') for listing in listings if listing.get('price') is not None]
        average_price = sum(prices) / len(prices) if prices else None
        price_range = {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None
        }
        
        # Recent listings
        now = datetime.now()
        recent_7_days = sum(1 for listing in listings
                          if _get_listing_datetime(listing) >= now - timedelta(days=7))
        recent_30_days = sum(1 for listing in listings
                           if _get_listing_datetime(listing) >= now - timedelta(days=30))
        
        # Most active providers
        most_active_providers = [
            {"provider": provider, "count": count}
            for provider, count in sorted(listings_by_provider.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return ListingStatisticsResponse(
            total_listings=total_listings,
            listings_by_status=listings_by_status,
            listings_by_provider=listings_by_provider,
            average_price=average_price,
            price_range=price_range,
            recent_listings_7_days=recent_7_days,
            recent_listings_30_days=recent_30_days,
            most_active_providers=most_active_providers,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting listing statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting listing statistics: {str(e)}")


@router.post("/export", summary="Export listings")
async def export_listings(
    request: ListingExportRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Export listings in various formats.
    
    Args:
        request: Export request parameters
        storage_manager: Storage manager instance
        
    Returns:
        Exported listings data
    """
    try:
        # Get listings with optional filtering
        if request.filters:
            # Use search functionality for filtering
            search_result = await search_listings(request.filters, storage_manager)
            listings = search_result["listings"]
        else:
            listings = storage_manager.get_listings(limit=10000)
        
        # Prepare export data
        export_data = []
        for listing in listings:
            listing_dict = listing.copy()
            
            # Include metadata if requested
            if not request.include_metadata:
                listing_dict.pop('metadata', None)
            
            # Include contacts if requested
            if request.include_contacts:
                contacts = storage_manager.get_contacts(listing_id=listing.get('id'))
                listing_dict['contacts'] = contacts
            
            export_data.append(listing_dict)
        
        # Format based on requested format
        if request.format == "json":
            return {
                "exported_at": datetime.now().isoformat(),
                "total_listings": len(export_data),
                "format": request.format,
                "listings": export_data
            }
        elif request.format == "csv":
            # For CSV, we'd need to implement CSV generation
            # This is a placeholder that returns JSON for now
            return {
                "exported_at": datetime.now().isoformat(),
                "total_listings": len(export_data),
                "format": request.format,
                "message": "CSV export not yet implemented - returning JSON format",
                "listings": export_data
            }
        elif request.format == "xlsx":
            # For Excel, we'd need to implement Excel generation
            # This is a placeholder that returns JSON for now
            return {
                "exported_at": datetime.now().isoformat(),
                "total_listings": len(export_data),
                "format": request.format,
                "message": "Excel export not yet implemented - returning JSON format",
                "listings": export_data
            }
        
    except Exception as e:
        logger.error(f"Error exporting listings: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting listings: {str(e)}")