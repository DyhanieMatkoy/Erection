"""Base model class"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BaseModel:
    id: int = 0
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
