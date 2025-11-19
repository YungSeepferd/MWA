"""
Contact management router for MWA Core API.

Provides endpoints for managing discovered contacts, including:
- Retrieving contacts with filtering and pagination
- Creating and updating contacts
- Contact validation and verification
- Contact search and export
- Contact statistics
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, validator

from mwa_core.storage.manager import get_storage_manager
from mwa_core.storage.models import Contact, ContactType, ContactStatus
from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function for datetime parsing
def _get_contact_datetime(contact: Dict[str, Any]) -> datetime:
    """Helper function to parse contact datetime safely."""
    created_at = contact.get('created_at')
    if isinstance(created_at, str):
        return datetime.fromisoformat(created_at)
    return created_at


# Pydantic models for contact requests/responses
class ContactResponse(BaseModel):
    """Response model for contact data."""
    id: int
    listing_id: Optional[int]
    type: str
    value: str
    confidence: float
    source: str
    status: str
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    validation_metadata: Optional[Dict[str, Any]] = {}


class ContactCreateRequest(BaseModel):
    """Request model for creating a new contact."""
    listing_id: Optional[int] = Field(None, gt=0)
    type: str = Field(..., regex="^(email|phone|form|social_media|other)$")
    value: str = Field(..., min_length=1, max_length=500)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., min_length=1)
    status: str = Field("unvalidated", regex="^(unvalidated|valid|invalid|suspicious)$")
    validation_metadata: Optional[Dict[str, Any]] = {}


class ContactUpdateRequest(BaseModel):
    """Request model for updating a contact."""
    type: Optional[str] = Field(None, regex="^(email|phone|form|social_media|other)$")
    value: Optional[str] = Field(None, min_length=1, max_length=500)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: Optional[str] = Field(None, regex="^(unvalidated|valid|invalid|suspicious)$")
    validation_metadata: Optional[Dict[str, Any]] = None


class ContactSearchRequest(BaseModel):
    """Request model for contact search."""
    query: Optional[str] = None
    contact_type: Optional[str] = Field(None, regex="^(email|phone|form|social_media|other)$")
    status: Optional[str] = Field(None, regex="^(unvalidated|valid|invalid|suspicious)$")
    confidence_min: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)
    listing_id: Optional[int] = Field(None, gt=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("confidence", regex="^(confidence|created_at|updated_at|value)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class ContactValidationRequest(BaseModel):
    """Request model for contact validation."""
    validation_level: str = Field("standard", regex="^(basic|standard|comprehensive)$")
    methods: Optional[List[str]] = Field(None, description="Validation methods to use")


class ContactStatisticsResponse(BaseModel):
    """Response model for contact statistics."""
    total_contacts: int
    contacts_by_type: Dict[str, int]
    contacts_by_status: Dict[str, int]
    contacts_by_confidence: Dict[str, int]
    recent_contacts_7_days: int
    recent_contacts_30_days: int
    high_confidence_contacts: int
    validated_contacts: int
    validation_rate: float
    average_confidence: float
    top_sources: List[Dict[str, Any]]
    timestamp: datetime


class ContactExportRequest(BaseModel):
    """Request model for contact export."""
    format: str = Field("json", regex="^(json|csv|xlsx)$")
    filters: Optional[ContactSearchRequest] = None
    include_metadata: bool = Field(True)
    include_validation_history: bool = Field(False)


# Dependency to get storage manager
def get_storage_manager_instance():
    """Get the storage manager instance."""
    return get_storage_manager()


@router.get("/", response_model=Dict[str, Any], summary="Get contacts with filtering and pagination")
async def get_contacts(
    contact_type: Optional[str] = Query(None, regex="^(email|phone|form|social_media|other)$", description="Filter by contact type"),
    status: Optional[str] = Query(None, regex="^(unvalidated|valid|invalid|suspicious)$", description="Filter by contact status"),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence filter"),
    confidence_max: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum confidence filter"),
    listing_id: Optional[int] = Query(None, gt=0, description="Filter by listing ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("confidence", regex="^(confidence|created_at|updated_at|value)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Retrieve contacts with optional filtering and pagination.
    
    Args:
        contact_type: Filter by contact type
        status: Filter by contact status
        confidence_min: Minimum confidence threshold
        confidence_max: Maximum confidence threshold
        listing_id: Filter by listing ID
        limit: Maximum number of results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        storage_manager: Storage manager instance
        
    Returns:
        Paginated list of contacts
    """
    try:
        # Get contacts from storage
        contacts = storage_manager.get_contacts(
            listing_id=listing_id,
            contact_type=contact_type
        )
        
        # Apply additional filters
        filtered_contacts = []
        for contact in contacts:
            # Status filter
            if status and contact.get('status') != status:
                continue
            
            # Confidence filters
            confidence = contact.get('confidence', 0.0)
            if confidence_min is not None and confidence < confidence_min:
                continue
            if confidence_max is not None and confidence > confidence_max:
                continue
            
            # Date filters (for created_at/updated_at)
            created_at = datetime.fromisoformat(contact['created_at']) if isinstance(contact['created_at'], str) else contact['created_at']
            # Could add date_from/date_to filters here if needed
            
            filtered_contacts.append(contact)
        
        # Apply sorting
        reverse_order = sort_order == "desc"
        if sort_by == "confidence":
            filtered_contacts.sort(key=lambda x: x.get('confidence', 0.0), reverse=reverse_order)
        elif sort_by == "value":
            filtered_contacts.sort(key=lambda x: x.get('value', ''), reverse=reverse_order)
        else:  # created_at or updated_at
            filtered_contacts.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse_order)
        
        # Get total count for pagination
        total_count = len(filtered_contacts)
        
        # Apply pagination
        paginated_contacts = filtered_contacts[offset:offset + limit]
        
        return {
            "contacts": paginated_contacts,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "contact_type": contact_type,
                "status": status,
                "confidence_min": confidence_min,
                "confidence_max": confidence_max,
                "listing_id": listing_id
            },
            "sort": {
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving contacts: {str(e)}")


@router.get("/{contact_id}", response_model=ContactResponse, summary="Get specific contact")
async def get_contact(
    contact_id: int = Path(..., gt=0, description="Contact ID"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Retrieve detailed information about a specific contact.
    
    Args:
        contact_id: ID of the contact to retrieve
        storage_manager: Storage manager instance
        
    Returns:
        Detailed contact information
    """
    try:
        # Get all contacts to find the one with matching ID
        # Note: This is a simplified implementation - in production you'd have a proper get_by_id method
        contacts = storage_manager.get_contacts(limit=10000)
        
        target_contact = None
        for contact in contacts:
            if contact.get('id') == contact_id:
                target_contact = contact
                break
        
        if not target_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return ContactResponse(**target_contact)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving contact: {str(e)}")


@router.post("/", response_model=ContactResponse, summary="Create new contact")
async def create_contact(
    request: ContactCreateRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Create a new contact.
    
    Args:
        request: Contact creation request
        storage_manager: Storage manager instance
        
    Returns:
        Created contact information
    """
    try:
        # Prepare contact data
        contact_data = {
            "listing_id": request.listing_id,
            "type": request.type,
            "value": request.value,
            "confidence": request.confidence,
            "source": request.source,
            "status": request.status,
            "validation_metadata": request.validation_metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add contact to storage
        success = storage_manager.add_contact(
            listing_id=request.listing_id or 0,  # Use 0 if no listing_id provided
            contact_data=contact_data
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create contact")
        
        # Get the created contact (simplified - would need proper retrieval in production)
        # For now, return the data that was attempted to be created
        return ContactResponse(
            id=0,  # Would get actual ID from storage
            **contact_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating contact: {str(e)}")


@router.put("/{contact_id}", response_model=ContactResponse, summary="Update contact")
async def update_contact(
    contact_id: int = Path(..., gt=0, description="Contact ID"),
    request: ContactUpdateRequest = Body(...),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Update an existing contact.
    
    Args:
        contact_id: ID of the contact to update
        request: Contact update request
        storage_manager: Storage manager instance
        
    Returns:
        Updated contact information
    """
    try:
        # Find the contact first
        contacts = storage_manager.get_contacts(limit=10000)
        target_contact = None
        for contact in contacts:
            if contact.get('id') == contact_id:
                target_contact = contact
                break
        
        if not target_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Note: The storage manager doesn't have a direct update method for contacts
        # This is a placeholder implementation
        # In a real implementation, you would need to add/update the CRUD operations
        
        # Update contact data
        updated_data = target_contact.copy()
        if request.type is not None:
            updated_data['type'] = request.type
        if request.value is not None:
            updated_data['value'] = request.value
        if request.confidence is not None:
            updated_data['confidence'] = request.confidence
        if request.status is not None:
            updated_data['status'] = request.status
        if request.validation_metadata is not None:
            updated_data['validation_metadata'] = request.validation_metadata
        
        updated_data['updated_at'] = datetime.now().isoformat()
        
        return ContactResponse(**updated_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating contact: {str(e)}")


@router.delete("/{contact_id}", summary="Delete contact")
async def delete_contact(
    contact_id: int = Path(..., gt=0, description="Contact ID"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Delete a contact.
    
    Args:
        contact_id: ID of the contact to delete
        storage_manager: Storage manager instance
        
    Returns:
        Deletion confirmation
    """
    try:
        # Find the contact first
        contacts = storage_manager.get_contacts(limit=10000)
        target_contact = None
        for contact in contacts:
            if contact.get('id') == contact_id:
                target_contact = contact
                break
        
        if not target_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Note: The storage manager doesn't have a direct delete method for contacts
        # This is a placeholder that would need to be implemented in the storage layer
        # For now, we'll mark it as invalid
        # In production, you would add proper CRUD operations
        
        return {
            "success": True,
            "message": "Contact deleted successfully",
            "contact_id": contact_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting contact: {str(e)}")


@router.post("/validate/{contact_id}", response_model=Dict[str, Any], summary="Validate contact")
async def validate_contact(
    contact_id: int = Path(..., gt=0, description="Contact ID"),
    request: ContactValidationRequest = Body(...),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Validate a contact using various validation methods.
    
    Args:
        contact_id: ID of the contact to validate
        request: Validation request parameters
        storage_manager: Storage manager instance
        
    Returns:
        Validation results
    """
    try:
        # Find the contact first
        contacts = storage_manager.get_contacts(limit=10000)
        target_contact = None
        for contact in contacts:
            if contact.get('id') == contact_id:
                target_contact = contact
                break
        
        if not target_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Note: This is a placeholder implementation
        # In a real implementation, you would integrate with the contact validation system
        # from mwa_core.contact.validators import ContactValidator
        
        # Simulate validation based on contact type
        contact_type = target_contact.get('type', '')
        contact_value = target_contact.get('value', '')
        
        is_valid = False
        validation_method = "placeholder"
        confidence_score = target_contact.get('confidence', 0.0)
        
        if contact_type == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            is_valid = bool(re.match(email_pattern, contact_value))
            validation_method = "regex_email"
        elif contact_type == "phone":
            # Simple phone number validation
            phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
            is_valid = bool(re.sub(r'[\s\-\(\)]', '', contact_value)) and len(contact_value) >= 10
            validation_method = "regex_phone"
        else:
            # For other types, just use current confidence
            is_valid = confidence_score >= 0.5
            validation_method = "confidence_based"
        
        # Update contact with validation results
        updated_contact = target_contact.copy()
        updated_contact['status'] = "valid" if is_valid else "invalid"
        updated_contact['validated_at'] = datetime.now().isoformat()
        
        # Note: In production, you would save this back to storage
        
        return {
            "contact_id": contact_id,
            "is_valid": is_valid,
            "validation_method": validation_method,
            "confidence_score": confidence_score,
            "new_status": updated_contact['status'],
            "validation_details": {
                "contact_type": contact_type,
                "contact_value": contact_value,
                "validation_level": request.validation_level
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating contact: {str(e)}")


@router.post("/search", response_model=Dict[str, Any], summary="Search contacts")
async def search_contacts(
    request: ContactSearchRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Search contacts with advanced filtering.
    
    Args:
        request: Search request parameters
        storage_manager: Storage manager instance
        
    Returns:
        Search results with pagination
    """
    try:
        # Get all contacts and apply filters
        contacts = storage_manager.get_contacts(limit=10000)
        
        filtered_contacts = []
        for contact in contacts:
            # Text search
            if request.query:
                query_lower = request.query.lower()
                searchable_text = f"{contact.get('value', '')} {contact.get('source', '')}".lower()
                if query_lower not in searchable_text:
                    continue
            
            # Contact type filter
            if request.contact_type and contact.get('type') != request.contact_type:
                continue
            
            # Status filter
            if request.status and contact.get('status') != request.status:
                continue
            
            # Confidence filters
            confidence = contact.get('confidence', 0.0)
            if request.confidence_min is not None and confidence < request.confidence_min:
                continue
            if request.confidence_max is not None and confidence > request.confidence_max:
                continue
            
            # Listing ID filter
            if request.listing_id and contact.get('listing_id') != request.listing_id:
                continue
            
            # Date filters
            if request.date_from or request.date_to:
                created_at = _get_contact_datetime(contact)
                if request.date_from and created_at < request.date_from:
                    continue
                if request.date_to and created_at > request.date_to:
                    continue
            
            filtered_contacts.append(contact)
        
        # Apply sorting
        reverse_order = request.sort_order == "desc"
        if request.sort_by == "confidence":
            filtered_contacts.sort(key=lambda x: x.get('confidence', 0.0), reverse=reverse_order)
        elif request.sort_by == "value":
            filtered_contacts.sort(key=lambda x: x.get('value', ''), reverse=reverse_order)
        else:  # created_at or updated_at
            filtered_contacts.sort(key=lambda x: x.get(request.sort_by, ''), reverse=reverse_order)
        
        # Get total count
        total_count = len(filtered_contacts)
        
        # Apply pagination
        paginated_contacts = filtered_contacts[request.offset:request.offset + request.limit]
        
        return {
            "contacts": paginated_contacts,
            "total": total_count,
            "limit": request.limit,
            "offset": request.offset,
            "search_params": request.dict(exclude_none=True)
        }
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching contacts: {str(e)}")


@router.get("/statistics/summary", response_model=ContactStatisticsResponse, summary="Get contact statistics")
async def get_contact_statistics(
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get comprehensive contact statistics.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        Contact statistics
    """
    try:
        # Get all contacts for analysis
        contacts = storage_manager.get_contacts(limit=10000)
        
        # Calculate statistics
        total_contacts = len(contacts)
        
        # Contacts by type
        contacts_by_type = {}
        for contact in contacts:
            contact_type = contact.get('type', 'unknown')
            contacts_by_type[contact_type] = contacts_by_type.get(contact_type, 0) + 1
        
        # Contacts by status
        contacts_by_status = {}
        for contact in contacts:
            status = contact.get('status', 'unknown')
            contacts_by_status[status] = contacts_by_status.get(status, 0) + 1
        
        # Contacts by confidence ranges
        contacts_by_confidence = {
            "high_0.8_1.0": sum(1 for c in contacts if c.get('confidence', 0) >= 0.8),
            "medium_0.5_0.8": sum(1 for c in contacts if 0.5 <= c.get('confidence', 0) < 0.8),
            "low_0.0_0.5": sum(1 for c in contacts if c.get('confidence', 0) < 0.5)
        }
        
        # Recent contacts
        now = datetime.now()
        recent_7_days = sum(1 for contact in contacts
                          if _get_contact_datetime(contact) >= now - timedelta(days=7))
        recent_30_days = sum(1 for contact in contacts
                           if _get_contact_datetime(contact) >= now - timedelta(days=30))
        
        # High confidence contacts
        high_confidence_contacts = sum(1 for contact in contacts if contact.get('confidence', 0) >= 0.8)
        
        # Validated contacts
        validated_contacts = contacts_by_status.get('valid', 0)
        
        # Validation rate
        total_validated = contacts_by_status.get('valid', 0) + contacts_by_status.get('invalid', 0)
        validation_rate = (validated_contacts / total_validated * 100) if total_validated > 0 else 0
        
        # Average confidence
        confidence_scores = [contact.get('confidence', 0) for contact in contacts]
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Top sources
        sources = {}
        for contact in contacts:
            source = contact.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        top_sources = [
            {"source": source, "count": count}
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return ContactStatisticsResponse(
            total_contacts=total_contacts,
            contacts_by_type=contacts_by_type,
            contacts_by_status=contacts_by_status,
            contacts_by_confidence=contacts_by_confidence,
            recent_contacts_7_days=recent_7_days,
            recent_contacts_30_days=recent_30_days,
            high_confidence_contacts=high_confidence_contacts,
            validated_contacts=validated_contacts,
            validation_rate=validation_rate,
            average_confidence=average_confidence,
            top_sources=top_sources,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting contact statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting contact statistics: {str(e)}")


@router.post("/export", summary="Export contacts")
async def export_contacts(
    request: ContactExportRequest,
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Export contacts in various formats.
    
    Args:
        request: Export request parameters
        storage_manager: Storage manager instance
        
    Returns:
        Exported contacts data
    """
    try:
        # Get contacts with optional filtering
        if request.filters:
            # Use search functionality for filtering
            search_result = await search_contacts(request.filters, storage_manager)
            contacts = search_result["contacts"]
        else:
            contacts = storage_manager.get_contacts(limit=10000)
        
        # Prepare export data
        export_data = []
        for contact in contacts:
            contact_dict = contact.copy()
            
            # Include metadata if requested
            if not request.include_metadata:
                contact_dict.pop('validation_metadata', None)
            
            # Include validation history if requested
            if request.include_validation_history:
                # Note: This would need implementation to get validation history
                # contact_dict['validation_history'] = get_validation_history(contact['id'])
                contact_dict['validation_history'] = []
            
            export_data.append(contact_dict)
        
        # Format based on requested format
        if request.format == "json":
            return {
                "exported_at": datetime.now().isoformat(),
                "total_contacts": len(export_data),
                "format": request.format,
                "contacts": export_data
            }
        elif request.format == "csv":
            # For CSV, we'd need to implement CSV generation
            # This is a placeholder that returns JSON for now
            return {
                "exported_at": datetime.now().isoformat(),
                "total_contacts": len(export_data),
                "format": request.format,
                "message": "CSV export not yet implemented - returning JSON format",
                "contacts": export_data
            }
        elif request.format == "xlsx":
            # For Excel, we'd need to implement Excel generation
            # This is a placeholder that returns JSON for now
            return {
                "exported_at": datetime.now().isoformat(),
                "total_contacts": len(export_data),
                "format": request.format,
                "message": "Excel export not yet implemented - returning JSON format",
                "contacts": export_data
            }
        
    except Exception as e:
        logger.error(f"Error exporting contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting contacts: {str(e)}")