"""Database manager with multi-backend support using SQLAlchemy"""
import sqlite3
import logging
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .database_config import DatabaseConfig
from .connection_string_builder import ConnectionStringBuilder
from .exceptions import DatabaseConnectionError, DatabaseConfigurationError, DatabaseOperationError
from .sqlalchemy_base import Base
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enhanced database manager with multi-backend support"""
    
    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    _config: Optional[DatabaseConfig] = None
    _connection: Optional[sqlite3.Connection] = None  # For backward compatibility
    _schema_manager: Optional[SchemaManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config_path: str = "env.ini") -> bool:
        """Initialize database from configuration
        
        Args:
            config_path: Path to configuration file (default: env.ini)
                        For backward compatibility, can also be a direct database path
                        
        Returns:
            True if initialization successful, False otherwise
            
        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseConfigurationError: If configuration is invalid
        """
        try:
            # Check if config_path is actually a database file path (backward compatibility)
            if config_path.endswith('.db') or config_path.endswith('.sqlite'):
                logger.info(f"Legacy initialization with database path: {config_path}")
                return self._initialize_legacy(config_path)
            
            # Load configuration
            try:
                self._config = DatabaseConfig(config_path)
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_path}: {e}")
                raise DatabaseConfigurationError(
                    f"Failed to load database configuration: {e}"
                )
            
            # Validate configuration
            if not self._config.validate():
                error_msg = f"Invalid database configuration for type: {self._config.get_db_type()}"
                logger.error(error_msg)
                raise DatabaseConfigurationError(error_msg)
            
            # Build connection string
            try:
                connection_string = ConnectionStringBuilder.build_from_config(
                    self._config.get_db_type(),
                    self._config.get_config_data()
                )
            except Exception as e:
                logger.error(f"Failed to build connection string: {e}")
                raise DatabaseConfigurationError(
                    f"Failed to build connection string for {self._config.get_db_type()}: {e}"
                )
            
            # Create engine with appropriate settings
            engine_kwargs = self._get_engine_kwargs()
            
            try:
                self._engine = create_engine(connection_string, **engine_kwargs)
                
                # Enable foreign key support for SQLite
                if self._config.is_sqlite():
                    @event.listens_for(self._engine, "connect")
                    def set_sqlite_pragma(dbapi_conn, connection_record):
                        cursor = dbapi_conn.cursor()
                        cursor.execute("PRAGMA foreign_keys=ON")
                        cursor.close()
                
                # Test the connection by attempting to connect
                try:
                    with self._engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.info(f"Successfully connected to {self._config.get_db_type()} database")
                except Exception as conn_error:
                    db_type = self._config.get_db_type()
                    config_data = self._config.get_config_data()
                    
                    # Build detailed error message without exposing password
                    if db_type == 'postgresql':
                        error_details = (
                            f"host={config_data.get('host', 'N/A')}, "
                            f"port={config_data.get('port', 'N/A')}, "
                            f"database={config_data.get('database', 'N/A')}, "
                            f"user={config_data.get('user', 'N/A')}"
                        )
                    elif db_type == 'mssql':
                        error_details = (
                            f"host={config_data.get('host', 'N/A')}, "
                            f"port={config_data.get('port', 'N/A')}, "
                            f"database={config_data.get('database', 'N/A')}, "
                            f"user={config_data.get('user', 'N/A')}, "
                            f"driver={config_data.get('driver', 'N/A')}"
                        )
                    else:
                        error_details = f"db_path={config_data.get('db_path', 'N/A')}"
                    
                    logger.error(
                        f"Failed to connect to {db_type} database. "
                        f"Connection details: {error_details}. "
                        f"Error: {conn_error}"
                    )
                    raise DatabaseConnectionError(
                        f"Failed to connect to {db_type} database: {conn_error}. "
                        f"Please verify connection parameters: {error_details}"
                    )
                
                # Create session factory
                self._session_factory = sessionmaker(
                    bind=self._engine,
                    autocommit=False,
                    autoflush=False
                )
                
                # Initialize schema manager
                self._schema_manager = SchemaManager(self._engine)
                
                # Create tables if needed (this will test the connection)
                self._create_tables_sqlalchemy()
                
            except DatabaseConnectionError:
                # Re-raise connection errors as-is
                raise
            except Exception as e:
                # Wrap other exceptions in DatabaseConnectionError
                logger.error(f"Failed to initialize {self._config.get_db_type()} database engine: {e}")
                raise DatabaseConnectionError(
                    f"Database engine initialization failed for {self._config.get_db_type()}: {e}"
                )
            
            # For backward compatibility with SQLite, maintain a connection
            if self._config.is_sqlite():
                db_path = self._config.get_config_data()['db_path']
                try:
                    self._connection = sqlite3.connect(db_path, check_same_thread=False)
                    self._connection.row_factory = sqlite3.Row
                except Exception as e:
                    logger.error(f"Failed to create SQLite connection for backward compatibility: {e}")
                    raise DatabaseConnectionError(
                        f"Failed to create SQLite connection to {db_path}: {e}"
                    )
            
            logger.info(f"Database initialized successfully: type={self._config.get_db_type()}")
            return True
            
        except DatabaseConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            # Fall back to SQLite with default path
            logger.warning("Falling back to SQLite with default configuration")
            try:
                return self._initialize_legacy("construction.db")
            except Exception as fallback_error:
                logger.error(f"Fallback initialization also failed: {fallback_error}")
                raise DatabaseConnectionError(
                    f"Failed to initialize database with configuration and fallback: {e}"
                )
            
        except DatabaseConnectionError:
            # Re-raise connection errors without wrapping
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {e}")
            raise DatabaseConnectionError(f"Database initialization failed: {e}")
    
    def _initialize_legacy(self, db_path: str) -> bool:
        """Legacy initialization for backward compatibility
        
        Args:
            db_path: Path to SQLite database file
            
        Returns:
            True if initialization successful
            
        Raises:
            DatabaseConnectionError: If initialization fails
        """
        try:
            # Create SQLite connection for backward compatibility
            try:
                self._connection = sqlite3.connect(db_path, check_same_thread=False)
                self._connection.row_factory = sqlite3.Row
                logger.debug(f"SQLite connection created: {db_path}")
            except sqlite3.Error as e:
                logger.error(f"Failed to create SQLite connection to {db_path}: {e}")
                raise DatabaseConnectionError(
                    f"Failed to connect to SQLite database at {db_path}: {e}"
                )
            
            # Also create SQLAlchemy engine for new code
            try:
                connection_string = f"sqlite:///{db_path}"
                self._engine = create_engine(connection_string, poolclass=NullPool)
                
                # Enable foreign key support
                @event.listens_for(self._engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
                
                # Test the connection
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.debug("SQLAlchemy engine created and tested")
            except Exception as e:
                logger.error(f"Failed to create SQLAlchemy engine for {db_path}: {e}")
                raise DatabaseConnectionError(
                    f"Failed to initialize SQLAlchemy engine for {db_path}: {e}"
                )
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Create tables using legacy method
            try:
                self._create_tables()
                self._create_indices()
                logger.debug("Database tables and indices created")
            except Exception as e:
                logger.error(f"Failed to create tables and indices: {e}")
                raise DatabaseOperationError(
                    f"Failed to create database schema: {e}"
                )
            
            logger.info(f"Database initialized (legacy mode): {db_path}")
            return True
            
        except (DatabaseConnectionError, DatabaseOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during legacy initialization: {e}")
            raise DatabaseConnectionError(
                f"Failed to initialize database in legacy mode: {e}"
            )
    
    def _get_engine_kwargs(self) -> dict:
        """Get engine configuration based on database type
        
        Returns:
            Dictionary of engine configuration options
        """
        kwargs = {
            'echo': False,  # Set to True for SQL query logging
        }
        
        if self._config.is_sqlite():
            # SQLite doesn't need connection pooling
            kwargs['poolclass'] = NullPool
            kwargs['connect_args'] = {'check_same_thread': False}
            
        elif self._config.is_postgresql() or self._config.is_mssql():
            # Configure connection pooling for PostgreSQL and MSSQL
            config_data = self._config.get_config_data()
            kwargs['poolclass'] = QueuePool
            kwargs['pool_size'] = config_data.get('pool_size', 5)
            kwargs['max_overflow'] = config_data.get('max_overflow', 10)
            kwargs['pool_timeout'] = config_data.get('pool_timeout', 30)
            kwargs['pool_recycle'] = config_data.get('pool_recycle', 3600)
            kwargs['pool_pre_ping'] = True  # Verify connections before using
        
        return kwargs
    
    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine
        
        Returns:
            SQLAlchemy Engine instance
            
        Raises:
            DatabaseConnectionError: If engine is not initialized
        """
        if self._engine is None:
            logger.error("Attempted to get engine before initialization")
            raise DatabaseConnectionError(
                "Database engine not initialized. Call initialize() first."
            )
        return self._engine
    
    def get_session(self) -> Session:
        """Get a new SQLAlchemy session
        
        Returns:
            SQLAlchemy Session instance
            
        Raises:
            DatabaseConnectionError: If session factory is not initialized
            DatabaseOperationError: If session creation fails
        """
        if self._session_factory is None:
            logger.error("Attempted to get session before initialization")
            raise DatabaseConnectionError(
                "Session factory not initialized. Call initialize() first."
            )
        
        try:
            session = self._session_factory()
            logger.debug("New database session created")
            return session
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            raise DatabaseOperationError(f"Failed to create database session: {e}")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations
        
        Yields:
            SQLAlchemy Session instance
            
        Raises:
            DatabaseOperationError: If any database operation fails
            
        Example:
            with db_manager.session_scope() as session:
                user = session.query(User).filter_by(id=1).first()
                user.name = "New Name"
                # Automatically commits on success, rolls back on exception
        """
        session = None
        try:
            session = self.get_session()
            yield session
            session.commit()
            logger.debug("Transaction committed successfully")
        except DatabaseConnectionError:
            # Re-raise connection errors without wrapping
            if session:
                session.rollback()
                logger.error("Transaction rolled back due to connection error")
            raise
        except Exception as e:
            if session:
                session.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            
            # Try to extract more context from the exception
            error_context = self._extract_error_context(e)
            
            # Build detailed error message
            error_msg = f"Database operation failed: {e}"
            if error_context:
                error_msg += f". Context: {error_context}"
            
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg)
        finally:
            if session:
                session.close()
                logger.debug("Session closed")
    
    def _extract_error_context(self, exception: Exception) -> str:
        """Extract contextual information from database exceptions
        
        Args:
            exception: The exception to extract context from
            
        Returns:
            String with error context information
        """
        context_parts = []
        
        # Check for SQLAlchemy-specific exceptions
        if hasattr(exception, 'statement'):
            # Truncate long SQL statements
            statement = str(exception.statement)
            if len(statement) > 200:
                statement = statement[:200] + "..."
            context_parts.append(f"SQL: {statement}")
        
        if hasattr(exception, 'params'):
            # Don't log sensitive parameter values, just indicate they exist
            context_parts.append(f"Parameters: {len(exception.params)} parameter(s)")
        
        # Check for connection pool errors
        if 'pool' in str(exception).lower():
            context_parts.append("Connection pool may be exhausted")
        
        # Check for constraint violations
        if 'constraint' in str(exception).lower() or 'foreign key' in str(exception).lower():
            context_parts.append("Database constraint violation")
        
        # Check for timeout errors
        if 'timeout' in str(exception).lower():
            context_parts.append("Operation timed out")
        
        return "; ".join(context_parts) if context_parts else ""
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection (backward compatibility)
        
        Returns:
            SQLite connection object
            
        Raises:
            DatabaseConnectionError: If connection is not available
            
        Note:
            This method is maintained for backward compatibility with existing code.
            New code should use session_scope() or get_session() instead.
        """
        if self._connection is None:
            logger.error("Attempted to get SQLite connection when not available")
            raise DatabaseConnectionError(
                "SQLite connection not available. This may be because you're using "
                "PostgreSQL or MSSQL backend. Use session_scope() instead."
            )
        return self._connection
    
    def get_schema_manager(self) -> SchemaManager:
        """Get the schema manager instance
        
        Returns:
            SchemaManager instance
            
        Raises:
            DatabaseConnectionError: If schema manager is not initialized
        """
        if self._schema_manager is None:
            logger.error("Attempted to get schema manager before initialization")
            raise DatabaseConnectionError(
                "Schema manager not initialized. Call initialize() first."
            )
        return self._schema_manager
    
    def _create_tables_sqlalchemy(self):
        """Create all tables using SQLAlchemy models and schema manager
        
        Raises:
            DatabaseOperationError: If table creation fails
        """
        try:
            # Import models to register them with Base
            try:
                from .models import sqlalchemy_models  # noqa: F401
                logger.debug("SQLAlchemy models imported successfully")
            except ImportError as e:
                logger.error(f"Failed to import SQLAlchemy models: {e}")
                raise DatabaseOperationError(
                    f"Failed to import database models: {e}"
                )
            
            # Use schema manager for proper initialization
            if self._schema_manager:
                try:
                    self._schema_manager.initialize_schema(use_alembic=True)
                    logger.info("Database schema initialized successfully using schema manager")
                except Exception as e:
                    logger.error(f"Schema manager initialization failed: {e}")
                    raise DatabaseOperationError(
                        f"Failed to initialize database schema: {e}"
                    )
            else:
                # Fallback to direct table creation
                try:
                    Base.metadata.create_all(bind=self._engine)
                    logger.info("Database tables created successfully using SQLAlchemy")
                except Exception as e:
                    logger.error(f"Direct table creation failed: {e}")
                    raise DatabaseOperationError(
                        f"Failed to create database tables: {e}"
                    )
            
        except DatabaseOperationError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during table creation: {e}")
            # Fall back to legacy table creation for SQLite only
            if self._config and self._config.is_sqlite():
                logger.warning("Falling back to legacy table creation for SQLite")
                try:
                    self._create_tables()
                    self._create_indices()
                    logger.info("Legacy table creation succeeded")
                except Exception as legacy_error:
                    logger.error(f"Legacy table creation also failed: {legacy_error}")
                    raise DatabaseOperationError(
                        f"Failed to create tables with both SQLAlchemy and legacy methods: {e}"
                    )
            else:
                # For non-SQLite backends, raise the exception
                raise DatabaseOperationError(
                    f"Failed to create database tables: {e}"
                )
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Query results
            
        Raises:
            DatabaseOperationError: If query execution fails
        """
        if self._connection is None:
            raise DatabaseConnectionError(
                "No database connection available. Call initialize() first."
            )
        
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            logger.debug(f"Query executed successfully, returned {len(results)} rows")
            return results
        except sqlite3.Error as e:
            # Truncate long queries for logging
            query_preview = query[:200] + "..." if len(query) > 200 else query
            logger.error(
                f"Query execution failed. Query: {query_preview}. "
                f"Parameters: {params if params else 'None'}. Error: {e}"
            )
            raise DatabaseOperationError(
                f"Failed to execute query: {e}. Query: {query_preview}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise DatabaseOperationError(f"Query execution failed: {e}")
    
    def execute_update(self, query: str, params: tuple = None):
        """Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Last inserted row ID
            
        Raises:
            DatabaseOperationError: If query execution fails
        """
        if self._connection is None:
            raise DatabaseConnectionError(
                "No database connection available. Call initialize() first."
            )
        
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self._connection.commit()
            last_id = cursor.lastrowid
            logger.debug(f"Update query executed successfully, last row ID: {last_id}")
            return last_id
        except sqlite3.IntegrityError as e:
            self._connection.rollback()
            # Truncate long queries for logging
            query_preview = query[:200] + "..." if len(query) > 200 else query
            logger.error(
                f"Integrity constraint violation. Query: {query_preview}. "
                f"Parameters: {params if params else 'None'}. Error: {e}"
            )
            raise DatabaseOperationError(
                f"Database constraint violation: {e}. Query: {query_preview}"
            )
        except sqlite3.Error as e:
            self._connection.rollback()
            # Truncate long queries for logging
            query_preview = query[:200] + "..." if len(query) > 200 else query
            logger.error(
                f"Update query execution failed. Query: {query_preview}. "
                f"Parameters: {params if params else 'None'}. Error: {e}"
            )
            raise DatabaseOperationError(
                f"Failed to execute update query: {e}. Query: {query_preview}"
            )
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Unexpected error during update query execution: {e}")
            raise DatabaseOperationError(f"Update query execution failed: {e}")
    
    def _create_tables(self):
        """Create all database tables"""
        cursor = self._connection.cursor()
        
        tables = [
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
            
            # Persons
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Organizations
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                default_responsible_id INTEGER REFERENCES persons(id),
                parent_id INTEGER REFERENCES organizations(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Counterparties
            """CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                contact_person TEXT,
                phone TEXT,
                parent_id INTEGER REFERENCES counterparties(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Objects
            """CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES counterparties(id),
                address TEXT,
                parent_id INTEGER REFERENCES objects(id),
                marked_for_deletion INTEGER DEFAULT 0
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
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Estimates
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
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Daily Report Lines
            """CREATE TABLE IF NOT EXISTS daily_report_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
                line_number INTEGER,
                work_id INTEGER REFERENCES works(id),
                planned_labor REAL,
                actual_labor REAL,
                deviation_percent REAL,
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
            
            # Work Execution Register (Регистр накопления ВыполнениеРабот)
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
            
            # Payroll Register (Регистр начислений и удержаний)
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
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # Add posting fields to documents if they don't exist
        self._add_posting_fields()
        
        self._connection.commit()
    
    def _add_posting_fields(self):
        """Add posting fields to documents (migration)"""
        cursor = self._connection.cursor()
        
        # Check if fields exist in estimates
        cursor.execute("PRAGMA table_info(estimates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_posted' not in columns:
            cursor.execute("ALTER TABLE estimates ADD COLUMN is_posted INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE estimates ADD COLUMN posted_at TIMESTAMP")
        
        if 'marked_for_deletion' not in columns:
            cursor.execute("ALTER TABLE estimates ADD COLUMN marked_for_deletion INTEGER DEFAULT 0")
            
        if 'estimate_type' not in columns:
            cursor.execute("ALTER TABLE estimates ADD COLUMN estimate_type TEXT DEFAULT 'General'")
            cursor.execute("UPDATE estimates SET estimate_type = 'General'")
            
        if 'base_document_id' not in columns:
            cursor.execute("ALTER TABLE estimates ADD COLUMN base_document_id INTEGER REFERENCES estimates(id)")
        
        # Check if fields exist in daily_reports
        cursor.execute("PRAGMA table_info(daily_reports)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_posted' not in columns:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN is_posted INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN posted_at TIMESTAMP")
        
        if 'marked_for_deletion' not in columns:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN marked_for_deletion INTEGER DEFAULT 0")
        
        if 'number' not in columns:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN number TEXT")
        
        # Add code field to works if it doesn't exist
        cursor.execute("PRAGMA table_info(works)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'code' not in columns:
            cursor.execute("ALTER TABLE works ADD COLUMN code TEXT")
        
        # Add grouping fields to estimate_lines if they don't exist
        cursor.execute("PRAGMA table_info(estimate_lines)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_group' not in columns:
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN is_group INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN group_name TEXT")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN parent_group_id INTEGER REFERENCES estimate_lines(id)")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN is_collapsed INTEGER DEFAULT 0")
        
        # Add grouping fields to daily_report_lines if they don't exist
        cursor.execute("PRAGMA table_info(daily_report_lines)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_group' not in columns:
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN is_group INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN group_name TEXT")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN parent_group_id INTEGER REFERENCES daily_report_lines(id)")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN is_collapsed INTEGER DEFAULT 0")
        
        # Add parent_id and is_group fields to references if they don't exist
        for table in ['persons', 'counterparties', 'objects', 'organizations', 'works']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'parent_id' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN parent_id INTEGER REFERENCES {table}(id)")
            
            if 'is_group' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_group INTEGER DEFAULT 0")
        
        # Add hourly_rate field to persons if it doesn't exist
        cursor.execute("PRAGMA table_info(persons)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'hourly_rate' not in columns:
            cursor.execute("ALTER TABLE persons ADD COLUMN hourly_rate REAL DEFAULT 0")
    
    def _create_indices(self):
        """Create database indices"""
        cursor = self._connection.cursor()
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",
            "CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)",
            # Audit Logs
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
            # Register indices
            "CREATE INDEX IF NOT EXISTS idx_register_recorder ON work_execution_register(recorder_type, recorder_id)",
            "CREATE INDEX IF NOT EXISTS idx_register_dimensions ON work_execution_register(period, object_id, estimate_id, work_id)",
            # Timesheet indices
            "CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_foreman ON timesheets(foreman_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_object ON timesheets(object_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_estimate ON timesheets(estimate_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_timesheet ON timesheet_lines(timesheet_id)",
            "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_employee ON timesheet_lines(employee_id)",
            # Payroll register indices
            "CREATE INDEX IF NOT EXISTS idx_payroll_recorder ON payroll_register(recorder_type, recorder_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_dimensions ON payroll_register(period, object_id, estimate_id, employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_date ON payroll_register(work_date)"
        ]
        
        for index_sql in indices:
            cursor.execute(index_sql)
        
        self._connection.commit()
