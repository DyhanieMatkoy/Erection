"""
FastAPI endpoints for work selector settings management.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..dependencies.database import get_db
from ..dependencies.auth import get_current_user
from src.services.user_settings_service import UserSettingsService
from src.data.models.sqlalchemy_models import User

router = APIRouter(prefix="/work-selector-settings", tags=["work-selector-settings"])


class WorkSelectorSettingsModel(BaseModel):
    open_modal: bool = True
    default_hierarchy_mode: str = "tree"
    show_hierarchy_controls: bool = True
    auto_expand_groups: bool = True


@router.get("/{user_id}")
async def get_work_selector_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get work selector settings for a user"""
    try:
        settings_service = UserSettingsService()
        settings = settings_service.get_work_selector_settings(user_id)
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}")
async def update_work_selector_settings(
    user_id: int,
    settings: WorkSelectorSettingsModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update work selector settings for a user"""
    try:
        settings_service = UserSettingsService()
        success = settings_service.set_work_selector_settings(
            user_id, 
            settings.dict()
        )
        
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))