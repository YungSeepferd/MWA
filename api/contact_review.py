"""
Enhanced contact review API for MWA Core with dashboard integration.

Provides comprehensive API endpoints for:
- Contact review and management
- Validation result analysis
- Contact approval workflows
- Bulk operations
- Export functionality
- Real-time updates
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv
from io import StringIO

from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from mwa_core.contact.models import (
    Contact, ContactMethod, ContactStatus, ConfidenceLevel
)
from mwa_core.contact.integration import ContactDiscoveryIntegration
from mwa_core.contact.validators import ContactValidator, ValidationResult
from mwa_core.storage.operations import StorageOperations
from mwa_core.storage.models import Contact as StorageContact, ContactValidation, Listing
from mwa_core.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ContactReviewRequest(BaseModel):
    """Request model for contact review operations."""
    contact_ids: List[int]
    action: str = Field(..., regex="^(approve|reject|flag|validate)$")
    reason: Optional[str] = None
    confidence_level: Optional[str] = None


class ContactBulkOperationRequest(BaseModel):
    """Request model for bulk contact operations."""
    contact_ids: List[int]
    operation: str = Field(..., regex="^(validate|export|delete|merge)$")
    parameters: Optional[Dict[str, Any]] = {}


class ContactSearchRequest(BaseModel):
    """Request model for contact search."""
    query: Optional[str] = None
    contact_type: Optional[str] = None
    status: Optional[str] = None
    confidence_min: Optional[float] = 0.0
    confidence_max: Optional[float] = 1.0
    listing_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class ContactExportRequest(BaseModel):
    """Request model for contact export."""
    contact_ids: Optional[List[int]] = None
    format: str = Field("csv", regex="^(csv|json|xlsx)$")
    include_metadata: bool = True
    include_validation_history: bool = False


class ContactResponse(BaseModel):
    """Response model for contact data."""
    id: int
    listing_id: Optional[int]
    type: str
    value: str
    confidence: float
    source: str
    status: str
    validated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    validation_history: Optional[List[Dict[str, Any]]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ContactStatisticsResponse(BaseModel):
    """Response model for contact statistics."""
    total_contacts: int
    contacts_by_type: Dict[str, int]
    contacts_by_status: Dict[str, int]
    contacts_by_confidence: Dict[str, int]
    recent_contacts_7_days: int
    recent_contacts_30_days: int
    high_confidence_contacts: int
    verified_contacts: int
    validation_rate: float
    average_confidence: float
    top_sources: List[Dict[str, Any]]
    validation_failures_7_days: int
    timestamp: datetime


class ContactReviewDashboard:
    """
    Enhanced contact review dashboard with comprehensive management capabilities.
    
    Features:
    - Contact review and approval workflows
    - Bulk operations and management
    - Advanced search and filtering
    - Export functionality
    - Real-time statistics
    - Validation integration
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.integration = ContactDiscoveryIntegration(settings)
        self.validator = ContactValidator(
            enable_smtp_verification=settings.contact_discovery.smtp_verification,
            enable_dns_verification=settings.contact_discovery.dns_verification
        )
    
    async def get_contacts_for_review(self, 
                                    status: str = "unvalidated",
                                    confidence_min: float = 0.0,
                                    limit: int = 50,
                                    offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get contacts that need review.
        
        Args:
            status: Contact status to filter by
            confidence_min: Minimum confidence threshold
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple of (contacts, total_count)
        """
        try:
            with self.integration.storage_ops.get_session() as session:
                # Build query
                query = session.query(StorageContact).filter(
                    StorageContact.status == status,
                    StorageContact.confidence >= confidence_min
                )
                
                # Get total count
                total_count = query.count()
                
                # Get paginated results
                contacts = query.order_by(
                    StorageContact.confidence.desc(),
                    StorageContact.created_at.desc()
                ).offset(offset).limit(limit).all()
                
                # Convert to response format
                contact_data = []
                for contact in contacts:
                    contact_dict = {
                        'id': contact.id,
                        'listing_id': contact.listing_id,
                        'type': contact.type,
                        'value': contact.value,
                        'confidence': contact.confidence,
                        'source': contact.source,
                        'status': contact.status,
                        'validated_at': contact.validated_at.isoformat() if contact.validated_at else None,
                        'created_at': contact.created_at.isoformat(),
                        'updated_at': contact.updated_at.isoformat(),
                        'validation_history': self._get_validation_history(session, contact.id),
                        'metadata': json.loads(contact.validation_metadata) if contact.validation_metadata else {}
                    }
                    contact_data.append(contact_dict)
                
                return contact_data, total_count
                
        except Exception as e:
            logger.error(f"Error getting contacts for review: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving contacts: {str(e)}")
    
    async def review_contacts(self, request: ContactReviewRequest) -> Dict[str, Any]:
        """
        Review and update contact status.
        
        Args:
            request: Contact review request
            
        Returns:
            Review results
        """
        try:
            results = []
            total_processed = 0
            
            with self.integration.storage_ops.get_session() as session:
                for contact_id in request.contact_ids:
                    contact = session.query(StorageContact).filter(StorageContact.id == contact_id).first()
                    if not contact:
                        results.append({
                            'contact_id': contact_id,
                            'success': False,
                            'error': 'Contact not found'
                        })
                        continue
                    
                    # Apply review action
                    if request.action == "approve":
                        contact.status = "valid"
                        contact.validated_at = datetime.now()
                    elif request.action == "reject":
                        contact.status = "invalid"
                        contact.validated_at = datetime.now()
                    elif request.action == "flag":
                        contact.status = "suspicious"
                        contact.validated_at = datetime.now()
                    elif request.action == "validate":
                        # Run validation
                        from mwa_core.contact.models import Contact, ContactMethod, ConfidenceLevel
                        discovery_contact = Contact(
                            method=ContactMethod(contact.type),
                            value=contact.value,
                            confidence=ConfidenceLevel(contact.confidence),
                            source_url="manual_review",
                            verification_status=ContactStatus.UNVERIFIED
                        )
                        
                        validation_result = await self.validator.validate_contact(discovery_contact)
                        
                        # Update contact based on validation
                        if validation_result.is_valid:
                            contact.status = "valid"
                        else:
                            contact.status = "invalid"
                        
                        contact.validated_at = datetime.now()
                        
                        # Store validation result
                        validation_record = ContactValidation(
                            contact_id=contact.id,
                            validation_method=validation_result.validation_method,
                            validation_result=validation_result.is_valid,
                            confidence_score=validation_result.confidence_score,
                            validation_metadata=json.dumps(validation_result.metadata)
                        )
                        session.add(validation_record)
                    
                    # Update metadata
                    if request.reason:
                        metadata = json.loads(contact.validation_metadata or '{}')
                        metadata['review_reason'] = request.reason
                        metadata['reviewed_by'] = 'manual_review'
                        metadata['reviewed_at'] = datetime.now().isoformat()
                        contact.validation_metadata = json.dumps(metadata)
                    
                    contact.updated_at = datetime.now()
                    total_processed += 1
                    
                    results.append({
                        'contact_id': contact_id,
                        'success': True,
                        'new_status': contact.status,
                        'action': request.action
                    })
                
                session.commit()
            
            logger.info(f"Reviewed {total_processed} contacts with action {request.action}")
            
            return {
                'success': True,
                'total_processed': total_processed,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reviewing contacts: {e}")
            raise HTTPException(status_code=500, detail=f"Error reviewing contacts: {str(e)}")
    
    async def bulk_operation(self, request: ContactBulkOperationRequest) -> Dict[str, Any]:
        """
        Perform bulk operations on contacts.
        
        Args:
            request: Bulk operation request
            
        Returns:
            Operation results
        """
        try:
            results = []
            total_processed = 0
            
            with self.integration.storage_ops.get_session() as session:
                if request.operation == "validate":
                    # Bulk validation
                    for contact_id in request.contact_ids:
                        contact = session.query(StorageContact).filter(StorageContact.id == contact_id).first()
                        if not contact:
                            results.append({
                                'contact_id': contact_id,
                                'success': False,
                                'error': 'Contact not found'
                            })
                            continue
                        
                        # Run validation
                        from mwa_core.contact.models import Contact, ContactMethod, ConfidenceLevel
                        discovery_contact = Contact(
                            method=ContactMethod(contact.type),
                            value=contact.value,
                            confidence=ConfidenceLevel(contact.confidence),
                            source_url="bulk_validation",
                            verification_status=ContactStatus.UNVERIFIED
                        )
                        
                        validation_result = await self.validator.validate_contact(discovery_contact)
                        
                        # Update contact
                        if validation_result.is_valid:
                            contact.status = "valid"
                        else:
                            contact.status = "invalid"
                        
                        contact.validated_at = datetime.now()
                        
                        # Store validation result
                        validation_record = ContactValidation(
                            contact_id=contact.id,
                            validation_method=validation_result.validation_method,
                            validation_result=validation_result.is_valid,
                            confidence_score=validation_result.confidence_score,
                            validation_metadata=json.dumps(validation_result.metadata)
                        )
                        session.add(validation_record)
                        
                        contact.updated_at = datetime.now()
                        total_processed += 1
                        
                        results.append({
                            'contact_id': contact_id,
                            'success': True,
                            'new_status': contact.status,
                            'validation_confidence': validation_result.confidence_score
                        })
                
                elif request.operation == "export":
                    # Export operation handled separately
                    return await self.export_contacts(ContactExportRequest(
                        contact_ids=request.contact_ids,
                        format=request.parameters.get('format', 'csv'),
                        include_metadata=request.parameters.get('include_metadata', True),
                        include_validation_history=request.parameters.get('include_validation_history', False)
                    ))
                
                elif request.operation == "delete":
                    # Bulk delete
                    deleted_count = 0
                    for contact_id in request.contact_ids:
                        contact = session.query(StorageContact).filter(StorageContact.id == contact_id).first()
                        if contact:
                            session.delete(contact)
                            deleted_count += 1
                    
                    total_processed = deleted_count
                    results.append({
                        'operation': 'delete',
                        'deleted_count': deleted_count
                    })
                
                elif request.operation == "merge":
                    # Contact merging logic
                    # This would implement intelligent merging of duplicate contacts
                    pass
                
                session.commit()
            
            logger.info(f"Bulk operation {request.operation} completed for {total_processed} contacts")
            
            return {
                'success': True,
                'total_processed': total_processed,
                'operation': request.operation,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}")
            raise HTTPException(status_code=500, detail=f"Error in bulk operation: {str(e)}")
    
    async def export_contacts(self, request: ContactExportRequest) -> StreamingResponse:
        """
        Export contacts in various formats.
        
        Args:
            request: Export request
            
        Returns:
            StreamingResponse with exported data
        """
        try:
            # Get contacts to export
            if request.contact_ids:
                with self.integration.storage_ops.get_session() as session:
                    contacts = session.query(StorageContact).filter(
                        StorageContact.id.in_(request.contact_ids)
                    ).all()
            else:
                # Export all contacts
                with self.integration.storage_ops.get_session() as session:
                    contacts = session.query(StorageContact).all()
            
            if not contacts:
                raise HTTPException(status_code=404, detail="No contacts found to export")
            
            # Prepare data
            export_data = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'listing_id': contact.listing_id,
                    'type': contact.type,
                    'value': contact.value,
                    'confidence': contact.confidence,
                    'source': contact.source,
                    'status': contact.status,
                    'validated_at': contact.validated_at.isoformat() if contact.validated_at else None,
                    'created_at': contact.created_at.isoformat(),
                    'updated_at': contact.updated_at.isoformat()
                }
                
                if request.include_metadata:
                    contact_dict['metadata'] = json.loads(contact.validation_metadata) if contact.validation_metadata else {}
                
                if request.include_validation_history:
                    contact_dict['validation_history'] = self._get_validation_history(session, contact.id)
                
                export_data.append(contact_dict)
            
            # Generate export based on format
            if request.format == "csv":
                return self._export_csv(export_data, "contacts_export.csv")
            elif request.format == "json":
                return self._export_json(export_data, "contacts_export.json")
            elif request.format == "xlsx":
                return self._export_excel(export_data, "contacts_export.xlsx")
            else:
                raise HTTPException(status_code=400, detail="Unsupported export format")
                
        except Exception as e:
            logger.error(f"Error exporting contacts: {e}")
            raise HTTPException(status_code=500, detail=f"Error exporting contacts: {str(e)}")
    
    def get_contact_statistics(self) -> ContactStatisticsResponse:
        """
        Get comprehensive contact statistics.
        
        Returns:
            Contact statistics
        """
        try:
            stats = self.integration.get_contact_statistics()
            
            # Calculate additional metrics
            with self.integration.storage_ops.get_session() as session:
                # Validation rate
                total_validated = session.query(StorageContact).filter(
                    StorageContact.status.in_(["valid", "invalid"])
                ).count()
                
                total_valid = session.query(StorageContact).filter(
                    StorageContact.status == "valid"
                ).count()
                
                validation_rate = (total_valid / total_validated * 100) if total_validated > 0 else 0
                
                # Average confidence
                avg_confidence = session.query(func.avg(StorageContact.confidence)).scalar() or 0
                
                # Validation failures in last 7 days
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=7)
                
                validation_failures = session.query(ContactValidation).join(StorageContact).filter(
                    ContactValidation.validation_result == False,
                    StorageContact.created_at >= cutoff_date
                ).count()
                
                # Top sources
                top_sources_query = session.query(
                    StorageContact.source,
                    func.count(StorageContact.id).label('count')
                ).group_by(StorageContact.source).order_by(
                    func.count(StorageContact.id).desc()
                ).limit(10).all()
                
                top_sources = [
                    {'source': source, 'count': count}
                    for source, count in top_sources_query
                ]
            
            return ContactStatisticsResponse(
                total_contacts=stats['total_contacts'],
                contacts_by_type=stats['contacts_by_type'],
                contacts_by_status=stats['contacts_by_status'],
                contacts_by_confidence=stats['contacts_by_confidence'],
                recent_contacts_7_days=stats['recent_contacts_30_days'] // 4,  # Approximate
                recent_contacts_30_days=stats['recent_contacts_30_days'],
                high_confidence_contacts=stats['high_confidence_contacts'],
                verified_contacts=stats.get('contacts_by_status', {}).get('valid', 0),
                validation_rate=validation_rate,
                average_confidence=avg_confidence,
                top_sources=top_sources,
                validation_failures_7_days=validation_failures,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting contact statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")
    
    async def search_contacts(self, request: ContactSearchRequest) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search contacts with advanced filtering.
        
        Args:
            request: Search request
            
        Returns:
            Tuple of (contacts, total_count)
        """
        try:
            with self.integration.storage_ops.get_session() as session:
                # Build query
                query = session.query(StorageContact)
                
                # Apply filters
                if request.query:
                    query = query.filter(
                        or_(
                            StorageContact.value.contains(request.query),
                            StorageContact.source.contains(request.query)
                        )
                    )
                
                if request.contact_type:
                    query = query.filter(StorageContact.type == request.contact_type)
                
                if request.status:
                    query = query.filter(StorageContact.status == request.status)
                
                if request.confidence_min is not None:
                    query = query.filter(StorageContact.confidence >= request.confidence_min)
                
                if request.confidence_max is not None:
                    query = query.filter(StorageContact.confidence <= request.confidence_max)
                
                if request.listing_id:
                    query = query.filter(StorageContact.listing_id == request.listing_id)
                
                if request.date_from:
                    query = query.filter(StorageContact.created_at >= request.date_from)
                
                if request.date_to:
                    query = query.filter(StorageContact.created_at <= request.date_to)
                
                # Get total count
                total_count = query.count()
                
                # Get paginated results
                contacts = query.order_by(
                    StorageContact.confidence.desc(),
                    StorageContact.created_at.desc()
                ).offset(request.offset).limit(request.limit).all()
                
                # Convert to response format
                contact_data = []
                for contact in contacts:
                    contact_dict = {
                        'id': contact.id,
                        'listing_id': contact.listing_id,
                        'type': contact.type,
                        'value': contact.value,
                        'confidence': contact.confidence,
                        'source': contact.source,
                        'status': contact.status,
                        'validated_at': contact.validated_at.isoformat() if contact.validated_at else None,
                        'created_at': contact.created_at.isoformat(),
                        'updated_at': contact.updated_at.isoformat()
                    }
                    contact_data.append(contact_dict)
                
                return contact_data, total_count
                
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            raise HTTPException(status_code=500, detail=f"Error searching contacts: {str(e)}")
    
    def _get_validation_history(self, session: Session, contact_id: int) -> List[Dict[str, Any]]:
        """Get validation history for a contact."""
        validations = session.query(ContactValidation).filter(
            ContactValidation.contact_id == contact_id
        ).order_by(ContactValidation.validated_at.desc()).all()
        
        history = []
        for validation in validations:
            history.append({
                'validation_method': validation.validation_method,
                'validation_result': validation.validation_result,
                'confidence_score': validation.confidence_score,
                'validated_at': validation.validated_at.isoformat(),
                'metadata': json.loads(validation.validation_metadata) if validation.validation_metadata else {}
            })
        
        return history
    
    def _export_csv(self, data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        """Export data as CSV."""
        output = StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    def _export_json(self, data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        """Export data as JSON."""
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'total_contacts': len(data),
            'contacts': data
        }
        
        return StreamingResponse(
            iter([json.dumps(json_data, indent=2, ensure_ascii=False)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    def _export_excel(self, data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        """Export data as Excel (simplified implementation)."""
        # For now, return CSV with Excel extension
        # In a real implementation, you would use openpyxl or similar
        return self._export_csv(data, filename.replace('.xlsx', '.csv'))


# FastAPI router setup
def create_contact_review_router(settings: Settings) -> FastAPI:
    """
    Create FastAPI router for contact review endpoints.
    
    Args:
        settings: Application settings
        
    Returns:
        FastAPI application with contact review endpoints
    """
    app = FastAPI(title="MWA Contact Review API", version="1.0.0")
    dashboard = ContactReviewDashboard(settings)
    
    @app.get("/contacts/review", response_model=Dict[str, Any])
    async def get_contacts_for_review(
        status: str = Query("unvalidated", regex="^(unvalidated|valid|invalid|suspicious)$"),
        confidence_min: float = Query(0.0, ge=0.0, le=1.0),
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0)
    ):
        """Get contacts that need review."""
        contacts, total = await dashboard.get_contacts_for_review(
            status=status,
            confidence_min=confidence_min,
            limit=limit,
            offset=offset
        )
        
        return {
            'contacts': contacts,
            'total': total,
            'limit': limit,
            'offset': offset,
            'status': status,
            'confidence_min': confidence_min
        }
    
    @app.post("/contacts/review", response_model=Dict[str, Any])
    async def review_contacts(request: ContactReviewRequest):
        """Review and update contact status."""
        return await dashboard.review_contacts(request)
    
    @app.post("/contacts/bulk", response_model=Dict[str, Any])
    async def bulk_operation(request: ContactBulkOperationRequest):
        """Perform bulk operations on contacts."""
        return await dashboard.bulk_operation(request)
    
    @app.post("/contacts/export")
    async def export_contacts(request: ContactExportRequest):
        """Export contacts in various formats."""
        return await dashboard.export_contacts(request)
    
    @app.get("/contacts/statistics", response_model=ContactStatisticsResponse)
    async def get_statistics():
        """Get comprehensive contact statistics."""
        return dashboard.get_contact_statistics()
    
    @app.post("/contacts/search", response_model=Dict[str, Any])
    async def search_contacts(request: ContactSearchRequest):
        """Search contacts with advanced filtering."""
        contacts, total = await dashboard.search_contacts(request)
        
        return {
            'contacts': contacts,
            'total': total,
            'limit': request.limit,
            'offset': request.offset,
            'search_params': request.dict(exclude_none=True)
        }
    
    @app.get("/contacts/{contact_id}", response_model=ContactResponse)
    async def get_contact(contact_id: int = FastAPIPath(..., gt=0)):
        """Get detailed information about a specific contact."""
        try:
            with dashboard.integration.storage_ops.get_session() as session:
                contact = session.query(StorageContact).filter(StorageContact.id == contact_id).first()
                if not contact:
                    raise HTTPException(status_code=404, detail="Contact not found")
                
                contact_dict = {
                    'id': contact.id,
                    'listing_id': contact.listing_id,
                    'type': contact.type,
                    'value': contact.value,
                    'confidence': contact.confidence,
                    'source': contact.source,
                    'status': contact.status,
                    'validated_at': contact.validated_at.isoformat() if contact.validated_at else None,
                    'created_at': contact.created_at.isoformat(),
                    'updated_at': contact.updated_at.isoformat(),
                    'validation_history': dashboard._get_validation_history(session, contact.id),
                    'metadata': json.loads(contact.validation_metadata) if contact.validation_metadata else {}
                }
                
                return ContactResponse(**contact_dict)
                
        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving contact: {str(e)}")
    
    @app.put("/contacts/{contact_id}/validate", response_model=Dict[str, Any])
    async def validate_contact(contact_id: int = FastAPIPath(..., gt=0),
                             validation_level: str = Query("standard", regex="^(basic|standard|comprehensive)$")):
        """Validate a specific contact."""
        try:
            with dashboard.integration.storage_ops.get_session() as session:
                contact = session.query(StorageContact).filter(StorageContact.id == contact_id).first()
                if not contact:
                    raise HTTPException(status_code=404, detail="Contact not found")
                
                # Convert to discovery contact
                                from mwa_core.contact.models import Contact, ContactMethod, ConfidenceLevel
                                discovery_contact = Contact(
                                    method=ContactMethod(contact.type),
                                    value=contact.value,
                                    confidence=ConfidenceLevel(contact.confidence),
                                    source_url="manual_validation",
                                    verification_status=ContactStatus.UNVERIFIED
                                )
                
                # Run validation
                validation_result = await dashboard.validator.validate_contact(discovery_contact, validation_level)
                
                # Update contact
                if validation_result.is_valid:
                    contact.status = "valid"
                else:
                    contact.status = "invalid"
                
                contact.validated_at = datetime.now()
                
                # Store validation result
                validation_record = ContactValidation(
                    contact_id=contact.id,
                    validation_method=validation_result.validation_method,
                    validation_result=validation_result.is_valid,
                    confidence_score=validation_result.confidence_score,
                    validation_metadata=json.dumps(validation_result.metadata)
                )
                session.add(validation_record)
                
                contact.updated_at = datetime.now()
                session.commit()
                
                return {
                    'success': True,
                    'contact_id': contact_id,
                    'is_valid': validation_result.is_valid,
                    'validation_method': validation_result.validation_method,
                    'confidence_score': validation_result.confidence_score,
                    'new_status': contact.status,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error validating contact {contact_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error validating contact: {str(e)}")
    
    @app.post("/contacts/discover", response_model=Dict[str, Any])
    async def discover_contacts_for_listing(
        listing_id: int = Query(..., gt=0),
        enable_crawling: bool = Query(True),
        enable_validation: bool = Query(True),
        max_depth: int = Query(2, ge=1, le=5)
    ):
        """Discover contacts for a specific listing."""
        try:
            with dashboard.integration.storage_ops.get_session() as session:
                listing = session.query(Listing).filter(Listing.id == listing_id).first()
                if not listing:
                    raise HTTPException(status_code=404, detail="Listing not found")
                
                listing_dict = {
                    'id': listing.id,
                    'title': listing.title,
                    'url': listing.url,
                    'description': listing.description,
                    'price': listing.price,
                    'address': listing.address
                }
                
                contacts, forms = await dashboard.integration.process_listing(listing_dict, listing_id)
                
                return {
                    'success': True,
                    'listing_id': listing_id,
                    'contacts_found': len(contacts),
                    'forms_found': len(forms),
                    'contacts': [c.to_dict() for c in contacts],
                    'forms': [f.to_contact().to_dict() for f in forms],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error discovering contacts for listing {listing_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error discovering contacts: {str(e)}")
    
    @app.get("/dashboard/overview", response_model=Dict[str, Any])
    async def get_dashboard_overview():
        """Get dashboard overview data."""
        try:
            stats = dashboard.get_contact_statistics()
            
            # Get recent activity
            with dashboard.integration.storage_ops.get_session() as session:
                from datetime import datetime, timedelta
                
                # Recent contacts (last 24 hours)
                yesterday = datetime.now() - timedelta(days=1)
                recent_contacts = session.query(StorageContact).filter(
                    StorageContact.created_at >= yesterday
                ).count()
                
                # Recent validations
                recent_validations = session.query(ContactValidation).filter(
                    ContactValidation.validated_at >= yesterday
                ).count()
                
                # Pending reviews
                pending_reviews = session.query(StorageContact).filter(
                    StorageContact.status == "unvalidated"
                ).count()
            
            return {
                'statistics': stats.dict(),
                'recent_activity': {
                    'contacts_24h': recent_contacts,
                    'validations_24h': recent_validations,
                    'pending_reviews': pending_reviews
                },
                'system_status': {
                    'contact_discovery_enabled': dashboard.settings.contact_discovery.enabled,
                    'validation_enabled': dashboard.settings.contact_discovery.validation_enabled,
                    'auto_cleanup_enabled': dashboard.settings.storage.auto_cleanup_enabled
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting dashboard overview: {str(e)}")


# Create the main API application
def create_contact_review_api(settings: Settings) -> FastAPI:
    """
    Create the main contact review API application.
    
    Args:
        settings: Application settings
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="MWA Contact Review API",
        version="1.0.0",
        description="Enhanced contact review and management API for MWA Core",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Include the contact review router
    contact_router = create_contact_review_router(settings)
    app.mount("/api/v1/contacts", contact_router)
    
    @app.get("/")
    async def root():
        return {
            "message": "MWA Contact Review API",
            "version": "1.0.0",
            "endpoints": {
                "contacts": "/api/v1/contacts",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    return app


# Convenience functions
async def start_contact_review_server(settings: Settings, host: str = "0.0.0.0", port: int = 8000):
    """
    Start the contact review server.
    
    Args:
        settings: Application settings
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn
    
    app = create_contact_review_api(settings)
    
    logger.info(f"Starting contact review server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Example usage
    settings = get_settings()
    asyncio.run(start_contact_review_server(settings))