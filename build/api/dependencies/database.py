"""
Database dependencies for FastAPI

Provides database session management through dependency injection.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Generator
from sqlalchemy.orm import Session
from src.data.database_manager import DatabaseManager
from src.data.exceptions import DatabaseConnectionError, DatabaseOperationError
from api.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize database manager as singleton
_db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """Get or initialize the database manager singleton
    
    Returns:
        DatabaseManager instance
        
    Raises:
        DatabaseConnectionError: If database initialization fails
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        
        # Try to initialize with config file first, fall back to legacy path
        try:
            # Check if config file exists
            if os.path.exists(settings.DATABASE_CONFIG_PATH):
                logger.info(f"Initializing database from config: {settings.DATABASE_CONFIG_PATH}")
                _db_manager.initialize(settings.DATABASE_CONFIG_PATH)
            else:
                # Fall back to legacy database path
                logger.info(f"Config file not found, using legacy database path: {settings.DATABASE_PATH}")
                _db_manager.initialize(settings.DATABASE_PATH)
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseConnectionError(f"Failed to initialize database: {e}")
    
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session
    
    Yields:
        SQLAlchemy Session instance
        
    Raises:
        DatabaseConnectionError: If database connection fails
        DatabaseOperationError: If session operations fail
        
    Example:
        @router.get("/items")
        async def list_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        yield session
        session.commit()
    except (HTTPException, RequestValidationError):
        # HTTPException and RequestValidationError are expected behavior (e.g., 401, 404, validation errors)
        # Don't rollback for these - they're application-level exceptions
        session.close()
        raise
    except Exception as e:
        # Actual errors - rollback the transaction
        session.rollback()
        logger.error(f"Database operation error, rolling back: {e}")
        session.close()
        raise DatabaseOperationError(f"Database operation failed: {e}")
    finally:
        # Ensure session is closed
        if session.is_active:
            session.close()


def get_db_connection():
    """FastAPI dependency to get legacy database connection (backward compatibility)
    
    Returns:
        SQLite connection object
        
    Raises:
        DatabaseConnectionError: If connection is not available
        
    Note:
        This is maintained for backward compatibility with existing endpoints
        that use raw SQL. New endpoints should use get_db() instead.
    """
    db_manager = get_db_manager()
    return db_manager.get_connection()
