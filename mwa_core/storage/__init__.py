"""
MWA Core storage system with notification history tracking.
"""

from .manager import StorageManager, get_storage_manager
from .models import (
    Listing, 
    Contact, 
    ScrapingRun, 
    ListingScrapingRun, 
    ContactValidation, 
    JobStore, 
    Configuration, 
    BackupMetadata,
    ListingStatus,
    ContactType,
    ContactStatus,
    JobStatus,
    DeduplicationStatus
)
from .operations import CRUDOperations
from .backup import BackupManager
from .notification_history import (
    NotificationHistoryManager,
    NotificationHistoryEntry,
    get_notification_history_manager,
    get_notification_history
)

__all__ = [
    'StorageManager',
    'get_storage_manager',
    'Listing',
    'Contact',
    'ScrapingRun',
    'ListingScrapingRun',
    'ContactValidation',
    'JobStore',
    'Configuration',
    'BackupMetadata',
    'ListingStatus',
    'ContactType',
    'ContactStatus',
    'JobStatus',
    'DeduplicationStatus',
    'CRUDOperations',
    'BackupManager',
    'NotificationHistoryManager',
    'NotificationHistoryEntry',
    'get_notification_history_manager',
    'get_notification_history',
]