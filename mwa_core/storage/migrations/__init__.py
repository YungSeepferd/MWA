"""
Database migration system for MWA Core storage.

Provides schema migration capabilities with version tracking and rollback support.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations."""
    
    def __init__(self, database_schema):
        """
        Initialize migration manager.
        
        Args:
            database_schema: DatabaseSchema instance
        """
        self.schema = database_schema
        self.migrations_dir = Path(__file__).parent
        self.migrations_table = "schema_migrations"
    
    def get_current_version(self) -> str:
        """Get current database schema version."""
        try:
            with self.schema.get_session() as session:
                # Check if migrations table exists
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                    {"table_name": self.migrations_table}
                ).fetchone()
                
                if not result:
                    return "0.0.0"  # No migrations table means initial state
                
                # Get latest migration version
                from sqlalchemy import text
                result = session.execute(
                    text(f"SELECT version FROM {self.migrations_table} ORDER BY applied_at DESC LIMIT 1")
                ).fetchone()
                
                return result[0] if result else "0.0.0"
                
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "0.0.0"
    
    def get_available_migrations(self) -> List[str]:
        """Get list of available migration versions."""
        try:
            migrations = []
            
            # Look for migration files
            for migration_file in self.migrations_dir.glob("migration_*.py"):
                version = migration_file.stem.replace("migration_", "").replace("_", ".")
                migrations.append(version)
            
            return sorted(migrations)
            
        except Exception as e:
            logger.error(f"Error getting available migrations: {e}")
            return []
    
    def migrate_to_version(self, target_version: str) -> bool:
        """
        Migrate database to specific version.
        
        Args:
            target_version: Target version string
            
        Returns:
            True if migration successful
        """
        try:
            current_version = self.get_current_version()
            
            if current_version == target_version:
                logger.info(f"Already at target version: {target_version}")
                return True
            
            # Determine migration direction
            if self._version_compare(current_version, target_version) < 0:
                # Upgrade
                return self._upgrade_to_version(current_version, target_version)
            else:
                # Downgrade
                return self._downgrade_to_version(current_version, target_version)
                
        except Exception as e:
            logger.error(f"Error migrating to version {target_version}: {e}")
            return False
    
    def _upgrade_to_version(self, from_version: str, to_version: str) -> bool:
        """Upgrade database to higher version."""
        try:
            available_migrations = self.get_available_migrations()
            
            # Find migrations to apply
            migrations_to_apply = []
            for migration_version in available_migrations:
                if (self._version_compare(from_version, migration_version) < 0 and
                    self._version_compare(migration_version, to_version) <= 0):
                    migrations_to_apply.append(migration_version)
            
            # Apply migrations in order
            for migration_version in migrations_to_apply:
                if not self._apply_migration(migration_version):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error upgrading to version {to_version}: {e}")
            return False
    
    def _downgrade_to_version(self, from_version: str, to_version: str) -> bool:
        """Downgrade database to lower version."""
        try:
            available_migrations = self.get_available_migrations()
            
            # Find migrations to rollback
            migrations_to_rollback = []
            for migration_version in reversed(available_migrations):
                if (self._version_compare(to_version, migration_version) < 0 and
                    self._version_compare(migration_version, from_version) <= 0):
                    migrations_to_rollback.append(migration_version)
            
            # Rollback migrations in reverse order
            for migration_version in migrations_to_rollback:
                if not self._rollback_migration(migration_version):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error downgrading to version {to_version}: {e}")
            return False
    
    def _apply_migration(self, version: str) -> bool:
        """Apply a specific migration."""
        try:
            migration_module = self._load_migration(version)
            if not migration_module:
                return False
            
            logger.info(f"Applying migration to version {version}")
            
            # Execute migration
            with self.schema.get_session() as session:
                migration_module.upgrade(session)
                
                # Check if version already exists before inserting
                from sqlalchemy import text
                result = session.execute(
                    text(f"SELECT version FROM {self.migrations_table} WHERE version = :version"),
                    {"version": version}
                ).fetchone()
                
                if not result:
                    # Record migration only if it doesn't exist
                    session.execute(
                        text(f"INSERT INTO {self.migrations_table} (version, applied_at) VALUES (:version, :applied_at)"),
                        {"version": version, "applied_at": datetime.utcnow()}
                    )
            
            logger.info(f"Successfully applied migration to version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying migration {version}: {e}")
            return False
    
    def _rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration."""
        try:
            migration_module = self._load_migration(version)
            if not migration_module:
                return False
            
            logger.info(f"Rolling back migration to version {version}")
            
            # Execute rollback
            with self.schema.get_session() as session:
                migration_module.downgrade(session)
                
                # Remove migration record
                from sqlalchemy import text
                session.execute(
                    text(f"DELETE FROM {self.migrations_table} WHERE version = :version"),
                    {"version": version}
                )
            
            logger.info(f"Successfully rolled back migration to version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back migration {version}: {e}")
            return False
    
    def _load_migration(self, version: str) -> Optional[Any]:
        """Load migration module for specific version."""
        try:
            # Convert version to filename format
            filename = f"migration_{version.replace('.', '_')}.py"
            migration_path = self.migrations_dir / filename
            
            if not migration_path.exists():
                logger.error(f"Migration file not found: {migration_path}")
                return None
            
            # Import migration module
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"migration_{version}", migration_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logger.error(f"Error loading migration {version}: {e}")
            return None
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """Compare two version strings."""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Error comparing versions {version1} and {version2}: {e}")
            return 0
    
    def create_migrations_table(self) -> bool:
        """Create migrations tracking table."""
        try:
            with self.schema.get_session() as session:
                from sqlalchemy import text
                session.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                        version VARCHAR(20) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating migrations table: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize database with latest schema."""
        try:
            # Create migrations table
            self.create_migrations_table()
            
            # Get latest version
            available_migrations = self.get_available_migrations()
            if not available_migrations:
                logger.info("No migrations available")
                return True
            
            latest_version = available_migrations[-1]
            current_version = self.get_current_version()
            
            if current_version == latest_version:
                logger.info(f"Database is already at latest version: {latest_version}")
                return True
            
            # Migrate to latest version
            return self.migrate_to_version(latest_version)
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False


# Migration base class
class Migration:
    """Base class for database migrations."""
    
    def upgrade(self, session: Session) -> None:
        """
        Apply migration changes.
        
        Args:
            session: Database session
        """
        raise NotImplementedError("Migration must implement upgrade method")
    
    def downgrade(self, session: Session) -> None:
        """
        Rollback migration changes.
        
        Args:
            session: Database session
        """
        raise NotImplementedError("Migration must implement downgrade method")