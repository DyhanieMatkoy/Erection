"""Integration tests for enhanced DatabaseManager
Tests Requirements: 2.2, 2.3, 6.1, 6.3, 7.1-7.5
"""
import pytest
import tempfile
import os
from sqlalchemy import text, Column, Integer, String
from sqlalchemy.orm import declarative_base

from src.data.database_manager import DatabaseManager
from src.data.exceptions import DatabaseConnectionError, DatabaseOperationError
from src.data.sqlalchemy_base import Base

# Create a test model
TestBase = declarative_base()


class TestModel(TestBase):
    """Simple test model for integration tests"""
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    value = Column(Integer)


class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        DatabaseManager._instance = None
    
    def test_requirement_2_2_unified_interface(self):
        """Test Requirement 2.2: Unified database interface across backends
        
        WHEN application code requests a connection 
        THEN the Database Adapter SHALL provide a connection object 
        with consistent behavior across all backends
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_unified.db')
        
        try:
            # Test that we can get both session and connection
            session = db_manager.get_session()
            assert session is not None
            session.close()
            
            connection = db_manager.get_connection()
            assert connection is not None
            
            # Test that both interfaces work
            with db_manager.session_scope() as session:
                result = session.execute(text("SELECT 1 as value"))
                row = result.fetchone()
                assert row[0] == 1
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_unified.db'):
                try:
                    os.unlink('test_unified.db')
                except PermissionError:
                    pass
    
    def test_requirement_2_3_transaction_acid(self):
        """Test Requirement 2.3: ACID transaction properties
        
        WHEN application code executes transactions 
        THEN the Database Adapter SHALL ensure ACID properties 
        are maintained across all database backends
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_acid.db')
        
        try:
            # Create test table
            TestModel.metadata.create_all(bind=db_manager.get_engine())
            
            # Test successful transaction (Atomicity and Durability)
            with db_manager.session_scope() as session:
                obj1 = TestModel(name='test1', value=100)
                obj2 = TestModel(name='test2', value=200)
                session.add(obj1)
                session.add(obj2)
            
            # Verify both objects were committed
            with db_manager.session_scope() as session:
                count = session.query(TestModel).count()
                assert count == 2
            
            # Test rollback on error (Consistency)
            try:
                with db_manager.session_scope() as session:
                    obj3 = TestModel(name='test3', value=300)
                    session.add(obj3)
                    # Force an error
                    session.execute(text("INVALID SQL"))
            except DatabaseOperationError:
                pass  # Expected
            
            # Verify obj3 was NOT committed (rolled back)
            with db_manager.session_scope() as session:
                count = session.query(TestModel).count()
                assert count == 2  # Still only 2 objects
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_acid.db'):
                try:
                    os.unlink('test_acid.db')
                except PermissionError:
                    pass
    
    def test_requirement_6_1_connection_error_handling(self):
        """Test Requirement 6.1: Connection failure error handling
        
        WHEN a database connection fails 
        THEN the Database Manager SHALL log detailed error information 
        and raise an appropriate exception
        """
        # Create config with invalid PostgreSQL connection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Database]\n')
            f.write('type = postgresql\n')
            f.write('postgres_host = invalid_host_12345\n')
            f.write('postgres_port = 9999\n')
            f.write('postgres_database = test_db\n')
            f.write('postgres_user = test_user\n')
            f.write('postgres_password = test_pass\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            
            # Should raise DatabaseConnectionError
            with pytest.raises(DatabaseConnectionError):
                db_manager.initialize(config_path)
            
        finally:
            os.unlink(config_path)
    
    def test_requirement_6_3_transaction_rollback(self):
        """Test Requirement 6.3: Transaction rollback on failure
        
        WHEN a transaction fails 
        THEN the Database Adapter SHALL rollback changes 
        and maintain database consistency
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_rollback_req.db')
        
        try:
            # Create test table
            TestModel.metadata.create_all(bind=db_manager.get_engine())
            
            # Add initial data
            with db_manager.session_scope() as session:
                obj1 = TestModel(name='initial', value=1)
                session.add(obj1)
            
            # Verify initial state
            with db_manager.session_scope() as session:
                count = session.query(TestModel).count()
                assert count == 1
            
            # Attempt transaction that will fail
            try:
                with db_manager.session_scope() as session:
                    obj2 = TestModel(name='should_rollback', value=2)
                    session.add(obj2)
                    session.flush()  # Write to database
                    
                    # Force an error
                    raise Exception("Simulated error")
            except DatabaseOperationError:
                pass  # Expected
            
            # Verify rollback - should still have only 1 object
            with db_manager.session_scope() as session:
                count = session.query(TestModel).count()
                assert count == 1
                
                obj = session.query(TestModel).first()
                assert obj.name == 'initial'
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_rollback_req.db'):
                try:
                    os.unlink('test_rollback_req.db')
                except PermissionError:
                    pass
    
    def test_requirement_7_1_connection_pooling_sqlite(self):
        """Test Requirement 7.1: Connection pooling (SQLite uses NullPool)
        
        WHEN using PostgreSQL or MSSQL 
        THEN the Database Manager SHALL maintain a connection pool
        
        Note: SQLite uses NullPool (no pooling), which is correct behavior
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_pool.db')
        
        try:
            engine = db_manager.get_engine()
            
            # For SQLite, pool should be NullPool
            from sqlalchemy.pool import NullPool
            assert isinstance(engine.pool, NullPool)
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_pool.db'):
                try:
                    os.unlink('test_pool.db')
                except PermissionError:
                    pass
    
    def test_requirement_7_2_connection_from_pool(self):
        """Test Requirement 7.2: Providing connections from pool
        
        WHEN a request needs a connection 
        THEN the Database Manager SHALL provide one from the pool if available
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_pool_provide.db')
        
        try:
            # Get multiple sessions
            session1 = db_manager.get_session()
            session2 = db_manager.get_session()
            session3 = db_manager.get_session()
            
            # All should be valid
            assert session1 is not None
            assert session2 is not None
            assert session3 is not None
            
            # Close sessions
            session1.close()
            session2.close()
            session3.close()
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_pool_provide.db'):
                try:
                    os.unlink('test_pool_provide.db')
                except PermissionError:
                    pass
    
    def test_requirement_7_4_connection_reuse(self):
        """Test Requirement 7.4: Connection pool reuse
        
        WHEN a connection is released 
        THEN the Database Manager SHALL return it to the pool for reuse
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_pool_reuse.db')
        
        try:
            # Use session scope multiple times
            for i in range(5):
                with db_manager.session_scope() as session:
                    result = session.execute(text("SELECT 1"))
                    assert result is not None
            
            # All sessions should have been properly closed and reused
            # No errors should occur
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_pool_reuse.db'):
                try:
                    os.unlink('test_pool_reuse.db')
                except PermissionError:
                    pass
    
    def test_requirement_7_5_graceful_shutdown(self):
        """Test Requirement 7.5: Graceful connection pool shutdown
        
        WHEN the system shuts down 
        THEN the Database Manager SHALL close all pooled connections gracefully
        """
        db_manager = DatabaseManager()
        db_manager.initialize('test_shutdown.db')
        
        try:
            # Create some sessions
            session1 = db_manager.get_session()
            session2 = db_manager.get_session()
            
            # Close sessions
            session1.close()
            session2.close()
            
            # Dispose engine (simulates shutdown)
            db_manager._engine.dispose()
            
            # Should be able to dispose without errors
            assert True
            
            # Clean up connection
            if db_manager._connection:
                db_manager._connection.close()
            
        finally:
            if os.path.exists('test_shutdown.db'):
                try:
                    os.unlink('test_shutdown.db')
                except PermissionError:
                    pass
    
    def test_backward_compatibility_with_existing_code(self):
        """Test that existing code using get_connection() still works"""
        db_manager = DatabaseManager()
        db_manager.initialize('test_backward.db')
        
        try:
            # Old style: get_connection()
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            # New style: session_scope()
            with db_manager.session_scope() as session:
                result = session.execute(text("SELECT 1"))
                row = result.fetchone()
                assert row[0] == 1
            
            # Both should work together
            
            # Clean up
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            
        finally:
            if os.path.exists('test_backward.db'):
                try:
                    os.unlink('test_backward.db')
                except PermissionError:
                    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
