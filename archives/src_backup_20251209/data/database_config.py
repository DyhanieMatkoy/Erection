"""Database configuration management for multi-backend support"""
import configparser
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Parse and validate database configuration from env.ini"""
    
    # Supported database types
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    
    # Default values
    DEFAULT_DB_TYPE = SQLITE
    DEFAULT_SQLITE_PATH = "construction.db"
    DEFAULT_POSTGRES_HOST = "localhost"
    DEFAULT_POSTGRES_PORT = 5432
    DEFAULT_MSSQL_HOST = "localhost"
    DEFAULT_MSSQL_PORT = 1433
    DEFAULT_MSSQL_DRIVER = "ODBC Driver 17 for SQL Server"
    DEFAULT_POOL_SIZE = 5
    DEFAULT_MAX_OVERFLOW = 10
    DEFAULT_POOL_TIMEOUT = 30
    DEFAULT_POOL_RECYCLE = 3600
    
    def __init__(self, config_path: str = "env.ini"):
        """Initialize database configuration from INI file
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.db_type = self.DEFAULT_DB_TYPE
        self.config_data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from INI file"""
        config = configparser.ConfigParser()
        
        # Check if config file exists
        if not Path(self.config_path).exists():
            logger.warning(f"Configuration file {self.config_path} not found. Using defaults.")
            self._set_defaults()
            return
        
        try:
            config.read(self.config_path, encoding='utf-8')
            
            # Check if Database section exists
            if not config.has_section('Database'):
                logger.warning("No [Database] section in config file. Using defaults.")
                self._set_defaults()
                return
            
            # Read database type
            self.db_type = config.get('Database', 'type', fallback=self.DEFAULT_DB_TYPE).lower()
            
            # Validate database type
            if self.db_type not in [self.SQLITE, self.POSTGRESQL, self.MSSQL]:
                logger.warning(f"Invalid database type '{self.db_type}'. Defaulting to SQLite.")
                self.db_type = self.DEFAULT_DB_TYPE
            
            # Load configuration based on database type
            if self.db_type == self.SQLITE:
                self._load_sqlite_config(config)
            elif self.db_type == self.POSTGRESQL:
                self._load_postgresql_config(config)
            elif self.db_type == self.MSSQL:
                self._load_mssql_config(config)
            
            logger.info(f"Database configuration loaded: type={self.db_type}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}. Using defaults.")
            self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default configuration (SQLite)"""
        self.db_type = self.DEFAULT_DB_TYPE
        self.config_data = {
            'db_path': self.DEFAULT_SQLITE_PATH
        }
    
    def _load_sqlite_config(self, config: configparser.ConfigParser) -> None:
        """Load SQLite configuration"""
        self.config_data = {
            'db_path': config.get('Database', 'sqlite_path', 
                                  fallback=self.DEFAULT_SQLITE_PATH)
        }
    
    def _load_postgresql_config(self, config: configparser.ConfigParser) -> None:
        """Load PostgreSQL configuration"""
        self.config_data = {
            'host': config.get('Database', 'postgres_host', 
                              fallback=self.DEFAULT_POSTGRES_HOST),
            'port': config.getint('Database', 'postgres_port', 
                                 fallback=self.DEFAULT_POSTGRES_PORT),
            'database': config.get('Database', 'postgres_database', fallback='construction'),
            'user': config.get('Database', 'postgres_user', fallback='postgres'),
            'password': config.get('Database', 'postgres_password', fallback=''),
            'pool_size': config.getint('Database', 'pool_size', 
                                      fallback=self.DEFAULT_POOL_SIZE),
            'max_overflow': config.getint('Database', 'max_overflow', 
                                         fallback=self.DEFAULT_MAX_OVERFLOW),
            'pool_timeout': config.getint('Database', 'pool_timeout', 
                                         fallback=self.DEFAULT_POOL_TIMEOUT),
            'pool_recycle': config.getint('Database', 'pool_recycle', 
                                         fallback=self.DEFAULT_POOL_RECYCLE)
        }
    
    def _load_mssql_config(self, config: configparser.ConfigParser) -> None:
        """Load MSSQL configuration"""
        self.config_data = {
            'host': config.get('Database', 'mssql_host', 
                              fallback=self.DEFAULT_MSSQL_HOST),
            'port': config.getint('Database', 'mssql_port', 
                                 fallback=self.DEFAULT_MSSQL_PORT),
            'database': config.get('Database', 'mssql_database', fallback='construction'),
            'user': config.get('Database', 'mssql_user', fallback='sa'),
            'password': config.get('Database', 'mssql_password', fallback=''),
            'driver': config.get('Database', 'mssql_driver', 
                                fallback=self.DEFAULT_MSSQL_DRIVER),
            'pool_size': config.getint('Database', 'pool_size', 
                                      fallback=self.DEFAULT_POOL_SIZE),
            'max_overflow': config.getint('Database', 'max_overflow', 
                                         fallback=self.DEFAULT_MAX_OVERFLOW),
            'pool_timeout': config.getint('Database', 'pool_timeout', 
                                         fallback=self.DEFAULT_POOL_TIMEOUT),
            'pool_recycle': config.getint('Database', 'pool_recycle', 
                                         fallback=self.DEFAULT_POOL_RECYCLE)
        }
    
    def get_db_type(self) -> str:
        """Get the configured database type"""
        return self.db_type
    
    def get_config_data(self) -> Dict[str, Any]:
        """Get the configuration data dictionary"""
        return self.config_data.copy()
    
    def is_sqlite(self) -> bool:
        """Check if SQLite is configured"""
        return self.db_type == self.SQLITE
    
    def is_postgresql(self) -> bool:
        """Check if PostgreSQL is configured"""
        return self.db_type == self.POSTGRESQL
    
    def is_mssql(self) -> bool:
        """Check if MSSQL is configured"""
        return self.db_type == self.MSSQL
    
    def validate(self) -> bool:
        """Validate the configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if self.db_type == self.SQLITE:
            return 'db_path' in self.config_data
        
        elif self.db_type == self.POSTGRESQL:
            required_fields = ['host', 'port', 'database', 'user']
            return all(field in self.config_data for field in required_fields)
        
        elif self.db_type == self.MSSQL:
            required_fields = ['host', 'port', 'database', 'user', 'driver']
            return all(field in self.config_data for field in required_fields)
        
        return False
