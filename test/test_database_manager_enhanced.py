"""Tests for enhanced DatabaseManager with SQLAlchemy support"""
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import text

from src.data.database_manager import DatabaseManager
from src.data.exceptions import DatabaseConnectionError, DatabaseOperationError


class TestDatabaseManagerEnhanced:
    """Test enhanced DatabaseManager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Reset singleton instance
        DatabaseManager._instance = None
        
    def test_initialize_with_config_file(self):
        """Test initialization with configuration file"""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = sqlite\n')
            f.write('sqlite_path = test_construction.db\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            result = db_manager.initialize(config_path)
            
            assert result is True
            assert db_manager._engine is not None
            assert db_manager._session_factory is not None
            
            # Clean up connections
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            os.unlink(config_path)
            if os.path.exists('test_construction.db'):
                try:
                    os.unlink('test_construction.db')
                except PermissionError:
                    pass  # File still locked, will be cleaned up later
    
    def test_initialize_legacy_mode(self):
        """Test backward compatibility with direct database path"""
        db_manager = DatabaseManager()
        result = db_manager.initialize('test_legacy.db')
        
        try:
            assert result is True
            assert db_manager._connection is not None
            assert db_manager._engine is not None
            assert db_manager._session_factory is not None
            
            # Clean up connections
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_legacy.db'):
                try:
                    os.unlink('test_legacy.db')
                except PermissionError:
                    pass
    
    def test_get_engine(self):
        """Test getting SQLAlchemy engine"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_engine.db')
        
        try:
            engine = db_manager.get_engine()
            assert engine is not None
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_engine.db'):
                try:
                    os.unlink('test_engine.db')
                except PermissionError:
                    pass
    
    def test_get_engine_not_initialized(self):
        """Test getting engine before initialization raises error"""
        db_manager = DatabaseManager()
        
        with pytest.raises(DatabaseConnectionError):
            db_manager.get_engine()
    
    def test_get_session(self):
        """Test getting SQLAlchemy session"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_session.db')
        
        try:
            session = db_manager.get_session()
            assert session is not None
            session.close()
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_session.db'):
                try:
                    os.unlink('test_session.db')
                except PermissionError:
                    pass
    
    def test_get_session_not_initialized(self):
        """Test getting session before initialization raises error"""
        db_manager = DatabaseManager()
        
        with pytest.raises(DatabaseConnectionError):
            db_manager.get_session()
    
    def test_session_scope_commit(self):
        """Test session_scope context manager commits on success"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_scope.db')
        
        try:
            # Use session scope to execute a query
            with db_manager.session_scope() as session:
                result = session.execute(text("SELECT 1"))
                assert result is not None
            
            # Session should be closed after context
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_scope.db'):
                try:
                    os.unlink('test_scope.db')
                except PermissionError:
                    pass
    
    def test_session_scope_rollback(self):
        """Test session_scope context manager rolls back on error"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_rollback.db')
        
        try:
            # Attempt to execute invalid SQL
            with pytest.raises(DatabaseOperationError):
                with db_manager.session_scope() as session:
                    session.execute(text("INVALID SQL STATEMENT"))
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_rollback.db'):
                try:
                    os.unlink('test_rollback.db')
                except PermissionError:
                    pass
    
    def test_get_connection_backward_compatibility(self):
        """Test backward compatibility with get_connection()"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_compat.db')
        
        try:
            connection = db_manager.get_connection()
            assert connection is not None
            
            # Test that we can execute queries
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result is not None
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_compat.db'):
                try:
                    os.unlink('test_compat.db')
                except PermissionError:
                    pass
    
    def test_singleton_pattern(self):
        """Test that DatabaseManager follows singleton pattern"""
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        
        assert db_manager1 is db_manager2
    
    def test_invalid_config_falls_back_to_sqlite(self):
        """Test that invalid configuration falls back to SQLite"""
        # Create a config file with invalid database type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = invalid_db_type\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            result = db_manager.initialize(config_path)
            
            # Should fall back to SQLite
            assert result is True
            assert db_manager._connection is not None
            
        finally:
            os.unlink(config_path)
            if os.path.exists('construction.db'):
                # Don't delete the main database if it exists
                pass
    
    def test_connection_pooling_config_postgresql(self):
        """Test that PostgreSQL configuration includes pooling settings"""
        # Create a config file for PostgreSQL
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = postgresql\n')
            f.write('postgres_host = localhost\n')
            f.write('postgres_port = 5432\n')
            f.write('postgres_database = test_db\n')
            f.write('postgres_user = test_user\n')
            f.write('postgres_password = test_pass\n')
            f.write('pool_size = 10\n')
            f.write('max_overflow = 20\n')
            f.write('pool_timeout = 60\n')
            f.write('pool_recycle = 7200\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            
            # This will fail to connect (no actual PostgreSQL server)
            # but we can verify the configuration was loaded
            try:
                db_manager.initialize(config_path)
            except DatabaseConnectionError:
                # Expected - no actual PostgreSQL server
                pass
            
            # Verify config was loaded
            assert db_manager._config is not None
            assert db_manager._config.is_postgresql()
            config_data = db_manager._config.get_config_data()
            assert config_data['pool_size'] == 10
            assert config_data['max_overflow'] == 20
            assert config_data['pool_timeout'] == 60
            assert config_data['pool_recycle'] == 7200
            
        finally:
            os.unlink(config_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
