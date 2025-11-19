"""
Configuration management Pydantic schemas for MWA Core API.

Provides request/response models for configuration management including
settings retrieval, updates, validation, export/import operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field, validator
from .common import SuccessResponse, ErrorResponse


# Configuration Response Models
class ConfigResponse(BaseModel):
    """Response model for configuration data."""
    config: Dict[str, Any] = Field(..., description="Configuration dictionary")
    config_path: str = Field(..., description="Path to configuration file")
    last_modified: Optional[datetime] = Field(None, description="Last modification time")
    validation_issues: List[str] = Field(default_factory=list, description="Configuration validation issues")
    
    class Config:
        schema_extra = {
            "example": {
                "config": {
                    "scraper": {
                        "enabled_providers": ["immoscout", "wg_gesucht"],
                        "request_delay_seconds": 2.0,
                        "timeout_seconds": 30
                    },
                    "contact_discovery": {
                        "enabled": True,
                        "confidence_threshold": 0.7
                    }
                },
                "config_path": "/path/to/config.json",
                "last_modified": "2025-11-19T11:18:08Z",
                "validation_issues": []
            }
        }


class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation."""
    is_valid: bool = Field(..., description="Whether configuration is valid")
    issues: List[str] = Field(default_factory=list, description="Validation issues")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    timestamp: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "issues": [],
                "warnings": ["Consider increasing request delay for better rate limiting"],
                "timestamp": "2025-11-19T11:18:08Z"
            }
        }


class ConfigSectionInfo(BaseModel):
    """Information about a configuration section."""
    name: str = Field(..., description="Section name")
    description: Optional[str] = Field(None, description="Section description")
    keys: List[str] = Field(..., description="Available configuration keys")
    required: List[str] = Field(default_factory=list, description="Required configuration keys")
    optional: List[str] = Field(default_factory=list, description="Optional configuration keys")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "scraper",
                "description": "Scraper configuration settings",
                "keys": ["enabled_providers", "request_delay_seconds", "timeout_seconds"],
                "required": ["enabled_providers"],
                "optional": ["request_delay_seconds", "timeout_seconds"]
            }
        }


# Configuration Request Models
class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    section: Optional[str] = Field(None, description="Configuration section to update")
    updates: Dict[str, Any] = Field(..., description="Configuration updates to apply")
    validate_before_save: bool = Field(True, description="Validate before saving")
    
    @validator('updates')
    def validate_updates(cls, v):
        if not isinstance(v, dict) or not v:
            raise ValueError('Updates must be a non-empty dictionary')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "section": "scraper",
                "updates": {
                    "request_delay_seconds": 3.0,
                    "timeout_seconds": 45
                },
                "validate_before_save": True
            }
        }


class ConfigExportRequest(BaseModel):
    """Request model for configuration export."""
    include_sensitive: bool = Field(False, description="Include sensitive data like passwords")
    sections: Optional[List[str]] = Field(None, description="Specific sections to export")
    format: str = Field("json", regex="^(json|yaml)$", description="Export format")
    
    class Config:
        schema_extra = {
            "example": {
                "include_sensitive": False,
                "sections": ["scraper", "contact_discovery"],
                "format": "json"
            }
        }


class ConfigImportRequest(BaseModel):
    """Request model for configuration import."""
    config_data: Dict[str, Any] = Field(..., description="Configuration data to import")
    merge_strategy: str = Field("replace", regex="^(replace|merge)$", description="Merge strategy")
    validate_before_import: bool = Field(True, description="Validate before importing")
    backup_current: bool = Field(True, description="Create backup of current config")
    
    class Config:
        schema_extra = {
            "example": {
                "config_data": {
                    "scraper": {
                        "enabled_providers": ["immoscout"],
                        "request_delay_seconds": 5.0
                    }
                },
                "merge_strategy": "replace",
                "validate_before_import": True,
                "backup_current": True
            }
        }


class ConfigResetRequest(BaseModel):
    """Request model for configuration reset."""
    section: Optional[str] = Field(None, description="Section to reset (all if None)")
    backup_current: bool = Field(True, description="Backup current configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "section": "scraper",
                "backup_current": True
            }
        }


# Configuration Management Models
class ConfigBackupInfo(BaseModel):
    """Information about a configuration backup."""
    path: str = Field(..., description="Backup file path")
    created_at: datetime = Field(..., description="Backup creation time")
    size_bytes: Optional[int] = Field(None, description="Backup size in bytes")
    sections_included: List[str] = Field(..., description="Sections included in backup")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "/path/to/config_backup_20251119_111808.json",
                "created_at": "2025-11-19T11:18:08Z",
                "size_bytes": 2048,
                "sections_included": ["scraper", "contact_discovery", "scheduler"]
            }
        }


class ConfigDiff(BaseModel):
    """Configuration difference between two versions."""
    added: Dict[str, Any] = Field(default_factory=dict, description="Added configuration keys")
    modified: Dict[str, Any] = Field(default_factory=dict, description="Modified configuration keys")
    removed: List[str] = Field(default_factory=list, description="Removed configuration keys")
    unchanged: List[str] = Field(default_factory=list, description="Unchanged configuration keys")
    
    class Config:
        schema_extra = {
            "example": {
                "added": {
                    "scraper.new_feature": True
                },
                "modified": {
                    "scraper.request_delay_seconds": {
                        "old": 2.0,
                        "new": 3.0
                    }
                },
                "removed": ["scraper.deprecated_setting"],
                "unchanged": ["contact_discovery.enabled"]
            }
        }


class ConfigSchema(BaseModel):
    """Schema definition for a configuration section."""
    type: str = Field(..., description="Configuration type")
    properties: Dict[str, Any] = Field(..., description="Configuration properties schema")
    required: List[str] = Field(default_factory=list, description="Required properties")
    description: Optional[str] = Field(None, description="Section description")
    additional_properties: bool = Field(False, description="Allow additional properties")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "object",
                "properties": {
                    "enabled_providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of enabled providers"
                    },
                    "request_delay_seconds": {
                        "type": "number",
                        "minimum": 0.1,
                        "maximum": 60.0,
                        "description": "Delay between requests"
                    }
                },
                "required": ["enabled_providers"],
                "description": "Scraper configuration schema",
                "additional_properties": False
            }
        }


# Specialized Configuration Models
class ProviderConfig(BaseModel):
    """Configuration for a specific provider."""
    name: str = Field(..., description="Provider name")
    enabled: bool = Field(..., description="Whether provider is enabled")
    base_url: str = Field(..., description="Provider base URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific settings")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "immoscout",
                "enabled": True,
                "base_url": "https://www.immoscout24.de",
                "headers": {
                    "User-Agent": "MWA-Bot/1.0"
                },
                "rate_limit": {
                    "requests_per_minute": 30,
                    "burst_limit": 5
                },
                "custom_settings": {
                    "max_pages": 10,
                    "include_furnished": True
                }
            }
        }


class NotificationConfig(BaseModel):
    """Configuration for notification system."""
    enabled: bool = Field(..., description="Whether notifications are enabled")
    channels: List[str] = Field(default_factory=list, description="Enabled notification channels")
    templates: Dict[str, str] = Field(default_factory=dict, description="Notification templates")
    default_recipients: List[str] = Field(default_factory=list, description="Default notification recipients")
    quiet_hours: Optional[Dict[str, Any]] = Field(None, description="Quiet hours configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "channels": ["email", "webhook"],
                "templates": {
                    "new_listing": "New listing found: {title}",
                    "error": "System error: {message}"
                },
                "default_recipients": ["admin@example.com"],
                "quiet_hours": {
                    "start": "22:00",
                    "end": "08:00",
                    "timezone": "Europe/Berlin"
                }
            }
        }


class DatabaseConfig(BaseModel):
    """Configuration for database settings."""
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(..., ge=1, le=100, description="Connection pool size")
    pool_timeout: int = Field(..., ge=1, le=300, description="Pool timeout in seconds")
    pool_recycle: int = Field(..., ge=300, description="Pool recycle time in seconds")
    echo: bool = Field(False, description="Enable SQL echo")
    backup_enabled: bool = Field(True, description="Enable automatic backups")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "sqlite:///./data/mwa_core.db",
                "pool_size": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
                "backup_enabled": True
            }
        }


class LoggingConfig(BaseModel):
    """Configuration for logging system."""
    level: str = Field(..., regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Log level")
    format: str = Field(..., description="Log format string")
    handlers: List[str] = Field(default_factory=list, description="Enabled log handlers")
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size: Optional[int] = Field(None, description="Max log file size in MB")
    backup_count: int = Field(..., ge=1, le=10, description="Number of backup log files")
    
    class Config:
        schema_extra = {
            "example": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console", "file"],
                "file_path": "logs/mwa_core.log",
                "max_file_size": 100,
                "backup_count": 5
            }
        }


# Configuration Management Responses
class ConfigOperationResponse(BaseModel):
    """Response for configuration operations."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")
    backup_created: Optional[ConfigBackupInfo] = Field(None, description="Backup information if created")
    validation_result: Optional[ConfigValidationResponse] = Field(None, description="Validation results")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Configuration updated successfully",
                "backup_created": {
                    "path": "/path/to/config_backup_20251119_111808.json",
                    "created_at": "2025-11-19T11:18:08Z",
                    "size_bytes": 2048,
                    "sections_included": ["scraper"]
                },
                "validation_result": {
                    "is_valid": True,
                    "issues": [],
                    "warnings": [],
                    "timestamp": "2025-11-19T11:18:08Z"
                },
                "timestamp": "2025-11-19T11:18:08Z"
            }
        }


class ConfigHistoryEntry(BaseModel):
    """Entry in configuration change history."""
    timestamp: datetime = Field(..., description="Change timestamp")
    action: str = Field(..., description="Change action (create/update/delete)")
    section: str = Field(..., description="Configuration section changed")
    user: Optional[str] = Field(None, description="User who made the change")
    changes: ConfigDiff = Field(..., description="Configuration changes")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-11-19T11:18:08Z",
                "action": "update",
                "section": "scraper",
                "user": "admin",
                "changes": {
                    "added": {},
                    "modified": {
                        "scraper.request_delay_seconds": {
                            "old": 2.0,
                            "new": 3.0
                        }
                    },
                    "removed": [],
                    "unchanged": ["scraper.enabled_providers"]
                }
            }
        }


# Configuration Templates
class ConfigTemplate(BaseModel):
    """Configuration template for common setups."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    config: Dict[str, Any] = Field(..., description="Template configuration")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "development",
                "description": "Development environment configuration",
                "config": {
                    "scraper": {
                        "enabled_providers": ["immoscout"],
                        "request_delay_seconds": 1.0,
                        "timeout_seconds": 15
                    },
                    "contact_discovery": {
                        "enabled": True,
                        "confidence_threshold": 0.8
                    }
                },
                "tags": ["development", "debugging", "fast"]
            }
        }


# Environment-specific Configurations
class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    environment: str = Field(..., description="Environment name (dev/staging/prod)")
    config: Dict[str, Any] = Field(..., description="Environment-specific config")
    parent_config: Optional[str] = Field(None, description="Parent configuration to inherit from")
    overrides: Dict[str, Any] = Field(default_factory=dict, description="Configuration overrides")
    
    class Config:
        schema_extra = {
            "example": {
                "environment": "development",
                "config": {
                    "logging": {
                        "level": "DEBUG"
                    },
                    "scraper": {
                        "timeout_seconds": 15
                    }
                },
                "parent_config": "base",
                "overrides": {
                    "database.echo": True
                }
            }
        }


# Validation and Constraint Models
class ConfigConstraint(BaseModel):
    """Configuration field constraint."""
    field_path: str = Field(..., description="Dot-separated path to field")
    constraint_type: str = Field(..., description="Type of constraint")
    value: Any = Field(..., description="Constraint value")
    message: Optional[str] = Field(None, description="Error message if constraint violated")
    
    class Config:
        schema_extra = {
            "example": {
                "field_path": "scraper.request_delay_seconds",
                "constraint_type": "range",
                "value": {"min": 0.1, "max": 60.0},
                "message": "Request delay must be between 0.1 and 60.0 seconds"
            }
        }


class ConfigValidationRule(BaseModel):
    """Configuration validation rule."""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    constraint: ConfigConstraint = Field(..., description="Rule constraint")
    severity: str = Field(..., regex="^(error|warning|info)$", description="Rule severity")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "provider_timeout_range",
                "description": "Provider timeout must be within reasonable limits",
                "constraint": {
                    "field_path": "scraper.timeout_seconds",
                    "constraint_type": "range",
                    "value": {"min": 5, "max": 300},
                    "message": "Timeout must be between 5 and 300 seconds"
                },
                "severity": "error"
            }
        }


# Configuration Environment Variables
class EnvVarMapping(BaseModel):
    """Mapping between environment variables and config keys."""
    env_var: str = Field(..., description="Environment variable name")
    config_key: str = Field(..., description="Configuration key path")
    required: bool = Field(False, description="Whether env var is required")
    default_value: Optional[Any] = Field(None, description="Default value if not set")
    description: Optional[str] = Field(None, description="Variable description")
    
    class Config:
        schema_extra = {
            "example": {
                "env_var": "MWA_DB_URL",
                "config_key": "database.url",
                "required": True,
                "default_value": "sqlite:///./data/mwa_core.db",
                "description": "Database connection URL"
            }
        }