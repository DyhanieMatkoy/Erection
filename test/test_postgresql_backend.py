"""
PostgreSQL Backend Integration Tests

Tests to verify PostgreSQL backend functionality including:
- Connection establishment
- Schema creation
- CRUD operations
- Connection pooling
- Concurrent access
- Transaction handling
"""

import pytest
import sys
import os
import tempfile
import configparser
from pathlib import Path
from datetime import datetime, date
import threading
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import (
    Base, User, Person, Organization, Counterparty, 
    Object as ObjectModel, Work, Estimate, EstimateLine
)
from sqlalchemy import text, inspect


# PostgreSQL connection parameters
POSTGRESQL_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'construction',
    'user': 'q1',
    'password': 'q1'
}


@pytest.fixture(scope='module')
def postgresql_config_file():
    """Create a temporary config file for PostgreSQL testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        config = configparser.ConfigParser()
        config['Database'] = {
            'type': 'postgresql',
            'postgres_host': POSTGRESQL_CONFIG['host'],
            'postgres_port': str(POSTGRESQL_CONFIG['port']),
            'postgres_database': POSTGRESQL_CONFIG['database'],
            'postgres_user': POSTGRESQL_CONFIG['user'],
            'postgres_password': POSTGRESQL_CONFIG['password'],
            'pool_size': '5',
            'max_overflow': '10',
            'pool_timeout': '30',
            'pool_recycle': '3600'
        }
        config.write(f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    try:
        os.unlink(config_path)
    except:
        pass


@pytest.fixture(scope='module')
def db_manager(postgresql_config_file):
    """Initialize database manager with PostgreSQL"""
    # Reset singleton
    DatabaseManager._instance = None
    DatabaseManager._engine = None
    DatabaseManager._session_factory = None
    
    manager = DatabaseManager()
    success = manager.initialize(postgresql_config_file)
    
    if not success:
        pytest.skip("Failed to initialize PostgreSQL database. Check connection parameters.")
    
    # Create schema
    try:
        Base.metadata.create_all(manager.get_engine())
    except Exception as e:
        pytest.skip(f"Failed to create schema: {e}")
    
    yield manager
    
    # Cleanup: Drop all tables
    try:
        Base.metadata.drop_all(manager.get_engine())
    except:
        pass


@pytest.fixture
def clean_database(db_manager):
    """Clean database before each test"""
    with db_manager.session_scope() as session:
        # Delete in correct order to respect foreign keys
        session.query(EstimateLine).delete()
        session.query(Estimate).delete()
        session.query(Work).delete()
        session.query(ObjectModel).delete()
        session.query(Counterparty).delete()
        session.query(Organization).delete()
        session.query(Person).delete()
        session.query(User).delete()
        session.commit()
    
    yield
    
    # Cleanup after test
    with db_manager.session_scope() as session:
        session.query(EstimateLine).delete()
        session.query(Estimate).delete()
        session.query(Work).delete()
        session.query(ObjectModel).delete()
        session.query(Counterparty).delete()
        session.query(Organization).delete()
        session.query(Person).delete()
        session.query(User).delete()
        session.commit()


class TestPostgreSQLConnection:
    """Test PostgreSQL connection functionality"""
    
    def test_connection_established(self, db_manager):
        """Test that connection to PostgreSQL is established"""
        engine = db_manager.get_engine()
        assert engine is not None
        assert str(engine.url).startswith('postgresql://')
    
    def test_can_execute_query(self, db_manager):
        """Test that we can execute a simple query"""
        with db_manager.session_scope() as session:
            result = session.execute(text("SELECT 1 as test")).fetchone()
            assert result[0] == 1
    
    def test_database_version(self, db_manager):
        """Test that we can query PostgreSQL version"""
        with db_manager.session_scope() as session:
            result = session.execute(text("SELECT version()")).fetchone()
            version = result[0]
            assert 'PostgreSQL' in version


class TestPostgreSQLSchema:
    """Test schema creation and management"""
    
    def test_tables_created(self, db_manager):
        """Test that all tables are created"""
        inspector = inspect(db_manager.get_engine())
        tables = inspector.get_table_names()
        
        expected_tables = [
            'users', 'persons', 'organizations', 'counterparties',
            'objects', 'works', 'estimates', 'estimate_lines'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
    
    def test_primary_keys_configured(self, db_manager):
        """Test that primary keys are properly configured"""
        inspector = inspect(db_manager.get_engine())
        
        # Check users table
        pk = inspector.get_pk_constraint('users')
        assert 'id' in pk['constrained_columns']
        
        # Check estimates table
        pk = inspector.get_pk_constraint('estimates')
        assert 'id' in pk['constrained_columns']
    
    def test_foreign_keys_configured(self, db_manager):
        """Test that foreign keys are properly configured"""
        inspector = inspect(db_manager.get_engine())
        
        # Check estimate_lines foreign key to estimates
        fks = inspector.get_foreign_keys('estimate_lines')
        estimate_fk = [fk for fk in fks if fk['referred_table'] == 'estimates']
        assert len(estimate_fk) > 0


class TestPostgreSQLCRUD:
    """Test CRUD operations with PostgreSQL"""
    
    def test_insert_user(self, db_manager, clean_database):
        """Test inserting a user"""
        with db_manager.session_scope() as session:
            user = User(
                username='testuser',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            session.add(user)
            session.commit()
            
            assert user.id is not None
            assert user.id > 0
    
    def test_query_user(self, db_manager, clean_database):
        """Test querying a user"""
        # Insert user
        with db_manager.session_scope() as session:
            user = User(
                username='testuser',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            session.add(user)
            session.commit()
            user_id = user.id
        
        # Query user
        with db_manager.session_scope() as session:
            found_user = session.query(User).filter_by(id=user_id).first()
            assert found_user is not None
            assert found_user.username == 'testuser'
    
    def test_update_user(self, db_manager, clean_database):
        """Test updating a user"""
        # Insert user
        with db_manager.session_scope() as session:
            user = User(
                username='testuser',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            session.add(user)
            session.commit()
            user_id = user.id
        
        # Update user
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            user.role = 'admin'
            session.commit()
        
        # Verify update
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            assert user.role == 'admin'
    
    def test_delete_user(self, db_manager, clean_database):
        """Test deleting a user"""
        # Insert user
        with db_manager.session_scope() as session:
            user = User(
                username='testuser',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            session.add(user)
            session.commit()
            user_id = user.id
        
        # Delete user
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            session.delete(user)
            session.commit()
        
        # Verify deletion
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            assert user is None


class TestPostgreSQLRelationships:
    """Test relationship handling"""
    
    def test_estimate_with_lines(self, db_manager, clean_database):
        """Test creating estimate with lines"""
        with db_manager.session_scope() as session:
            # Create required references
            org = Organization(name='Test Org', marked_for_deletion=False)
            session.add(org)
            session.flush()
            
            counterparty = Counterparty(name='Test Customer', marked_for_deletion=False)
            session.add(counterparty)
            session.flush()
            
            obj = ObjectModel(name='Test Object', marked_for_deletion=False)
            session.add(obj)
            session.flush()
            
            person = Person(full_name='Test Person', marked_for_deletion=False)
            session.add(person)
            session.flush()
            
            # Create estimate
            estimate = Estimate(
                number='EST-001',
                date=date.today(),
                customer_id=counterparty.id,
                object_id=obj.id,
                contractor_id=org.id,
                responsible_id=person.id,
                marked_for_deletion=False
            )
            session.add(estimate)
            session.flush()
            
            # Add lines
            line1 = EstimateLine(
                estimate_id=estimate.id,
                line_number=1,
                quantity=10.0,
                unit='pcs',
                price=100.0,
                sum=1000.0
            )
            line2 = EstimateLine(
                estimate_id=estimate.id,
                line_number=2,
                quantity=5.0,
                unit='pcs',
                price=200.0,
                sum=1000.0
            )
            session.add_all([line1, line2])
            session.commit()
            
            estimate_id = estimate.id
        
        # Verify
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            assert estimate is not None
            assert len(estimate.lines) == 2


class TestPostgreSQLConnectionPool:
    """Test connection pooling behavior"""
    
    def test_pool_reuse(self, db_manager, clean_database):
        """Test that connections are reused from pool"""
        # Get initial pool status
        engine = db_manager.get_engine()
        pool = engine.pool
        
        # Execute multiple operations
        for i in range(10):
            with db_manager.session_scope() as session:
                session.execute(text("SELECT 1"))
        
        # Pool should have reused connections
        pool_size = db_manager._config.config_data.get('pool_size', 5)
        max_overflow = db_manager._config.config_data.get('max_overflow', 10)
        assert pool.size() <= pool_size + max_overflow
    
    def test_concurrent_access(self, db_manager, clean_database):
        """Test concurrent database access"""
        results = []
        errors = []
        
        def insert_user(username):
            try:
                with db_manager.session_scope() as session:
                    user = User(
                        username=username,
                        password_hash='hash123',
                        role='user',
                        is_active=True
                    )
                    session.add(user)
                    session.commit()
                    results.append(user.id)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=insert_user, args=(f'user{i}',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        
        # Verify all users were created
        with db_manager.session_scope() as session:
            count = session.query(User).count()
            assert count == 10


class TestPostgreSQLTransactions:
    """Test transaction handling"""
    
    def test_transaction_commit(self, db_manager, clean_database):
        """Test that transactions commit properly"""
        with db_manager.session_scope() as session:
            user = User(
                username='testuser',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            session.add(user)
            # Commit happens automatically at end of context
        
        # Verify committed
        with db_manager.session_scope() as session:
            count = session.query(User).count()
            assert count == 1
    
    def test_transaction_rollback(self, db_manager, clean_database):
        """Test that transactions rollback on error"""
        from src.data.exceptions import DatabaseOperationError
        
        try:
            with db_manager.session_scope() as session:
                user = User(
                    username='testuser',
                    password_hash='hash123',
                    role='user',
                    is_active=True
                )
                session.add(user)
                session.flush()
                
                # Force an error
                raise ValueError("Test error")
        except DatabaseOperationError:
            # Expected - session_scope wraps exceptions
            pass
        
        # Verify rollback
        with db_manager.session_scope() as session:
            count = session.query(User).count()
            assert count == 0


class TestPostgreSQLDataTypes:
    """Test PostgreSQL-specific data type handling"""
    
    def test_serial_primary_key(self, db_manager, clean_database):
        """Test SERIAL primary key generation"""
        ids = []
        
        for i in range(5):
            with db_manager.session_scope() as session:
                user = User(
                    username=f'user{i}',
                    password_hash='hash123',
                    role='user',
                    is_active=True
                )
                session.add(user)
                session.commit()
                ids.append(user.id)
        
        # Verify sequential IDs
        assert len(ids) == 5
        assert len(set(ids)) == 5  # All unique
        assert all(id > 0 for id in ids)
    
    def test_boolean_type(self, db_manager, clean_database):
        """Test boolean type handling"""
        with db_manager.session_scope() as session:
            user1 = User(
                username='active_user',
                password_hash='hash123',
                role='user',
                is_active=True
            )
            user2 = User(
                username='inactive_user',
                password_hash='hash123',
                role='user',
                is_active=False
            )
            session.add_all([user1, user2])
            session.commit()
        
        # Query by boolean
        with db_manager.session_scope() as session:
            active_users = session.query(User).filter_by(is_active=True).all()
            assert len(active_users) == 1
            assert active_users[0].username == 'active_user'
    
    def test_date_type(self, db_manager, clean_database):
        """Test date type handling"""
        test_date = date(2024, 1, 15)
        
        with db_manager.session_scope() as session:
            # Create required references
            org = Organization(name='Test Org', marked_for_deletion=False)
            counterparty = Counterparty(name='Test Customer', marked_for_deletion=False)
            obj = ObjectModel(name='Test Object', marked_for_deletion=False)
            person = Person(full_name='Test Person', marked_for_deletion=False)
            session.add_all([org, counterparty, obj, person])
            session.flush()
            
            estimate = Estimate(
                number='EST-001',
                date=test_date,
                customer_id=counterparty.id,
                object_id=obj.id,
                contractor_id=org.id,
                responsible_id=person.id,
                marked_for_deletion=False
            )
            session.add(estimate)
            session.commit()
            estimate_id = estimate.id
        
        # Verify date
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            assert estimate.date == test_date


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
