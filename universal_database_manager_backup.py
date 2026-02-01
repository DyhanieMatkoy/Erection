#!/usr/bin/env python3
"""Unified Database Manager

Manages database connections and operations for SQLite, PostgreSQL, and MySQL.
Integrates with Docker and multi-dialect migration system.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sql_dialect_translator import SQLDialectTranslator, SQLDialect
from multi_dialect_migration_manager import MultiDialectMigrationManager
from docker_database_manager import DockerDatabaseManager


class UnifiedDatabaseManager:
    """Universal database manager supporting multiple SQL dialects"""
    
    def __init__(self, logger: Optional[logging.Logger] = None, use_docker: bool = True):
        """Initialize universal database manager
        
        Args:
            logger: Optional logger instance
            use_docker: Whether to use Docker for external databases
        """
        self.logger = logger or logging.getLogger(__name__)
        self.use_docker = use_docker
        
        # Initialize components
        self.translator = SQLDialectTranslator(self.logger)
        self.migration_manager = MultiDialectMigrationManager(self.logger)
        
        # Initialize Docker manager if requested
        self.docker_manager: Optional[DockerDatabaseManager] = None
        if use_docker:
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
        
        # Database connections
        self.engines: Dict[str, Engine] = {}
        self.sessions: Dict[str, sessionmaker] = {}
        
        self.logger.info("Universal database manager initialized")
    
    def connect_to_database(self, connection_string: str, connection_id: str = "default") -> bool:
        """Connect to database using connection string
        
        Args:
            connection_string: Database connection string
            connection_id: Unique identifier for this connection
            
        Returns:
            True if connection successful
        """
        try:
            self.logger.info(f"Connecting to database: {connection_id}")
            
            # Detect SQL dialect
            dialect = self.translator.get_dialect_from_connection_string(connection_string)
            self.logger.debug(f"Detected dialect: {dialect.value}")
            
            # Create engine
            engine = create_engine(
                connection_string,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Test connection
            with engine.connect() as conn:
                if dialect == SQLDialect.SQLITE:
                    conn.execute(text("SELECT 1"))
                elif dialect == SQLDialect.POSTGRESQL:
                    conn.execute(text("SELECT version()"))
                elif dialect == SQLDialect.MYSQL:
                    conn.execute(text("SELECT VERSION()"))
            
            # Store engine and create session factory
            self.engines[connection_id] = engine
            self.sessions[connection_id] = sessionmaker(bind=engine)
            
            self.logger.info(f"Database connection established: {connection_id} ({dialect.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def get_engine(self, connection_id: str = "default") -> Optional[Engine]:
        """Get SQLAlchemy engine for connection
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            SQLAlchemy engine or None
        """
        return self.engines.get(connection_id)
    
    def get_session(self, connection_id: str = "default"):
        """Get SQLAlchemy session for connection
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            SQLAlchemy session or None
        """
        session_factory = self.sessions.get(connection_id)
        return session_factory() if session_factory else None
    
    def execute_sql(self, sql: str, connection_id: str = "default", 
                   parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute SQL statement
        
        Args:
            sql: SQL statement to execute
            connection_id: Connection identifier
            parameters: Optional SQL parameters
            
        Returns:
            Query result
        """
        try:
            engine = self.get_engine(connection_id)
            if not engine:
                raise Exception(f"No engine found for connection: {connection_id}")
            
            with engine.connect() as conn:
                if parameters:
                    result = conn.execute(text(sql), parameters)
                else:
                    result = conn.execute(text(sql))
                
                # Commit for non-SELECT statements
                if not sql.strip().upper().startswith('SELECT'):
                    conn.commit()
                
                return result
                
        except Exception as e:
            self.logger.error(f"SQL execution failed: {e}")
            raise
    
    def translate_and_execute_sql(self, sql: str, source_dialect: SQLDialect,
                                 connection_id: str = "default",
                                 parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Translate SQL to target dialect and execute
        
        Args:
            sql: SQL statement in source dialect
            source_dialect: Source SQL dialect
            connection_id: Connection identifier
            parameters: Optional SQL parameters
            
        Returns:
            Query result
        """
        try:
            # Get target dialect from connection
            engine = self.get_engine(connection_id)
            if not engine:
                raise Exception(f"No engine found for connection: {connection_id}")
            
            target_dialect = self.translator.get_dialect_from_connection_string(str(engine.url))
            
            # Translate SQL if needed
            if source_dialect != target_dialect:
                translated_sql = self.translator.translate_sql(sql, source_dialect, target_dialect)
                self.logger.debug(f"Translated SQL from {source_dialect.value} to {target_dialect.value}")
            else:
                translated_sql = sql
            
            # Execute translated SQL
            return self.execute_sql(translated_sql, connection_id, parameters)
            
        except Exception as e:
            self.logger.error(f"Translate and execute failed: {e}")
            raise
    
    def setup_database_with_docker(self, dialect: SQLDialect, database_name: str = "construction_prod") -> Optional[str]:
        """Setup database using Docker
        
        Args:
            dialect: SQL dialect
            database_name: Database name
            
        Returns:
            Connection string if successful
        """
        if not self.use_docker or not self.docker_manager:
            self.logger.error("Docker is not available")
            return None
        
        try:
            self.logger.info(f"Setting up {dialect.value} database with Docker")
            
            # Start Docker container
            if not self.docker_manager.start_database_containers([dialect.value]):
                raise Exception(f"Failed to start {dialect.value} container")
            
            # Get connection configuration
            config = self.docker_manager.get_database_config(dialect.value)
            if not config:
                raise Exception(f"Failed to get {dialect.value} configuration")
            
            # First connect to default database to create our database
            if dialect == SQLDialect.POSTGRESQL:
                # Connect to default postgres database first
                default_connection = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/postgres"
                
                # Create our database
                try:
                    import psycopg2
                    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                    
                    conn = psycopg2.connect(
                        host=config['host'],
                        port=config['port'],
                        user=config['username'],
                        password=config['password'],
                        database='postgres'
                    )
                    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cursor = conn.cursor()
                    
                    # Create database if it doesn't exist
                    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE DATABASE {database_name}")
                        self.logger.info(f"Created PostgreSQL database: {database_name}")
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    self.logger.warning(f"Database creation failed, will try to connect anyway: {e}")
                
                connection_string = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{database_name}"
                
            elif dialect == SQLDialect.MYSQL:
                # Connect to default mysql database first
                try:
                    import pymysql
                    
                    conn = pymysql.connect(
                        host=config['host'],
                        port=config['port'],
                        user=config['username'],
                        password=config['password']
                    )
                    cursor = conn.cursor()
                    
                    # Create database if it doesn't exist
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
                    self.logger.info(f"Created MySQL database: {database_name}")
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    self.logger.warning(f"Database creation failed, will try to connect anyway: {e}")
                
                connection_string = f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{database_name}"
            else:
                raise Exception(f"Docker not supported for {dialect.value}")
            
            # Test connection to our database
            if self.connect_to_database(connection_string, f"docker_{dialect.value}"):
                self.logger.info(f"Docker database ready: {dialect.value}")
                return connection_string
            else:
                raise Exception("Connection test failed")
                
        except Exception as e:
            self.logger.error(f"Docker database setup failed: {e}")
            return None
    
    def run_migrations(self, connection_id: str = "default", target_revision: str = "head") -> bool:
        """Run database migrations
        
        Args:
            connection_id: Connection identifier
            target_revision: Target migration revision
            
        Returns:
            True if migrations successful
        """
        try:
            engine = self.get_engine(connection_id)
            if not engine:
                raise Exception(f"No engine found for connection: {connection_id}")
            
            # Detect dialect
            dialect = self.translator.get_dialect_from_connection_string(str(engine.url))
            
            # For SQLite, we need to use a different approach to avoid Alembic config issues
            if dialect == SQLDialect.SQLITE:
                return self._run_sqlite_migrations_direct(engine, target_revision)
            else:
                # Run migrations for external databases using multi-dialect manager
                success = self.migration_manager.upgrade_database(dialect, str(engine.url), target_revision)
                
                if success:
                    self.logger.info(f"Migrations completed for {dialect.value}")
                else:
                    self.logger.error(f"Migrations failed for {dialect.value}")
                
                return success
            
        except Exception as e:
            self.logger.error(f"Migration execution failed: {e}")
            return False
    
    def _run_sqlite_migrations_direct(self, engine, target_revision: str = "head") -> bool:
        """Run SQLite migrations directly without Alembic config issues
        
        Args:
            engine: SQLAlchemy engine
            target_revision: Target revision
            
        Returns:
            True if successful
        """
        try:
            self.logger.info("Running SQLite migrations directly")
            
            # Import all models to ensure tables are created
            try:
                from src.data.models.sync_models import SyncNode, SyncChange, ObjectVersionHistory
                from src.data.models.estimate_models import Estimate, EstimateWork
                from src.data.models.work_models import Work, WorkUnit
                from src.data.models.reference_models import Person, Organization
                
                # Create all tables
                from sqlalchemy import MetaData
                metadata = MetaData()
                
                # Bind metadata to engine and create all tables
                SyncNode.__table__.create(engine, checkfirst=True)
                SyncChange.__table__.create(engine, checkfirst=True)
                ObjectVersionHistory.__table__.create(engine, checkfirst=True)
                
                # Create main business tables
                Person.__table__.create(engine, checkfirst=True)
                Organization.__table__.create(engine, checkfirst=True)
                Work.__table__.create(engine, checkfirst=True)
                WorkUnit.__table__.create(engine, checkfirst=True)
                Estimate.__table__.create(engine, checkfirst=True)
                EstimateWork.__table__.create(engine, checkfirst=True)
                
                self.logger.info("SQLite tables created successfully")
                return True
                
            except ImportError as e:
                self.logger.warning(f"Could not import models, using basic table creation: {e}")
                
                # Fallback: create basic tables manually with proper SQL translation
                with engine.connect() as conn:
                    # Get legacy database manager SQL statements
                    legacy_sql_statements = self._get_legacy_database_sql_statements()
                    
                    # Translate each SQL statement from universal format to SQLite
                    for sql_statement in legacy_sql_statements:
                        try:
                            # Translate SQL from any dialect to SQLite
                            translated_sql = self.translator.translate_sql(
                                sql_statement, 
                                'any',  # Use universal rules for any source to SQLite
                                SQLDialect.SQLITE
                            )
                            
                            # Execute translated SQL
                            conn.execute(text(translated_sql))
                            
                        except Exception as sql_error:
                            self.logger.warning(f"Failed to execute SQL statement: {sql_error}")
                            self.logger.debug(f"Original SQL: {sql_statement}")
                            self.logger.debug(f"Translated SQL: {translated_sql}")
                            # Continue with other statements
                    
                    conn.commit()
                
                self.logger.info("Basic SQLite tables created successfully with SQL translation")
                return True
                
        except Exception as e:
            self.logger.error(f"SQLite migration failed: {e}")
            return False
    
    def _get_legacy_database_sql_statements(self) -> List[str]:
        """Get SQL statements from legacy database manager
        
        Returns:
            List of SQL statements that need translation
        """
        # Always use the corrected SQL statements that match legacy database manager
        # This ensures consistency between Universal and Legacy Database Managers
        return self._extract_sql_from_legacy_manager()
    
    def _extract_sql_from_legacy_manager(self) -> List[str]:
        """Extract SQL statements from legacy database manager source code"""
        try:
            # Import the legacy database manager to get the actual SQL statements
            from src.data.database_manager import DatabaseManager as LegacyDatabaseManager
            
            # Create a temporary instance to access the SQL statements
            legacy_manager = LegacyDatabaseManager()
            
            # Get the SQL statements from the legacy manager's _create_tables method
            # We need to extract the table creation SQL from the legacy manager
            return self._get_sql_statements_from_legacy_manager()
            
        except ImportError as e:
            self.logger.warning(f"Could not import legacy database manager: {e}")
            # Fallback to hardcoded statements that match the legacy manager
            return self._get_fallback_sql_statements()
        except Exception as e:
            self.logger.warning(f"Error extracting SQL from legacy manager: {e}")
            # Fallback to hardcoded statements that match the legacy manager
            return self._get_fallback_sql_statements()
    
    def _get_sql_statements_from_legacy_manager(self) -> List[str]:
        """Get SQL statements that exactly match the legacy database manager"""
        # These SQL statements are extracted from src/data/database_manager.py _create_tables method
        # and MUST be kept in sync with that file to ensure schema consistency
        return [
            # Sync Tables - CRITICAL: Must be created first for sync system
            """CREATE TABLE IF NOT EXISTS sync_nodes (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_sync_in TIMESTAMP,
                last_sync_out TIMESTAMP,
                received_packet_no INTEGER,
                sent_packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS sync_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                entity_type TEXT NOT NULL,
                entity_uuid TEXT NOT NULL,
                operation TEXT NOT NULL,
                packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS object_version_history (
                id TEXT PRIMARY KEY,
                entity_uuid TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source_node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                serialized_data TEXT NOT NULL,
                conflict_resolution TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Audit Logs
            """CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )""",
            
            # Persons - FIXED: Use full_name instead of name
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0,
                hourly_rate REAL DEFAULT 0
            )""",
            
                        # Organizations
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                default_responsible_id INTEGER REFERENCES persons(id),
                parent_id INTEGER REFERENCES organizations(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Counterparties
            """CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                contact_person TEXT,
                phone TEXT,
                parent_id INTEGER REFERENCES counterparties(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Objects
            """CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES counterparties(id),
                address TEXT,
                parent_id INTEGER REFERENCES objects(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Works
            """CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                parent_id INTEGER REFERENCES works(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Estimates - ПРАВИЛЬНАЯ СХЕМА из Legacy Database Manager
            """CREATE TABLE IF NOT EXISTS estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                customer_id INTEGER REFERENCES counterparties(id),
                object_id INTEGER REFERENCES objects(id),
                contractor_id INTEGER REFERENCES organizations(id),
                responsible_id INTEGER REFERENCES persons(id),
                total_sum REAL DEFAULT 0,
                total_labor REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                estimate_type TEXT DEFAULT 'General',
                base_document_id INTEGER REFERENCES estimates(id)
            )""",
            
            # Estimate Lines
            """CREATE TABLE IF NOT EXISTS estimate_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
                line_number INTEGER,
                work_id INTEGER REFERENCES works(id),
                quantity REAL,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                sum REAL,
                planned_labor REAL,
                is_group INTEGER DEFAULT 0,
                group_name TEXT,
                parent_group_id INTEGER REFERENCES estimate_lines(id),
                is_collapsed INTEGER DEFAULT 0
            )""",
            
                        # Daily Reports
            """CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                number TEXT
            )""",
            
            # Daily Report Lines
            """CREATE TABLE IF NOT EXISTS daily_report_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
                line_number INTEGER,
                work_id INTEGER REFERENCES works(id),
                planned_labor REAL,
                actual_labor REAL,
                labor_deviation_percent REAL,
                is_group INTEGER DEFAULT 0,
                group_name TEXT,
                parent_group_id INTEGER REFERENCES daily_report_lines(id),
                is_collapsed INTEGER DEFAULT 0
            )""",
            
            # Daily Report Executors
            """CREATE TABLE IF NOT EXISTS daily_report_executors (
                report_line_id INTEGER REFERENCES daily_report_lines(id) ON DELETE CASCADE,
                executor_id INTEGER REFERENCES persons(id),
                PRIMARY KEY (report_line_id, executor_id)
            )""",
            
            # User Settings
            """CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER REFERENCES users(id),
                form_name TEXT,
                setting_key TEXT,
                setting_value TEXT,
                PRIMARY KEY (user_id, form_name, setting_key)
            )""",
            
            # Constants
            """CREATE TABLE IF NOT EXISTS constants (
                key TEXT PRIMARY KEY,
                value TEXT
            )""",
            
            # Work Execution Register
            """CREATE TABLE IF NOT EXISTS work_execution_register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorder_type TEXT NOT NULL,
                recorder_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                period DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                work_id INTEGER REFERENCES works(id),
                quantity_income REAL DEFAULT 0,
                quantity_expense REAL DEFAULT 0,
                sum_income REAL DEFAULT 0,
                sum_expense REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Timesheets
            """CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                month_year TEXT NOT NULL,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Timesheet Lines
            """CREATE TABLE IF NOT EXISTS timesheet_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timesheet_id INTEGER REFERENCES timesheets(id) ON DELETE CASCADE,
                line_number INTEGER,
                employee_id INTEGER REFERENCES persons(id),
                hourly_rate REAL DEFAULT 0,
                day_01 REAL DEFAULT 0,
                day_02 REAL DEFAULT 0,
                day_03 REAL DEFAULT 0,
                day_04 REAL DEFAULT 0,
                day_05 REAL DEFAULT 0,
                day_06 REAL DEFAULT 0,
                day_07 REAL DEFAULT 0,
                day_08 REAL DEFAULT 0,
                day_09 REAL DEFAULT 0,
                day_10 REAL DEFAULT 0,
                day_11 REAL DEFAULT 0,
                day_12 REAL DEFAULT 0,
                day_13 REAL DEFAULT 0,
                day_14 REAL DEFAULT 0,
                day_15 REAL DEFAULT 0,
                day_16 REAL DEFAULT 0,
                day_17 REAL DEFAULT 0,
                day_18 REAL DEFAULT 0,
                day_19 REAL DEFAULT 0,
                day_20 REAL DEFAULT 0,
                day_21 REAL DEFAULT 0,
                day_22 REAL DEFAULT 0,
                day_23 REAL DEFAULT 0,
                day_24 REAL DEFAULT 0,
                day_25 REAL DEFAULT 0,
                day_26 REAL DEFAULT 0,
                day_27 REAL DEFAULT 0,
                day_28 REAL DEFAULT 0,
                day_29 REAL DEFAULT 0,
                day_30 REAL DEFAULT 0,
                day_31 REAL DEFAULT 0,
                total_hours REAL DEFAULT 0,
                total_amount REAL DEFAULT 0
            )""",
            
            # Payroll Register
            """CREATE TABLE IF NOT EXISTS payroll_register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorder_type TEXT NOT NULL,
                recorder_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                period DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                employee_id INTEGER REFERENCES persons(id),
                work_date DATE NOT NULL,
                hours_worked REAL DEFAULT 0,
                amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(object_id, estimate_id, employee_id, work_date)
            )"""
        ]
    
    def _get_fallback_sql_statements(self) -> List[str]:
        """Fallback SQL statements that match Legacy Database Manager exactly"""
        # These SQL statements MUST match the Legacy Database Manager exactly
        # to ensure schema consistency between Universal and Legacy systems
        return [
            # Sync Tables - CRITICAL: Must be created first for sync system
            """CREATE TABLE IF NOT EXISTS sync_nodes (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_sync_in TIMESTAMP,
                last_sync_out TIMESTAMP,
                received_packet_no INTEGER,
                sent_packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS sync_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                entity_type TEXT NOT NULL,
                entity_uuid TEXT NOT NULL,
                operation TEXT NOT NULL,
                packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS object_version_history (
                id TEXT PRIMARY KEY,
                entity_uuid TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source_node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                serialized_data TEXT NOT NULL,
                conflict_resolution TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Audit Logs
            """CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )""",
            
            # Persons - FIXED: Use full_name instead of name
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0,
                hourly_rate REAL DEFAULT 0
            )""",
            
                        # Organizations
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                default_responsible_id INTEGER REFERENCES persons(id),
                parent_id INTEGER REFERENCES organizations(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Counterparties
            """CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                contact_person TEXT,
                phone TEXT,
                parent_id INTEGER REFERENCES counterparties(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Objects
            """CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES counterparties(id),
                address TEXT,
                parent_id INTEGER REFERENCES objects(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Works
            """CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                parent_id INTEGER REFERENCES works(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",
            
                        # Estimates - ПРАВИЛЬНАЯ СХЕМА из Legacy Database Manager
            """CREATE TABLE IF NOT EXISTS estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                customer_id INTEGER REFERENCES counterparties(id),
                object_id INTEGER REFERENCES objects(id),
                contractor_id INTEGER REFERENCES organizations(id),
                responsible_id INTEGER REFERENCES persons(id),
                total_sum REAL DEFAULT 0,
                total_labor REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                estimate_type TEXT DEFAULT 'General',
                base_document_id INTEGER REFERENCES estimates(id)
            )""",
            
                        # Daily Reports
            """CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                number TEXT
            )""",
            
            # Timesheets
            """CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                month_year TEXT NOT NULL,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
    
    def create_migration(self, message: str, base_dialect: SQLDialect = SQLDialect.SQLITE) -> Dict[SQLDialect, str]:
        """Create migration for all supported dialects
        
        Args:
            message: Migration message
            base_dialect: Base dialect to create migration from
            
        Returns:
            Dictionary mapping dialects to migration file paths
        """
        try:
            return self.migration_manager.create_migration_for_all_dialects(message, base_dialect)
            
        except Exception as e:
            self.logger.error(f"Migration creation failed: {e}")
            return {}
    
    def get_database_info(self, connection_id: str = "default") -> Dict[str, Any]:
        """Get database information
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Database information
        """
        try:
            engine = self.get_engine(connection_id)
            if not engine:
                return {'error': f'No connection found: {connection_id}'}
            
            dialect = self.translator.get_dialect_from_connection_string(str(engine.url))
            
            # Get database-specific information
            info = {
                'connection_id': connection_id,
                'dialect': dialect.value,
                'url': str(engine.url),
                'driver': engine.dialect.name,
                'connected': True
            }
            
            # Get version information
            try:
                with engine.connect() as conn:
                    if dialect == SQLDialect.SQLITE:
                        result = conn.execute(text("SELECT sqlite_version()"))
                        info['version'] = result.scalar()
                    elif dialect == SQLDialect.POSTGRESQL:
                        result = conn.execute(text("SELECT version()"))
                        info['version'] = result.scalar()
                    elif dialect == SQLDialect.MYSQL:
                        result = conn.execute(text("SELECT VERSION()"))
                        info['version'] = result.scalar()
            except Exception as e:
                info['version_error'] = str(e)
            
            # Get migration status
            try:
                migration_status = self.migration_manager.get_migration_status(dialect, str(engine.url))
                info['migration_status'] = migration_status
            except Exception as e:
                info['migration_error'] = str(e)
            
            return info
            
        except Exception as e:
            return {
                'connection_id': connection_id,
                'error': str(e),
                'connected': False
            }
    
    def close_connection(self, connection_id: str = "default") -> bool:
        """Close database connection
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            True if closed successfully
        """
        try:
            if connection_id in self.engines:
                self.engines[connection_id].dispose()
                del self.engines[connection_id]
            
            if connection_id in self.sessions:
                del self.sessions[connection_id]
            
            self.logger.info(f"Database connection closed: {connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close connection: {e}")
            return False
    
    def close_all_connections(self) -> None:
        """Close all database connections"""
        for connection_id in list(self.engines.keys()):
            self.close_connection(connection_id)
    
    def setup_production_environment(self, config: Dict[str, Any]) -> bool:
        """Setup production environment with specified configuration
        
        Args:
            config: Production configuration
            
        Returns:
            True if setup successful
        """
        try:
            self.logger.info("Setting up production environment")
            
            # Determine database type
            db_type = config.get('database_type', 'postgresql').lower()
            
            if db_type not in ['sqlite', 'postgresql', 'mysql']:
                raise Exception(f"Unsupported database type: {db_type}")
            
            dialect = SQLDialect(db_type)
            
            # Setup database
            if self.use_docker and db_type in ['postgresql', 'mysql']:
                # Use Docker for external databases
                connection_string = self.setup_database_with_docker(dialect, config.get('database_name', 'construction_prod'))
                if not connection_string:
                    raise Exception(f"Failed to setup Docker database: {db_type}")
            else:
                # Use provided connection string
                connection_string = config.get('connection_string')
                if not connection_string:
                    raise Exception("Connection string required for non-Docker setup")
                
                if not self.connect_to_database(connection_string, "production"):
                    raise Exception("Failed to connect to production database")
            
            # Run migrations
            if not self.run_migrations("production"):
                raise Exception("Migration execution failed")
            
            self.logger.info("Production environment setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Production environment setup failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all_connections()
        
        # Stop Docker containers if we started them
        if self.use_docker and self.docker_manager:
            try:
                self.docker_manager.stop_all_containers()
            except Exception as e:
                self.logger.warning(f"Failed to stop Docker containers: {e}")


def main():
    """Test universal database manager"""
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Unified Database Manager')
    parser.add_argument('--setup-docker', choices=['postgresql', 'mysql'],
                       help='Setup database with Docker')
    parser.add_argument('--connect', type=str,
                       help='Connect to database using connection string')
    parser.add_argument('--info', action='store_true',
                       help='Show database information')
    parser.add_argument('--migrate', action='store_true',
                       help='Run database migrations')
    parser.add_argument('--create-migration', type=str,
                       help='Create new migration')
    
    args = parser.parse_args()
    
    with UnifiedDatabaseManager(logger) as db_manager:
        
        if args.setup_docker:
            dialect = SQLDialect(args.setup_docker)
            connection_string = db_manager.setup_database_with_docker(dialect)
            if connection_string:
                print(f"✅ Docker database ready: {connection_string}")
            else:
                print("❌ Docker database setup failed")
        
        elif args.connect:
            success = db_manager.connect_to_database(args.connect)
            print("✅ Connected" if success else "❌ Connection failed")
        
        elif args.info:
            info = db_manager.get_database_info()
            print("Database Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        
        elif args.migrate:
            success = db_manager.run_migrations()
            print("✅ Migrations completed" if success else "❌ Migrations failed")
        
        elif args.create_migration:
            results = db_manager.create_migration(args.create_migration)
            print(f"✅ Created migrations for {len(results)} dialects: {list(results.keys())}")
        
        else:
            parser.print_help()


if __name__ == '__main__':
    main()