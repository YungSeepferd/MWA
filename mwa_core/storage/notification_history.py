"""
Notification history tracking and storage for MWA Core.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from mwa_core.notifier.base import NotificationResult, NotificationStatus, NotificationChannel

logger = logging.getLogger(__name__)


@dataclass
class NotificationHistoryEntry:
    """Represents a notification history entry."""
    
    message_id: str
    channel: str
    status: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    response_data: Dict[str, Any] = None
    delivery_confirmation: Optional[str] = None
    message_type: Optional[str] = None
    message_title: Optional[str] = None
    recipients: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.response_data is None:
            self.response_data = {}
        if self.recipients is None:
            self.recipients = []
    
    @classmethod
    def from_notification_result(cls, result: NotificationResult, 
                               message_type: str = None,
                               message_title: str = None,
                               recipients: List[str] = None) -> 'NotificationHistoryEntry':
        """Create history entry from notification result."""
        return cls(
            message_id=result.message_id,
            channel=result.channel.value,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            retry_count=result.retry_count,
            response_data=result.response_data,
            delivery_confirmation=result.delivery_confirmation,
            message_type=message_type,
            message_title=message_title,
            recipients=recipients or []
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['sent_at'] = self.sent_at.isoformat()
        if self.delivered_at:
            data['delivered_at'] = self.delivered_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationHistoryEntry':
        """Create from dictionary."""
        # Convert ISO format strings back to datetime objects
        data = data.copy()
        data['sent_at'] = datetime.fromisoformat(data['sent_at'])
        if data.get('delivered_at'):
            data['delivered_at'] = datetime.fromisoformat(data['delivered_at'])
        return cls(**data)


class NotificationHistoryManager:
    """Manages notification history storage and retrieval."""
    
    def __init__(self, storage_path: str = "data/notification_history.json", 
                 max_entries: int = 10000,
                 retention_days: int = 30):
        """
        Initialize notification history manager.
        
        Args:
            storage_path: Path to the history file
            max_entries: Maximum number of entries to keep
            retention_days: Number of days to retain entries
        """
        self.storage_path = Path(storage_path)
        self.max_entries = max_entries
        self.retention_days = retention_days
        self.history: List[NotificationHistoryEntry] = []
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self._load_history()
    
    def _load_history(self):
        """Load notification history from file."""
        if not self.storage_path.exists():
            logger.info(f"Notification history file not found at {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.history = [
                NotificationHistoryEntry.from_dict(entry) 
                for entry in data.get('entries', [])
            ]
            
            logger.info(f"Loaded {len(self.history)} notification history entries")
            
        except Exception as e:
            logger.error(f"Failed to load notification history: {e}")
            self.history = []
    
    def _save_history(self):
        """Save notification history to file."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_entries': len(self.history),
                'entries': [entry.to_dict() for entry in self.history]
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.history)} notification history entries")
            
        except Exception as e:
            logger.error(f"Failed to save notification history: {e}")
    
    def add_entry(self, entry: NotificationHistoryEntry):
        """
        Add a notification history entry.
        
        Args:
            entry: Notification history entry to add
        """
        self.history.append(entry)
        
        # Maintain size limit
        if len(self.history) > self.max_entries:
            # Remove oldest entries
            remove_count = len(self.history) - self.max_entries
            self.history = self.history[remove_count:]
            logger.info(f"Removed {remove_count} old notification history entries")
        
        # Save to file
        self._save_history()
    
    def add_result(self, result: NotificationResult, 
                   message_type: str = None,
                   message_title: str = None,
                   recipients: List[str] = None):
        """
        Add a notification result to history.
        
        Args:
            result: Notification result to add
            message_type: Type of the original message
            message_title: Title of the original message
            recipients: List of recipients
        """
        entry = NotificationHistoryEntry.from_notification_result(
            result, message_type, message_title, recipients
        )
        self.add_entry(entry)
    
    def get_recent_entries(self, hours: int = 24, 
                          channel: NotificationChannel = None,
                          status: NotificationStatus = None) -> List[NotificationHistoryEntry]:
        """
        Get recent notification history entries.
        
        Args:
            hours: Number of hours to look back
            channel: Filter by channel (optional)
            status: Filter by status (optional)
            
        Returns:
            List of matching history entries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_entries = [
            entry for entry in self.history
            if entry.sent_at >= cutoff_time
            and (channel is None or entry.channel == channel.value)
            and (status is None or entry.status == status.value)
        ]
        
        return filtered_entries
    
    def get_entries_by_message_id(self, message_id: str) -> List[NotificationHistoryEntry]:
        """
        Get all entries for a specific message ID.
        
        Args:
            message_id: Message ID to search for
            
        Returns:
            List of matching entries
        """
        return [entry for entry in self.history if entry.message_id == message_id]
    
    def get_failed_entries(self, max_age_hours: int = 24) -> List[NotificationHistoryEntry]:
        """
        Get failed notification entries within the specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            List of failed entries
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        return [
            entry for entry in self.history
            if entry.status == NotificationStatus.FAILED.value
            and entry.sent_at >= cutoff_time
        ]
    
    def get_success_rate(self, hours: int = 24, 
                        channel: NotificationChannel = None) -> float:
        """
        Get success rate for notifications.
        
        Args:
            hours: Number of hours to analyze
            channel: Filter by channel (optional)
            
        Returns:
            Success rate as a float (0.0 to 1.0)
        """
        recent_entries = self.get_recent_entries(hours, channel)
        
        if not recent_entries:
            return 0.0
        
        successful_count = sum(
            1 for entry in recent_entries
            if entry.status in [NotificationStatus.SENT.value, NotificationStatus.DELIVERED.value]
        )
        
        return successful_count / len(recent_entries)
    
    def get_channel_stats(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics by channel.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with channel statistics
        """
        recent_entries = self.get_recent_entries(hours)
        
        stats = {}
        
        for channel in NotificationChannel:
            channel_entries = [e for e in recent_entries if e.channel == channel.value]
            
            if channel_entries:
                total = len(channel_entries)
                successful = sum(
                    1 for e in channel_entries
                    if e.status in [NotificationStatus.SENT.value, NotificationStatus.DELIVERED.value]
                )
                failed = total - successful
                
                stats[channel.value] = {
                    "total": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / total if total > 0 else 0.0
                }
        
        return stats
    
    def cleanup_old_entries(self):
        """Remove old entries based on retention policy."""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        original_count = len(self.history)
        self.history = [
            entry for entry in self.history
            if entry.sent_at >= cutoff_time
        ]
        
        removed_count = original_count - len(self.history)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} old notification history entries")
            self._save_history()
    
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get a summary of notification activity.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        recent_entries = self.get_recent_entries(hours)
        
        if not recent_entries:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "by_channel": {},
                "recent_failures": []
            }
        
        total = len(recent_entries)
        successful = sum(
            1 for entry in recent_entries
            if entry.status in [NotificationStatus.SENT.value, NotificationStatus.DELIVERED.value]
        )
        failed = total - successful
        
        by_channel = self.get_channel_stats(hours)
        
        # Get recent failures
        recent_failures = [
            {
                "message_id": entry.message_id,
                "channel": entry.channel,
                "message_type": entry.message_type,
                "message_title": entry.message_title,
                "error_message": entry.error_message,
                "sent_at": entry.sent_at.isoformat()
            }
            for entry in recent_entries
            if entry.status == NotificationStatus.FAILED.value
        ][-5:]  # Last 5 failures
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total,
            "by_channel": by_channel,
            "recent_failures": recent_failures
        }
    
    def export_to_csv(self, filepath: str, hours: int = None) -> bool:
        """
        Export notification history to CSV file.
        
        Args:
            filepath: Path to export CSV file
            hours: Optional hours filter (export all if None)
            
        Returns:
            True if export successful
        """
        try:
            import csv
            
            entries = self.get_recent_entries(hours) if hours else self.history
            
            if not entries:
                logger.warning("No entries to export")
                return False
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Message ID', 'Channel', 'Status', 'Sent At', 'Delivered At',
                    'Error Message', 'Retry Count', 'Message Type', 'Message Title',
                    'Recipients'
                ])
                
                # Write entries
                for entry in entries:
                    writer.writerow([
                        entry.message_id,
                        entry.channel,
                        entry.status,
                        entry.sent_at.isoformat(),
                        entry.delivered_at.isoformat() if entry.delivered_at else '',
                        entry.error_message or '',
                        entry.retry_count,
                        entry.message_type or '',
                        entry.message_title or '',
                        ', '.join(entry.recipients)
                    ])
            
            logger.info(f"Exported {len(entries)} entries to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export notification history: {e}")
            return False
    
    def clear_history(self):
        """Clear all notification history."""
        self.history.clear()
        self._save_history()
        logger.info("Cleared all notification history")


# Convenience functions
def get_notification_history_manager(storage_path: str = None, 
                                   max_entries: int = None,
                                   retention_days: int = None) -> NotificationHistoryManager:
    """
    Get or create a notification history manager.
    
    Args:
        storage_path: Path to storage file
        max_entries: Maximum entries to keep
        retention_days: Retention period in days
        
    Returns:
        NotificationHistoryManager instance
    """
    from mwa_core.config import get_settings
    
    settings = get_settings()
    
    # Use settings if parameters not provided
    if storage_path is None:
        storage_path = settings.database_path.replace('.db', '_notification_history.json')
    if max_entries is None:
        max_entries = settings.max_notification_queue_size
    if retention_days is None:
        retention_days = settings.notification_history_retention_days
    
    return NotificationHistoryManager(storage_path, max_entries, retention_days)


# Global history manager instance
_history_manager = None

def get_notification_history() -> NotificationHistoryManager:
    """Get the global notification history manager."""
    global _history_manager
    if _history_manager is None:
        _history_manager = get_notification_history_manager()
    return _history_manager