"""
MWA Core API Pydantic Schemas Package

This package contains comprehensive Pydantic models and schemas for the MWA Core API.
Provides request/response models for all 55 endpoints across 6 router modules.

Schema Modules:
- common: Shared models, enums, pagination, and validation helpers
- config: Configuration management and settings models
- contacts: Contact management, validation, and discovery models
- listings: Apartment listing models and filtering
- scraper: Scraper operations and status models
- scheduler: Job scheduling and execution models
- system: System monitoring, health check, and metrics models
"""

# Import all models for easy access and documentation
from .common import (
    # Enums
    ContactType,
    ContactStatus,
    ListingStatus,
    JobStatus,
    SortOrder,
    ValidationLevel,
    
    # Base Models
    PaginationParams,
    SortParams,
    DateRange,
    SearchParams,
    
    # Base Filter Models
    BaseFilter,
    ContactFilter,
    ListingFilter,
    
    # Response Models
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    StatisticsResponse,
    
    # Validation Fields
    EmailField,
    PhoneField,
    UrlField,
    ConfidenceField,
    
    # Utility Models
    ApiInfo,
    RateLimitInfo,
    ComponentHealth,
    HealthCheckResponse,
    
    # Field Descriptions
    CONTACT_TYPE_DESCRIPTIONS,
    CONTACT_STATUS_DESCRIPTIONS,
    LISTING_STATUS_DESCRIPTIONS,
    JOB_STATUS_DESCRIPTIONS,
)

from .config import (
    # Response Models
    ConfigResponse,
    ConfigValidationResponse,
    ConfigSectionInfo,
    ConfigBackupInfo,
    ConfigDiff,
    ConfigSchema,
    
    # Request Models
    ConfigUpdateRequest,
    ConfigExportRequest,
    ConfigImportRequest,
    ConfigResetRequest,
    
    # Configuration Types
    ProviderConfig,
    NotificationConfig,
    DatabaseConfig,
    LoggingConfig,
    
    # Management Models
    ConfigOperationResponse,
    ConfigHistoryEntry,
    ConfigTemplate,
    EnvironmentConfig,
    
    # Validation Models
    ConfigConstraint,
    ConfigValidationRule,
    EnvVarMapping,
)

from .contacts import (
    # Response Models
    ContactResponse,
    ListingSummary,
    ValidationHistoryEntry,
    ContactSearchResponse,
    
    # Request Models
    ContactCreateRequest,
    ContactUpdateRequest,
    ContactSearchRequest,
    ContactFilter,
    
    # Validation Models
    ContactValidationRequest,
    ContactValidationResult,
    ContactValidationResponse,
    
    # Statistics Models
    ContactStatisticsResponse,
    ValidationMethodStatistics,
    
    # Review Models
    ContactReviewRequest,
    ContactReviewResult,
    ContactReviewResponse,
    
    # Discovery Models
    ContactDiscoveryRequest,
    ContactDiscoveryResult,
    
    # Bulk Operations
    ContactBulkOperationRequest,
    ContactBulkOperationResponse,
    
    # Quality Models
    ContactQualityMetrics,
)

from .listings import (
    # Response Models
    ListingResponse,
    ContactSummary,
    ListingSearchResponse,
    ListingStatisticsResponse,
    
    # Request Models
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingSearchRequest,
    ListingFilter,
    
    # Statistics Models
    ListingStatisticsResponse,
    PriceStatistics,
    ProviderStatistics,
    
    # Export/Import Models
    ListingExportRequest,
    ListingExportResponse,
    
    # Deduplication Models
    ListingDuplicateGroup,
    ListingDeduplicationRequest,
    ListingDeduplicationResponse,
    
    # Quality Models
    ListingQualityMetrics,
    ListingQualityReport,
    
    # Bulk Operations
    ListingBulkUpdateRequest,
    ListingBulkOperationResponse,
)

from .scraper import (
    # Status Models
    ScraperStatusResponse,
    
    # Run Management
    ScraperRunRequest,
    ScraperRunResponse,
    ScrapingRunHistory,
    
    # Statistics
    ScraperStatisticsResponse,
    ProviderStatistics as ScraperProviderStatistics,
    
    # Configuration
    ScraperConfigRequest,
    ScraperConfigResponse,
    
    # Testing
    ScraperTestRequest,
    ScraperTestResult,
    
    # Performance
    PerformanceMetrics,
    ScraperHealthCheck,
    
    # Job Management
    ScraperJobRequest,
    ScraperJobResponse,
    
    # Resource Management
    ResourceUsage,
    RateLimitStatus,
    
    # Error Handling
    ScraperError,
    ErrorSummary as ScraperErrorSummary,
)

from .scheduler import (
    # Status Models
    SchedulerStatusResponse,
    
    # Job Management
    JobInfo,
    JobCreateRequest,
    JobUpdateRequest,
    JobControlRequest,
    JobControlResponse,
    
    # Execution Models
    JobExecutionResponse,
    JobExecutionHistory,
    
    # Configuration
    SchedulerConfigResponse,
    SchedulerConfigRequest,
    
    # Templates and Statistics
    JobTemplate,
    JobStatistics,
    
    # Workflows
    JobDependency,
    JobWorkflow,
    
    # Worker Management
    WorkerInfo,
    WorkerStatistics,
    
    # Scheduling
    SchedulePattern,
    ScheduleConflict,
    
    # Recovery
    JobRecoveryRequest,
    JobRecoveryResponse,
)

from .system import (
    # Health Check Models
    HealthCheckResponse as SystemHealthCheckResponse,
    ComponentHealth as SystemComponentHealth,
    
    # System Information
    SystemInfoResponse,
    ApplicationInfo,
    SystemSpecs,
    
    # Performance Metrics
    PerformanceMetricsResponse,
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    
    # Error Reporting
    ErrorReportRequest,
    ErrorReportResponse,
    ErrorSummary as SystemErrorSummary,
    
    # Log Management
    LogEntry,
    LogSearchRequest,
    LogSearchResponse,
    
    # System Metrics
    SystemMetricsResponse,
    MetricPoint,
    MetricSeries,
    
    # System Control
    SystemShutdownRequest,
    SystemShutdownResponse,
    
    # Resource Monitoring
    ResourceUsage as SystemResourceUsage,
    ResourceAlert,
    
    # Maintenance
    MaintenanceWindow,
    SystemMaintenanceRequest,
    
    # Version Management
    VersionInfo,
    SystemStatusResponse,
)

# Package metadata
__version__ = "1.0.0"
__author__ = "MWA Core Team"
__description__ = "MWA Core API Pydantic Schemas"

# Convenience imports for common usage patterns
# =============================================

# Most commonly used response models
MostUsedResponses = [
    "ContactResponse",
    "ListingResponse", 
    "ScraperStatusResponse",
    "JobInfo",
    "SystemStatusResponse",
    "ConfigResponse"
]

# Most commonly used request models
MostUsedRequests = [
    "ContactSearchRequest",
    "ListingSearchRequest",
    "ContactCreateRequest",
    "ListingCreateRequest",
    "JobCreateRequest",
    "ConfigUpdateRequest"
]

# Statistics models
StatisticsModels = [
    "ContactStatisticsResponse",
    "ListingStatisticsResponse", 
    "ScraperStatisticsResponse",
    "JobStatistics",
    "PerformanceMetricsResponse"
]

# Filter and pagination models
FilterModels = [
    "ContactFilter",
    "ListingFilter",
    "PaginationParams",
    "DateRange",
    "SearchParams"
]

# Validation models
ValidationModels = [
    "ContactValidationRequest",
    "ContactValidationResponse",
    "ContactReviewRequest",
    "ContactReviewResponse",
    "ConfigValidationResponse"
]

# Bulk operation models
BulkOperationModels = [
    "ContactBulkOperationRequest",
    "ContactBulkOperationResponse",
    "ListingBulkUpdateRequest",
    "ListingBulkOperationResponse"
]

# Export comprehensive model list
__all__ = [
    # Common models
    "ContactType",
    "ContactStatus", 
    "ListingStatus",
    "JobStatus",
    "SortOrder",
    "ValidationLevel",
    "PaginationParams",
    "SortParams",
    "DateRange",
    "SearchParams",
    "BaseFilter",
    "ContactFilter",
    "ListingFilter",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "StatisticsResponse",
    "EmailField",
    "PhoneField",
    "UrlField",
    "ConfidenceField",
    "ApiInfo",
    "RateLimitInfo",
    "ComponentHealth",
    "HealthCheckResponse",
    
    # Config models
    "ConfigResponse",
    "ConfigValidationResponse", 
    "ConfigSectionInfo",
    "ConfigBackupInfo",
    "ConfigDiff",
    "ConfigSchema",
    "ConfigUpdateRequest",
    "ConfigExportRequest",
    "ConfigImportRequest",
    "ConfigResetRequest",
    "ProviderConfig",
    "NotificationConfig",
    "DatabaseConfig",
    "LoggingConfig",
    "ConfigOperationResponse",
    "ConfigHistoryEntry",
    "ConfigTemplate",
    "EnvironmentConfig",
    "ConfigConstraint",
    "ConfigValidationRule",
    "EnvVarMapping",
    
    # Contact models
    "ContactResponse",
    "ListingSummary",
    "ValidationHistoryEntry", 
    "ContactSearchResponse",
    "ContactCreateRequest",
    "ContactUpdateRequest",
    "ContactSearchRequest",
    "ContactFilter",
    "ContactValidationRequest",
    "ContactValidationResult",
    "ContactValidationResponse",
    "ContactStatisticsResponse",
    "ValidationMethodStatistics",
    "ContactReviewRequest",
    "ContactReviewResult",
    "ContactReviewResponse",
    "ContactDiscoveryRequest",
    "ContactDiscoveryResult",
    "ContactBulkOperationRequest",
    "ContactBulkOperationResponse",
    "ContactQualityMetrics",
    
    # Listing models
    "ListingResponse",
    "ContactSummary",
    "ListingSearchResponse",
    "ListingStatisticsResponse",
    "ListingCreateRequest", 
    "ListingUpdateRequest",
    "ListingSearchRequest",
    "ListingFilter",
    "ListingStatisticsResponse",
    "PriceStatistics",
    "ProviderStatistics",
    "ListingExportRequest",
    "ListingExportResponse",
    "ListingDuplicateGroup",
    "ListingDeduplicationRequest",
    "ListingDeduplicationResponse",
    "ListingQualityMetrics",
    "ListingQualityReport",
    "ListingBulkUpdateRequest",
    "ListingBulkOperationResponse",
    
    # Scraper models
    "ScraperStatusResponse",
    "ScraperRunRequest",
    "ScraperRunResponse",
    "ScrapingRunHistory",
    "ScraperStatisticsResponse",
    "ScraperProviderStatistics",
    "ScraperConfigRequest",
    "ScraperConfigResponse",
    "ScraperTestRequest",
    "ScraperTestResult",
    "PerformanceMetrics",
    "ScraperHealthCheck",
    "ScraperJobRequest",
    "ScraperJobResponse",
    "ResourceUsage",
    "RateLimitStatus",
    "ScraperError",
    "ScraperErrorSummary",
    
    # Scheduler models
    "SchedulerStatusResponse",
    "JobInfo",
    "JobCreateRequest",
    "JobUpdateRequest",
    "JobControlRequest",
    "JobControlResponse",
    "JobExecutionResponse",
    "JobExecutionHistory",
    "SchedulerConfigResponse",
    "SchedulerConfigRequest",
    "JobTemplate",
    "JobStatistics",
    "JobDependency",
    "JobWorkflow",
    "WorkerInfo",
    "WorkerStatistics",
    "SchedulePattern",
    "ScheduleConflict",
    "JobRecoveryRequest",
    "JobRecoveryResponse",
    
    # System models
    "SystemHealthCheckResponse",
    "SystemComponentHealth",
    "SystemInfoResponse",
    "ApplicationInfo",
    "SystemSpecs",
    "PerformanceMetricsResponse",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "ErrorReportRequest",
    "ErrorReportResponse",
    "SystemErrorSummary",
    "LogEntry",
    "LogSearchRequest",
    "LogSearchResponse",
    "SystemMetricsResponse",
    "MetricPoint",
    "MetricSeries",
    "SystemShutdownRequest",
    "SystemShutdownResponse",
    "SystemResourceUsage",
    "ResourceAlert",
    "MaintenanceWindow",
    "SystemMaintenanceRequest",
    "VersionInfo",
    "SystemStatusResponse",
    
    # Model collections
    "MostUsedResponses",
    "MostUsedRequests", 
    "StatisticsModels",
    "FilterModels",
    "ValidationModels",
    "BulkOperationModels",
]

# Schema package documentation
"""
Schema Package Structure:

api/schemas/
├── __init__.py          # Package initialization and exports
├── common.py            # Shared models and utilities
├── config.py            # Configuration management
├── contacts.py          # Contact management and validation
├── listings.py          # Listing management and filtering
├── scraper.py           # Scraper operations and monitoring
├── scheduler.py         # Job scheduling and execution
└── system.py            # System health and metrics

Key Features:
- Comprehensive Pydantic models with validation
- Type hints and field descriptions for FastAPI docs
- Custom validators for complex fields (emails, URLs, etc.)
- Pagination and filtering support across all endpoints
- Error response models with consistent structure
- Statistics and metrics models for monitoring
- Bulk operation models for efficient data processing
- Quality assessment models for data validation
- System monitoring and health check models
- Configuration management with templates
- Job scheduling and execution tracking
- Scraper operations and performance monitoring

Usage Examples:
```python
from api.schemas import (
    ContactResponse,
    ContactSearchRequest,
    PaginatedResponse,
    ErrorResponse
)

# Contact listing with search and pagination
def get_contacts(search: ContactSearchRequest) -> PaginatedResponse[ContactResponse]:
    # Implementation here
    pass

# Error handling
def handle_errors() -> ErrorResponse:
    return ErrorResponse(
        error="ValidationError",
        message="Invalid contact data provided",
        details={"field": "email", "value": "invalid-email"}
    )
```

Integration Points:
- FastAPI automatic validation and documentation
- Pydantic models for request/response validation
- Integration with mwa_core database models
- Support for all 55 API endpoints across 6 routers
- Consistent error handling and response patterns
"""