"""Tests for database configuration system

This test suite verifies the database configuration system implementation
for multi-database support (SQLite, PostgreSQL, MSSQL).
"""
import sys
import os
import tempfile
import configparser
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.database_config import DatabaseConfig
from data.connection_string_builder import ConnectionStringBuilder


def test_sqlite_default_configuration():
    """Test that SQLite is used by default with sensible defaults"""
    # Test with non-existent config file
    config = DatabaseConfig("nonexistent_file.ini")
    
    assert config.get_db_type() == "sqlite"
    assert config.is_sqlite()
    assert config.validate()
    
    config_data = config.get_config_data()
    assert config_data['db_path'] == "construction.db"
    
    print("✓ SQLite default configuration works")


def test_sqlite_configuration_from_file():
    """Test SQLite configuration from env.ini"""
    config = DatabaseConfig("env.ini")
    
    assert config.get_db_type() == "sqlite"
    assert config.is_sqlite()
    assert not config.is_postgresql()
    assert not config.is_mssql()
    assert config.validate()
    
    config_data = config.get_config_data()
    assert 'db_path' in config_data
    
    print("✓ SQLite configuration from file works")


def test_postgresql_configuration():
    """Test PostgreSQL configuration parsing"""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[Database]
type = postgresql
postgres_host = db.example.com
postgres_port = 5433
postgres_database = mydb
postgres_user = dbuser
postgres_password = secret123
pool_size = 10
max_overflow = 20
pool_timeout = 60
pool_recycle = 7200
""")
        temp_file = f.name
    
    try:
        config = DatabaseConfig(temp_file)
        
        assert config.get_db_type() == "postgresql"
        assert config.is_postgresql()
        assert config.validate()
        
        config_data = config.get_config_data()
        assert config_data['host'] == "db.example.com"
        assert config_data['port'] == 5433
        assert config_data['database'] == "mydb"
        assert config_data['user'] == "dbuser"
        assert config_data['password'] == "secret123"
        assert config_data['pool_size'] == 10
        assert config_data['max_overflow'] == 20
        assert config_data['pool_timeout'] == 60
        assert config_data['pool_recycle'] == 7200
        
        print("✓ PostgreSQL configuration parsing works")
    finally:
        os.unlink(temp_file)


def test_mssql_configuration():
    """Test MSSQL configuration parsing"""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[Database]
type = mssql
mssql_host = sqlserver.example.com
mssql_port = 1434
mssql_database = construction_db
mssql_user = sa
mssql_password = P@ssw0rd
mssql_driver = ODBC Driver 18 for SQL Server
pool_size = 8
max_overflow = 15
pool_timeout = 45
pool_recycle = 5400
""")
        temp_file = f.name
    
    try:
        config = DatabaseConfig(temp_file)
        
        assert config.get_db_type() == "mssql"
        assert config.is_mssql()
        assert config.validate()
        
        config_data = config.get_config_data()
        assert config_data['host'] == "sqlserver.example.com"
        assert config_data['port'] == 1434
        assert config_data['database'] == "construction_db"
        assert config_data['user'] == "sa"
        assert config_data['password'] == "P@ssw0rd"
        assert config_data['driver'] == "ODBC Driver 18 for SQL Server"
        assert config_data['pool_size'] == 8
        assert config_data['max_overflow'] == 15
        assert config_data['pool_timeout'] == 45
        assert config_data['pool_recycle'] == 5400
        
        print("✓ MSSQL configuration parsing works")
    finally:
        os.unlink(temp_file)


def test_invalid_database_type_defaults_to_sqlite():
    """Test that invalid database type defaults to SQLite"""
    # Create temporary config file with invalid type
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[Database]
type = mongodb
""")
        temp_file = f.name
    
    try:
        config = DatabaseConfig(temp_file)
        
        # Should default to SQLite
        assert config.get_db_type() == "sqlite"
        assert config.is_sqlite()
        assert config.validate()
        
        print("✓ Invalid database type defaults to SQLite")
    finally:
        os.unlink(temp_file)


def test_connection_string_builder_sqlite():
    """Test SQLite connection string builder"""
    conn_str = ConnectionStringBuilder.build_sqlite("test.db")
    assert conn_str == "sqlite:///test.db"
    
    conn_str = ConnectionStringBuilder.build_sqlite("path/to/database.db")
    assert conn_str == "sqlite:///path/to/database.db"
    
    print("✓ SQLite connection string builder works")


def test_connection_string_builder_postgresql():
    """Test PostgreSQL connection string builder"""
    conn_str = ConnectionStringBuilder.build_postgresql(
        "localhost", 5432, "testdb", "user", "pass"
    )
    assert conn_str == "postgresql://user:pass@localhost:5432/testdb"
    
    # Test with special characters in password
    conn_str = ConnectionStringBuilder.build_postgresql(
        "db.example.com", 5433, "mydb", "admin", "p@ss#word!"
    )
    assert "postgresql://admin:" in conn_str
    assert "@db.example.com:5433/mydb" in conn_str
    # Password should be URL-encoded
    assert "p@ss#word!" not in conn_str
    
    print("✓ PostgreSQL connection string builder works")


def test_connection_string_builder_mssql():
    """Test MSSQL connection string builder"""
    conn_str = ConnectionStringBuilder.build_mssql(
        "localhost", 1433, "testdb", "sa", "pass",
        "ODBC Driver 17 for SQL Server"
    )
    assert "mssql+pyodbc://sa:" in conn_str
    assert "@localhost:1433/testdb" in conn_str
    assert "driver=ODBC+Driver+17+for+SQL+Server" in conn_str
    
    print("✓ MSSQL connection string builder works")


def test_connection_string_from_config():
    """Test building connection string from config"""
    # Test SQLite
    conn_str = ConnectionStringBuilder.build_from_config(
        "sqlite", {"db_path": "test.db"}
    )
    assert conn_str == "sqlite:///test.db"
    
    # Test PostgreSQL
    conn_str = ConnectionStringBuilder.build_from_config(
        "postgresql",
        {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "user",
            "password": "pass"
        }
    )
    assert "postgresql://user:pass@localhost:5432/testdb" == conn_str
    
    # Test MSSQL
    conn_str = ConnectionStringBuilder.build_from_config(
        "mssql",
        {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
            "user": "sa",
            "password": "pass",
            "driver": "ODBC Driver 17 for SQL Server"
        }
    )
    assert "mssql+pyodbc://sa:pass@localhost:1433/testdb" in conn_str
    
    print("✓ Connection string from config works")


def test_pool_settings_defaults():
    """Test that pool settings have sensible defaults"""
    # Create config without pool settings
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = testdb
postgres_user = user
postgres_password = pass
""")
        temp_file = f.name
    
    try:
        config = DatabaseConfig(temp_file)
        config_data = config.get_config_data()
        
        # Check defaults
        assert config_data['pool_size'] == 5
        assert config_data['max_overflow'] == 10
        assert config_data['pool_timeout'] == 30
        assert config_data['pool_recycle'] == 3600
        
        print("✓ Pool settings have sensible defaults")
    finally:
        os.unlink(temp_file)


def test_missing_database_section():
    """Test handling of missing Database section"""
    # Create config without Database section
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[Auth]
login = admin
password = admin
""")
        temp_file = f.name
    
    try:
        config = DatabaseConfig(temp_file)
        
        # Should default to SQLite
        assert config.get_db_type() == "sqlite"
        assert config.validate()
        
        print("✓ Missing Database section defaults to SQLite")
    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    print("Testing Database Configuration System")
    print("=" * 60)
    
    try:
        test_sqlite_default_configuration()
        test_sqlite_configuration_from_file()
        test_postgresql_configuration()
        test_mssql_configuration()
        test_invalid_database_type_defaults_to_sqlite()
        test_connection_string_builder_sqlite()
        test_connection_string_builder_postgresql()
        test_connection_string_builder_mssql()
        test_connection_string_from_config()
        test_pool_settings_defaults()
        test_missing_database_section()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
