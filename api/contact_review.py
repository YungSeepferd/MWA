"""
Contact Review Dashboard API.

This module provides a FastAPI-based API for reviewing and managing
extracted contacts through a web interface.
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from mafa.contacts.models import ContactMethod, ConfidenceLevel, ContactStatus
from mafa.contacts.storage import ContactStorage
from mafa.db.manager import ListingRepository

logger = logging.getLogger(__name__)

# Pydantic models for API
class ContactResponse(BaseModel):
    """Contact response model."""
    id: int
    source: str
    method: ContactMethod
    value: str
    confidence: ConfidenceLevel
    status: ContactStatus
    created_at: datetime
    updated_at: datetime
    context: Dict = Field(default_factory=dict)
    raw_data: Dict = Field(default_factory=dict)

class ContactUpdateRequest(BaseModel):
    """Contact update request model."""
    status: ContactStatus
    notes: Optional[str] = None

class ContactFilterRequest(BaseModel):
    """Contact filter request model."""
    method: Optional[ContactMethod] = None
    confidence: Optional[ConfidenceLevel] = None
    status: Optional[ContactStatus] = None
    source: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class ContactStatsResponse(BaseModel):
    """Contact statistics response model."""
    total_contacts: int
    contacts_by_method: Dict[str, int]
    contacts_by_status: Dict[str, int]
    contacts_by_confidence: Dict[str, int]
    recent_contacts_7_days: int
    top_sources: List[Dict[str, Union[str, int]]]

class ContactReviewDashboard:
    """
    Contact review dashboard for managing extracted contacts.
    
    Provides web interface for reviewing, approving, rejecting,
    and exporting contacts with confidence scoring.
    """
    
    def __init__(
        self,
        contact_storage: ContactStorage,
        listing_repository: Optional[ListingRepository] = None,
        templates_dir: Optional[Path] = None,
        static_dir: Optional[Path] = None
    ):
        """
        Initialize contact review dashboard.
        
        Args:
            contact_storage: Contact storage instance
            listing_repository: Listing repository instance (optional)
            templates_dir: Directory for HTML templates
            static_dir: Directory for static files (CSS, JS)
        """
        self.contact_storage = contact_storage
        self.listing_repository = listing_repository
        
        # Setup FastAPI app
        self.app = FastAPI(
            title="MAFA Contact Review Dashboard",
            description="Web interface for reviewing and managing extracted contacts",
            version="1.0.0"
        )
        
        # Setup templates and static files
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "dashboard" / "templates"
        self.static_dir = static_dir or Path(__file__).parent.parent / "dashboard" / "static"
        
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Mount static files
        if self.static_dir.exists():
            self.app.mount(
                "/static",
                StaticFiles(directory=str(self.static_dir)),
                name="static"
            )
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Contact review dashboard initialized")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Dashboard home page."""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/contacts", response_class=HTMLResponse)
        async def contacts_page(request: Request):
            """Contacts list page."""
            return self.templates.TemplateResponse("contacts.html", {"request": request})
        
        @self.app.get("/api/contacts", response_model=List[ContactResponse])
        async def get_contacts(
            method: Optional[ContactMethod] = Query(None),
            confidence: Optional[ConfidenceLevel] = Query(None),
            status: Optional[ContactStatus] = Query(None),
            source: Optional[str] = Query(None),
            date_from: Optional[datetime] = Query(None),
            date_to: Optional[datetime] = Query(None),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """Get contacts with optional filtering."""
            try:
                # Build filter conditions
                conditions = []
                params = {}
                
                if method:
                    conditions.append("method = :method")
                    params["method"] = method.value
                
                if confidence:
                    conditions.append("confidence = :confidence")
                    params["confidence"] = confidence.value
                
                if status:
                    conditions.append("status = :status")
                    params["status"] = status.value
                
                if source:
                    conditions.append("source LIKE :source")
                    params["source"] = f"%{source}%"
                
                if date_from:
                    conditions.append("created_at >= :date_from")
                    params["date_from"] = date_from
                
                if date_to:
                    conditions.append("created_at <= :date_to")
                    params["date_to"] = date_to
                
                # Build query
                query = "SELECT * FROM contacts"
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = offset
                
                # Execute query
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(query, params)
                    rows = cursor.fetchall()
                
                # Convert to response models
                contacts = []
                for row in rows:
                    contact = ContactResponse(
                        id=row["id"],
                    source=row["source"],
                    method=ContactMethod(row["method"]),
                    value=row["value"],
                    confidence=ConfidenceLevel(row["confidence"]),
                    status=ContactStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    context=json.loads(row["context"]) if row["context"] else {},
                    raw_data=json.loads(row["raw_data"]) if row["raw_data"] else {}
                )
                contacts.append(contact)
                
                return contacts
                
            except Exception as e:
                logger.error(f"Failed to fetch contacts: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch contacts")
        
        @self.app.get("/api/contacts/{contact_id}", response_model=ContactResponse)
        async def get_contact(contact_id: int):
            """Get a specific contact by ID."""
            try:
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(
                        "SELECT * FROM contacts WHERE id = ?",
                        (contact_id,)
                    )
                    row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Contact not found")
                
                return ContactResponse(
                    id=row["id"],
                    source=row["source"],
                    method=ContactMethod(row["method"]),
                    value=row["value"],
                    confidence=ConfidenceLevel(row["confidence"]),
                    status=ContactStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    context=json.loads(row["context"]) if row["context"] else {},
                    raw_data=json.loads(row["raw_data"]) if row["raw_data"] else {}
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to fetch contact {contact_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch contact")
        
        @self.app.patch("/api/contacts/{contact_id}", response_model=ContactResponse)
        async def update_contact(contact_id: int, request: ContactUpdateRequest):
            """Update a contact's status and notes."""
            try:
                # Check if contact exists
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(
                        "SELECT * FROM contacts WHERE id = ?",
                        (contact_id,)
                    )
                    row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Contact not found")
                
                # Update contact
                updated_at = datetime.utcnow()
                
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(
                        """
                        UPDATE contacts 
                        SET status = ?, notes = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (request.status.value, request.notes, updated_at.isoformat(), contact_id)
                    )
                    
                    # Fetch updated contact
                    cursor = self.contact_storage.conn.execute(
                        "SELECT * FROM contacts WHERE id = ?",
                        (contact_id,)
                    )
                    row = cursor.fetchone()
                
                return ContactResponse(
                    id=row["id"],
                    source=row["source"],
                    method=ContactMethod(row["method"]),
                    value=row["value"],
                    confidence=ConfidenceLevel(row["confidence"]),
                    status=ContactStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    context=json.loads(row["context"]) if row["context"] else {},
                    raw_data=json.loads(row["raw_data"]) if row["raw_data"] else {}
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to update contact {contact_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to update contact")
        
        @self.app.post("/api/contacts/bulk-update")
        async def bulk_update_contacts(
            contact_ids: List[int],
            status: ContactStatus,
            notes: Optional[str] = None
        ):
            """Bulk update contacts' status and notes."""
            try:
                if not contact_ids:
                    raise HTTPException(status_code=400, detail="No contact IDs provided")
                
                updated_at = datetime.utcnow()
                updated_count = 0
                
                with self.contact_storage.conn:
                    for contact_id in contact_ids:
                        cursor = self.contact_storage.conn.execute(
                            """
                            UPDATE contacts 
                            SET status = ?, notes = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (status.value, notes, updated_at.isoformat(), contact_id)
                        )
                        updated_count += cursor.rowcount
                
                return {
                    "success": True,
                    "updated_count": updated_count,
                    "message": f"Successfully updated {updated_count} contacts"
                }
                
            except Exception as e:
                logger.error(f"Failed to bulk update contacts: {e}")
                raise HTTPException(status_code=500, detail="Failed to bulk update contacts")
        
        @self.app.get("/api/contacts/stats", response_model=ContactStatsResponse)
        async def get_contact_stats():
            """Get contact statistics."""
            try:
                stats = self.contact_storage.get_contact_statistics()
                
                # Convert to response model
                return ContactStatsResponse(
                    total_contacts=stats["total_contacts"],
                    contacts_by_method=stats["contacts_by_method"],
                    contacts_by_status=stats["contacts_by_status"],
                    contacts_by_confidence=stats["contacts_by_confidence"],
                    recent_contacts_7_days=stats["recent_contacts_7_days"],
                    top_sources=stats["top_sources"]
                )
                
            except Exception as e:
                logger.error(f"Failed to fetch contact statistics: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch contact statistics")
        
        @self.app.get("/api/contacts/export")
        async def export_contacts(
            status: Optional[ContactStatus] = Query(None),
            format: str = Query("csv", regex="^(csv|json)$")
        ):
            """Export contacts in CSV or JSON format."""
            try:
                # Build query
                query = "SELECT * FROM contacts WHERE status = :status" if status else "SELECT * FROM contacts"
                params = {"status": status.value} if status else {}
                
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(query, params)
                    rows = cursor.fetchall()
                
                if format == "csv":
                    # Generate CSV
                    import csv
                    import io
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # Write header
                    writer.writerow([
                        "id", "source", "method", "value", "confidence",
                        "status", "created_at", "updated_at", "notes"
                    ])
                    
                    # Write data
                    for row in rows:
                        writer.writerow([
                            row["id"],
                            row["source"],
                            row["method"],
                            row["value"],
                            row["confidence"],
                            row["status"],
                            row["created_at"],
                            row["updated_at"],
                            row["notes"] or ""
                        ])
                    
                    content = output.getvalue()
                    output.close()
                    
                    return JSONResponse(
                        content={"csv": content},
                        headers={"Content-Type": "text/csv"}
                    )
                
                elif format == "json":
                    # Generate JSON
                    contacts = []
                    for row in rows:
                        contact = {
                            "id": row["id"],
                            "source": row["source"],
                            "method": row["method"],
                            "value": row["value"],
                            "confidence": row["confidence"],
                            "status": row["status"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "notes": row["notes"],
                            "context": json.loads(row["context"]) if row["context"] else {},
                            "raw_data": json.loads(row["raw_data"]) if row["raw_data"] else {}
                        }
                        contacts.append(contact)
                    
                    return JSONResponse(content={"contacts": contacts})
                
            except Exception as e:
                logger.error(f"Failed to export contacts: {e}")
                raise HTTPException(status_code=500, detail="Failed to export contacts")
        
        @self.app.get("/api/sources")
        async def get_sources():
            """Get unique sources."""
            try:
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute(
                        "SELECT DISTINCT source FROM contacts ORDER BY source"
                    )
                    rows = cursor.fetchall()
                
                sources = [row["source"] for row in rows]
                return {"sources": sources}
                
            except Exception as e:
                logger.error(f"Failed to fetch sources: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch sources")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                # Check database connectivity
                with self.contact_storage.conn:
                    cursor = self.contact_storage.conn.execute("SELECT 1")
                    cursor.fetchone()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "connected"
                }
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail="Health check failed")
    
    def run(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """
        Run the dashboard server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, log_level="debug" if debug else "info")


# Example usage
if __name__ == "__main__":
    from ..mafa.contacts.storage import ContactStorage
    
    # Initialize contact storage
    contact_storage = ContactStorage("data/contacts.db")
    
    # Initialize dashboard
    dashboard = ContactReviewDashboard(contact_storage)
    
    # Run dashboard
    dashboard.run(host="0.0.0.0", port=8080, debug=True)