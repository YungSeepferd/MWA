"""
Contact storage and persistence layer.

Provides database storage for discovered contacts with SQLite backend,
including schema creation, CRUD operations, and deduplication.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib

from .models import Contact, ContactForm, ContactMethod, ContactStatus, ConfidenceLevel
from ..exceptions import DatabaseError
from ..security import SecurityValidator


class ContactStorage:
    """
    SQLite-based storage for contact information.
    
    Provides methods to store, retrieve, and manage contacts and forms
    discovered during the scraping process.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize contact storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                # Contacts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        method TEXT NOT NULL,
                        value TEXT NOT NULL,
                        confidence TEXT NOT NULL,
                        verification_status TEXT NOT NULL DEFAULT 'unverified',
                        source_url TEXT NOT NULL,
                        discovery_path TEXT,  -- JSON array
                        timestamp TEXT NOT NULL,
                        metadata TEXT,  -- JSON object
                        contact_hash TEXT UNIQUE NOT NULL,
                        listing_id INTEGER,  -- Foreign key to listings
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (listing_id) REFERENCES listings (id)
                    )
                """)
                
                # Contact forms table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS contact_forms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_url TEXT NOT NULL,
                        method TEXT NOT NULL DEFAULT 'POST',
                        fields TEXT,  -- JSON array
                        required_fields TEXT,  -- JSON array
                        csrf_token TEXT,
                        source_url TEXT NOT NULL,
                        confidence TEXT NOT NULL,
                        metadata TEXT,  -- JSON object
                        contact_hash TEXT UNIQUE NOT NULL,
                        listing_id INTEGER,  -- Foreign key to listings
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (listing_id) REFERENCES listings (id)
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contacts_method 
                    ON contacts(method)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contacts_source_url 
                    ON contacts(source_url)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contacts_contact_hash 
                    ON contacts(contact_hash)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contacts_listing_id 
                    ON contacts(listing_id)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contact_forms_action_url 
                    ON contact_forms(action_url)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contact_forms_listing_id 
                    ON contact_forms(listing_id)
                """)
                
                conn.commit()
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create contact tables: {str(e)}")
    
    def store_contact(self, contact: Contact, listing_id: Optional[int] = None) -> bool:
        """
        Store a single contact in the database.
        
        Args:
            contact: Contact to store
            listing_id: Associated listing ID (optional)
            
        Returns:
            True if stored successfully, False if duplicate
        """
        try:
            # Sanitize contact data
            sanitized_value = SecurityValidator.sanitize_text(contact.value, max_length=500)
            sanitized_source_url = SecurityValidator.sanitize_text(contact.source_url, max_length=1000)
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO contacts (
                        method, value, confidence, verification_status,
                        source_url, discovery_path, timestamp, metadata,
                        contact_hash, listing_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact.method.value,
                    sanitized_value,
                    contact.confidence.value,
                    contact.verification_status.value,
                    sanitized_source_url,
                    json.dumps(contact.discovery_path),
                    contact.timestamp.isoformat(),
                    json.dumps(contact.metadata),
                    contact.contact_hash,
                    listing_id
                ))
                
                # Check if insertion was successful
                return conn.total_changes > 0
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to store contact: {str(e)}")
    
    def store_contacts(self, contacts: List[Contact], listing_id: Optional[int] = None) -> Dict[str, int]:
        """
        Store multiple contacts with summary of results.
        
        Args:
            contacts: List of contacts to store
            listing_id: Associated listing ID (optional)
            
        Returns:
            Dictionary with counts of stored, duplicate, and failed contacts
        """
        summary = {
            'stored': 0,
            'duplicates': 0,
            'failed': 0
        }
        
        for contact in contacts:
            try:
                if self.store_contact(contact, listing_id):
                    summary['stored'] += 1
                else:
                    summary['duplicates'] += 1
            except Exception as e:
                summary['failed'] += 1
        
        return summary
    
    def store_contact_form(self, form: ContactForm, listing_id: Optional[int] = None) -> bool:
        """
        Store a contact form in the database.
        
        Args:
            form: Contact form to store
            listing_id: Associated listing ID (optional)
            
        Returns:
            True if stored successfully, False if duplicate
        """
        try:
            # Sanitize form data
            sanitized_action_url = SecurityValidator.sanitize_text(form.action_url, max_length=1000)
            sanitized_source_url = SecurityValidator.sanitize_text(form.source_url, max_length=1000)
            
            # Generate hash for deduplication
            hash_input = f"form:{sanitized_action_url}:{sanitized_source_url}"
            form_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO contact_forms (
                        action_url, method, fields, required_fields,
                        csrf_token, source_url, confidence, metadata,
                        contact_hash, listing_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sanitized_action_url,
                    form.method,
                    json.dumps(form.fields),
                    json.dumps(form.required_fields),
                    form.csrf_token,
                    sanitized_source_url,
                    form.confidence.value,
                    json.dumps(form.metadata),
                    form_hash,
                    listing_id
                ))
                
                # Check if insertion was successful
                return conn.total_changes > 0
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to store contact form: {str(e)}")
    
    def get_contacts_by_listing(self, listing_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all contacts for a specific listing.
        
        Args:
            listing_id: ID of the listing
            
        Returns:
            List of contact dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM contacts 
                    WHERE listing_id = ? 
                    ORDER BY confidence DESC, timestamp DESC
                """, (listing_id,))
                
                contacts = []
                for row in cursor.fetchall():
                    contact_dict = dict(row)
                    contact_dict['discovery_path'] = json.loads(contact_dict['discovery_path'] or '[]')
                    contact_dict['metadata'] = json.loads(contact_dict['metadata'] or '{}')
                    contacts.append(contact_dict)
                
                return contacts
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve contacts for listing {listing_id}: {str(e)}")
    
    def get_contacts_by_source(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Retrieve all contacts from a specific source URL.
        
        Args:
            source_url: Source URL to filter by
            
        Returns:
            List of contact dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM contacts 
                    WHERE source_url = ? 
                    ORDER BY confidence DESC, timestamp DESC
                """, (source_url,))
                
                contacts = []
                for row in cursor.fetchall():
                    contact_dict = dict(row)
                    contact_dict['discovery_path'] = json.loads(contact_dict['discovery_path'] or '[]')
                    contact_dict['metadata'] = json.loads(contact_dict['metadata'] or '{}')
                    contacts.append(contact_dict)
                
                return contacts
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve contacts from {source_url}: {str(e)}")
    
    def get_contacts_by_method(self, method: ContactMethod) -> List[Dict[str, Any]]:
        """
        Retrieve all contacts of a specific method type.
        
        Args:
            method: Contact method to filter by
            
        Returns:
            List of contact dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM contacts 
                    WHERE method = ? 
                    ORDER BY confidence DESC, timestamp DESC
                """, (method.value,))
                
                contacts = []
                for row in cursor.fetchall():
                    contact_dict = dict(row)
                    contact_dict['discovery_path'] = json.loads(contact_dict['discovery_path'] or '[]')
                    contact_dict['metadata'] = json.loads(contact_dict['metadata'] or '{}')
                    contacts.append(contact_dict)
                
                return contacts
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve contacts by method {method.value}: {str(e)}")
    
    def update_contact_verification(self, contact_id: int, status: ContactStatus, metadata: Optional[Dict] = None) -> bool:
        """
        Update contact verification status.
        
        Args:
            contact_id: ID of the contact
            status: New verification status
            metadata: Additional metadata to update
            
        Returns:
            True if update was successful
        """
        try:
            with self._get_connection() as conn:
                if metadata:
                    # Merge with existing metadata
                    cursor = conn.execute("""
                        SELECT metadata FROM contacts WHERE id = ?
                    """, (contact_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        existing_metadata = json.loads(row[0] or '{}')
                        existing_metadata.update(metadata)
                        metadata_json = json.dumps(existing_metadata)
                    else:
                        metadata_json = json.dumps(metadata)
                else:
                    metadata_json = None
                
                conn.execute("""
                    UPDATE contacts 
                    SET verification_status = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status.value, metadata_json, contact_id))
                
                return conn.total_changes > 0
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update contact verification status: {str(e)}")
    
    def get_contact_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about stored contacts.
        
        Returns:
            Dictionary with contact statistics
        """
        try:
            with self._get_connection() as conn:
                # Total contacts
                total_cursor = conn.execute("SELECT COUNT(*) FROM contacts")
                total_contacts = total_cursor.fetchone()[0]
                
                # Contacts by method
                method_cursor = conn.execute("""
                    SELECT method, COUNT(*) as count 
                    FROM contacts 
                    GROUP BY method
                """)
                contacts_by_method = {row[0]: row[1] for row in method_cursor.fetchall()}
                
                # Contacts by verification status
                status_cursor = conn.execute("""
                    SELECT verification_status, COUNT(*) as count 
                    FROM contacts 
                    GROUP BY verification_status
                """)
                contacts_by_status = {row[0]: row[1] for row in status_cursor.fetchall()}
                
                # Contacts by confidence level
                confidence_cursor = conn.execute("""
                    SELECT confidence, COUNT(*) as count 
                    FROM contacts 
                    GROUP BY confidence
                """)
                contacts_by_confidence = {row[0]: row[1] for row in confidence_cursor.fetchall()}
                
                # Recent activity (last 7 days)
                recent_cursor = conn.execute("""
                    SELECT COUNT(*) FROM contacts 
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                recent_contacts = recent_cursor.fetchone()[0]
                
                # Top sources
                sources_cursor = conn.execute("""
                    SELECT source_url, COUNT(*) as count 
                    FROM contacts 
                    GROUP BY source_url 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                top_sources = [dict(row) for row in sources_cursor.fetchall()]
                
                return {
                    'total_contacts': total_contacts,
                    'contacts_by_method': contacts_by_method,
                    'contacts_by_status': contacts_by_status,
                    'contacts_by_confidence': contacts_by_confidence,
                    'recent_contacts_7_days': recent_contacts,
                    'top_sources': top_sources
                }
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get contact statistics: {str(e)}")
    
    def search_contacts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search contacts by value or metadata content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching contact dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM contacts 
                    WHERE value LIKE ? OR metadata LIKE ?
                    ORDER BY confidence DESC, timestamp DESC
                    LIMIT ?
                """, (f'%{query}%', f'%{query}%', limit))
                
                contacts = []
                for row in cursor.fetchall():
                    contact_dict = dict(row)
                    contact_dict['discovery_path'] = json.loads(contact_dict['discovery_path'] or '[]')
                    contact_dict['metadata'] = json.loads(contact_dict['metadata'] or '{}')
                    contacts.append(contact_dict)
                
                return contacts
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to search contacts: {str(e)}")
    
    def cleanup_old_contacts(self, days_old: int = 90) -> int:
        """
        Remove contacts older than specified days.
        
        Args:
            days_old: Number of days after which contacts should be deleted
            
        Returns:
            Number of contacts deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM contacts 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to cleanup old contacts: {str(e)}")
    
    def get_contact_forms_by_listing(self, listing_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all contact forms for a specific listing.
        
        Args:
            listing_id: ID of the listing
            
        Returns:
            List of form dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM contact_forms 
                    WHERE listing_id = ? 
                    ORDER BY confidence DESC, created_at DESC
                """, (listing_id,))
                
                forms = []
                for row in cursor.fetchall():
                    form_dict = dict(row)
                    form_dict['fields'] = json.loads(form_dict['fields'] or '[]')
                    form_dict['required_fields'] = json.loads(form_dict['required_fields'] or '[]')
                    form_dict['metadata'] = json.loads(form_dict['metadata'] or '{}')
                    forms.append(form_dict)
                
                return forms
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve forms for listing {listing_id}: {str(e)}")
    
    def optimize_database(self) -> None:
        """Optimize database performance."""
        try:
            with self._get_connection() as conn:
                # Analyze table statistics
                conn.execute("ANALYZE")
                
                # Vacuum to reclaim space
                conn.execute("VACUUM")
                
                # Set performance pragmas
                conn.execute("PRAGMA optimize")
                
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to optimize database: {str(e)}")