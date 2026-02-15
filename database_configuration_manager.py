"""Database Configuration Manager

This module manages database configurations for different database types
(PostgreSQL, MySQL, SQLite) in the multi-database testing framework.
"""

import os
import sys
import json
import logging
import configparser
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class DatabaseType(Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class DatabaseConfig:
    """Database configuration data class"""
    db_type: DatabaseType
    connection_string: str
    driver: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None


class DatabaseConfigurationManager:
    """Manages database configurations for multi-database testing"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize database configuration manager
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
        # Database configuration templates
        self.db_configs = {
            DatabaseType.POSTGRESQL: {
                'driver': 'psycopg2',
                'default_port': 5432,
                'connection_template': 'postgresql://{username}:{password}@{host}:{port}/{database}',
                'test_database': 'construction_test_db',
                'test_user': 'test_user',
                'test_password': 'test_password'
            },
            DatabaseType.MYSQL: {
                'driver': 'pymysql',
                'default_port': 3306,
                'connection_template': 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}',
                'test_database': 'construction_test_db',
                'test_user': 'test_user',
                'test_password': 'test_password'
            },
            DatabaseType.SQLITE: {
                'driver': 'sqlite3',
                'default_port': None,
                'connection_template': 'sqlite:///{database_path}',
                'test_database': None,
                'test_user': None,
                'test_password': None
            }
        }
        
        # Current configurations
        self.server_config: Optional[DatabaseConfig] = None
        self.client_configs: Dict[str, DatabaseConfig] = {}
        
        self.logger.info("Database configuration manager initialized")
    
    def create_server_config(self, db_type: DatabaseType, **kwargs) -> DatabaseConfig:
        """Create server database configuration
        
        Args:
            db_type: Type of database
            **kwargs: Additional configuration parameters
            
        Returns:
            DatabaseConfig instance for server
        """
        try:
            self.logger.info(f"Creating server configuration for {db_type.value}")
            
            config_template = self.db_configs[db_type]
            
            if db_type == DatabaseType.SQLITE:
                # SQLite configuration
                database_path = kwargs.get('database_path', 'test_databases/server_test.db')
                
                # Ensure directory exists
                Path(database_path).parent.mkdir(parents=True, exist_ok=True)
                
                config = DatabaseConfig(
                    db_type=db_type,
                    connection_string=config_template['connection_template'].format(
                        database_path=database_path
                    ),
                    driver=config_template['driver'],
                    additional_params={'database_path': database_path}
                )
                
            else:
                # PostgreSQL or MySQL configuration
                host = kwargs.get('host', 'localhost')
                port = kwargs.get('port', config_template['default_port'])
                database = kwargs.get('database', config_template['test_database'])
                username = kwargs.get('username', config_template['test_user'])
                password = kwargs.get('password', config_template['test_password'])
                
                config = DatabaseConfig(
                    db_type=db_type,
                    connection_string=config_template['connection_template'].format(
                        username=username,
                        password=password,
                        host=host,
                        port=port,
                        database=database
                    ),
                    driver=config_template['driver'],
                    host=host,
                    port=port,
                    database=database,
                    username=username,
                    password=password
                )
            
            self.server_config = config
            self.logger.info(f"Server configuration created: {db_type.value}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to create server config for {db_type.value}: {e}")
            raise
    
    def create_client_config(self, client_id: str, db_type: DatabaseType, **kwargs) -> DatabaseConfig:
        """Create desktop client database configuration
        
        Args:
            client_id: Unique client identifier
            db_type: Type of database
            **kwargs: Additional configuration parameters
            
        Returns:
            DatabaseConfig instance for client
        """
        try:
            self.logger.info(f"Creating client configuration for {client_id} ({db_type.value})")
            
            config_template = self.db_configs[db_type]
            
            if db_type == DatabaseType.SQLITE:
                # SQLite configuration for client
                database_path = kwargs.get('database_path', f'test_databases/{client_id}_test.db')
                
                # Ensure directory exists
                Path(database_path).parent.mkdir(parents=True, exist_ok=True)
                
                config = DatabaseConfig(
                    db_type=db_type,
                    connection_string=config_template['connection_template'].format(
                        database_path=database_path
                    ),
                    driver=config_template['driver'],
                    additional_params={'database_path': database_path}
                )
                
            else:
                # PostgreSQL or MySQL configuration for client
                host = kwargs.get('host', 'localhost')
                port = kwargs.get('port', config_template['default_port'])
                database = kwargs.get('database', f"{config_template['test_database']}_{client_id}")
                username = kwargs.get('username', config_template['test_user'])
                password = kwargs.get('password', config_template['test_password'])
                
                config = DatabaseConfig(
                    db_type=db_type,
                    connection_string=config_template['connection_template'].format(
                        username=username,
                        password=password,
                        host=host,
                        port=port,
                        database=database
                    ),
                    driver=config_template['driver'],
                    host=host,
                    port=port,
                    database=database,
                    username=username,
                    password=password
                )
            
            self.client_configs[client_id] = config
            self.logger.info(f"Client configuration created: {client_id} ({db_type.value})")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to create client config for {client_id} ({db_type.value}): {e}")
            raise
    
    def get_server_config(self) -> Optional[DatabaseConfig]:
        """Get current server database configuration
        
        Returns:
            Server DatabaseConfig or None if not set
        """
        return self.server_config
    
    def get_client_config(self, client_id: str) -> Optional[DatabaseConfig]:
        """Get client database configuration
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client DatabaseConfig or None if not found
        """
        return self.client_configs.get(client_id)
    
    def get_all_client_configs(self) -> Dict[str, DatabaseConfig]:
        """Get all client database configurations
        
        Returns:
            Dictionary of client configurations
        """
        return self.client_configs.copy()
    
    def validate_database_connectivity(self, config: DatabaseConfig) -> Tuple[bool, Optional[str]]:
        """Validate database connectivity for given configuration
        
        Args:
            config: Database configuration to validate
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.debug(f"Validating connectivity for {config.db_type.value}")
            
            if config.db_type == DatabaseType.SQLITE:
                # For SQLite, just check if we can create/access the file
                database_path = config.additional_params['database_path']
                
                # Try to create a connection
                import sqlite3
                conn = sqlite3.connect(database_path)
                conn.execute("SELECT 1")
                conn.close()
                
                return True, None
                
            elif config.db_type == DatabaseType.POSTGRESQL:
                # Test PostgreSQL connection
                import psycopg2
                
                conn = psycopg2.connect(
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    user=config.username,
                    password=config.password
                )
                conn.close()
                
                return True, None
                
            elif config.db_type == DatabaseType.MYSQL:
                # Test MySQL connection
                import pymysql
                
                conn = pymysql.connect(
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    user=config.username,
                    password=config.password
                )
                conn.close()
                
                return True, None
            
            else:
                return False, f"Unsupported database type: {config.db_type}"
                
        except ImportError as e:
            error_msg = f"Database driver not available: {e}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Database connectivity test failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def setup_database_for_testing(self, config: DatabaseConfig) -> bool:
        """Setup database for testing (create database, user, etc.)
        
        Args:
            config: Database configuration
            
        Returns:
            True if setup successful
        """
        try:
            self.logger.info(f"Setting up database for testing: {config.db_type.value}")
            
            if config.db_type == DatabaseType.SQLITE:
                # SQLite setup - just ensure directory exists
                database_path = config.additional_params['database_path']
                Path(database_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Create empty database file
                import sqlite3
                conn = sqlite3.connect(database_path)
                conn.close()
                
                return True
                
            elif config.db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL setup
                return self._setup_postgresql_database(config)
                
            elif config.db_type == DatabaseType.MYSQL:
                # MySQL setup
                return self._setup_mysql_database(config)
            
            else:
                self.logger.error(f"Unsupported database type for setup: {config.db_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database setup failed for {config.db_type.value}: {e}")
            return False
    
    def _setup_postgresql_database(self, config: DatabaseConfig) -> bool:
        """Setup PostgreSQL database for testing"""
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect to PostgreSQL server (not specific database)
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user='postgres',  # Assume postgres superuser for setup
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config.database}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE DATABASE {config.database}")
                self.logger.debug(f"Created PostgreSQL database: {config.database}")
            
            # Create user if it doesn't exist
            cursor.execute(f"SELECT 1 FROM pg_user WHERE usename = '{config.username}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE USER {config.username} WITH PASSWORD '{config.password}'")
                self.logger.debug(f"Created PostgreSQL user: {config.username}")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {config.database} TO {config.username}")
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"PostgreSQL database setup completed: {config.database}")
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL setup failed: {e}")
            return False
    
    def _setup_mysql_database(self, config: DatabaseConfig) -> bool:
        """Setup MySQL database for testing"""
        try:
            import pymysql
            
            # Connect to MySQL server (not specific database)
            conn = pymysql.connect(
                host=config.host,
                port=config.port,
                user='root',  # Assume root user for setup
                password=os.getenv('MYSQL_ROOT_PASSWORD', 'root')
            )
            
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.database}")
            self.logger.debug(f"Created MySQL database: {config.database}")
            
            # Create user if it doesn't exist
            cursor.execute(f"CREATE USER IF NOT EXISTS '{config.username}'@'localhost' IDENTIFIED BY '{config.password}'")
            self.logger.debug(f"Created MySQL user: {config.username}")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {config.database}.* TO '{config.username}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"MySQL database setup completed: {config.database}")
            return True
            
        except Exception as e:
            self.logger.error(f"MySQL setup failed: {e}")
            return False
    
    def cleanup_database(self, config: DatabaseConfig) -> bool:
        """Clean up database after testing
        
        Args:
            config: Database configuration to clean up
            
        Returns:
            True if cleanup successful
        """
        try:
            self.logger.info(f"Cleaning up database: {config.db_type.value}")
            
            if config.db_type == DatabaseType.SQLITE:
                # SQLite cleanup - remove database file
                database_path = config.additional_params['database_path']
                if os.path.exists(database_path):
                    os.remove(database_path)
                    self.logger.debug(f"Removed SQLite database: {database_path}")
                
                return True
                
            elif config.db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL cleanup
                return self._cleanup_postgresql_database(config)
                
            elif config.db_type == DatabaseType.MYSQL:
                # MySQL cleanup
                return self._cleanup_mysql_database(config)
            
            else:
                self.logger.warning(f"No cleanup procedure for database type: {config.db_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"Database cleanup failed for {config.db_type.value}: {e}")
            return False
    
    def _cleanup_postgresql_database(self, config: DatabaseConfig) -> bool:
        """Clean up PostgreSQL database"""
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user='postgres',
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Drop database
            cursor.execute(f"DROP DATABASE IF EXISTS {config.database}")
            self.logger.debug(f"Dropped PostgreSQL database: {config.database}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL cleanup failed: {e}")
            return False
    
    def _cleanup_mysql_database(self, config: DatabaseConfig) -> bool:
        """Clean up MySQL database"""
        try:
            import pymysql
            
            # Connect to MySQL server
            conn = pymysql.connect(
                host=config.host,
                port=config.port,
                user='root',
                password=os.getenv('MYSQL_ROOT_PASSWORD', 'root')
            )
            
            cursor = conn.cursor()
            
            # Drop database
            cursor.execute(f"DROP DATABASE IF EXISTS {config.database}")
            self.logger.debug(f"Dropped MySQL database: {config.database}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"MySQL cleanup failed: {e}")
            return False
    
    def save_configuration_to_file(self, file_path: str) -> bool:
        """Save current configurations to file
        
        Args:
            file_path: Path to save configuration file
            
        Returns:
            True if saved successfully
        """
        try:
            config_data = {
                'server_config': self._config_to_dict(self.server_config) if self.server_config else None,
                'client_configs': {
                    client_id: self._config_to_dict(config)
                    for client_id, config in self.client_configs.items()
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {file_path}: {e}")
            return False
    
    def load_configuration_from_file(self, file_path: str) -> bool:
        """Load configurations from file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            # Load server config
            if config_data.get('server_config'):
                self.server_config = self._dict_to_config(config_data['server_config'])
            
            # Load client configs
            self.client_configs = {}
            for client_id, config_dict in config_data.get('client_configs', {}).items():
                self.client_configs[client_id] = self._dict_to_config(config_dict)
            
            self.logger.info(f"Configuration loaded from: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {file_path}: {e}")
            return False
    
    def _config_to_dict(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Convert DatabaseConfig to dictionary"""
        return {
            'db_type': config.db_type.value,
            'connection_string': config.connection_string,
            'driver': config.driver,
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'username': config.username,
            'password': config.password,
            'additional_params': config.additional_params
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> DatabaseConfig:
        """Convert dictionary to DatabaseConfig"""
        return DatabaseConfig(
            db_type=DatabaseType(config_dict['db_type']),
            connection_string=config_dict['connection_string'],
            driver=config_dict['driver'],
            host=config_dict.get('host'),
            port=config_dict.get('port'),
            database=config_dict.get('database'),
            username=config_dict.get('username'),
            password=config_dict.get('password'),
            additional_params=config_dict.get('additional_params')
        )
    
    def get_database_type_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get data type mappings between different database types
        
        Returns:
            Dictionary of database type mappings
        """
        return {
            'postgresql_to_sqlite': {
                'SERIAL': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'VARCHAR(n)': 'TEXT',
                'TIMESTAMP': 'DATETIME',
                'BOOLEAN': 'INTEGER',
                'INTEGER': 'INTEGER',
                'TEXT': 'TEXT',
                'REAL': 'REAL'
            },
            'mysql_to_sqlite': {
                'AUTO_INCREMENT': 'AUTOINCREMENT',
                'VARCHAR(n)': 'TEXT',
                'DATETIME': 'DATETIME',
                'TINYINT(1)': 'INTEGER',
                'INT': 'INTEGER',
                'TEXT': 'TEXT',
                'DECIMAL': 'REAL'
            },
            'sqlite_to_mysql': {
                'AUTOINCREMENT': 'AUTO_INCREMENT',
                'TEXT': 'VARCHAR(255)',
                'DATETIME': 'DATETIME',
                'INTEGER': 'INT',
                'REAL': 'DECIMAL(10,2)'
            },
            'sqlite_to_postgresql': {
                'AUTOINCREMENT': 'SERIAL',
                'TEXT': 'VARCHAR(255)',
                'DATETIME': 'TIMESTAMP',
                'INTEGER': 'INTEGER',
                'REAL': 'REAL'
            },
            'mysql_to_postgresql': {
                'AUTO_INCREMENT': 'SERIAL',
                'VARCHAR(n)': 'VARCHAR(n)',
                'DATETIME': 'TIMESTAMP',
                'TINYINT(1)': 'BOOLEAN',
                'INT': 'INTEGER',
                'TEXT': 'TEXT',
                'DECIMAL': 'DECIMAL'
            },
            'postgresql_to_mysql': {
                'SERIAL': 'INT AUTO_INCREMENT',
                'VARCHAR(n)': 'VARCHAR(n)',
                'TIMESTAMP': 'DATETIME',
                'BOOLEAN': 'TINYINT(1)',
                'INTEGER': 'INT',
                'TEXT': 'TEXT',
                'REAL': 'DECIMAL(10,2)'
            }
        }