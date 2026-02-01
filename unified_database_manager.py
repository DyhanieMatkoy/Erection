#!/usr/bin/env python3
"""Unified Database Manager

This module provides a unified database manager that combines the best features
of both Legacy Database Manager and Universal Database Manager.

Features:
- Multi-database support (SQLite, PostgreSQL, MySQL)
- Consistent schema across all database types
- Backward compatibility with existing code
- Docker integration for external databases
- SQL dialect translation
- Proper sync tables for synchronization system
"""

import os
import sys
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Universal Database Manager components
try:
    from sql_dialect_translator import SQLDialectTranslator, SQLDialect
    from docker_database_manager import DockerDatabaseManager
    SQL_TRANSLATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SQL translator not available: {e}")
    SQL_TRANSLATOR_AVAILABLE = False
    SQLDialectTranslator = None
    SQLDialect = None
    DockerDatabaseManager = None

# Import Legacy Database Manager components
try:
    from src.data.database_config import DatabaseConfig
    from src.data.connection_string_builder import ConnectionStringBuilder
    from src.data.exceptions import DatabaseConnectionError, DatabaseConfigurationError, DatabaseOperationError
    from src.data.sqlalchemy_base import Base
    LEGACY_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Legacy components not available: {e}")
    LEGACY_COMPONENTS_AVAILABLE = False
    DatabaseConfig = None
    ConnectionStringBuilder = None
    DatabaseConnectionError = Exception
    DatabaseConfigurationError = Exception
    DatabaseOperationError = Exception
    Base = None


class UnifiedDatabaseManager:
    """Unified database manager combining Legacy and Universal features"""
    
    _instance: Optional['UnifiedDatabaseManager'] = None
    
    def __init__(self, logger: Optional[logging.Logger] = None, use_docker: bool = True):
        """Initialize unified database manager
        
        Args:
            logger: Optional logger instance
            use_docker: Whether to use Docker for external databases
        """
        self.logger = logger or logging.getLogger(__name__)
        self.use_docker = use_docker
        
        # SQLAlchemy components
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
        # Legacy SQLite connection for backward compatibility
        self._connection: Optional[sqlite3.Connection] = None
        
        # Configuration
        self._config: Optional[DatabaseConfig] = None
        
        # Multi-database components
        self.translator: Optional[SQLDialectTranslator] = None
        self.docker_manager: Optional[DockerDatabaseManager] = None
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("Unified database manager initialized")
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for backward compatibility"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _initialize_components(self):
        """Initialize multi-database components"""
        # Initialize SQL translator
        if SQL_TRANSLATOR_AVAILABLE:
            try:
                self.translator = SQLDialectTranslator(self.logger)
                self.logger.debug("SQL translator initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SQL translator: {e}")
                self.translator = None
        
        # Initialize Docker manager
        if self.use_docker and DockerDatabaseManager:
            try:
                self.docker_manager = DockerDatabaseManager(self.logger)
                docker_available, error = self.docker_manager.check_docker_availability()
                if not docker_available:
                    self.logger.warning(f"Docker not available: {error}")
                    self.use_docker = False
                    self.docker_manager = None
            except Exception as e:
                self.logger.warning(f"Failed to initialize Docker manager: {e}")
                self.use_docker = False
                self.docker_manager = None
    
    def initialize(self, config_path: str = "env.ini") -> bool:
        """Initialize database from configuration or path
        
        Args:
            config_path: Path to configuration file or direct database path
                        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if config_path is actually a database file path (backward compatibility)
            if config_path.endswith('.db') or config_path.endswith('.sqlite'):
                self.logger.info(f"Legacy initialization with database path: {config_path}")
                return self._initialize_sqlite_legacy(config_path)
            
            # Try to load configuration if legacy components are available
            if LEGACY_COMPONENTS_AVAILABLE:
                try:
                    self._config = DatabaseConfig(config_path)
                    return self._initialize_with_config()
                except Exception as e:
                    self.logger.warning(f"Failed to load configuration: {e}")
            
            # Fallback to SQLite with default path
            self.logger.warning("Falling back to SQLite with default configuration")
            return self._initialize_sqlite_legacy("construction.db")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
    
    def initialize_with_connection_string(self, connection_string: str) -> bool:
        """Initialize database with a direct connection string
        
        Args:
            connection_string: Database connection string
            
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info(f"Initializing with connection string: {connection_string[:50]}...")
            
            # Determine database type from connection string
            if connection_string.startswith('sqlite:'):
                db_type = 'sqlite'
                dialect = SQLDialect.SQLITE if SQL_TRANSLATOR_AVAILABLE else None
            elif connection_string.startswith('postgresql:'):
                db_type = 'postgresql'
                dialect = SQLDialect.POSTGRESQL if SQL_TRANSLATOR_AVAILABLE else None
            elif connection_string.startswith('mysql:') or connection_string.startswith('mysql+'):
                db_type = 'mysql'
                dialect = SQLDialect.MYSQL if SQL_TRANSLATOR_AVAILABLE else None
            elif connection_string.startswith('mssql:') or connection_string.startswith('mssql+'):
                db_type = 'mssql'
                dialect = SQLDialect.MSSQL if SQL_TRANSLATOR_AVAILABLE else None
            else:
                raise Exception(f"Unsupported database type in connection string: {connection_string[:50]}")
            
            # Create engine
            engine_kwargs = self._get_engine_kwargs_for_type(db_type)
            self._engine = create_engine(connection_string, **engine_kwargs)
            
            # Enable foreign key support for SQLite
            if db_type == 'sqlite':
                @event.listens_for(self._engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Create tables
            self._create_tables_unified(dialect)
            
            # For SQLite, maintain backward compatibility connection
            if db_type == 'sqlite':
                db_path = connection_string.replace('sqlite:///', '').replace('sqlite://', '')
                self._connection = sqlite3.connect(db_path, check_same_thread=False)
                self._connection.row_factory = sqlite3.Row
            
            self.logger.info(f"Database initialized successfully: {db_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize with connection string: {e}")
            return False
    
    def _initialize_with_config(self) -> bool:
        """Initialize database using configuration"""
        try:
            # Validate configuration
            if not self._config.validate():
                raise Exception(f"Invalid database configuration")
            
            # Build connection string
            connection_string = ConnectionStringBuilder.build_from_config(
                self._config.get_db_type(),
                self._config.get_config_data()
            )
            
            return self.initialize_with_connection_string(connection_string)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize with config: {e}")
            return False
    
    def _initialize_sqlite_legacy(self, db_path: str) -> bool:
        """Initialize SQLite database (legacy compatibility)
        
        Args:
            db_path: Path to SQLite database file
            
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info(f"Initializing SQLite database: {db_path}")
            
            # Create SQLite connection for backward compatibility with improved settings
            self._connection = sqlite3.connect(
                db_path, 
                check_same_thread=False,
                timeout=30.0,  # 30 second timeout for database locks
                isolation_level=None  # Autocommit mode to reduce lock contention
            )
            self._connection.row_factory = sqlite3.Row
            
            # Set SQLite pragmas for better concurrency
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
            cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
            cursor.execute("PRAGMA cache_size=10000")  # Larger cache for better performance
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
            cursor.close()
            
            # Create SQLAlchemy engine with improved settings
            connection_string = f"sqlite:///{db_path}"
            self._engine = create_engine(
                connection_string, 
                poolclass=NullPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30,  # 30 second timeout
                }
            )
            
            # Enable foreign key support and WAL mode for SQLAlchemy connections
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
            
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Create tables using unified method
            dialect = SQLDialect.SQLITE if SQL_TRANSLATOR_AVAILABLE else None
            self._create_tables_unified(dialect)
            
            # Create initial data
            self._create_initial_data_sqlite(db_path)
            
            self.logger.info(f"SQLite database initialized successfully: {db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite database: {e}")
            return False
    
    # def _create_tables_unified(self, dialect: Optional['SQLDialect'] = None):
    #     """Create all database tables using unified schema
        
    #     Args:
    #         dialect: SQL dialect for translation (optional)
    #     """
    #     try:
    #         # For testing, use simplified initialization
    #         if hasattr(self, '_test_mode') and self._test_mode:
    #             from simple_database_initializer import SimpleDatabaseInitializer
    #             initializer = SimpleDatabaseInitializer(self.logger)
                
    #             # Get connection string from engine
    #             connection_string = str(self._engine.url)
                
    #             if initializer.initialize_test_database(connection_string):
    #                 self.logger.info("Tables created using simplified test initializer")
    #                 return
    #             else:
    #                 self.logger.warning("Simplified initializer failed, falling back to SQLAlchemy")
            
    #         # Use SQLAlchemy if available and models are imported
    #         if Base is not None:
    #             try:
    #                 # Try to import models
    #                 from src.data.models import sqlalchemy_models  # noqa: F401
    #                 Base.metadata.create_all(bind=self._engine)
    #                 self.logger.info("Tables created using SQLAlchemy models")
    #                 return
    #             except ImportError:
    #                 self.logger.debug("SQLAlchemy models not available, using SQL statements")
            
    #         # Fallback to SQL statements
    #         self._create_tables_sql(dialect)
            
    #     except Exception as e:
    #         self.logger.error(f"Failed to create tables: {e}")
    #         raise
    def _create_tables_unified(self, dialect: Optional['SQLDialect'] = None):
        """Create all database tables using unified schema"""
        try:
            # Всегда использовать SQLAlchemy модели
            if Base is not None:
                try:
                    # Импортировать модели чтобы они зарегистрировались у Base
                    from src.data.models import sqlalchemy_models  # noqa: F401
                    
                    # Создать все таблицы из моделей
                    Base.metadata.create_all(bind=self._engine)
                    self.logger.info("Tables created using SQLAlchemy models")
                    
                    # Добавить индексы и специфичные настройки
                    self._create_missing_indices_and_constraints()
                    return
                except ImportError as e:
                    self.logger.error(f"Cannot import SQLAlchemy models: {e}")
                    raise
            
            # Fallback если модели недоступны
            self._create_tables_sql(dialect)
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise

    def _create_missing_indices_and_constraints(self):
        """Create indices and constraints not defined in SQLAlchemy models"""
        index_definitions = [
            # Синхронизационные индексы
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid)",
        ]
        
        if self._engine:
            with self._engine.connect() as conn:
                for index_sql in index_definitions:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        self.logger.warning(f"Failed to create index: {e}")
                conn.commit()
    
    def enable_test_mode(self):
        """Enable test mode for simplified table creation"""
        self._test_mode = True
        self.logger.debug("Test mode enabled - will use simplified table creation")
    
    # def _create_tables_sql(self, dialect: Optional['SQLDialect'] = None):
    #     """Create tables using SQL statements"""
        
    #     # Unified table definitions (combining Legacy + Universal schemas)
    #     # ALL TABLES NOW INCLUDE: uuid, updated_at, is_deleted fields for synchronization
    #     table_definitions = [
    #         # Audit Logs
    #         """CREATE TABLE IF NOT EXISTS audit_logs (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             user_id INTEGER,
    #             username TEXT,
    #             action TEXT,
    #             resource_type TEXT,
    #             resource_id INTEGER,
    #             details TEXT,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Users
    #         """CREATE TABLE IF NOT EXISTS users (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             username TEXT UNIQUE NOT NULL,
    #             password_hash TEXT NOT NULL,
    #             role TEXT NOT NULL,
    #             is_active INTEGER DEFAULT 1,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Persons - UNIFIED: Use full_name (not name) + ALL sync fields
    #         """CREATE TABLE IF NOT EXISTS persons (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             full_name TEXT NOT NULL,
    #             position TEXT,
    #             phone TEXT,
    #             user_id INTEGER REFERENCES users(id),
    #             parent_id INTEGER REFERENCES persons(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             is_group INTEGER DEFAULT 0,
    #             hourly_rate REAL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Organizations
    #         """CREATE TABLE IF NOT EXISTS organizations (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             name TEXT NOT NULL,
    #             inn TEXT,
    #             default_responsible_id INTEGER REFERENCES persons(id),
    #             parent_id INTEGER REFERENCES organizations(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             is_group INTEGER DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Counterparties
    #         """CREATE TABLE IF NOT EXISTS counterparties (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             name TEXT NOT NULL,
    #             inn TEXT,
    #             contact_person TEXT,
    #             phone TEXT,
    #             parent_id INTEGER REFERENCES counterparties(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             is_group INTEGER DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Objects
    #         """CREATE TABLE IF NOT EXISTS objects (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             name TEXT NOT NULL,
    #             owner_id INTEGER REFERENCES counterparties(id),
    #             address TEXT,
    #             parent_id INTEGER REFERENCES objects(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             is_group INTEGER DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Works
    #         """CREATE TABLE IF NOT EXISTS works (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             name TEXT NOT NULL,
    #             code TEXT,
    #             unit TEXT,
    #             unit_id INTEGER REFERENCES units(id),
    #             price REAL,
    #             labor_rate REAL,
    #             parent_id INTEGER REFERENCES works(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             is_group INTEGER DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Estimates
    #         """CREATE TABLE IF NOT EXISTS estimates (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE,
    #             number TEXT NOT NULL,
    #             date DATE NOT NULL,
    #             customer_id INTEGER REFERENCES counterparties(id),
    #             object_id INTEGER REFERENCES objects(id),
    #             contractor_id INTEGER REFERENCES organizations(id),
    #             responsible_id INTEGER REFERENCES persons(id),
    #             total_sum REAL DEFAULT 0,
    #             total_labor REAL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_posted INTEGER DEFAULT 0,
    #             posted_at TIMESTAMP,
    #             marked_for_deletion INTEGER DEFAULT 0,
    #             estimate_type TEXT NOT NULL DEFAULT 'General',
    #             base_document_id INTEGER REFERENCES estimates(id),
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Estimate Lines
    #         """CREATE TABLE IF NOT EXISTS estimate_lines (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
    #             line_number INTEGER,
    #             work_id INTEGER REFERENCES works(id),
    #             quantity REAL,
    #             unit TEXT,
    #             price REAL,
    #             labor_rate REAL,
    #             sum REAL,
    #             planned_labor REAL,
    #             is_group INTEGER DEFAULT 0,
    #             group_name TEXT,
    #             parent_group_id INTEGER REFERENCES estimate_lines(id),
    #             is_collapsed INTEGER DEFAULT 0,
    #             material_id INTEGER REFERENCES materials(id),
    #             material_quantity REAL DEFAULT 0,
    #             material_price REAL DEFAULT 0,
    #             material_sum REAL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Daily Reports
    #         """CREATE TABLE IF NOT EXISTS daily_reports (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             date DATE NOT NULL,
    #             estimate_id INTEGER REFERENCES estimates(id),
    #             foreman_id INTEGER REFERENCES persons(id),
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_posted INTEGER DEFAULT 0,
    #             posted_at TIMESTAMP,
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             number TEXT,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Daily Report Lines
    #         """CREATE TABLE IF NOT EXISTS daily_report_lines (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
    #             line_number INTEGER,
    #             work_id INTEGER REFERENCES works(id),
    #             planned_labor REAL,
    #             actual_labor REAL,
    #             labor_deviation_percent REAL,
    #             is_group INTEGER DEFAULT 0,
    #             group_name TEXT,
    #             parent_group_id INTEGER REFERENCES daily_report_lines(id),
    #             is_collapsed INTEGER DEFAULT 0,
    #             material_id INTEGER REFERENCES materials(id),
    #             planned_material_quantity REAL DEFAULT 0,
    #             actual_material_quantity REAL DEFAULT 0,
    #             material_deviation_percent REAL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Daily Report Executors
    #         """CREATE TABLE IF NOT EXISTS daily_report_executors (
    #             report_line_id INTEGER REFERENCES daily_report_lines(id) ON DELETE CASCADE,
    #             executor_id INTEGER REFERENCES persons(id),
    #             PRIMARY KEY (report_line_id, executor_id)
    #         )""",
            
    #         # Timesheets
    #         """CREATE TABLE IF NOT EXISTS timesheets (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             number TEXT NOT NULL,
    #             date DATE NOT NULL,
    #             object_id INTEGER REFERENCES objects(id),
    #             estimate_id INTEGER REFERENCES estimates(id),
    #             foreman_id INTEGER REFERENCES persons(id),
    #             month_year TEXT NOT NULL,
    #             is_posted INTEGER DEFAULT 0,
    #             posted_at TIMESTAMP,
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Timesheet Lines
    #         """CREATE TABLE IF NOT EXISTS timesheet_lines (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             timesheet_id INTEGER REFERENCES timesheets(id) ON DELETE CASCADE,
    #             line_number INTEGER,
    #             employee_id INTEGER REFERENCES persons(id),
    #             hourly_rate REAL DEFAULT 0,
    #             day_01 REAL DEFAULT 0,
    #             day_02 REAL DEFAULT 0,
    #             day_03 REAL DEFAULT 0,
    #             day_04 REAL DEFAULT 0,
    #             day_05 REAL DEFAULT 0,
    #             day_06 REAL DEFAULT 0,
    #             day_07 REAL DEFAULT 0,
    #             day_08 REAL DEFAULT 0,
    #             day_09 REAL DEFAULT 0,
    #             day_10 REAL DEFAULT 0,
    #             day_11 REAL DEFAULT 0,
    #             day_12 REAL DEFAULT 0,
    #             day_13 REAL DEFAULT 0,
    #             day_14 REAL DEFAULT 0,
    #             day_15 REAL DEFAULT 0,
    #             day_16 REAL DEFAULT 0,
    #             day_17 REAL DEFAULT 0,
    #             day_18 REAL DEFAULT 0,
    #             day_19 REAL DEFAULT 0,
    #             day_20 REAL DEFAULT 0,
    #             day_21 REAL DEFAULT 0,
    #             day_22 REAL DEFAULT 0,
    #             day_23 REAL DEFAULT 0,
    #             day_24 REAL DEFAULT 0,
    #             day_25 REAL DEFAULT 0,
    #             day_26 REAL DEFAULT 0,
    #             day_27 REAL DEFAULT 0,
    #             day_28 REAL DEFAULT 0,
    #             day_29 REAL DEFAULT 0,
    #             day_30 REAL DEFAULT 0,
    #             day_31 REAL DEFAULT 0,
    #             total_hours REAL DEFAULT 0,
    #             total_amount REAL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Work Execution Register
    #         """CREATE TABLE IF NOT EXISTS work_execution_register (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             recorder_type TEXT NOT NULL,
    #             recorder_id INTEGER NOT NULL,
    #             line_number INTEGER NOT NULL,
    #             period DATE NOT NULL,
    #             object_id INTEGER REFERENCES objects(id),
    #             estimate_id INTEGER REFERENCES estimates(id),
    #             work_id INTEGER REFERENCES works(id),
    #             quantity_income REAL DEFAULT 0,
    #             quantity_expense REAL DEFAULT 0,
    #             sum_income REAL DEFAULT 0,
    #             sum_expense REAL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Payroll Register
    #         """CREATE TABLE IF NOT EXISTS payroll_register (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             recorder_type TEXT NOT NULL,
    #             recorder_id INTEGER NOT NULL,
    #             line_number INTEGER NOT NULL,
    #             period DATE NOT NULL,
    #             object_id INTEGER REFERENCES objects(id),
    #             estimate_id INTEGER REFERENCES estimates(id),
    #             employee_id INTEGER REFERENCES persons(id),
    #             work_date DATE NOT NULL,
    #             hours_worked REAL DEFAULT 0,
    #             amount REAL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0,
    #             UNIQUE(object_id, estimate_id, employee_id, work_date)
    #         )""",
            
    #         # User Settings
    #         """CREATE TABLE IF NOT EXISTS user_settings (
    #             user_id INTEGER REFERENCES users(id),
    #             form_name TEXT,
    #             setting_key TEXT,
    #             setting_value TEXT,
    #             PRIMARY KEY (user_id, form_name, setting_key)
    #         )""",
            
    #         # User Table Part Settings
    #         """CREATE TABLE IF NOT EXISTS user_table_part_settings (
    #             id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             user_id INTEGER REFERENCES users(id) NOT NULL,
    #             document_type TEXT NOT NULL,
    #             table_part_id TEXT NOT NULL,
    #             settings_data TEXT NOT NULL,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             UNIQUE(user_id, document_type, table_part_id)
    #         )""",
            
    #         # Table Part Command Config
    #         """CREATE TABLE IF NOT EXISTS table_part_command_config (
    #             id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             document_type TEXT NOT NULL,
    #             table_part_id TEXT NOT NULL,
    #             user_id INTEGER REFERENCES users(id),
    #             command_id TEXT NOT NULL,
    #             is_visible INTEGER DEFAULT 1,
    #             is_enabled INTEGER DEFAULT 1,
    #             position INTEGER DEFAULT 0,
    #             is_in_more_menu INTEGER DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             UNIQUE(document_type, table_part_id, user_id, command_id)
    #         )""",
            
    #         # Constants
    #         """CREATE TABLE IF NOT EXISTS constants (
    #             key TEXT PRIMARY KEY,
    #             value TEXT
    #         )""",
            
    #         # Materials
    #         """CREATE TABLE IF NOT EXISTS materials (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             code TEXT,
    #             description TEXT,
    #             price REAL DEFAULT 0,
    #             unit TEXT,
    #             unit_id INTEGER REFERENCES units(id),
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Units
    #         """CREATE TABLE IF NOT EXISTS units (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             name TEXT NOT NULL UNIQUE,
    #             description TEXT,
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Cost Items
    #         """CREATE TABLE IF NOT EXISTS cost_items (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             parent_id INTEGER REFERENCES cost_items(id),
    #             code TEXT,
    #             description TEXT,
    #             is_folder INTEGER DEFAULT 0,
    #             price REAL DEFAULT 0,
    #             unit TEXT,
    #             unit_id INTEGER REFERENCES units(id),
    #             labor_coefficient REAL DEFAULT 0,
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Cost Item Materials
    #         """CREATE TABLE IF NOT EXISTS cost_item_materials (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             work_id INTEGER REFERENCES works(id) ON DELETE CASCADE NOT NULL,
    #             cost_item_id INTEGER REFERENCES cost_items(id) ON DELETE CASCADE NOT NULL,
    #             material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
    #             quantity_per_unit REAL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0,
    #             UNIQUE(work_id, cost_item_id, material_id)
    #         )""",
            
    #         # Work Specifications
    #         """CREATE TABLE IF NOT EXISTS work_specifications (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))),
    #             work_id INTEGER REFERENCES works(id) ON DELETE CASCADE NOT NULL,
    #             component_type TEXT NOT NULL,
    #             component_name TEXT NOT NULL,
    #             unit_id INTEGER REFERENCES units(id),
    #             material_id INTEGER REFERENCES materials(id),
    #             consumption_rate REAL NOT NULL DEFAULT 0,
    #             unit_price REAL NOT NULL DEFAULT 0,
    #             total_cost REAL DEFAULT 0,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             marked_for_deletion INTEGER NOT NULL DEFAULT 0,
    #             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #             is_deleted INTEGER NOT NULL DEFAULT 0
    #         )""",
            
    #         # Work Unit Migration
    #         """CREATE TABLE IF NOT EXISTS work_unit_migration (
    #             work_id INTEGER REFERENCES works(id) PRIMARY KEY,
    #             legacy_unit TEXT,
    #             matched_unit_id INTEGER REFERENCES units(id),
    #             migration_status TEXT NOT NULL DEFAULT 'pending',
    #             confidence_score REAL DEFAULT 0,
    #             manual_review_reason TEXT,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #         )""",
            
    #         # SYNC TABLES - UNIFIED SCHEMA (matching Universal Database Manager)
    #         """CREATE TABLE IF NOT EXISTS sync_nodes (
    #             id TEXT PRIMARY KEY,
    #             code TEXT UNIQUE NOT NULL,
    #             name TEXT NOT NULL,
    #             last_sync_in TIMESTAMP,
    #             last_sync_out TIMESTAMP,
    #             received_packet_no INTEGER,
    #             sent_packet_no INTEGER,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #         )""",
            
    #         """CREATE TABLE IF NOT EXISTS sync_changes (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             node_id TEXT NOT NULL REFERENCES sync_nodes(id),
    #             entity_type TEXT NOT NULL,
    #             entity_uuid TEXT NOT NULL,
    #             operation TEXT NOT NULL,
    #             packet_no INTEGER,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             processed_at TIMESTAMP,
    #             error_message TEXT
    #         )""",
            
    #         """CREATE TABLE IF NOT EXISTS object_version_history (
    #             id TEXT PRIMARY KEY,
    #             entity_uuid TEXT NOT NULL,
    #             entity_type TEXT NOT NULL,
    #             source_node_id TEXT NOT NULL REFERENCES sync_nodes(id),
    #             arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             serialized_data TEXT NOT NULL,
    #             conflict_resolution TEXT,
    #             resolved_at TIMESTAMP,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #         )"""
    #     ]
        
    #     # Create tables
    #     if self._engine:
    #         # Use SQLAlchemy engine
    #         with self._engine.connect() as conn:
    #             for table_sql in table_definitions:
    #                 try:
    #                     # Translate SQL if needed
    #                     if self.translator and dialect:
    #                         translated_sql = self.translator.translate_sql(table_sql, 'any', dialect)
    #                     else:
    #                         translated_sql = table_sql
                        
    #                     conn.execute(text(translated_sql))
    #                 except Exception as e:
    #                     self.logger.error(f"Failed to create table: {e}")
    #                     raise
                
    #             conn.commit()
        
    #     elif self._connection:
    #         # Use SQLite connection
    #         cursor = self._connection.cursor()
    #         for table_sql in table_definitions:
    #             try:
    #                 cursor.execute(table_sql)
    #             except Exception as e:
    #                 self.logger.error(f"Failed to create table: {e}")
    #                 raise
            
    #         self._connection.commit()
        
    #     else:
    #         raise Exception("No database connection available")
        
    #     # Create indices
    #     self._create_indices_unified()
        
    #     self.logger.info("Unified database tables created successfully")
    
    def _create_indices_unified(self):
        """Create database indices"""
        
        index_definitions = [
            # Business table indices
            "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",
            "CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_foreman ON timesheets(foreman_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_object ON timesheets(object_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_estimate ON timesheets(estimate_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_timesheet ON timesheet_lines(timesheet_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_employee ON timesheet_lines(employee_id)",
            
            # Sync table indices - CRITICAL for performance
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_sync_changes_node_operation ON sync_changes(node_id, operation)",
            "CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_object_version_conflict ON object_version_history(entity_type, entity_uuid, resolved_at)"
        ]
        
        # Create indices
        if self._engine:
            with self._engine.connect() as conn:
                for index_sql in index_definitions:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        self.logger.warning(f"Failed to create index: {e}")
                conn.commit()
        
        elif self._connection:
            cursor = self._connection.cursor()
            for index_sql in index_definitions:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    self.logger.warning(f"Failed to create index: {e}")
            self._connection.commit()
        
        self.logger.info("Database indices created successfully")
    
    # def _create_initial_data_sqlite(self, db_path: str):
    #     """Create initial data for SQLite database"""
    #     try:
    #         # Import and use existing initial data logic
    #         if LEGACY_COMPONENTS_AVAILABLE:
    #             from src.data.initial_data import ensure_admin_user_exists
    #             ensure_admin_user_exists(db_path)
    #         else:
    #             self.logger.warning("Legacy initial data not available")
    #     except Exception as e:
    #         self.logger.error(f"Failed to create initial data: {e}")


    # def _create_initial_data_sqlite(self, db_path: str):
    #     """Create initial data for SQLite database"""
    #     try:
    #         # Использовать SQLAlchemy сессию для создания пользователя
    #         Session = sessionmaker(bind=self._engine)
    #         session = Session()
            
    #         try:
    #             from src.data.initial_data import ensure_admin_user_exists
    #             ensure_admin_user_exists(session, db_path)
    #         except ImportError:
    #             # Fallback если initial_data недоступен
    #             self._create_admin_user_fallback(session)
    #         finally:
    #             session.close()
                
    #     except Exception as e:
    #         self.logger.error(f"Failed to create initial data: {e}")


    def _create_initial_data_sqlite(self, db_path: str):
        """Create initial data for SQLite database"""
        try:
            # Уберите второй аргумент или измените вызов
            from src.data.initial_data import ensure_admin_user_exists
            
            # Версия 1: с одним аргументом (если функция принимает только db_path)
            success = ensure_admin_user_exists(db_path)
            
            # ИЛИ версия 2: если функция изменилась и принимает session
            # Session = sessionmaker(bind=self._engine)
            # session = Session()
            # success = ensure_admin_user_exists(session)
            # session.close()
            
            if not success:
                self.logger.error("Failed to create admin user")
                
        except ImportError as e:
            self.logger.error(f"Cannot import initial_data: {e}")
            # Создать пользователя напрямую
            self._create_admin_user_directly(db_path)
        except Exception as e:
            self.logger.error(f"Failed to create initial data: {e}")
            
    def _create_admin_user_fallback(self, session: Session):
        """Fallback method to create admin user"""
        try:
            from src.data.models.sqlalchemy_models import User
            import hashlib
            
            # Проверить существование
            admin_exists = session.query(User).filter_by(username='admin').first()
            if admin_exists:
                return
            
            # Создать пользователя
            password_hash = hashlib.sha256('admin'.encode()).hexdigest()
            admin_user = User(
                username='admin',
                password_hash=password_hash,
                role='admin',
                is_active=True
            )
            
            session.add(admin_user)
            session.commit()
            self.logger.info("Admin user created successfully")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to create admin user: {e}")
            raise
    
    def _get_engine_kwargs_for_type(self, db_type: str) -> dict:
        """Get engine configuration based on database type"""
        kwargs = {'echo': False}
        
        if db_type == 'sqlite':
            kwargs['poolclass'] = NullPool
            kwargs['connect_args'] = {'check_same_thread': False, 'timeout': 30}
        elif db_type == 'postgresql':
            kwargs['poolclass'] = QueuePool
            kwargs['pool_size'] = 10
            kwargs['max_overflow'] = 20
            kwargs['pool_timeout'] = 60
            kwargs['pool_recycle'] = 3600
            kwargs['pool_pre_ping'] = True
            kwargs['connect_args'] = {
                'connect_timeout': 60,
                'server_side_cursors': False
            }
        elif db_type == 'mysql':
            kwargs['poolclass'] = QueuePool
            kwargs['pool_size'] = 15
            kwargs['max_overflow'] = 25
            kwargs['pool_timeout'] = 120
            kwargs['pool_recycle'] = 1800  # Recycle connections every 30 minutes
            kwargs['pool_pre_ping'] = True
            kwargs['connect_args'] = {
                'connect_timeout': 60,
                'read_timeout': 600,
                'write_timeout': 600,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False,
                'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
            }
        elif db_type == 'mssql':
            kwargs['poolclass'] = QueuePool
            kwargs['pool_size'] = 5
            kwargs['max_overflow'] = 10
            kwargs['pool_timeout'] = 30
            kwargs['pool_recycle'] = 3600
            kwargs['pool_pre_ping'] = True
        
        return kwargs
    
    # Backward compatibility methods from Legacy Database Manager
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        if self._engine is None:
            raise Exception("Database engine not initialized")
        return self._engine
    
    def get_session(self) -> Session:
        """Get SQLAlchemy session"""
        if self._session_factory is None:
            raise Exception("Session factory not initialized")
        return self._session_factory()
    
    @contextmanager
    def session_scope(self):
        """Provide transactional scope for database operations with retry logic"""
        session = None
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                session = self.get_session()
                yield session
                session.commit()
                self.logger.debug("Transaction committed successfully")
                break
            except Exception as e:
                if session:
                    try:
                        session.rollback()
                    except Exception as rollback_error:
                        self.logger.warning(f"Rollback failed: {rollback_error}")
                    finally:
                        try:
                            session.close()
                        except Exception as close_error:
                            self.logger.warning(f"Session close failed: {close_error}")
                        session = None
                
                # Check if it's a retryable error
                error_str = str(e).lower()
                retryable_errors = [
                    "database is locked",
                    "database disk image is malformed", 
                    "lost connection to mysql server",
                    "mysql server has gone away",
                    "connection was killed",
                    "can't connect to mysql server",
                    "connection refused",
                    "timeout expired",
                    "deadlock found",
                    "lock wait timeout exceeded",
                    "connection reset by peer",
                    "broken pipe"
                ]
                
                is_retryable = any(error in error_str for error in retryable_errors)
                
                if is_retryable and attempt < max_retries - 1:
                    self.logger.warning(f"Database operation failed, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 5.0)  # Exponential backoff with max 5s
                    continue
                else:
                    self.logger.error(f"Transaction failed after {attempt + 1} attempts: {e}")
                    raise
            finally:
                if session:
                    try:
                        session.close()
                        self.logger.debug("Session closed")
                    except Exception as close_error:
                        self.logger.warning(f"Final session close failed: {close_error}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection (backward compatibility)"""
        if self._connection is None:
            raise Exception("SQLite connection not available")
        return self._connection
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute SELECT query (backward compatibility)"""
        if self._connection is None:
            raise Exception("No SQLite connection available")
        
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                cursor = self._connection.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                return results
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"Query execution failed: {e}")
                    raise
            except Exception as e:
                self.logger.error(f"Query execution failed: {e}")
                raise
    
    def execute_update(self, query: str, params: tuple = None):
        """Execute INSERT/UPDATE/DELETE query (backward compatibility)"""
        if self._connection is None:
            raise Exception("No SQLite connection available")
        
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                cursor = self._connection.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self._connection.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    self._connection.rollback()
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    self._connection.rollback()
                    self.logger.error(f"Update execution failed: {e}")
                    raise
            except Exception as e:
                self._connection.rollback()
                self.logger.error(f"Update execution failed: {e}")
                raise
    
    # Universal Database Manager compatibility methods
    
    def connect_to_database(self, connection_string: str, connection_id: str = "default") -> bool:
        """Connect to database using connection string (Universal compatibility)"""
        return self.initialize_with_connection_string(connection_string)
    
    def run_migrations(self, connection_id: str = "default", target_revision: str = "head") -> bool:
        """Run database migrations (compatibility method)
        
        Args:
            connection_id: Connection identifier
            target_revision: Target migration revision
            
        Returns:
            True if migrations successful (always True as migrations are handled during initialization)
        """
        # Migrations are handled during table creation in _create_tables_unified
        # This method exists for compatibility with Universal Database Manager interface
        self.logger.info(f"Migration request for {connection_id} - handled during initialization")
        return True
        """Connect to database using connection string (Universal compatibility)"""
        return self.initialize_with_connection_string(connection_string)
    
    def setup_database_with_docker(self, dialect: 'SQLDialect', database_name: str = "construction_test") -> Optional[str]:
        """Setup database using Docker (Universal compatibility)"""
        if not self.use_docker or not self.docker_manager:
            return None
        
        try:
            # Start Docker container
            if not self.docker_manager.start_database_containers([dialect.value]):
                return None
            
            # Get connection configuration
            config = self.docker_manager.get_database_config(dialect.value)
            if not config:
                return None
            
            # Create database and return connection string
            if dialect == SQLDialect.POSTGRESQL:
                connection_string = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{database_name}"
            elif dialect == SQLDialect.MYSQL:
                connection_string = f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{database_name}"
            else:
                return None
            
            # Test connection
            if self.initialize_with_connection_string(connection_string):
                return connection_string
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Docker database setup failed: {e}")
            return None
    
    def close_connection(self, connection_id: str = "default") -> bool:
        """Close database connection safely"""
        try:
            # Close SQLAlchemy engine
            if self._engine:
                # Wait for active connections to finish
                self._engine.dispose()
                self._engine = None
                self.logger.debug("SQLAlchemy engine disposed")
            
            # Close SQLite connection
            if self._connection:
                try:
                    # Execute a checkpoint to ensure WAL is written to main database
                    cursor = self._connection.cursor()
                    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    cursor.close()
                except Exception as e:
                    self.logger.warning(f"WAL checkpoint failed: {e}")
                
                self._connection.close()
                self._connection = None
                self.logger.debug("SQLite connection closed")
            
            # Clear session factory
            if self._session_factory:
                self._session_factory = None
            
            self.logger.info("Database connection closed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close connection: {e}")
            return False


# Create global instance for backward compatibility
database_manager = UnifiedDatabaseManager()


def main():
    """Test unified database manager"""
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Unified Database Manager')
    parser.add_argument('--test-sqlite', action='store_true', help='Test SQLite initialization')
    parser.add_argument('--test-connection', type=str, help='Test connection string')
    parser.add_argument('--db-path', type=str, default='test_unified.db', help='SQLite database path')
    
    args = parser.parse_args()
    
    manager = UnifiedDatabaseManager(logger)
    
    if args.test_sqlite:
        success = manager.initialize(args.db_path)
        print(f"SQLite test: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.test_connection:
        success = manager.initialize_with_connection_string(args.test_connection)
        print(f"Connection test: {'SUCCESS' if success else 'FAILED'}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()