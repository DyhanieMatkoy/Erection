"""
API endpoints for panel configuration management.

This module provides REST API endpoints for managing table part
panel configurations, including saving, loading, and resetting
user-specific panel settings.

Requirements: 9.5
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..dependencies.database import get_db
from ..dependencies.auth import get_current_user
from src.services.panel_configuration_service import PanelConfigurationService
from src.data.models.table_part_models import TablePartCommand, PanelSettings

router = APIRouter(prefix="/panel-configuration", tags=["panel-configuration"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CommandRequest(BaseModel):
    """Request model for table part command"""
    id: str
    name: str
    icon: str
    tooltip: str
    shortcut: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    form_method: Optional[str] = None
    position: int = 0
    requires_selection: bool = False


class PanelSettingsRequest(BaseModel):
    """Request model for panel settings"""
    visible_commands: List[str]
    hidden_commands: List[str] = []
    button_size: str = "medium"
    show_tooltips: bool = True
    compact_mode: bool = False


class SaveConfigurationRequest(BaseModel):
    """Request model for saving panel configuration"""
    user_id: int
    document_type: str
    commands: List[CommandRequest]
    panel_settings: PanelSettingsRequest
    apply_to_all_table_parts: bool = True


class ResetConfigurationRequest(BaseModel):
    """Request model for resetting panel configuration"""
    user_id: int
    document_type: str
    apply_to_all_table_parts: bool = True


class CommandResponse(BaseModel):
    """Response model for table part command"""
    id: str
    name: str
    icon: str
    tooltip: str
    shortcut: Optional[str] = None
    enabled: bool
    visible: bool
    form_method: Optional[str] = None
    position: int
    requires_selection: bool


class PanelSettingsResponse(BaseModel):
    """Response model for panel settings"""
    visible_commands: List[str]
    hidden_commands: List[str]
    button_size: str
    show_tooltips: bool
    compact_mode: bool


class LoadConfigurationResponse(BaseModel):
    """Response model for loading panel configuration"""
    commands: List[CommandResponse]
    panel_settings: PanelSettingsResponse


class ConfigurationSummaryResponse(BaseModel):
    """Response model for configuration summary"""
    total_configurations: int
    document_types: Dict[str, Dict[str, Any]]
    last_modified: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/", response_model=Dict[str, bool])
async def save_panel_configuration(
    request: SaveConfigurationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Save panel configuration for a document type.
    
    Requirements: 9.5
    """
    try:
        service = PanelConfigurationService(db)
        
        # Convert request models to domain models
        commands = []
        for cmd_req in request.commands:
            command = TablePartCommand(
                id=cmd_req.id,
                name=cmd_req.name,
                icon=cmd_req.icon,
                tooltip=cmd_req.tooltip,
                shortcut=cmd_req.shortcut,
                enabled=cmd_req.enabled,
                visible=cmd_req.visible,
                form_method=cmd_req.form_method,
                position=cmd_req.position,
                requires_selection=cmd_req.requires_selection
            )
            commands.append(command)
        
        panel_settings = PanelSettings(
            visible_commands=request.panel_settings.visible_commands,
            hidden_commands=request.panel_settings.hidden_commands,
            button_size=request.panel_settings.button_size,
            show_tooltips=request.panel_settings.show_tooltips,
            compact_mode=request.panel_settings.compact_mode
        )
        
        success = service.save_panel_configuration(
            user_id=request.user_id,
            document_type=request.document_type,
            commands=commands,
            panel_settings=panel_settings,
            apply_to_all_table_parts=request.apply_to_all_table_parts
        )
        
        return {"success": success}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving panel configuration: {str(e)}")


@router.get("/", response_model=LoadConfigurationResponse)
async def load_panel_configuration(
    user_id: int = Query(..., description="User ID"),
    document_type: str = Query(..., description="Document type"),
    table_part_id: Optional[str] = Query(None, description="Table part ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Load panel configuration for a document type and table part.
    
    Requirements: 9.5
    """
    try:
        service = PanelConfigurationService(db)
        
        commands, panel_settings = service.load_panel_configuration(
            user_id=user_id,
            document_type=document_type,
            table_part_id=table_part_id
        )
        
        # Convert domain models to response models
        command_responses = []
        for cmd in commands:
            cmd_response = CommandResponse(
                id=cmd.id,
                name=cmd.name,
                icon=cmd.icon,
                tooltip=cmd.tooltip,
                shortcut=cmd.shortcut,
                enabled=cmd.enabled,
                visible=cmd.visible,
                form_method=cmd.form_method,
                position=cmd.position,
                requires_selection=cmd.requires_selection
            )
            command_responses.append(cmd_response)
        
        panel_settings_response = PanelSettingsResponse(
            visible_commands=panel_settings.visible_commands,
            hidden_commands=panel_settings.hidden_commands,
            button_size=panel_settings.button_size,
            show_tooltips=panel_settings.show_tooltips,
            compact_mode=panel_settings.compact_mode
        )
        
        return LoadConfigurationResponse(
            commands=command_responses,
            panel_settings=panel_settings_response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading panel configuration: {str(e)}")


@router.post("/reset", response_model=Dict[str, bool])
async def reset_panel_configuration(
    request: ResetConfigurationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Reset panel configuration to defaults.
    
    Requirements: 9.5
    """
    try:
        service = PanelConfigurationService(db)
        
        success = service.reset_panel_configuration(
            user_id=request.user_id,
            document_type=request.document_type,
            apply_to_all_table_parts=request.apply_to_all_table_parts
        )
        
        return {"success": success}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting panel configuration: {str(e)}")


@router.get("/summary", response_model=ConfigurationSummaryResponse)
async def get_panel_configuration_summary(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get panel configuration summary for a user.
    """
    try:
        service = PanelConfigurationService(db)
        
        summary = service.get_panel_configuration_summary(user_id)
        
        return ConfigurationSummaryResponse(
            total_configurations=summary['total_configurations'],
            document_types=summary['document_types'],
            last_modified=summary['last_modified']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting panel configuration summary: {str(e)}")


@router.post("/migrate", response_model=Dict[str, bool])
async def migrate_panel_settings(
    user_id: int,
    from_version: str,
    to_version: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Migrate panel settings between versions.
    """
    try:
        service = PanelConfigurationService(db)
        
        success = service.migrate_panel_settings(
            user_id=user_id,
            from_version=from_version,
            to_version=to_version
        )
        
        return {"success": success}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error migrating panel settings: {str(e)}")


@router.get("/defaults/{document_type}", response_model=LoadConfigurationResponse)
async def get_default_configuration(
    document_type: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get default panel configuration for a document type.
    """
    try:
        service = PanelConfigurationService(db)
        
        commands = service._get_default_commands(document_type)
        panel_settings = service._get_default_panel_settings(document_type)
        
        # Convert to response models
        command_responses = []
        for cmd in commands:
            cmd_response = CommandResponse(
                id=cmd.id,
                name=cmd.name,
                icon=cmd.icon,
                tooltip=cmd.tooltip,
                shortcut=cmd.shortcut,
                enabled=cmd.enabled,
                visible=cmd.visible,
                form_method=cmd.form_method,
                position=cmd.position,
                requires_selection=cmd.requires_selection
            )
            command_responses.append(cmd_response)
        
        panel_settings_response = PanelSettingsResponse(
            visible_commands=panel_settings.visible_commands,
            hidden_commands=panel_settings.hidden_commands,
            button_size=panel_settings.button_size,
            show_tooltips=panel_settings.show_tooltips,
            compact_mode=panel_settings.compact_mode
        )
        
        return LoadConfigurationResponse(
            commands=command_responses,
            panel_settings=panel_settings_response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting default configuration: {str(e)}")