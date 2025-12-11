"""
Integration tests for MSSQL backend support

This test suite verifies that all database operations work correctly with MSSQL backend.
It tests:
- Connection establishment
- Schema creation
- Repository operations (CRUD)
- Connection pooling
- Transaction handling
- Error handling

Prerequisites:
- MSSQL Server running on localhost
- Database: construction
- User: q1
- Password: q1
- ODBC Driver 17 for SQL Server installed
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, date
import tempfile
import configparser

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database_manager import DatabaseManager
from src.data.database_config import DatabaseConfig
from src.data.connection_string_builder import ConnectionStringBuilder
from src.data.models.sqlalchemy_models import (
    Base, User, Person, Organization, Counterparty, Object as ObjectModel,
    Work, Estimate, EstimateLine
)
from src.data.repositories.estimate_repository import EstimateRepository
from src.data.repositories.reference_repository import ReferenceRepository
from src.data.repositories.user_repository import UserRepository
from sqlalchemy import text


# MSSQL connection parameters
MSSQL_CONFIG = {
    'host': 'localhost',
    'port': 1433,
    'database': 'construction',
    'user': 'q1',
    'password': 'q1',
    'driver': 'ODBC Driver 17 for SQL Server'
}


@pytest.fixture(scope="module")
def mssql_config_file():
    """Create a temporary config file for MSSQL testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        config = configparser.ConfigParser()
        config['Database'] = {
            'type': 'mssql',
            'mssql_host': MSSQL_CONFIG['host'],
            'mssql_port': str(MSSQL_CONFIG['port']),
            'mssql_database': MSSQL_CONFIG['database'],
            'mssql_user': MSSQL_CONFIG['user'],
            'mssql_password': MSSQL_CONFIG['password'],
            'mssql_driver': MSSQL_CONFIG['driver'],
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


@pytest.fixture(scope="module")
def db_manager(mssql_config_file):
    """Initialize DatabaseManager with MSSQL configuration"""
    # Reset singleton
    DatabaseManager._instance = None
    DatabaseManager._engine = None
    DatabaseManager._session_factory = None
    
    manager = DatabaseManager()
    success = manager.initialize(mssql_config_file)
    
    if not success:
        pytest.skip("Failed to initialize MSSQL database. Check connection parameters.")
    
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
    engine = db_manager.get_engine()
    
    # Delete all data from tables (in correct order to respect foreign keys)
    with db_manager.session_scope() as session:
        try:
            session.execute(text("DELETE FROM estimate_lines"))
            session.execute(text("DELETE FROM estimates"))
            session.execute(text("DELETE FROM works"))
            session.execute(text("DELETE FROM objects"))
            session.execute(text("DELETE FROM counterparties"))
            session.execute(text("DELETE FROM organizations"))
            session.execute(text("DELETE FROM persons"))
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Warning: Failed to clean database: {e}")
    
    yield
    
    # Cleanup after test
    with db_manager.session_scope() as session:
        try:
            session.execute(text("DELETE FROM estimate_lines"))
            session.execute(text("DELETE FROM estimates"))
            session.execute(text("DELETE FROM works"))
            session.execute(text("DELETE FROM objects"))
            session.execute(text("DELETE FROM counterparties"))
            session.execute(text("DELETE FROM organizations"))
            session.execute(text("DELETE FROM persons"))
            session.execute(text("DELETE FROM users"))
            session.commit()
        except:
            session.rollback()


class TestMSSQLConnection:
    """Test MSSQL connection and configuration"""
    
    def test_connection_string_generation(self):
        """Test MSSQL connection string is generated correctly"""
        conn_str = ConnectionStringBuilder.build_mssql(
            MSSQL_CONFIG['host'],
            MSSQL_CONFIG['port'],
            MSSQL_CONFIG['database'],
            MSSQL_CONFIG['user'],
            MSSQL_CONFIG['password'],
            MSSQL_CONFIG['driver']
        )
        
        assert 'mssql+pyodbc://' in conn_str
        assert MSSQL_CONFIG['user'] in conn_str
        assert MSSQL_CONFIG['host'] in conn_str
        assert str(MSSQL_CONFIG['port']) in conn_str
        assert MSSQL_CONFIG['database'] in conn_str
        assert 'driver=' in conn_str
    
    def test_database_manager_initialization(self, db_manager):
        """Test DatabaseManager initializes with MSSQL"""
        assert db_manager is not None
        assert db_manager.get_engine() is not None
        assert db_manager._session_factory is not None
    
    def test_connection_pool_exists(self, db_manager):
        """Test connection pool is configured for MSSQL"""
        engine = db_manager.get_engine()
        pool = engine.pool
        
        # Check pool configuration
        assert pool is not None
        assert pool.size() >= 0  # Pool should be initialized


class TestMSSQLSchemaCreation:
    """Test schema creation on MSSQL"""
    
    def test_tables_created(self, db_manager):
        """Test all tables are created in MSSQL"""
        engine = db_manager.get_engine()
        
        # Check that tables exist
        with db_manager.session_scope() as session:
            # Query information schema to check tables
            result = session.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_CATALOG = :db_name
            """), {'db_name': MSSQL_CONFIG['database']})
            
            tables = [row[0] for row in result]
            
            # Check key tables exist
            expected_tables = ['users', 'persons', 'organizations', 'counterparties',
                             'objects', 'works', 'estimates', 'estimate_lines']
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"
    
    def test_foreign_keys_created(self, db_manager):
        """Test foreign key constraints are created"""
        with db_manager.session_scope() as session:
            # Check foreign keys exist
            result = session.execute(text("""
                SELECT 
                    fk.name AS constraint_name,
                    tp.name AS parent_table,
                    tr.name AS referenced_table
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.tables AS tp ON fk.parent_object_id = tp.object_id
                INNER JOIN sys.tables AS tr ON fk.referenced_object_id = tr.object_id
            """))
            
            foreign_keys = list(result)
            assert len(foreign_keys) > 0, "No foreign keys found"


class TestMSSQLUserRepository:
    """Test UserRepository with MSSQL backend"""
    
    def test_create_user(self, db_manager, clean_database):
        """Test creating a user in MSSQL"""
        repo = UserRepository()
        
        user = User(
            username='testuser',
            password_hash='hashed_password',
            role='user',
            is_active=True
        )
        
        with db_manager.session_scope() as session:
            session.add(user)
            session.commit()
            user_id = user.id
        
        assert user_id is not None
        assert user_id > 0
        
        # Verify user was created
        with db_manager.session_scope() as session:
            retrieved_user = session.query(User).filter_by(id=user_id).first()
            assert retrieved_user is not None
            assert retrieved_user.username == 'testuser'
            assert retrieved_user.role == 'user'
    
    def test_find_user_by_username(self, db_manager, clean_database):
        """Test finding user by username"""
        repo = UserRepository()
        
        # Create user
        user = User(
            username='findme',
            password_hash='hashed',
            role='admin',
            is_active=True
        )
        
        with db_manager.session_scope() as session:
            session.add(user)
            session.commit()
        
        # Find user
        found_user = repo.find_by_username('findme')
        assert found_user is not None
        assert found_user.username == 'findme'
        assert found_user.role == 'admin'


class TestMSSQLReferenceRepository:
    """Test ReferenceRepository with MSSQL backend"""
    
    def test_create_person(self, db_manager, clean_database):
        """Test creating a person in MSSQL"""
        repo = ReferenceRepository()
        
        person = Person(
            full_name='John Doe',
            position='Engineer',
            phone='123-456-7890',
            hourly_rate=50.0,
            marked_for_deletion=False
        )
        
        with db_manager.session_scope() as session:
            session.add(person)
            session.commit()
            person_id = person.id
        
        assert person_id is not None
        
        # Verify person was created
        with db_manager.session_scope() as session:
            retrieved = session.query(Person).filter_by(id=person_id).first()
            assert retrieved is not None
            assert retrieved.full_name == 'John Doe'
            assert retrieved.hourly_rate == 50.0
    
    def test_create_organization(self, db_manager, clean_database):
        """Test creating an organization"""
        org = Organization(
            name='Test Company',
            inn='1234567890',
            marked_for_deletion=False
        )
        
        with db_manager.session_scope() as session:
            session.add(org)
            session.commit()
            org_id = org.id
        
        assert org_id is not None
        
        # Verify
        with db_manager.session_scope() as session:
            retrieved = session.query(Organization).filter_by(id=org_id).first()
            assert retrieved is not None
            assert retrieved.name == 'Test Company'


class TestMSSQLEstimateRepository:
    """Test EstimateRepository with MSSQL backend"""
    
    def test_create_estimate_with_lines(self, db_manager, clean_database):
        """Test creating estimate with lines in MSSQL"""
        # Create required references
        with db_manager.session_scope() as session:
            customer = Counterparty(name='Customer 1', marked_for_deletion=False)
            obj = ObjectModel(name='Project 1', marked_for_deletion=False)
            contractor = Organization(name='Contractor 1', marked_for_deletion=False)
            person = Person(full_name='Manager 1', marked_for_deletion=False)
            work = Work(name='Work Item 1', unit='m2', marked_for_deletion=False)
            
            session.add_all([customer, obj, contractor, person, work])
            session.commit()
            
            customer_id = customer.id
            obj_id = obj.id
            contractor_id = contractor.id
            person_id = person.id
            work_id = work.id
        
        # Create estimate
        estimate = Estimate(
            number='EST-001',
            date=date.today(),
            customer_id=customer_id,
            object_id=obj_id,
            contractor_id=contractor_id,
            responsible_id=person_id,
            marked_for_deletion=False
        )
        
        # Add line
        line = EstimateLine(
            line_number=1,
            work_id=work_id,
            quantity=100.0,
            price=50.0,
            sum=5000.0
        )
        estimate.lines.append(line)
        
        with db_manager.session_scope() as session:
            session.add(estimate)
            session.commit()
            estimate_id = estimate.id
        
        assert estimate_id is not None
        
        # Verify estimate and lines
        with db_manager.session_scope() as session:
            retrieved = session.query(Estimate).filter_by(id=estimate_id).first()
            assert retrieved is not None
            assert retrieved.number == 'EST-001'
            assert len(retrieved.lines) == 1
            assert retrieved.lines[0].quantity == 100.0
    
    def test_update_estimate(self, db_manager, clean_database):
        """Test updating an estimate"""
        # Create estimate
        with db_manager.session_scope() as session:
            customer = Counterparty(name='Customer 2', marked_for_deletion=False)
            obj = ObjectModel(name='Project 2', marked_for_deletion=False)
            contractor = Organization(name='Contractor 2', marked_for_deletion=False)
            person = Person(full_name='Manager 2', marked_for_deletion=False)
            
            session.add_all([customer, obj, contractor, person])
            session.commit()
            
            estimate = Estimate(
                number='EST-002',
                date=date.today(),
                customer_id=customer.id,
                object_id=obj.id,
                contractor_id=contractor.id,
                responsible_id=person.id,
                marked_for_deletion=False
            )
            session.add(estimate)
            session.commit()
            estimate_id = estimate.id
        
        # Update estimate
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            estimate.number = 'EST-002-UPDATED'
            session.commit()
        
        # Verify update
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            assert estimate.number == 'EST-002-UPDATED'
    
    def test_delete_estimate_cascade(self, db_manager, clean_database):
        """Test deleting estimate cascades to lines"""
        # Create estimate with lines
        with db_manager.session_scope() as session:
            customer = Counterparty(name='Customer 3', marked_for_deletion=False)
            obj = ObjectModel(name='Project 3', marked_for_deletion=False)
            contractor = Organization(name='Contractor 3', marked_for_deletion=False)
            person = Person(full_name='Manager 3', marked_for_deletion=False)
            work = Work(name='Work Item 2', unit='m2', marked_for_deletion=False)
            
            session.add_all([customer, obj, contractor, person, work])
            session.commit()
            
            estimate = Estimate(
                number='EST-003',
                date=date.today(),
                customer_id=customer.id,
                object_id=obj.id,
                contractor_id=contractor.id,
                responsible_id=person.id,
                marked_for_deletion=False
            )
            
            line = EstimateLine(
                line_number=1,
                work_id=work.id,
                quantity=50.0,
                price=100.0,
                sum=5000.0
            )
            estimate.lines.append(line)
            
            session.add(estimate)
            session.commit()
            estimate_id = estimate.id
        
        # Delete estimate
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            session.delete(estimate)
            session.commit()
        
        # Verify estimate and lines are deleted
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            assert estimate is None
            
            lines = session.query(EstimateLine).filter_by(estimate_id=estimate_id).all()
            assert len(lines) == 0


class TestMSSQLTransactions:
    """Test transaction handling with MSSQL"""
    
    def test_transaction_commit(self, db_manager, clean_database):
        """Test transaction commits successfully"""
        with db_manager.session_scope() as session:
            user = User(
                username='txtest1',
                password_hash='hash',
                role='user',
                is_active=True
            )
            session.add(user)
            # Commit happens automatically at end of context
        
        # Verify user was committed
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(username='txtest1').first()
            assert user is not None
    
    def test_transaction_rollback_on_error(self, db_manager, clean_database):
        """Test transaction rolls back on error"""
        from src.data.exceptions import DatabaseOperationError
        
        try:
            with db_manager.session_scope() as session:
                user = User(
                    username='txtest2',
                    password_hash='hash',
                    role='user',
                    is_active=True
                )
                session.add(user)
                session.flush()  # Force write to DB
                
                # Cause an error
                raise ValueError("Intentional error")
        except DatabaseOperationError:
            pass
        
        # Verify user was not committed
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(username='txtest2').first()
            assert user is None


class TestMSSQLConnectionPooling:
    """Test connection pooling behavior"""
    
    def test_multiple_sessions(self, db_manager, clean_database):
        """Test multiple sessions can be created"""
        sessions = []
        
        # Create multiple sessions
        for i in range(3):
            session = db_manager.get_session()
            sessions.append(session)
        
        # All sessions should be valid
        for session in sessions:
            assert session is not None
            # Execute a simple query
            result = session.execute(text("SELECT 1"))
            assert result is not None
        
        # Close sessions
        for session in sessions:
            session.close()
    
    def test_session_reuse(self, db_manager, clean_database):
        """Test connections are reused from pool"""
        # Create and close multiple sessions
        for i in range(10):
            with db_manager.session_scope() as session:
                result = session.execute(text("SELECT 1"))
                assert result is not None
        
        # Pool should have reused connections
        pool = db_manager.get_engine().pool
        assert pool is not None


class TestMSSQLDataTypes:
    """Test data type handling in MSSQL"""
    
    def test_string_storage(self, db_manager, clean_database):
        """Test string data types"""
        with db_manager.session_scope() as session:
            person = Person(
                full_name='Test Person',
                position='Test Position',
                phone='123-456-7890',
                marked_for_deletion=False
            )
            session.add(person)
            session.commit()
            person_id = person.id
        
        with db_manager.session_scope() as session:
            person = session.query(Person).filter_by(id=person_id).first()
            assert person.full_name == 'Test Person'
            assert person.position == 'Test Position'
    
    def test_numeric_storage(self, db_manager, clean_database):
        """Test numeric data types"""
        with db_manager.session_scope() as session:
            person = Person(
                full_name='Numeric Test',
                hourly_rate=123.45,
                marked_for_deletion=False
            )
            session.add(person)
            session.commit()
            person_id = person.id
        
        with db_manager.session_scope() as session:
            person = session.query(Person).filter_by(id=person_id).first()
            assert abs(person.hourly_rate - 123.45) < 0.01
    
    def test_date_storage(self, db_manager, clean_database):
        """Test date storage and retrieval"""
        test_date = date(2024, 1, 15)
        
        with db_manager.session_scope() as session:
            customer = Counterparty(name='Date Test', marked_for_deletion=False)
            obj = ObjectModel(name='Date Project', marked_for_deletion=False)
            contractor = Organization(name='Date Contractor', marked_for_deletion=False)
            person = Person(full_name='Date Manager', marked_for_deletion=False)
            
            session.add_all([customer, obj, contractor, person])
            session.commit()
            
            estimate = Estimate(
                number='DATE-001',
                date=test_date,
                customer_id=customer.id,
                object_id=obj.id,
                contractor_id=contractor.id,
                responsible_id=person.id,
                marked_for_deletion=False
            )
            session.add(estimate)
            session.commit()
            estimate_id = estimate.id
        
        with db_manager.session_scope() as session:
            estimate = session.query(Estimate).filter_by(id=estimate_id).first()
            assert estimate.date == test_date
    
    def test_boolean_storage(self, db_manager, clean_database):
        """Test boolean storage"""
        with db_manager.session_scope() as session:
            user = User(
                username='booltest',
                password_hash='hash',
                role='user',
                is_active=True
            )
            session.add(user)
            session.commit()
            user_id = user.id
        
        with db_manager.session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            assert user.is_active is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
