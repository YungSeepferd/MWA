"""
Configuration management router for MWA Core API.

Provides endpoints for managing application settings, including:
- Retrieving current configuration
- Updating configuration values
- Validating configuration
- Resetting to defaults
- Exporting/importing configuration
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, validator

from mwa_core.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for configuration requests/responses
class ConfigResponse(BaseModel):
    """Response model for configuration data."""
    config: Dict[str, Any]
    config_path: str
    last_modified: Optional[datetime] = None
    validation_issues: List[str] = []


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    section: Optional[str] = Field(None, description="Configuration section to update (e.g., 'scraper', 'notification')")
    updates: Dict[str, Any] = Field(..., description="Configuration updates to apply")
    validate_before_save: bool = Field(True, description="Validate configuration before saving")


class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation."""
    is_valid: bool
    issues: List[str] = []
    warnings: List[str] = []
    timestamp: datetime


class ConfigExportRequest(BaseModel):
    """Request model for configuration export."""
    include_sensitive: bool = Field(False, description="Include sensitive data like passwords and tokens")
    sections: Optional[List[str]] = Field(None, description="Specific sections to export (null for all)")


class ConfigImportRequest(BaseModel):
    """Request model for configuration import."""
    config_data: Dict[str, Any] = Field(..., description="Configuration data to import")
    merge_strategy: str = Field("replace", regex="^(replace|merge)$", description="How to handle existing config")
    validate_before_import: bool = Field(True, description="Validate configuration before importing")
    backup_current: bool = Field(True, description="Create backup of current configuration")


# Dependency to get settings instance
def get_settings_instance() -> Settings:
    """Get the current settings instance."""
    return get_settings()


@router.get("/", response_model=ConfigResponse, summary="Get current configuration")
async def get_configuration(
    section: Optional[str] = Query(None, description="Specific configuration section to retrieve"),
    include_sensitive: bool = Query(False, description="Include sensitive data like passwords"),
    settings: Settings = Depends(get_settings_instance)
):
    """
    Retrieve the current application configuration.
    
    Args:
        section: Optional section name to retrieve specific configuration
        include_sensitive: Whether to include sensitive data in response
        settings: Settings instance from dependency injection
        
    Returns:
        Current configuration data
    """
    try:
        # Get full configuration
        config_dict = settings.dict(exclude_none=True)
        
        # Filter by section if specified
        if section:
            if section not in config_dict:
                raise HTTPException(status_code=404, detail=f"Configuration section '{section}' not found")
            config_dict = {section: config_dict[section]}
        
        # Remove sensitive data unless explicitly requested
        if not include_sensitive:
            config_dict = _remove_sensitive_data(config_dict)
        
        # Get validation issues
        validation_issues = settings.validate_configuration()
        
        return ConfigResponse(
            config=config_dict,
            config_path=str(settings.config_path),
            last_modified=datetime.fromtimestamp(settings.config_path.stat().st_mtime) if settings.config_path.exists() else None,
            validation_issues=validation_issues
        )
        
    except Exception as e:
        logger.error(f"Error retrieving configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")


@router.put("/", response_model=ConfigResponse, summary="Update configuration")
async def update_configuration(
    request: ConfigUpdateRequest,
    settings: Settings = Depends(get_settings_instance)
):
    """
    Update application configuration.
    
    Args:
        request: Configuration update request
        settings: Settings instance from dependency injection
        
    Returns:
        Updated configuration data
    """
    try:
        # Get current configuration
        current_config = settings.dict(exclude_none=True)
        
        # Apply updates
        if request.section:
            # Update specific section
            if request.section not in current_config:
                raise HTTPException(status_code=404, detail=f"Configuration section '{request.section}' not found")
            
            # Merge updates into section
            if request.section in current_config and isinstance(current_config[request.section], dict):
                current_config[request.section].update(request.updates)
            else:
                current_config[request.section] = request.updates
        else:
            # Update entire configuration
            current_config.update(request.updates)
        
        # Validate if requested
        if request.validate_before_save:
            temp_settings = Settings.parse_obj(current_config)
            validation_issues = temp_settings.validate_configuration()
            if validation_issues:
                return ConfigResponse(
                    config=current_config,
                    config_path=str(settings.config_path),
                    validation_issues=validation_issues
                )
        
        # Save updated configuration
        updated_settings = Settings.parse_obj(current_config)
        updated_settings.save()
        
        # Reload settings to apply changes
        from mwa_core.config.settings import reload_settings
        reload_settings()
        
        # Get validation issues for final config
        validation_issues = updated_settings.validate_configuration()
        
        return ConfigResponse(
            config=updated_settings.dict(exclude_none=True),
            config_path=str(updated_settings.config_path),
            validation_issues=validation_issues
        )
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


@router.post("/validate", response_model=ConfigValidationResponse, summary="Validate configuration")
async def validate_configuration(
    config_data: Optional[Dict[str, Any]] = Body(None, description="Configuration data to validate (null for current)"),
    settings: Settings = Depends(get_settings_instance)
):
    """
    Validate configuration data.
    
    Args:
        config_data: Configuration data to validate (uses current if not provided)
        settings: Settings instance from dependency injection
        
    Returns:
        Validation results
    """
    try:
        if config_data is None:
            # Validate current configuration
            validation_issues = settings.validate_configuration()
            return ConfigValidationResponse(
                is_valid=len(validation_issues) == 0,
                issues=validation_issues,
                timestamp=datetime.now()
            )
        else:
            # Validate provided configuration
            try:
                temp_settings = Settings.parse_obj(config_data)
                validation_issues = temp_settings.validate_configuration()
                return ConfigValidationResponse(
                    is_valid=len(validation_issues) == 0,
                    issues=validation_issues,
                    timestamp=datetime.now()
                )
            except Exception as e:
                return ConfigValidationResponse(
                    is_valid=False,
                    issues=[f"Configuration parsing error: {str(e)}"],
                    timestamp=datetime.now()
                )
                
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating configuration: {str(e)}")


@router.post("/reset", response_model=ConfigResponse, summary="Reset configuration to defaults")
async def reset_configuration(
    section: Optional[str] = Query(None, description="Specific section to reset (null for all)"),
    backup_current: bool = Query(True, description="Create backup before resetting"),
    settings: Settings = Depends(get_settings_instance)
):
    """
    Reset configuration to default values.
    
    Args:
        section: Optional section to reset (resets all if not provided)
        backup_current: Whether to create backup of current configuration
        settings: Settings instance from dependency injection
        
    Returns:
        Reset configuration data
    """
    try:
        # Create backup if requested
        if backup_current:
            backup_path = settings.config_path.parent / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            settings.save(backup_path)
            logger.info(f"Created configuration backup at {backup_path}")
        
        # Get default configuration
        default_config = Settings.generate_example_config()
        
        if section:
            # Reset specific section
            current_config = settings.dict(exclude_none=True)
            if section not in default_config:
                raise HTTPException(status_code=404, detail=f"Default configuration for section '{section}' not found")
            
            current_config[section] = default_config[section]
            updated_config = current_config
        else:
            # Reset entire configuration
            updated_config = default_config
        
        # Save and reload
        updated_settings = Settings.parse_obj(updated_config)
        updated_settings.save()
        
        from mwa_core.config.settings import reload_settings
        reload_settings()
        
        validation_issues = updated_settings.validate_configuration()
        
        return ConfigResponse(
            config=updated_config,
            config_path=str(updated_settings.config_path),
            validation_issues=validation_issues
        )
        
    except Exception as e:
        logger.error(f"Error resetting configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting configuration: {str(e)}")


@router.post("/export", response_model=Dict[str, Any], summary="Export configuration")
async def export_configuration(
    request: ConfigExportRequest,
    settings: Settings = Depends(get_settings_instance)
):
    """
    Export configuration data.
    
    Args:
        request: Export request parameters
        settings: Settings instance from dependency injection
        
    Returns:
        Exported configuration data
    """
    try:
        config_dict = settings.dict(exclude_none=True)
        
        # Filter by sections if specified
        if request.sections:
            filtered_config = {}
            for section in request.sections:
                if section in config_dict:
                    filtered_config[section] = config_dict[section]
                else:
                    logger.warning(f"Section '{section}' not found in configuration")
            config_dict = filtered_config
        
        # Remove sensitive data unless explicitly requested
        if not request.include_sensitive:
            config_dict = _remove_sensitive_data(config_dict)
        
        return {
            "exported_at": datetime.now().isoformat(),
            "config": config_dict,
            "sections_included": list(config_dict.keys()),
            "sensitive_data_included": request.include_sensitive
        }
        
    except Exception as e:
        logger.error(f"Error exporting configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting configuration: {str(e)}")


@router.post("/import", response_model=ConfigResponse, summary="Import configuration")
async def import_configuration(
    request: ConfigImportRequest,
    settings: Settings = Depends(get_settings_instance)
):
    """
    Import configuration data.
    
    Args:
        request: Import request parameters
        settings: Settings instance from dependency injection
        
    Returns:
        Imported configuration data
    """
    try:
        # Create backup if requested
        if request.backup_current:
            backup_path = settings.config_path.parent / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            settings.save(backup_path)
            logger.info(f"Created configuration backup at {backup_path}")
        
        # Get current configuration
        current_config = settings.dict(exclude_none=True)
        
        # Apply import based on merge strategy
        if request.merge_strategy == "replace":
            imported_config = request.config_data
        else:  # merge
            imported_config = current_config.copy()
            _deep_merge(imported_config, request.config_data)
        
        # Validate if requested
        if request.validate_before_import:
            try:
                temp_settings = Settings.parse_obj(imported_config)
                validation_issues = temp_settings.validate_configuration()
                if validation_issues:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Configuration validation failed: {validation_issues}"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Configuration validation error: {str(e)}"
                )
        
        # Save imported configuration
        imported_settings = Settings.parse_obj(imported_config)
        imported_settings.save()
        
        # Reload settings to apply changes
        from mwa_core.config.settings import reload_settings
        reload_settings()
        
        validation_issues = imported_settings.validate_configuration()
        
        return ConfigResponse(
            config=imported_config,
            config_path=str(imported_settings.config_path),
            validation_issues=validation_issues
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error importing configuration: {str(e)}")


@router.get("/sections", response_model=List[str], summary="List configuration sections")
async def list_configuration_sections(
    settings: Settings = Depends(get_settings_instance)
):
    """
    Get list of available configuration sections.
    
    Args:
        settings: Settings instance from dependency injection
        
    Returns:
        List of configuration section names
    """
    try:
        config_dict = settings.dict(exclude_none=True)
        return list(config_dict.keys())
        
    except Exception as e:
        logger.error(f"Error listing configuration sections: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing configuration sections: {str(e)}")


def _remove_sensitive_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data from configuration dictionary."""
    sensitive_keys = [
        'password', 'token', 'secret', 'key', 'webhook_url', 
        'smtp_password', 'bot_token', 'api_key'
    ]
    
    def _remove_sensitive_recursive(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: _remove_sensitive_recursive(v) 
                for k, v in obj.items() 
                if not any(sensitive in k.lower() for sensitive in sensitive_keys)
            }
        elif isinstance(obj, list):
            return [_remove_sensitive_recursive(item) for item in obj]
        else:
            return obj
    
    return _remove_sensitive_recursive(config)


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Deep merge source dictionary into target dictionary."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value