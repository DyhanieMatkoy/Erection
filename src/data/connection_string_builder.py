"""Connection string builder for different database backends"""
import urllib.parse
from typing import Dict, Any


class ConnectionStringBuilder:
    """Build database connection strings for different backends"""
    
    @staticmethod
    def build_sqlite(db_path: str) -> str:
        """Build SQLite connection string
        
        Args:
            db_path: Path to the SQLite database file
            
        Returns:
            SQLite connection string
            
        Example:
            >>> ConnectionStringBuilder.build_sqlite("construction.db")
            'sqlite:///construction.db'
        """
        return f"sqlite:///{db_path}"
    
    @staticmethod
    def build_postgresql(host: str, port: int, database: str, 
                        user: str, password: str) -> str:
        """Build PostgreSQL connection string
        
        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Username for authentication
            password: Password for authentication
            
        Returns:
            PostgreSQL connection string
            
        Example:
            >>> ConnectionStringBuilder.build_postgresql(
            ...     "localhost", 5432, "construction", "postgres", "secret"
            ... )
            'postgresql://postgres:secret@localhost:5432/construction'
        """
        # URL-encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
    
    @staticmethod
    def build_mssql(host: str, port: int, database: str,
                   user: str, password: str, driver: str) -> str:
        """Build MSSQL connection string
        
        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Username for authentication
            password: Password for authentication
            driver: ODBC driver name (e.g., "ODBC Driver 17 for SQL Server")
            
        Returns:
            MSSQL connection string
            
        Example:
            >>> ConnectionStringBuilder.build_mssql(
            ...     "localhost", 1433, "construction", "sa", "secret",
            ...     "ODBC Driver 17 for SQL Server"
            ... )
            'mssql+pyodbc://sa:secret@localhost:1433/construction?driver=ODBC+Driver+17+for+SQL+Server'
        """
        # URL-encode the password and driver to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        encoded_driver = urllib.parse.quote_plus(driver)
        
        return (f"mssql+pyodbc://{user}:{encoded_password}@{host}:{port}/"
                f"{database}?driver={encoded_driver}")
    
    @staticmethod
    def build_from_config(db_type: str, config_data: Dict[str, Any]) -> str:
        """Build connection string from configuration data
        
        Args:
            db_type: Database type ('sqlite', 'postgresql', or 'mssql')
            config_data: Configuration dictionary
            
        Returns:
            Connection string for the specified database type
            
        Raises:
            ValueError: If database type is not supported or required fields are missing
        """
        db_type = db_type.lower()
        
        if db_type == 'sqlite':
            if 'db_path' not in config_data:
                raise ValueError("SQLite configuration requires 'db_path'")
            return ConnectionStringBuilder.build_sqlite(config_data['db_path'])
        
        elif db_type == 'postgresql':
            required_fields = ['host', 'port', 'database', 'user', 'password']
            missing_fields = [f for f in required_fields if f not in config_data]
            if missing_fields:
                raise ValueError(f"PostgreSQL configuration missing fields: {missing_fields}")
            
            return ConnectionStringBuilder.build_postgresql(
                config_data['host'],
                config_data['port'],
                config_data['database'],
                config_data['user'],
                config_data['password']
            )
        
        elif db_type == 'mssql':
            required_fields = ['host', 'port', 'database', 'user', 'password', 'driver']
            missing_fields = [f for f in required_fields if f not in config_data]
            if missing_fields:
                raise ValueError(f"MSSQL configuration missing fields: {missing_fields}")
            
            return ConnectionStringBuilder.build_mssql(
                config_data['host'],
                config_data['port'],
                config_data['database'],
                config_data['user'],
                config_data['password'],
                config_data['driver']
            )
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
