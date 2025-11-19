"""
Backup and restore functionality for MWA Core storage system.

Provides data backup, restore, export/import functionality, and data integrity checks.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, BinaryIO
from zipfile import ZipFile, ZIP_DEFLATED

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .models import Base, BackupMetadata
from .schema import DatabaseSchema

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backup and restore operations."""
    
    def __init__(self, database_schema: DatabaseSchema):
        """
        Initialize backup manager.
        
        Args:
            database_schema: DatabaseSchema instance
        """
        self.schema = database_schema
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_full_backup(self, backup_name: Optional[str] = None, 
                          compress: bool = True) -> Optional[str]:
        """
        Create a full database backup.
        
        Args:
            backup_name: Optional backup name, defaults to timestamp
            compress: Whether to compress the backup
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not backup_name:
                backup_name = f"full_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup metadata
            backup_metadata = BackupMetadata(
                backup_type="full",
                backup_path="",
                status="running",
                created_by="system"
            )
            
            with self.schema.get_session() as session:
                session.add(backup_metadata)
                session.flush()
                
                # Create backup file
                backup_path = self.backup_dir / f"{backup_name}.sql"
                if compress:
                    backup_path = backup_path.with_suffix('.sql.gz')
                
                # Export database
                success = self._export_database(backup_path, compress)
                
                if success:
                    # Calculate file size and checksum
                    file_size = backup_path.stat().st_size
                    checksum = self._calculate_file_checksum(backup_path)
                    
                    # Update backup metadata
                    backup_metadata.backup_path = str(backup_path)
                    backup_metadata.backup_size_mb = file_size / (1024 * 1024)
                    backup_metadata.status = "completed"
                    backup_metadata.completed_at = datetime.utcnow()
                    backup_metadata.checksum = checksum
                    
                    logger.info(f"Full backup created: {backup_path} ({file_size} bytes)")
                    return str(backup_path)
                else:
                    backup_metadata.status = "failed"
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            return None
    
    def create_schema_backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """
        Create a schema-only backup.
        
        Args:
            backup_name: Optional backup name
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not backup_name:
                backup_name = f"schema_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            backup_metadata = BackupMetadata(
                backup_type="schema",
                backup_path="",
                status="running",
                created_by="system"
            )
            
            with self.schema.get_session() as session:
                session.add(backup_metadata)
                session.flush()
                
                backup_path = self.backup_dir / f"{backup_name}_schema.sql"
                
                # Export schema only
                success = self._export_schema(backup_path)
                
                if success:
                    file_size = backup_path.stat().st_size
                    checksum = self._calculate_file_checksum(backup_path)
                    
                    backup_metadata.backup_path = str(backup_path)
                    backup_metadata.backup_size_mb = file_size / (1024 * 1024)
                    backup_metadata.status = "completed"
                    backup_metadata.completed_at = datetime.utcnow()
                    backup_metadata.checksum = checksum
                    
                    logger.info(f"Schema backup created: {backup_path}")
                    return str(backup_path)
                else:
                    backup_metadata.status = "failed"
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating schema backup: {e}")
            return None
    
    def create_incremental_backup(self, last_backup_date: datetime, 
                                backup_name: Optional[str] = None) -> Optional[str]:
        """
        Create an incremental backup with changes since last backup.
        
        Args:
            last_backup_date: Date of last backup
            backup_name: Optional backup name
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not backup_name:
                backup_name = f"incremental_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            backup_metadata = BackupMetadata(
                backup_type="incremental",
                backup_path="",
                status="running",
                created_by="system"
            )
            
            with self.schema.get_session() as session:
                session.add(backup_metadata)
                session.flush()
                
                backup_path = self.backup_dir / f"{backup_name}.json.gz"
                
                # Export changed data
                success = self._export_incremental_data(backup_path, last_backup_date)
                
                if success:
                    file_size = backup_path.stat().st_size
                    checksum = self._calculate_file_checksum(backup_path)
                    
                    backup_metadata.backup_path = str(backup_path)
                    backup_metadata.backup_size_mb = file_size / (1024 * 1024)
                    backup_metadata.status = "completed"
                    backup_metadata.completed_at = datetime.utcnow()
                    backup_metadata.checksum = checksum
                    
                    logger.info(f"Incremental backup created: {backup_path}")
                    return str(backup_path)
                else:
                    backup_metadata.status = "failed"
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str, verify_checksum: bool = True) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            verify_checksum: Whether to verify checksum before restore
            
        Returns:
            True if restore successful
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Verify checksum if requested
            if verify_checksum:
                if not self._verify_backup_checksum(backup_path):
                    logger.error("Backup checksum verification failed")
                    return False
            
            # Determine backup type and restore accordingly
            if backup_path.endswith("_schema.sql"):
                return self._restore_schema(backup_path)
            elif backup_path.endswith(".json.gz"):
                return self._restore_incremental_data(backup_path)
            else:
                return self._restore_full_backup(backup_path)
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def export_data(self, format_type: str = "json", 
                   filters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Export data in various formats.
        
        Args:
            format_type: Export format (json, csv, xml)
            filters: Optional filters for data export
            
        Returns:
            Path to exported file or None if failed
        """
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            export_path = self.backup_dir / f"export_{timestamp}.{format_type}"
            
            if format_type == "json":
                return self._export_json(export_path, filters)
            elif format_type == "csv":
                return self._export_csv(export_path, filters)
            elif format_type == "xml":
                return self._export_xml(export_path, filters)
            else:
                logger.error(f"Unsupported export format: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None
    
    def import_data(self, import_path: str, format_type: str = "json") -> bool:
        """
        Import data from various formats.
        
        Args:
            import_path: Path to import file
            format_type: Import format
            
        Returns:
            True if import successful
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            if format_type == "json":
                return self._import_json(import_path)
            elif format_type == "csv":
                return self._import_csv(import_path)
            elif format_type == "xml":
                return self._import_xml(import_path)
            else:
                logger.error(f"Unsupported import format: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """
        Verify data integrity and consistency.
        
        Returns:
            Dictionary with integrity check results
        """
        try:
            results = {
                "valid": True,
                "checks": {},
                "errors": [],
                "warnings": []
            }
            
            # Check 1: Verify table relationships
            relationship_check = self._check_relationships()
            results["checks"]["relationships"] = relationship_check
            
            # Check 2: Verify data consistency
            consistency_check = self._check_data_consistency()
            results["checks"]["consistency"] = consistency_check
            
            # Check 3: Verify hash signatures
            hash_check = self._check_hash_signatures()
            results["checks"]["hash_signatures"] = hash_check
            
            # Check 4: Verify deduplication status
            dedup_check = self._check_deduplication_consistency()
            results["checks"]["deduplication"] = dedup_check
            
            # Check 5: Verify backup metadata
            backup_check = self._check_backup_metadata()
            results["checks"]["backup_metadata"] = backup_check
            
            # Overall validity
            results["valid"] = all(check.get("valid", False) 
                                 for check in results["checks"].values())
            
            return results
            
        except Exception as e:
            logger.error(f"Error verifying data integrity: {e}")
            return {"valid": False, "error": str(e)}
    
    def _export_database(self, backup_path: Path, compress: bool = True) -> bool:
        """Export database to SQL file."""
        try:
            if self.schema.engine.name == "sqlite":
                return self._export_sqlite_database(backup_path, compress)
            else:
                # For other databases, use SQLAlchemy reflection
                return self._export_generic_database(backup_path, compress)
                
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return False
    
    def _export_sqlite_database(self, backup_path: Path, compress: bool) -> bool:
        """Export SQLite database using SQLite backup API."""
        try:
            import sqlite3
            
            # Get database file path from engine URL
            db_path = self.schema.database_url.replace("sqlite:///", "")
            
            if compress:
                # Create compressed backup
                with sqlite3.connect(db_path) as source_conn:
                    with gzip.open(backup_path, 'wt') as f:
                        for line in source_conn.iterdump():
                            f.write(line + '\n')
            else:
                # Create uncompressed backup
                with sqlite3.connect(db_path) as source_conn:
                    with open(backup_path, 'w') as f:
                        for line in source_conn.iterdump():
                            f.write(line + '\n')
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting SQLite database: {e}")
            return False
    
    def _export_generic_database(self, backup_path: Path, compress: bool) -> bool:
        """Export generic database using SQLAlchemy."""
        try:
            # Get all table data
            inspector = inspect(self.schema.engine)
            all_data = {}
            
            for table_name in inspector.get_table_names():
                table_data = []
                
                with self.schema.get_session() as session:
                    # Get table data
                    result = session.execute(f"SELECT * FROM {table_name}")
                    columns = result.keys()
                    
                    for row in result:
                        table_data.append(dict(zip(columns, row)))
                
                all_data[table_name] = table_data
            
            # Write to file
            if compress:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=2, default=str)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting generic database: {e}")
            return False
    
    def _export_schema(self, backup_path: Path) -> bool:
        """Export database schema only."""
        try:
            # Get schema creation SQL
            schema_sql = []
            
            for table_name, table in Base.metadata.tables.items():
                create_sql = str(table.compile(self.schema.engine))
                schema_sql.append(create_sql + ";")
                
                # Add indexes
                for index in table.indexes:
                    index_sql = str(index.create(self.schema.engine))
                    schema_sql.append(index_sql + ";")
            
            # Write schema to file
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(schema_sql))
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting schema: {e}")
            return False
    
    def _export_incremental_data(self, backup_path: Path, since_date: datetime) -> bool:
        """Export incremental data since specified date."""
        try:
            incremental_data = {}
            
            # Get changed data for each table
            tables_to_check = [
                "listings", "contacts", "scraping_runs", "contact_validations"
            ]
            
            for table_name in tables_to_check:
                table_data = []
                
                with self.schema.get_session() as session:
                    # Query for recent changes
                    result = session.execute(f"""
                        SELECT * FROM {table_name} 
                        WHERE updated_at >= :since_date OR created_at >= :since_date
                    """, {"since_date": since_date})
                    
                    columns = result.keys()
                    for row in result:
                        table_data.append(dict(zip(columns, row)))
                
                if table_data:
                    incremental_data[table_name] = table_data
            
            # Write to compressed JSON file
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(incremental_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting incremental data: {e}")
            return False
    
    def _restore_full_backup(self, backup_path: str) -> bool:
        """Restore from full backup."""
        try:
            # For safety, create a backup of current data first
            current_backup = self.create_full_backup("pre_restore_backup")
            if current_backup:
                logger.info(f"Created pre-restore backup: {current_backup}")
            
            # Drop existing tables
            Base.metadata.drop_all(self.schema.engine)
            
            # Restore from backup
            if backup_path.endswith('.gz'):
                return self._restore_compressed_sql(backup_path)
            else:
                return self._restore_sql_file(backup_path)
                
        except Exception as e:
            logger.error(f"Error restoring full backup: {e}")
            return False
    
    def _restore_schema(self, backup_path: str) -> bool:
        """Restore schema from backup."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Execute schema SQL
            with self.schema.get_session() as session:
                session.execute(schema_sql)
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring schema: {e}")
            return False
    
    def _restore_incremental_data(self, backup_path: str) -> bool:
        """Restore incremental data."""
        try:
            # Load incremental data
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                incremental_data = json.load(f)
            
            # Apply incremental changes
            with self.schema.get_session() as session:
                for table_name, table_data in incremental_data.items():
                    for row in table_data:
                        # Insert or update row
                        # This is a simplified implementation
                        columns = list(row.keys())
                        values = list(row.values())
                        
                        placeholders = ', '.join(['?' for _ in values])
                        column_names = ', '.join(columns)
                        
                        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
                        session.execute(insert_sql, values)
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring incremental data: {e}")
            return False
    
    def _restore_compressed_sql(self, backup_path: str) -> bool:
        """Restore from compressed SQL backup."""
        try:
            import gzip
            import sqlite3
            
            # Extract and execute SQL
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute SQL statements
            with self.schema.get_session() as session:
                # Split and execute SQL statements
                statements = sql_content.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        try:
                            session.execute(statement)
                        except Exception as e:
                            logger.warning(f"Error executing SQL statement: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring compressed SQL: {e}")
            return False
    
    def _restore_sql_file(self, backup_path: str) -> bool:
        """Restore from SQL file."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with self.schema.get_session() as session:
                statements = sql_content.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        try:
                            session.execute(statement)
                        except Exception as e:
                            logger.warning(f"Error executing SQL statement: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring SQL file: {e}")
            return False
    
    def _export_json(self, export_path: Path, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Export data to JSON format."""
        try:
            export_data = {}
            
            # Get data from each table
            inspector = inspect(self.schema.engine)
            for table_name in inspector.get_table_names():
                table_data = []
                
                with self.schema.get_session() as session:
                    query = f"SELECT * FROM {table_name}"
                    if filters:
                        # Apply filters (simplified implementation)
                        conditions = []
                        for key, value in filters.items():
                            conditions.append(f"{key} = '{value}'")
                        if conditions:
                            query += " WHERE " + " AND ".join(conditions)
                    
                    result = session.execute(query)
                    columns = result.keys()
                    
                    for row in result:
                        table_data.append(dict(zip(columns, row)))
                
                export_data[table_name] = table_data
            
            # Write to JSON file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None
    
    def _export_csv(self, export_path: Path, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Export data to CSV format."""
        try:
            import csv
            
            # For simplicity, export main tables as separate CSV files
            main_tables = ["listings", "contacts", "scraping_runs"]
            
            for table_name in main_tables:
                csv_path = export_path.parent / f"{table_name}_{export_path.stem}.csv"
                
                with self.schema.get_session() as session:
                    result = session.execute(f"SELECT * FROM {table_name}")
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result]
                
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(rows)
            
            return str(export_path.parent)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def _export_xml(self, export_path: Path, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Export data to XML format."""
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.Element("mwa_data")
            
            inspector = inspect(self.schema.engine)
            for table_name in inspector.get_table_names():
                table_elem = ET.SubElement(root, table_name)
                
                with self.schema.get_session() as session:
                    result = session.execute(f"SELECT * FROM {table_name}")
                    columns = result.keys()
                    
                    for row in result:
                        row_elem = ET.SubElement(table_elem, "row")
                        for col, val in zip(columns, row):
                            col_elem = ET.SubElement(row_elem, col)
                            col_elem.text = str(val) if val is not None else ""
            
            # Write to XML file
            tree = ET.ElementTree(root)
            tree.write(export_path, encoding='utf-8', xml_declaration=True)
            
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Error exporting to XML: {e}")
            return None
    
    def _import_json(self, import_path: str) -> bool:
        """Import data from JSON file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            with self.schema.get_session() as session:
                for table_name, table_data in import_data.items():
                    for row in table_data:
                        # Insert row
                        columns = list(row.keys())
                        values = list(row.values())
                        
                        placeholders = ', '.join(['?' for _ in values])
                        column_names = ', '.join(columns)
                        
                        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                        session.execute(insert_sql, values)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
            return False
    
    def _import_csv(self, import_path: str) -> bool:
        """Import data from CSV file."""
        try:
            import csv
            
            # For simplicity, assume CSV file matches table structure
            table_name = Path(import_path).stem.split('_')[0]  # Extract table name
            
            with open(import_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            with self.schema.get_session() as session:
                for row in rows:
                    columns = list(row.keys())
                    values = list(row.values())
                    
                    placeholders = ', '.join(['?' for _ in values])
                    column_names = ', '.join(columns)
                    
                    insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                    session.execute(insert_sql, values)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return False
    
    def _import_xml(self, import_path: str) -> bool:
        """Import data from XML file."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(import_path)
            root = tree.getroot()
            
            with self.schema.get_session() as session:
                for table_elem in root:
                    table_name = table_elem.tag
                    
                    for row_elem in table_elem.findall('row'):
                        columns = []
                        values = []
                        
                        for col_elem in row_elem:
                            columns.append(col_elem.tag)
                            values.append(col_elem.text or "")
                        
                        if columns and values:
                            placeholders = ', '.join(['?' for _ in values])
                            column_names = ', '.join(columns)
                            
                            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                            session.execute(insert_sql, values)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing XML: {e}")
            return False
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file checksum: {e}")
            return ""
    
    def _verify_backup_checksum(self, backup_path: str) -> bool:
        """Verify backup file checksum against metadata."""
        try:
            with self.schema.get_session() as session:
                # Find backup metadata
                backup_metadata = session.query(BackupMetadata).filter_by(
                    backup_path=backup_path
                ).order_by(BackupMetadata.created_at.desc()).first()
                
                if not backup_metadata or not backup_metadata.checksum:
                    logger.warning("No checksum found for backup verification")
                    return True  # Assume valid if no checksum
                
                # Calculate current checksum
                current_checksum = self._calculate_file_checksum(Path(backup_path))
                
                return current_checksum == backup_metadata.checksum
                
        except Exception as e:
            logger.error(f"Error verifying backup checksum: {e}")
            return False
    
    def _check_relationships(self) -> Dict[str, Any]:
        """Check database table relationships."""
        try:
            results = {"valid": True, "issues": []}
            
            with self.schema.get_session() as session:
                # Check foreign key relationships
                # Example: Check that all contacts have valid listing IDs
                orphan_contacts = session.execute("""
                    SELECT c.id, c.listing_id 
                    FROM contacts c 
                    LEFT JOIN listings l ON c.listing_id = l.id 
                    WHERE l.id IS NULL
                """).fetchall()
                
                if orphan_contacts:
                    results["issues"].extend([
                        f"Orphan contact {contact[0]} references non-existent listing {contact[1]}"
                        for contact in orphan_contacts
                    ])
                    results["valid"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking relationships: {e}")
            return {"valid": False, "error": str(e)}
    
    def _check_data_consistency(self) -> Dict[str, Any]:
        """Check data consistency."""
        try:
            results = {"valid": True, "issues": []}
            
            with self.schema.get_session() as session:
                # Check for invalid enum values
                invalid_statuses = session.execute("""
                    SELECT id, status 
                    FROM listings 
                    WHERE status NOT IN ('active', 'inactive', 'expired', 'rented', 'deleted')
                """).fetchall()
                
                if invalid_statuses:
                    results["issues"].extend([
                        f"Listing {listing[0]} has invalid status: {listing[1]}"
                        for listing in invalid_statuses
                    ])
                    results["valid"] = False
                
                # Check for negative values
                negative_counts = session.execute("""
                    SELECT id, view_count 
                    FROM listings 
                    WHERE view_count < 0
                """).fetchall()
                
                if negative_counts:
                    results["issues"].extend([
                        f"Listing {listing[0]} has negative view_count: {listing[1]}"
                        for listing in negative_counts
                    ])
                    results["valid"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            return {"valid": False, "error": str(e)}
    
    def _check_hash_signatures(self) -> Dict[str, Any]:
        """Check hash signature consistency."""
        try:
            results = {"valid": True, "issues": []}
            
            with self.schema.get_session() as session:
                # Check listings with hash signatures
                listings_with_hash = session.execute("""
                    SELECT id, provider, external_id, title, price, size, rooms, address, hash_signature
                    FROM listings 
                    WHERE hash_signature IS NOT NULL
                """).fetchall()
                
                for listing in listings_with_hash:
                    # Recalculate hash
                    expected_hash = self._recalculate_listing_hash(listing)
                    if expected_hash != listing[8]:  # hash_signature is 9th column
                        results["issues"].append(
                            f"Listing {listing[0]} has incorrect hash signature"
                        )
                        results["valid"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking hash signatures: {e}")
            return {"valid": False, "error": str(e)}
    
    def _check_deduplication_consistency(self) -> Dict[str, Any]:
        """Check deduplication consistency."""
        try:
            results = {"valid": True, "issues": []}
            
            with self.schema.get_session() as session:
                # Check for duplicates referencing non-existent originals
                orphan_duplicates = session.execute("""
                    SELECT d.id, d.duplicate_of_id 
                    FROM listings d 
                    LEFT JOIN listings o ON d.duplicate_of_id = o.id 
                    WHERE d.deduplication_status = 'duplicate' AND o.id IS NULL
                """).fetchall()
                
                if orphan_duplicates:
                    results["issues"].extend([
                        f"Duplicate listing {dup[0]} references non-existent original {dup[1]}"
                        for dup in orphan_duplicates
                    ])
                    results["valid"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking deduplication consistency: {e}")
            return {"valid": False, "error": str(e)}
    
    def _check_backup_metadata(self) -> Dict[str, Any]:
        """Check backup metadata consistency."""
        try:
            results = {"valid": True, "issues": []}
            
            with self.schema.get_session() as session:
                # Check for backups with missing files
                missing_backups = session.execute("""
                    SELECT id, backup_path, status 
                    FROM backup_metadata 
                    WHERE status = 'completed'
                """).fetchall()
                
                for backup in missing_backups:
                    backup_path = Path(backup[1])
                    if not backup_path.exists():
                        results["issues"].append(
                            f"Backup {backup[0]} references missing file: {backup[1]}"
                        )
                        results["valid"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking backup metadata: {e}")
            return {"valid": False, "error": str(e)}
    
    def _recalculate_listing_hash(self, listing_data) -> str:
        """Recalculate hash for a listing."""
        try:
            # Create hash string from listing data
            hash_components = [
                listing_data[1],  # provider
                listing_data[2] or "",  # external_id
                listing_data[3],  # title
                listing_data[4] or "",  # price
                listing_data[5] or "",  # size
                listing_data[6] or "",  # rooms
                listing_data[7] or ""  # address
            ]
            
            hash_string = "|".join(str(comp) for comp in hash_components)
            return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Error recalculating listing hash: {e}")
            return ""
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Clean up old backup files and metadata.
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Number of backups cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            with self.schema.get_session() as session:
                # Get old backups
                old_backups = session.query(BackupMetadata).filter(
                    BackupMetadata.created_at < cutoff_date
                ).all()
                
                for backup in old_backups:
                    try:
                        # Delete backup file
                        backup_path = Path(backup.backup_path)
                        if backup_path.exists():
                            backup_path.unlink()
                        
                        # Delete backup metadata
                        session.delete(backup)
                        cleaned_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error cleaning up backup {backup.id}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old backups")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0