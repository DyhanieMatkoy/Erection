"""Schema management for database migrations and initialization

This module provides functionality for:
- Automatic schema creation for empty databases
- Schema verification and updates for existing databases
- Alembic migration management
- Index creation across all backends
"""

import logging
from typing import Optional
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from .sqlalchemy_base import Base
from .exceptions import DatabaseOperationError

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema creation, verification, and migrations"""
    
    def __init__(self, engine: Engine):
        """Initialize schema manager
        
        Args:
            engine: SQLAlchemy engine instance
        """
        self.engine = engine
        self.alembic_cfg = self._get_alembic_config()
    
    def _get_alembic_config(self) -> Config:
        """Get Alembic configuration
        
        Returns:
            Alembic Config instance
        """
        # Get the path to alembic.ini
        alembic_ini_path = Path(__file__).parent.parent.parent / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise DatabaseOperationError(f"Alembic configuration not found: {alembic_ini_path}")
        
        cfg = Config(str(alembic_ini_path))
        
        # Override the sqlalchemy.url with our engine's URL
        cfg.set_main_option("sqlalchemy.url", str(self.engine.url))
        
        return cfg
    
    def is_database_empty(self) -> bool:
        """Check if database has no tables
        
        Returns:
            True if database is empty, False otherwise
        """
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        return len(tables) == 0
    
    def has_alembic_version_table(self) -> bool:
        """Check if alembic_version table exists
        
        Returns:
            True if alembic_version table exists, False otherwise
        """
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        return 'alembic_version' in tables
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database schema revision
        
        Returns:
            Current revision string, or None if no migrations applied
        """
        if not self.has_alembic_version_table():
            return None
        
        try:
            with self.engine.begin() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.warning(f"Failed to get current revision: {e}")
            return None
    
    def get_head_revision(self) -> str:
        """Get the latest available migration revision
        
        Returns:
            Head revision string
        """
        script = ScriptDirectory.from_config(self.alembic_cfg)
        return script.get_current_head()
    
    def needs_migration(self) -> bool:
        """Check if database needs migration
        
        Returns:
            True if migrations are pending, False otherwise
        """
        current = self.get_current_revision()
        head = self.get_head_revision()
        
        if current is None:
            # No migrations applied yet
            return not self.is_database_empty()
        
        return current != head
    
    def initialize_schema(self, use_alembic: bool = True) -> bool:
        """Initialize database schema
        
        This method will:
        1. Create all tables if database is empty
        2. Stamp with current revision if using Alembic
        3. Apply pending migrations if needed
        
        Args:
            use_alembic: Whether to use Alembic for schema management (default: True)
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.is_database_empty():
                logger.info("Database is empty, creating initial schema")
                self._create_initial_schema(use_alembic)
                return True
            
            if use_alembic and self.needs_migration():
                logger.info("Database needs migration, applying pending migrations")
                self.upgrade_schema()
                return True
            
            logger.info("Database schema is up to date")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise DatabaseOperationError(f"Schema initialization failed: {e}")
    
    def _create_initial_schema(self, use_alembic: bool = True):
        """Create initial database schema
        
        Args:
            use_alembic: Whether to stamp with Alembic version
        """
        # Import models to register them with Base
        from .models import sqlalchemy_models  # noqa: F401
        
        # Ensure foreign keys are enabled for SQLite
        self.ensure_foreign_keys_enabled()
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Created all database tables")
        
        # Create indices
        self._create_indices()
        logger.info("Created all database indices")
        
        # Stamp with current revision if using Alembic
        if use_alembic:
            try:
                # Manually create alembic_version table and insert version
                head_revision = self.get_head_revision()
                
                with self.engine.begin() as conn:
                    # Create alembic_version table
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        )
                    """))
                    
                    # Insert the head revision
                    conn.execute(
                        text("INSERT OR REPLACE INTO alembic_version (version_num) VALUES (:version)"),
                        {"version": head_revision}
                    )
                
                logger.info(f"Stamped database with Alembic revision: {head_revision}")
            except Exception as e:
                logger.warning(f"Failed to stamp database with Alembic: {e}")
    
    def _create_indices(self):
        """Create additional indices not defined in models
        
        Note: Most indices are defined in the SQLAlchemy models.
        This method is for any additional indices needed.
        """
        # Composite indices are defined in model __table_args__
        # Individual column indices are defined with index=True in Column definitions
        # This method is kept for any future custom indices
        pass
    
    def upgrade_schema(self, revision: str = "head") -> bool:
        """Upgrade database schema to specified revision
        
        Args:
            revision: Target revision (default: "head" for latest)
            
        Returns:
            True if upgrade successful, False otherwise
        """
        try:
            logger.info(f"Upgrading database schema to revision: {revision}")
            command.upgrade(self.alembic_cfg, revision)
            logger.info("Database schema upgraded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upgrade schema: {e}")
            raise DatabaseOperationError(f"Schema upgrade failed: {e}")
    
    def downgrade_schema(self, revision: str) -> bool:
        """Downgrade database schema to specified revision
        
        Args:
            revision: Target revision
            
        Returns:
            True if downgrade successful, False otherwise
        """
        try:
            logger.info(f"Downgrading database schema to revision: {revision}")
            command.downgrade(self.alembic_cfg, revision)
            logger.info("Database schema downgraded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to downgrade schema: {e}")
            raise DatabaseOperationError(f"Schema downgrade failed: {e}")
    
    def verify_schema(self) -> dict:
        """Verify database schema integrity
        
        Returns:
            Dictionary with verification results:
            {
                'valid': bool,
                'missing_tables': list,
                'extra_tables': list,
                'current_revision': str,
                'head_revision': str,
                'needs_migration': bool
            }
        """
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())
        
        # Import models to get expected tables
        from .models import sqlalchemy_models  # noqa: F401
        expected_tables = set(Base.metadata.tables.keys())
        
        missing_tables = expected_tables - existing_tables
        extra_tables = existing_tables - expected_tables - {'alembic_version'}
        
        current_rev = self.get_current_revision()
        head_rev = self.get_head_revision()
        
        result = {
            'valid': len(missing_tables) == 0 and not self.needs_migration(),
            'missing_tables': list(missing_tables),
            'extra_tables': list(extra_tables),
            'current_revision': current_rev,
            'head_revision': head_rev,
            'needs_migration': self.needs_migration()
        }
        
        return result
    
    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration script
        
        Args:
            message: Migration message/description
            autogenerate: Whether to auto-generate migration from model changes
            
        Returns:
            Path to generated migration file
        """
        try:
            logger.info(f"Creating new migration: {message}")
            
            if autogenerate:
                command.revision(
                    self.alembic_cfg,
                    message=message,
                    autogenerate=True
                )
            else:
                command.revision(
                    self.alembic_cfg,
                    message=message
                )
            
            logger.info("Migration created successfully")
            return "Migration created"
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise DatabaseOperationError(f"Migration creation failed: {e}")
    
    def get_migration_history(self) -> list:
        """Get migration history
        
        Returns:
            List of migration revisions
        """
        script = ScriptDirectory.from_config(self.alembic_cfg)
        revisions = []
        
        for revision in script.walk_revisions():
            revisions.append({
                'revision': revision.revision,
                'down_revision': revision.down_revision,
                'message': revision.doc,
                'is_current': revision.revision == self.get_current_revision()
            })
        
        return revisions
    
    def ensure_foreign_keys_enabled(self):
        """Ensure foreign key constraints are enabled (SQLite specific)
        
        For SQLite, foreign keys must be enabled per connection.
        This method sets up an event listener to enable them automatically.
        """
        if self.engine.dialect.name == 'sqlite':
            from sqlalchemy import event
            
            # Remove any existing listeners first
            try:
                event.remove(self.engine, "connect", self._enable_sqlite_fk)
            except:
                pass
            
            # Add event listener to enable foreign keys on each connection
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            
            logger.info("Configured foreign key constraints for SQLite")
    
    def _enable_sqlite_fk(self, dbapi_conn, connection_record):
        """Helper to enable SQLite foreign keys"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
