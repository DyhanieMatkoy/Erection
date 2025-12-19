from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class UserFormSettingsBase(BaseModel):
    form_id: str = Field(..., description="Unique identifier for the form")
    settings_type: str = Field(..., description="Type of settings (columns, filters, etc.)")
    settings_data: Dict[str, Any] = Field(..., description="JSON data for the settings")

class UserFormSettingsCreate(UserFormSettingsBase):
    pass

class UserFormSettingsUpdate(BaseModel):
    settings_data: Dict[str, Any] = Field(..., description="Updated JSON data")

class UserFormSettings(UserFormSettingsBase):
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FormCommandConfigurationBase(BaseModel):
    form_id: str
    command_id: str
    is_visible: bool = True
    is_enabled: bool = True
    position: Optional[int] = None
    is_in_more_menu: bool = False

class FormCommandConfigurationCreate(FormCommandConfigurationBase):
    pass

class FormCommandConfigurationUpdate(BaseModel):
    is_visible: Optional[bool] = None
    is_enabled: Optional[bool] = None
    position: Optional[int] = None
    is_in_more_menu: Optional[bool] = None

class FormCommandConfiguration(FormCommandConfigurationBase):
    id: str
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
