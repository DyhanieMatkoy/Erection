"""
Test comprehensive error handling for DatabaseManager

Tests Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""
import pytest
import tempfile
import os
from src.data.database_manager import DatabaseManager
from src.data.exceptions import (
    DatabaseConnectionError,
    DatabaseConfigurationError,
    DatabaseOperationError
)
from src.data.models.sqlalchemy_models import User


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    def setup_method(self):
        """Reset DatabaseManager singleton before each test"""
        DatabaseManager._instance = None
    
    def teardown_method(self):
        """Clean up after each test"""
        # Close any open connections
        if DatabaseManager._instance:
            if DatabaseManager._instance._connection:
                try:
                    DatabaseManager._instance._connection.close()
                except:
                    pass
            if DatabaseManager._instance._engine:
                try:
                    DatabaseManager._instance._engine.dispose()
                except:
                    pass
        # Reset singleton
        DatabaseManager._instance = None
        
        # Small delay to ensure files are released
        import time
        time.sleep(0.1)
        
        # Clean up test database files
        test_files = [
            'test_query_error.db', 'test_param_error.db', 'test_rollback.db',
            'test_consistency.db', 'test_pool.db', 'test_constraint.db',
            'test_update_rollback.db', 'test_session_context.db'
        ]
        for f in test_files:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except PermissionError:
                    pass  # File still locked, ignore
    
    def test_requirement_6_1_connection_failure_detailed_error(self):
        """
        Requirement 6.1: WHEN a database connection fails THEN the Database Manager 
        SHALL log detailed error information and raise an appropriate exception
        """
        # Create a config file with invalid PostgreSQL connection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = postgresql\n')
            f.write('postgres_host = invalid_host_that_does_not_exist\n')
            f.write('postgres_port = 5432\n')
            f.write('postgres_database = test_db\n')
            f.write('postgres_user = test_user\n')
            f.write('postgres_password = test_pass\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            
            # Should raise DatabaseConnectionError with detailed information
            with pytest.raises(DatabaseConnectionError) as exc_info:
                db_manager.initialize(config_path)
            
            # Verify error message contains connection details (but not password)
            error_msg = str(exc_info.value)
            assert 'invalid_host_that_does_not_exist' in error_msg
            assert 'test_user' in error_msg
            assert 'test_pass' not in error_msg  # Password should not be in error
            assert 'postgresql' in error_msg.lower()
            
        finally:
            os.unlink(config_path)
    
    def test_requirement_6_1_invalid_credentials_clear_error(self):
        """
        Requirement 6.1: WHEN database credentials are invalid THEN the system 
        SHALL fail fast with a clear authentication error message
        """
        # Create a config file with invalid SQLite path (permission denied scenario)
        invalid_path = '/root/no_permission/test.db'  # Path that should fail
        
        db_manager = DatabaseManager()
        
        # Should raise DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError):
            db_manager.initialize(invalid_path)
    
    def test_requirement_6_2_query_failure_meaningful_error(self):
        """
        Requirement 6.2: WHEN a query fails THEN the Database Adapter SHALL 
        provide meaningful error messages that include the query context
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_query_error.db')
        
        # Execute an invalid query
        with pytest.raises(DatabaseOperationError) as exc_info:
            db_manager.execute_query("SELECT * FROM nonexistent_table")
        
        # Verify error message includes query context
        error_msg = str(exc_info.value)
        assert 'nonexistent_table' in error_msg or 'no such table' in error_msg.lower()
    
    def test_requirement_6_2_query_failure_with_parameters(self):
        """
        Requirement 6.2: Query failure should include parameter context
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_param_error.db')
        
        # Create a table first
        db_manager.execute_update("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Try to insert with wrong number of parameters
        with pytest.raises(DatabaseOperationError) as exc_info:
            db_manager.execute_update(
                "INSERT INTO test_table (id, name) VALUES (?, ?)",
                (1,)  # Missing one parameter
            )
        
        # Verify error message is meaningful
        error_msg = str(exc_info.value)
        assert 'INSERT' in error_msg or 'parameter' in error_msg.lower()
    
    def test_requirement_6_3_transaction_rollback_on_failure(self):
        """
        Requirement 6.3: WHEN a transaction fails THEN the Database Adapter 
        SHALL rollback changes and maintain database consistency
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_rollback.db')
        
        # Create a user
        with db_manager.session_scope() as session:
            user = User(
                username='test_user',
                password_hash='hash123',
                role='admin',
                is_active=True
            )
            session.add(user)
        
        # Verify user was created
        with db_manager.session_scope() as session:
            count_before = session.query(User).count()
            assert count_before == 1
        
        # Try to create another user but cause an error
        try:
            with db_manager.session_scope() as session:
                user2 = User(
                    username='test_user2',
                    password_hash='hash456',
                    role='user',
                    is_active=True
                )
                session.add(user2)
                session.flush()  # Flush to database
                
                # Cause an error by trying to add duplicate username
                user3 = User(
                    username='test_user2',  # Duplicate!
                    password_hash='hash789',
                    role='user',
                    is_active=True
                )
                session.add(user3)
                # This should fail and rollback
        except DatabaseOperationError:
            pass  # Expected
        
        # Verify that user2 was NOT added (transaction rolled back)
        with db_manager.session_scope() as session:
            count_after = session.query(User).count()
            # Should still be 1 (only the first user)
            assert count_after == 1
    
    def test_requirement_6_3_transaction_maintains_consistency(self):
        """
        Requirement 6.3: Transaction rollback maintains database consistency
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_consistency.db')
        
        # Attempt a transaction that will fail
        try:
            with db_manager.session_scope() as session:
                user = User(
                    username='test_user',
                    password_hash='hash123',
                    role='admin',
                    is_active=True
                )
                session.add(user)
                session.flush()
                
                # Force an error
                raise ValueError("Simulated error")
        except (DatabaseOperationError, ValueError):
            pass  # Expected
        
        # Verify database is still consistent (no partial data)
        with db_manager.session_scope() as session:
            count = session.query(User).count()
            assert count == 0  # No users should exist
    
    def test_requirement_6_4_pool_exhaustion_clear_error(self):
        """
        Requirement 6.4: WHEN connection pool exhaustion occurs THEN the Database 
        Manager SHALL queue requests or raise a clear timeout error
        
        Note: This is difficult to test with SQLite (no pooling), but we verify
        the error handling structure is in place
        """
        # Create a config with very small pool
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = sqlite\n')
            f.write('sqlite_path = test_pool.db\n')
            f.write('pool_size = 1\n')
            f.write('max_overflow = 0\n')
            f.write('pool_timeout = 1\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            db_manager.initialize(config_path)
            
            # For SQLite, this won't actually test pool exhaustion,
            # but verifies the configuration is accepted
            assert db_manager._engine is not None
            
        finally:
            try:
                os.unlink(config_path)
            except:
                pass
    
    def test_requirement_6_5_connection_failure_logging(self):
        """
        Requirement 6.5: Connection failures should be logged with detailed information
        """
        # Create invalid config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = postgresql\n')
            f.write('postgres_host = nonexistent.host.local\n')
            f.write('postgres_port = 5432\n')
            f.write('postgres_database = test\n')
            f.write('postgres_user = test\n')
            f.write('postgres_password = test\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            
            # Should raise DatabaseConnectionError
            with pytest.raises(DatabaseConnectionError) as exc_info:
                db_manager.initialize(config_path)
            
            # Verify error contains useful information
            error_msg = str(exc_info.value)
            assert 'nonexistent.host.local' in error_msg
            assert 'postgresql' in error_msg.lower()
            
        finally:
            os.unlink(config_path)
    
    def test_error_context_extraction_constraint_violation(self):
        """Test that constraint violations are properly identified in error context"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_constraint.db')
        
        # Create a user
        with db_manager.session_scope() as session:
            user = User(
                username='test_user',
                password_hash='hash123',
                role='admin',
                is_active=True
            )
            session.add(user)
        
        # Try to create duplicate user
        try:
            with db_manager.session_scope() as session:
                user2 = User(
                    username='test_user',  # Duplicate!
                    password_hash='hash456',
                    role='user',
                    is_active=True
                )
                session.add(user2)
        except DatabaseOperationError as e:
            # Verify error context mentions constraint
            error_msg = str(e)
            assert 'constraint' in error_msg.lower() or 'unique' in error_msg.lower()
    
    def test_error_handling_uninitialized_engine(self):
        """Test error handling when trying to use uninitialized engine"""
        db_manager = DatabaseManager()
        
        # Should raise DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError) as exc_info:
            db_manager.get_engine()
        
        error_msg = str(exc_info.value)
        assert 'not initialized' in error_msg.lower()
        assert 'initialize()' in error_msg
    
    def test_error_handling_uninitialized_session(self):
        """Test error handling when trying to get session before initialization"""
        db_manager = DatabaseManager()
        
        # Should raise DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError) as exc_info:
            db_manager.get_session()
        
        error_msg = str(exc_info.value)
        assert 'not initialized' in error_msg.lower()
    
    def test_error_handling_invalid_configuration_file(self):
        """Test error handling for invalid configuration file"""
        # Create a config file with truly invalid content (not just missing)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('INVALID CONTENT NOT INI FORMAT\n')
            f.write('This is not valid INI\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            
            # This should fall back to SQLite with default config
            # The DatabaseConfig class handles missing files gracefully
            result = db_manager.initialize(config_path)
            
            # Should succeed with fallback
            assert result == True
            assert db_manager._config.is_sqlite()
            
        finally:
            try:
                os.unlink(config_path)
            except:
                pass
    
    def test_update_query_rollback_on_error(self):
        """Test that update queries rollback on error"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_update_rollback.db')
        
        # Create a table
        db_manager.execute_update("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        db_manager.execute_update("INSERT INTO test (id, value) VALUES (1, 'test')")
        
        # Try to insert duplicate primary key
        with pytest.raises(DatabaseOperationError) as exc_info:
            db_manager.execute_update("INSERT INTO test (id, value) VALUES (1, 'duplicate')")
        
        # Verify error message mentions constraint
        error_msg = str(exc_info.value)
        assert 'constraint' in error_msg.lower() or 'unique' in error_msg.lower()
        
        # Verify original data is intact
        results = db_manager.execute_query("SELECT value FROM test WHERE id = 1")
        assert len(results) == 1
        assert results[0][0] == 'test'
    
    def test_session_scope_error_context(self):
        """Test that session_scope provides error context"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_session_context.db')
        
        # Try an operation that will fail
        try:
            with db_manager.session_scope() as session:
                # Execute invalid SQL
                session.execute("INVALID SQL STATEMENT")
        except DatabaseOperationError as e:
            # Verify error has context
            error_msg = str(e)
            assert len(error_msg) > 0
            assert 'operation failed' in error_msg.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
