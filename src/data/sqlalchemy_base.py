"""Base SQLAlchemy configuration module

This module provides the foundation for SQLAlchemy ORM support,
including the declarative base class and common utilities.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create declarative base for all ORM models
Base = declarative_base()


class SQLAlchemyConfig:
    """Configuration class for SQLAlchemy setup"""
    
    def __init__(self):
        self.engine: Optional[object] = None
        self.session_factory: Optional[sessionmaker] = None
    
    def create_engine_from_url(self, connection_url: str, **kwargs) -> object:
        """Create SQLAlchemy engine from connection URL
        
        Args:
            connection_url: Database connection URL
            **kwargs: Additional engine configuration options
            
        Returns:
            SQLAlchemy Engine instance
        """
        # Default engine options
        engine_options = {
            'echo': False,  # Set to True for SQL query logging
            'future': True,  # Use SQLAlchemy 2.0 style
        }
        
        # Merge with provided options
        engine_options.update(kwargs)
        
        # Create engine
        engine = create_engine(connection_url, **engine_options)
        
        # Enable foreign key support for SQLite
        if connection_url.startswith('sqlite'):
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        self.engine = engine
        logger.info(f"Created SQLAlchemy engine for: {connection_url.split('@')[-1]}")
        
        return engine
    
    def create_session_factory(self, engine: object = None) -> sessionmaker:
        """Create session factory for database sessions
        
        Args:
            engine: SQLAlchemy engine (uses self.engine if not provided)
            
        Returns:
            sessionmaker instance
        """
        if engine is None:
            engine = self.engine
        
        if engine is None:
            raise ValueError("Engine must be provided or created first")
        
        self.session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            future=True
        )
        
        logger.info("Created SQLAlchemy session factory")
        return self.session_factory
    
    def get_session(self) -> Session:
        """Get a new database session
        
        Returns:
            SQLAlchemy Session instance
        """
        if self.session_factory is None:
            raise ValueError("Session factory not initialized. Call create_session_factory first.")
        
        return self.session_factory()
    
    def create_all_tables(self, engine: object = None):
        """Create all tables defined in Base metadata
        
        Args:
            engine: SQLAlchemy engine (uses self.engine if not provided)
        """
        if engine is None:
            engine = self.engine
        
        if engine is None:
            raise ValueError("Engine must be provided or created first")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Created all database tables")
    
    def drop_all_tables(self, engine: object = None):
        """Drop all tables defined in Base metadata
        
        WARNING: This will delete all data!
        
        Args:
            engine: SQLAlchemy engine (uses self.engine if not provided)
        """
        if engine is None:
            engine = self.engine
        
        if engine is None:
            raise ValueError("Engine must be provided or created first")
        
        Base.metadata.drop_all(bind=engine)
        logger.warning("Dropped all database tables")


# Global SQLAlchemy configuration instance
sqlalchemy_config = SQLAlchemyConfig()


def get_sqlalchemy_config() -> SQLAlchemyConfig:
    """Get the global SQLAlchemy configuration instance
    
    Returns:
        SQLAlchemyConfig instance
    """
    return sqlalchemy_config
