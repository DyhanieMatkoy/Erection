"""
Authentication models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class UserInfo(BaseModel):
    """User information model"""
    id: int
    username: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserInfo


class TokenData(BaseModel):
    """Token payload data"""
    sub: int  # user_id
    username: str
    role: str
    exp: datetime
    iat: datetime
