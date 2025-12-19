"""
FastAPI endpoints for table part settings management.

This module provides REST API endpoints for managing user table part settings,
including CRUD operations, import/export, and migration functionality.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ..dependencies.database import get_db
from ..dependencies.auth import get_current_user
from ...src.services.table_part_settings_service import TablePartSettingsService
from ...src.services.table_part_settings_migration import TablePartSettingsMigrator
from ...src.data.models.table_part_models import TablePartSettingsData
from ...src.data.models.sqlalchemy_models import User

router = APIRouter(prefix="/table-part-settings", tags=["table-part-settings"])


# Pydantic models for API
class PanelSettingsModel(BaseModel):
    visible_commands: List[str] = Field(default_factory=list)
    hidden_commands: List[str] = Field(default_factory=list)
    button_size: str = Field(default="medium")
    show_tooltips: bool = Field(default=True)
    compact_mode: bool = Field(default=False)


class ShortcutSettingsModel(BaseModel):
    enabled: bool = Field(default=True)
    custom_mappings: Dict[str, str] = Field(default_factory=dict)


class TablePartSettingsModel(BaseModel):
    column_widths: Dict[str, int] = Field(default_factory=dict)
    column_order: List[str] = Field(default_factory=list)
    hidden_columns: List[str] = Field(default_factory=list)
    panel_settings: PanelSettingsModel
    shortcuts: ShortcutSettingsModel
    sort_column: Optional[str] = None
    sort_direction: str = Field(default="asc")
    version: Optional[str] = None
    updated_at: Optional[str] = None


class SaveSettingsRequest(BaseModel):
    settings_data: TablePartSettingsModel


class ImportSettingsRequest(BaseModel):
    import_data: Dict[str, Any]
    overwrite_existing: bool = Field(default=False)


class SettingsResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class UserSettingsResponse(BaseModel):
    user_id: int
    document_type: str
    table_part_id: str
    settings_data: TablePartSettingsModel
    created_at: datetime
    updated_at: datetime


def convert_to_settings_data(model: TablePartSettingsModel) -> TablePartSettingsData:
    """Convert Pydantic model to internal data model"""
    from ...src.data.models.table_part_models import PanelSettings, ShortcutSettings
    
    panel_settings = PanelSettings(
        visible_commands=model.panel_settings.visible_commands,
        hidden_commands=model.panel_settings.hidden_commands,
        button_size=model.panel_settings.button_size,
        show_tooltips=model.panel_settings.show_tooltips,
        compact_mode=model.panel_settings.compact_mode
    )
    
    shortcuts = ShortcutSettings(
        enabled=model.shortcuts.enabled,
        custom_mappings=model.shortcuts.custom_mappings
    )
    
    return TablePartSettingsData(
        column_widths=model.column_widths,
        column_order=model.column_order,
        hidden_columns=model.hidden_columns,
        panel_settings=panel_settings,
        shortcuts=shortcuts,
        sort_column=model.sort_column,
        sort_direction=model.sort_direction
    )


def convert_from_settings_data(data: TablePartSettingsData) -> TablePartSettingsModel:
    """Convert internal data model to Pydantic model"""
    panel_settings = PanelSettingsModel(
        visible_commands=data.panel_settings.visible_commands,
        hidden_commands=data.panel_settings.hidden_commands,
        button_size=data.panel_settings.button_size,
        show_tooltips=data.panel_settings.show_tooltips,
        compact_mode=data.panel_settings.compact_mode
    )
    
    shortcuts = ShortcutSettingsModel(
        enabled=data.shortcuts.enabled,
        custom_mappings=data.shortcuts.custom_mappings
    )
    
    return TablePartSettingsModel(
        column_widths=data.column_widths,
        column_order=data.column_order,
        hidden_columns=data.hidden_columns,
        panel_settings=panel_settings,
        shortcuts=shortcuts,
        sort_column=data.sort_column,
        sort_direction=data.sort_direction
    )


@router.get("/{user_id}/{document_type}/{table_part_id}")
async def get_user_settings(
    user_id: int,
    document_type: str,
    table_part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserSettingsResponse:
    """Get user settings for a specific table part"""
    
    # Check if user can access these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    settings_data = settings_service.get_user_settings(
        user_id, document_type, table_part_id
    )
    
    if not settings_data:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    # Get the database record for timestamps
    from ...src.data.models.sqlalchemy_models import UserTablePartSettings
    from sqlalchemy import and_
    
    settings_record = db.query(UserTablePartSettings).filter(
        and_(
            UserTablePartSettings.user_id == user_id,
            UserTablePartSettings.document_type == document_type,
            UserTablePartSettings.table_part_id == table_part_id
        )
    ).first()
    
    if not settings_record:
        raise HTTPException(status_code=404, detail="Settings record not found")
    
    return UserSettingsResponse(
        user_id=user_id,
        document_type=document_type,
        table_part_id=table_part_id,
        settings_data=convert_from_settings_data(settings_data),
        created_at=settings_record.created_at,
        updated_at=settings_record.updated_at
    )


@router.put("/{user_id}/{document_type}/{table_part_id}")
async def save_user_settings(
    user_id: int,
    document_type: str,
    table_part_id: str,
    request: SaveSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SettingsResponse:
    """Save user settings for a table part"""
    
    # Check if user can modify these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    # Convert to internal data model
    settings_data = convert_to_settings_data(request.settings_data)
    
    # Validate settings
    is_valid, errors = settings_service.validate_settings_data(settings_data.to_json())
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid settings data: {'; '.join(errors)}"
        )
    
    success = settings_service.save_user_settings(
        user_id, document_type, table_part_id, settings_data
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    
    return SettingsResponse(
        success=True,
        message="Settings saved successfully"
    )


@router.delete("/{user_id}/{document_type}/{table_part_id}")
async def reset_user_settings(
    user_id: int,
    document_type: str,
    table_part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SettingsResponse:
    """Reset user settings to defaults"""
    
    # Check if user can modify these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    success = settings_service.reset_user_settings(
        user_id, document_type, table_part_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset settings")
    
    return SettingsResponse(
        success=True,
        message="Settings reset to defaults"
    )


@router.get("/{user_id}")
async def get_all_user_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all table part settings for a user"""
    
    # Check if user can access these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    all_settings = settings_service.get_all_user_settings(user_id)
    
    return {
        "user_id": user_id,
        "settings": all_settings
    }


@router.get("/{user_id}/export")
async def export_user_settings(
    user_id: int,
    document_type: Optional[str] = Query(None),
    table_part_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export user settings for backup or transfer"""
    
    # Check if user can access these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    export_data = settings_service.export_user_settings(
        user_id, document_type, table_part_id
    )
    
    if 'error' in export_data:
        raise HTTPException(status_code=500, detail=export_data['error'])
    
    return export_data


@router.post("/{user_id}/import")
async def import_user_settings(
    user_id: int,
    request: ImportSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Import user settings from backup or transfer"""
    
    # Check if user can modify these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    result = settings_service.import_user_settings(
        user_id, request.import_data, request.overwrite_existing
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', 'Import failed'))
    
    return result


@router.get("/{user_id}/defaults/{document_type}/{table_part_id}")
async def get_default_settings(
    user_id: int,
    document_type: str,
    table_part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TablePartSettingsModel:
    """Get default settings for a table part"""
    
    # Check if user can access these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings_service = TablePartSettingsService(db)
    
    default_settings = settings_service.get_default_settings(
        document_type, table_part_id
    )
    
    return convert_from_settings_data(default_settings)


@router.post("/migrate")
async def migrate_all_settings(
    target_version: str = Query("1.0"),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Migrate all user settings to target version (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    migrator = TablePartSettingsMigrator(db)
    
    migration_report = migrator.migrate_all_user_settings(
        target_version, dry_run
    )
    
    return migration_report


@router.post("/{user_id}/migrate")
async def migrate_user_settings(
    user_id: int,
    target_version: str = Query("1.0"),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Migrate settings for a specific user"""
    
    # Check if user can modify these settings
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    migrator = TablePartSettingsMigrator(db)
    
    migration_report = migrator.migrate_user_settings(
        user_id, target_version, dry_run
    )
    
    return migration_report


@router.get("/validate/all")
async def validate_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate all settings records (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    migrator = TablePartSettingsMigrator(db)
    
    validation_report = migrator.validate_all_settings()
    
    return validation_report


@router.post("/backup")
async def create_settings_backup(
    backup_path: str = Query(..., description="Path to save backup file"),
    user_id: Optional[int] = Query(None, description="User ID to backup (all users if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a backup of settings data (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    migrator = TablePartSettingsMigrator(db)
    
    backup_result = migrator.backup_settings(backup_path, user_id)
    
    if not backup_result['success']:
        raise HTTPException(status_code=500, detail=backup_result['error'])
    
    return backup_result


@router.post("/restore")
async def restore_settings_backup(
    backup_path: str = Query(..., description="Path to backup file"),
    overwrite_existing: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Restore settings from backup file (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    migrator = TablePartSettingsMigrator(db)
    
    restore_result = migrator.restore_settings(backup_path, overwrite_existing)
    
    if not restore_result['success']:
        raise HTTPException(status_code=500, detail=restore_result['error'])
    
    return restore_result


@router.get("/migration-status")
async def get_migration_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current migration status for all settings (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    migrator = TablePartSettingsMigrator(db)
    
    status = migrator.get_migration_status()
    
    return status