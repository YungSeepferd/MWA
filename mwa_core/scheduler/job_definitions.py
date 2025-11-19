"""
Enhanced job definitions for MWA Core scheduler with contact discovery support.

Defines job types and configurations for:
- Contact discovery operations
- Contact validation and verification
- Storage cleanup and maintenance
- Performance monitoring
- Batch processing operations
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..contact.integration import ContactDiscoveryIntegration
from ..contact.validators import ContactValidator
from ..storage.operations import StorageOperations
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Types of scheduled jobs."""
    CONTACT_DISCOVERY = "contact_discovery"
    CONTACT_VALIDATION = "contact_validation"
    STORAGE_CLEANUP = "storage_cleanup"
    PERFORMANCE_MONITORING = "performance_monitoring"
    BATCH_PROCESSING = "batch_processing"
    BACKUP = "backup"
    DEDUPLICATION = "deduplication"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class JobConfig:
    """Configuration for a scheduled job."""
    job_type: JobType
    name: str
    description: str
    function: str
    trigger_type: str  # interval, cron, date
    trigger_config: Dict[str, Any]
    enabled: bool = True
    priority: JobPriority = JobPriority.MEDIUM
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 300
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobResult:
    """Result of job execution."""
    success: bool
    job_id: str
    job_type: JobType
    execution_time: float
    items_processed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# Job function definitions
async def contact_discovery_job(listing_ids: Optional[List[int]] = None, 
                               batch_size: int = 10,
                               validation_level: str = "standard",
                               config: Optional[Settings] = None) -> JobResult:
    """
    Job to discover contacts for listings.
    
    Args:
        listing_ids: Specific listing IDs to process (None for all)
        batch_size: Number of listings to process in each batch
        validation_level: Level of validation to apply
        config: Application configuration
        
    Returns:
        JobResult with execution details
    """
    start_time = datetime.now()
    errors = []
    warnings = []
    metadata = {}
    
    try:
        if config is None:
            from ..config.settings import get_settings
            config = get_settings()
        
        if not config.contact_discovery.enabled:
            warnings.append("Contact discovery is disabled in configuration")
            return JobResult(
                success=True,
                job_id="contact_discovery",
                job_type=JobType.CONTACT_DISCOVERY,
                execution_time=0,
                warnings=warnings
            )
        
        # Initialize integration
        integration = ContactDiscoveryIntegration(config)
        
        # Get listings to process
        with integration.storage_ops.get_session() as session:
            from ..storage.models import Listing
            
            if listing_ids:
                listings = session.query(Listing).filter(Listing.id.in_(listing_ids)).all()
            else:
                # Get listings without contacts or with old contacts
                cutoff_date = datetime.now() - timedelta(days=30)
                listings = session.query(Listing).filter(
                    (Listing.contacts.is_(None)) | 
                    (Listing.contacts == '') |
                    (Listing.updated_at < cutoff_date)
                ).limit(batch_size * 10).all()
            
            if not listings:
                warnings.append("No listings found to process")
                return JobResult(
                    success=True,
                    job_id="contact_discovery",
                    job_type=JobType.CONTACT_DISCOVERY,
                    execution_time=0,
                    warnings=warnings
                )
            
            # Process in batches
            total_processed = 0
            total_contacts = 0
            total_forms = 0
            
            for i in range(0, len(listings), batch_size):
                batch_listings = listings[i:i + batch_size]
                listing_dicts = []
                listing_ids_batch = []
                
                for listing in batch_listings:
                    listing_dicts.append({
                        'id': listing.id,
                        'title': listing.title,
                        'url': listing.url,
                        'description': listing.description,
                        'price': listing.price,
                        'address': listing.address
                    })
                    listing_ids_batch.append(listing.id)
                
                # Process batch
                try:
                    summary = await integration.process_listings_batch(
                        listing_dicts, listing_ids_batch
                    )
                    
                    total_processed += summary['processed']
                    total_contacts += summary['contacts_found']
                    total_forms += summary['forms_found']
                    
                    if summary['errors'] > 0:
                        errors.append(f"Batch {i//batch_size + 1}: {summary['errors']} errors")
                    
                except Exception as e:
                    error_msg = f"Error processing batch {i//batch_size + 1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            metadata.update({
                'total_listings': len(listings),
                'batches_processed': (len(listings) + batch_size - 1) // batch_size,
                'validation_level': validation_level,
                'cultural_context': config.contact_discovery.cultural_context,
                'language_preference': config.contact_discovery.language_preference
            })
            
            logger.info(f"Contact discovery job completed: {total_contacts} contacts, {total_forms} forms from {total_processed} listings")
            
            return JobResult(
                success=len(errors) == 0,
                job_id="contact_discovery",
                job_type=JobType.CONTACT_DISCOVERY,
                execution_time=execution_time,
                items_processed=total_contacts + total_forms,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
    except Exception as e:
        error_msg = f"Contact discovery job failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return JobResult(
            success=False,
            job_id="contact_discovery",
            job_type=JobType.CONTACT_DISCOVERY,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )


async def contact_validation_job(contact_ids: Optional[List[int]] = None,
                                validation_level: str = "standard",
                                batch_size: int = 50,
                                config: Optional[Settings] = None) -> JobResult:
    """
    Job to validate discovered contacts.
    
    Args:
        contact_ids: Specific contact IDs to validate (None for all unvalidated)
        validation_level: Level of validation to apply
        batch_size: Number of contacts to validate in each batch
        config: Application configuration
        
    Returns:
        JobResult with validation results
    """
    start_time = datetime.now()
    errors = []
    warnings = []
    metadata = {}
    
    try:
        if config is None:
            from ..config.settings import get_settings
            config = get_settings()
        
        # Initialize validator
        validator = ContactValidator(
            enable_smtp_verification=config.contact_discovery.smtp_verification,
            enable_dns_verification=config.contact_discovery.dns_verification,
            rate_limit_seconds=config.contact_discovery.rate_limit_seconds
        )
        
        # Initialize integration
        integration = ContactDiscoveryIntegration(config)
        
        # Get contacts to validate
        with integration.storage_ops.get_session() as session:
            from ..storage.models import Contact as StorageContact
            
            if contact_ids:
                contacts = session.query(StorageContact).filter(
                    StorageContact.id.in_(contact_ids),
                    StorageContact.status == "unvalidated"
                ).all()
            else:
                # Get unvalidated contacts
                contacts = session.query(StorageContact).filter(
                    StorageContact.status == "unvalidated"
                ).limit(batch_size * 5).all()
            
            if not contacts:
                warnings.append("No unvalidated contacts found")
                return JobResult(
                    success=True,
                    job_id="contact_validation",
                    job_type=JobType.CONTACT_VALIDATION,
                    execution_time=0,
                    warnings=warnings
                )
            
            # Convert to discovery contacts
            discovery_contacts = []
            for storage_contact in contacts:
                from ..contact.models import Contact, ContactMethod, ConfidenceLevel
                contact = Contact(
                    method=ContactMethod(storage_contact.type),
                    value=storage_contact.value,
                    confidence=ConfidenceLevel.HIGH if storage_contact.confidence > 0.8 else ConfidenceLevel.MEDIUM,
                    source_url="stored_contact",
                    verification_status=ContactStatus.UNVERIFIED
                )
                discovery_contacts.append(contact)
            
            # Validate in batches
            total_validated = 0
            total_valid = 0
            total_invalid = 0
            
            for i in range(0, len(discovery_contacts), batch_size):
                batch_contacts = discovery_contacts[i:i + batch_size]
                
                try:
                    validation_results = await validator.validate_contacts_batch(
                        batch_contacts, validation_level
                    )
                    
                    # Update storage with validation results
                    for storage_contact, result in zip(contacts[i:i + batch_size], validation_results):
                        if result.is_valid:
                            storage_contact.status = "valid"
                            storage_contact.validated_at = datetime.now()
                            total_valid += 1
                        else:
                            storage_contact.status = "invalid"
                            total_invalid += 1
                        
                        # Store validation metadata
                        from ..storage.models import ContactValidation
                        validation_record = ContactValidation(
                            contact_id=storage_contact.id,
                            validation_method=result.validation_method,
                            validation_result=result.is_valid,
                            confidence_score=result.confidence_score,
                            validation_metadata=json.dumps(result.metadata)
                        )
                        session.add(validation_record)
                    
                    total_validated += len(batch_contacts)
                    
                except Exception as e:
                    error_msg = f"Error validating batch {i//batch_size + 1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            session.commit()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            metadata.update({
                'total_contacts': len(contacts),
                'batches_processed': (len(contacts) + batch_size - 1) // batch_size,
                'validation_level': validation_level,
                'valid_contacts': total_valid,
                'invalid_contacts': total_invalid,
                'validation_rate': total_valid / total_validated if total_validated > 0 else 0
            })
            
            logger.info(f"Contact validation job completed: {total_valid} valid, {total_invalid} invalid out of {total_validated} validated")
            
            return JobResult(
                success=len(errors) == 0,
                job_id="contact_validation",
                job_type=JobType.CONTACT_VALIDATION,
                execution_time=execution_time,
                items_processed=total_validated,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
    except Exception as e:
        error_msg = f"Contact validation job failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return JobResult(
            success=False,
            job_id="contact_validation",
            job_type=JobType.CONTACT_VALIDATION,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )


async def storage_cleanup_job(days_old: int = 90,
                             dry_run: bool = False,
                             config: Optional[Settings] = None) -> JobResult:
    """
    Job to clean up old contacts and validation history.
    
    Args:
        days_old: Age in days after which items are considered old
        dry_run: If True, only show what would be deleted
        config: Application configuration
        
    Returns:
        JobResult with cleanup results
    """
    start_time = datetime.now()
    errors = []
    warnings = []
    metadata = {}
    
    try:
        if config is None:
            from ..config.settings import get_settings
            config = get_settings()
        
        if not config.storage.auto_cleanup_enabled:
            warnings.append("Auto cleanup is disabled in configuration")
            return JobResult(
                success=True,
                job_id="storage_cleanup",
                job_type=JobType.STORAGE_CLEANUP,
                execution_time=0,
                warnings=warnings
            )
        
        # Initialize integration
        integration = ContactDiscoveryIntegration(config)
        
        # Get statistics before cleanup
        stats_before = integration.get_contact_statistics()
        
        if dry_run:
            # Calculate what would be deleted
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with integration.storage_ops.get_session() as session:
                from ..storage.models import Contact as StorageContact, ContactValidation
                
                # Count old contacts
                old_contacts = session.query(StorageContact).filter(
                    StorageContact.created_at < cutoff_date
                ).count()
                
                # Count old validation records
                old_validations = session.query(ContactValidation).join(StorageContact).filter(
                    StorageContact.created_at < cutoff_date
                ).count()
            
            metadata.update({
                'contacts_to_delete': old_contacts,
                'validations_to_delete': old_validations,
                'dry_run': True
            })
            
            logger.info(f"Storage cleanup dry run: would delete {old_contacts} contacts and {old_validations} validation records")
            
            return JobResult(
                success=True,
                job_id="storage_cleanup",
                job_type=JobType.STORAGE_CLEANUP,
                execution_time=0,
                warnings=warnings,
                metadata=metadata
            )
        
        # Perform actual cleanup
        deleted_contacts = integration.cleanup_old_contacts(days_old)
        
        # Get statistics after cleanup
        stats_after = integration.get_contact_statistics()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        metadata.update({
            'days_old': days_old,
            'contacts_deleted': deleted_contacts,
            'contacts_before': stats_before['total_contacts'],
            'contacts_after': stats_after['total_contacts'],
            'space_saved': stats_before['total_contacts'] - stats_after['total_contacts']
        })
        
        logger.info(f"Storage cleanup job completed: deleted {deleted_contacts} old contacts")
        
        return JobResult(
            success=True,
            job_id="storage_cleanup",
            job_type=JobType.STORAGE_CLEANUP,
            execution_time=execution_time,
            items_processed=deleted_contacts,
            warnings=warnings,
            metadata=metadata
        )
        
    except Exception as e:
        error_msg = f"Storage cleanup job failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return JobResult(
            success=False,
            job_id="storage_cleanup",
            job_type=JobType.STORAGE_CLEANUP,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )


async def performance_monitoring_job(config: Optional[Settings] = None) -> JobResult:
    """
    Job to monitor and report contact discovery performance.
    
    Args:
        config: Application configuration
        
    Returns:
        JobResult with performance metrics
    """
    start_time = datetime.now()
    errors = []
    warnings = []
    metadata = {}
    
    try:
        if config is None:
            from ..config.settings import get_settings
            config = get_settings()
        
        # Initialize integration
        integration = ContactDiscoveryIntegration(config)
        
        # Collect performance metrics
        stats = integration.get_contact_statistics()
        
        # Get recent discovery activity
        with integration.storage_ops.get_session() as session:
            from ..storage.models import Contact as StorageContact, ScrapingRun
            
            # Recent contacts (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            recent_contacts = session.query(StorageContact).filter(
                StorageContact.created_at >= recent_date
            ).count()
            
            # Recent scraping runs
            recent_runs = session.query(ScrapingRun).filter(
                ScrapingRun.started_at >= recent_date
            ).all()
            
            # Calculate performance metrics
            total_runs = len(recent_runs)
            successful_runs = sum(1 for run in recent_runs if run.status == "completed")
            failed_runs = sum(1 for run in recent_runs if run.status == "failed")
            
            avg_listings_per_run = 0
            avg_contacts_per_run = 0
            avg_duration = 0
            
            if total_runs > 0:
                total_listings = sum(run.listings_found for run in recent_runs)
                total_contacts = sum(run.listings_found for run in recent_runs)  # Approximate
                total_duration = sum((run.completed_at - run.started_at).total_seconds() 
                                   for run in recent_runs if run.completed_at and run.started_at)
                
                avg_listings_per_run = total_listings / total_runs
                avg_contacts_per_run = total_contacts / total_runs
                avg_duration = total_duration / total_runs if total_duration > 0 else 0
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        metadata.update({
            'total_contacts': stats['total_contacts'],
            'recent_contacts_7_days': recent_contacts,
            'total_runs_7_days': total_runs,
            'successful_runs': successful_runs,
            'failed_runs': failed_runs,
            'success_rate': (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            'avg_listings_per_run': avg_listings_per_run,
            'avg_contacts_per_run': avg_contacts_per_run,
            'avg_duration_seconds': avg_duration,
            'high_confidence_contacts': stats.get('high_confidence_contacts', 0),
            'contacts_by_type': stats.get('contacts_by_type', {}),
            'contacts_by_status': stats.get('contacts_by_status', {})
        })
        
        # Generate performance alerts
        if avg_duration > 60:  # More than 1 minute average
            warnings.append(f"High average execution time: {avg_duration:.1f} seconds")
        
        if total_runs > 0 and successful_runs / total_runs < 0.8:  # Less than 80% success rate
            warnings.append(f"Low success rate: {successful_runs/total_runs*100:.1f}%")
        
        if stats.get('high_confidence_contacts', 0) / stats.get('total_contacts', 1) < 0.3:  # Less than 30% high confidence
            warnings.append("Low percentage of high-confidence contacts")
        
        logger.info(f"Performance monitoring job completed: {stats['total_contacts']} total contacts, {recent_contacts} recent contacts")
        
        return JobResult(
            success=True,
            job_id="performance_monitoring",
            job_type=JobType.PERFORMANCE_MONITORING,
            execution_time=execution_time,
            metadata=metadata,
            warnings=warnings
        )
        
    except Exception as e:
        error_msg = f"Performance monitoring job failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return JobResult(
            success=False,
            job_id="performance_monitoring",
            job_type=JobType.PERFORMANCE_MONITORING,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )


async def backup_job(backup_type: str = "full",
                    compress: bool = True,
                    config: Optional[Settings] = None) -> JobResult:
    """
    Job to create database backups.
    
    Args:
        backup_type: Type of backup (full, incremental, schema)
        compress: Whether to compress the backup
        config: Application configuration
        
    Returns:
        JobResult with backup details
    """
    start_time = datetime.now()
    errors = []
    warnings = []
    metadata = {}
    
    try:
        if config is None:
            from ..config.settings import get_settings
            config = get_settings()
        
        if not config.storage.backup_enabled:
            warnings.append("Backup is disabled in configuration")
            return JobResult(
                success=True,
                job_id="backup",
                job_type=JobType.BACKUP,
                execution_time=0,
                warnings=warnings
            )
        
        from ..storage.backup import BackupManager
        
        backup_manager = BackupManager(config)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_type}_{timestamp}.db"
        if compress:
            backup_filename += ".gz"
        
        # Create backup
        success = backup_manager.create_backup(backup_filename, compress)
        
        if not success:
            errors.append("Backup creation failed")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        metadata.update({
            'backup_type': backup_type,
            'backup_filename': backup_filename,
            'compressed': compress,
            'backup_size_mb': 0,  # Would be populated by backup manager
            'success': success
        })
        
        logger.info(f"Backup job completed: {backup_filename} ({'compressed' if compress else 'uncompressed'})")
        
        return JobResult(
            success=success and len(errors) == 0,
            job_id="backup",
            job_type=JobType.BACKUP,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
        
    except Exception as e:
        error_msg = f"Backup job failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return JobResult(
            success=False,
            job_id="backup",
            job_type=JobType.BACKUP,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )


# Predefined job configurations
DEFAULT_JOB_CONFIGS = [
    # Daily contact discovery for new listings
    JobConfig(
        job_type=JobType.CONTACT_DISCOVERY,
        name="Daily Contact Discovery",
        description="Discover contacts for new and updated listings",
        function="mwa_core.scheduler.job_definitions:contact_discovery_job",
        trigger_type="cron",
        trigger_config={"hour": 2, "minute": 0},  # 2 AM daily
        enabled=True,
        priority=JobPriority.HIGH,
        kwargs={"batch_size": 20, "validation_level": "standard"}
    ),
    
    # Weekly contact validation
    JobConfig(
        job_type=JobType.CONTACT_VALIDATION,
        name="Weekly Contact Validation",
        description="Validate discovered contacts for accuracy",
        function="mwa_core.scheduler.job_definitions:contact_validation_job",
        trigger_type="cron",
        trigger_config={"day_of_week": "sun", "hour": 3, "minute": 0},  # Sunday 3 AM
        enabled=True,
        priority=JobPriority.MEDIUM,
        kwargs={"validation_level": "standard", "batch_size": 100}
    ),
    
    # Monthly storage cleanup
    JobConfig(
        job_type=JobType.STORAGE_CLEANUP,
        name="Monthly Storage Cleanup",
        description="Clean up old contacts and validation history",
        function="mwa_core.scheduler.job_definitions:storage_cleanup_job",
        trigger_type="cron",
        trigger_config={"day": 1, "hour": 4, "minute": 0},  # 1st day of month, 4 AM
        enabled=True,
        priority=JobPriority.LOW,
        kwargs={"days_old": 90, "dry_run": False}
    ),
    
    # Daily performance monitoring
    JobConfig(
        job_type=JobType.PERFORMANCE_MONITORING,
        name="Daily Performance Monitoring",
        description="Monitor and report contact discovery performance",
        function="mwa_core.scheduler.job_definitions:performance_monitoring_job",
        trigger_type="cron",
        trigger_config={"hour": 6, "minute": 0},  # 6 AM daily
        enabled=True,
        priority=JobPriority.MEDIUM
    ),
    
    # Weekly backup
    JobConfig(
        job_type=JobType.BACKUP,
        name="Weekly Full Backup",
        description="Create full database backup",
        function="mwa_core.scheduler.job_definitions:backup_job",
        trigger_type="cron",
        trigger_config={"day_of_week": "sat", "hour": 1, "minute": 0},  # Saturday 1 AM
        enabled=True,
        priority=JobPriority.HIGH,
        kwargs={"backup_type": "full", "compress": True}
    ),
    
    # Hourly incremental backup (if enabled)
    JobConfig(
        job_type=JobType.BACKUP,
        name="Hourly Incremental Backup",
        description="Create incremental database backup",
        function="mwa_core.scheduler.job_definitions:backup_job",
        trigger_type="cron",
        trigger_config={"minute": 0},  # Every hour
        enabled=False,  # Disabled by default
        priority=JobPriority.LOW,
        kwargs={"backup_type": "incremental", "compress": True}
    )
]


def get_job_config(job_type: JobType, name: str) -> Optional[JobConfig]:
    """
    Get job configuration by type and name.
    
    Args:
        job_type: Type of job
        name: Name of the job
        
    Returns:
        JobConfig if found, None otherwise
    """
    for config in DEFAULT_JOB_CONFIGS:
        if config.job_type == job_type and config.name == name:
            return config
    return None


def get_all_job_configs() -> List[JobConfig]:
    """
    Get all default job configurations.
    
    Returns:
        List of all job configurations
    """
    return DEFAULT_JOB_CONFIGS.copy()


def get_job_configs_by_type(job_type: JobType) -> List[JobConfig]:
    """
    Get all job configurations of a specific type.
    
    Args:
        job_type: Type of job to filter by
        
    Returns:
        List of job configurations of the specified type
    """
    return [config for config in DEFAULT_JOB_CONFIGS if config.job_type == job_type]


def create_custom_job_config(job_type: JobType,
                           name: str,
                           description: str,
                           function: str,
                           trigger_type: str,
                           trigger_config: Dict[str, Any],
                           **kwargs) -> JobConfig:
    """
    Create a custom job configuration.
    
    Args:
        job_type: Type of job
        name: Name of the job
        description: Job description
        function: Function to execute
        trigger_type: Type of trigger (interval, cron, date)
        trigger_config: Trigger configuration
        **kwargs: Additional job configuration parameters
        
    Returns:
        Custom JobConfig
    """
    return JobConfig(
        job_type=job_type,
        name=name,
        description=description,
        function=function,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        **kwargs
    )


# Convenience functions for job execution
async def run_contact_discovery_job(listing_ids: Optional[List[int]] = None,
                                  config: Optional[Settings] = None) -> JobResult:
    """Convenience function to run contact discovery job."""
    return await contact_discovery_job(listing_ids=listing_ids, config=config)


async def run_contact_validation_job(contact_ids: Optional[List[int]] = None,
                                   config: Optional[Settings] = None) -> JobResult:
    """Convenience function to run contact validation job."""
    return await contact_validation_job(contact_ids=contact_ids, config=config)


async def run_storage_cleanup_job(days_old: int = 90,
                                config: Optional[Settings] = None) -> JobResult:
    """Convenience function to run storage cleanup job."""
    return await storage_cleanup_job(days_old=days_old, config=config)


# Job execution tracking
class JobExecutionTracker:
    """Track job execution history and statistics."""
    
    def __init__(self, storage_ops: StorageOperations):
        self.storage_ops = storage_ops
    
    def record_job_execution(self, result: JobResult) -> None:
        """Record job execution result."""
        try:
            with self.storage_ops.get_session() as session:
                from ..storage.models import JobExecution
                
                execution = JobExecution(
                    job_id=result.job_id,
                    job_type=result.job_type.value,
                    success=result.success,
                    execution_time=result.execution_time,
                    items_processed=result.items_processed,
                    errors=json.dumps(result.errors),
                    warnings=json.dumps(result.warnings),
                    metadata=json.dumps(result.metadata)
                )
                
                session.add(execution)
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to record job execution: {e}")
    
    def get_job_statistics(self, job_id: str, days: int = 30) -> Dict[str, Any]:
        """Get job execution statistics."""
        try:
            with self.storage_ops.get_session() as session:
                from ..storage.models import JobExecution
                from datetime import datetime, timedelta
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                executions = session.query(JobExecution).filter(
                    JobExecution.job_id == job_id,
                    JobExecution.created_at >= cutoff_date
                ).all()
                
                if not executions:
                    return {}
                
                total_executions = len(executions)
                successful_executions = sum(1 for e in executions if e.success)
                failed_executions = total_executions - successful_executions
                
                avg_execution_time = sum(e.execution_time for e in executions) / total_executions
                total_items_processed = sum(e.items_processed for e in executions if e.items_processed)
                
                return {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'failed_executions': failed_executions,
                    'success_rate': successful_executions / total_executions * 100,
                    'avg_execution_time': avg_execution_time,
                    'total_items_processed': total_items_processed,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            return {}


# Export job functions and configurations
__all__ = [
    'JobType',
    'JobPriority',
    'JobConfig',
    'JobResult',
    'contact_discovery_job',
    'contact_validation_job',
    'storage_cleanup_job',
    'performance_monitoring_job',
    'backup_job',
    'DEFAULT_JOB_CONFIGS',
    'get_job_config',
    'get_all_job_configs',
    'get_job_configs_by_type',
    'create_custom_job_config',
    'run_contact_discovery_job',
    'run_contact_validation_job',
    'run_storage_cleanup_job',
    'JobExecutionTracker'
]