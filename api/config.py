"""
Configuration management for the API
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database - Support both legacy path and new config file
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "construction.db")
    DATABASE_CONFIG_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "env.ini")
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 8
    
    # CORS - Use string that will be parsed manually
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:8000,http://127.0.0.1:8000"
    
    # API
    API_PREFIX: str = "/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Parse CORS_ORIGINS from comma-separated string to list
if isinstance(settings.CORS_ORIGINS, str):
    settings.CORS_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS.split(',') if origin.strip()]
elif not isinstance(settings.CORS_ORIGINS, list):
    settings.CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"]
