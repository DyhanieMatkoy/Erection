"""Tests for schema management functionality

This module tests:
- Automatic schema creation for empty databases
- Schema verification and updates
- Alembic migration management
- Index creation across all backends
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

from src.data.schema_manager import SchemaManager
from src.data.sqlalchemy_base import Base
from src.data.models import sqlalchemy_models  # noqa: F401


@pytest.fixture
def temp_db_path():
    """Create a temporary database file"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def empty_engine(temp_db_path):
    """Create an engine for an empty database"""
    from sqlalchemy import event
    
    connection_string = f"sqlite:///{temp_db_path}"
    engine = create_engine(connection_string, poolclass=NullPool)
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    yield engine
    engine.dispose()


@pytest.fixture
def schema_manager(empty_engine):
    """Create a schema manager instance"""
    return SchemaManager(empty_engine)


def test_is_database_empty(schema_manager):
    """Test detection of empty database"""
    assert schema_manager.is_database_empty() is True


def test_initialize_empty_database(schema_manager, empty_engine):
    """Test schema initialization on empty database"""
    # Initialize schema
    result = schema_manager.initialize_schema(use_alembic=True)
    assert result is True
    
    # Verify tables were created
    inspector = inspect(empty_engine)
    tables = inspector.get_table_names()
    
    # Check for key tables
    expected_tables = [
        'users', 'persons', 'organizations', 'counterparties',
        'objects', 'works', 'estimates', 'estimate_lines',
        'daily_reports', 'daily_report_lines', 'timesheets',
        'timesheet_lines', 'work_execution_register', 'payroll_register'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} not created"
    
    # Verify alembic_version table exists
    assert 'alembic_version' in tables


def test_has_alembic_version_table(schema_manager, empty_engine):
    """Test detection of alembic_version table"""
    # Initially should not exist
    assert schema_manager.has_alembic_version_table() is False
    
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Now should exist
    assert schema_manager.has_alembic_version_table() is True


def test_get_current_revision(schema_manager):
    """Test getting current database revision"""
    # Before initialization, should return None
    assert schema_manager.get_current_revision() is None
    
    # After initialization, should return head revision
    schema_manager.initialize_schema(use_alembic=True)
    current = schema_manager.get_current_revision()
    head = schema_manager.get_head_revision()
    
    assert current is not None
    assert current == head


def test_verify_schema(schema_manager):
    """Test schema verification"""
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Verify schema
    result = schema_manager.verify_schema()
    
    assert result['valid'] is True
    assert len(result['missing_tables']) == 0
    assert result['needs_migration'] is False
    assert result['current_revision'] == result['head_revision']


def test_foreign_keys_enabled(schema_manager, empty_engine):
    """Test that foreign key constraints are enabled"""
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Ensure foreign keys are enabled
    schema_manager.ensure_foreign_keys_enabled()
    
    # Verify foreign keys are on
    with empty_engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys"))
        fk_status = result.scalar()
        assert fk_status == 1


def test_indices_created(schema_manager, empty_engine):
    """Test that indices are created properly"""
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Check for some key indices
    inspector = inspect(empty_engine)
    
    # Check estimates table indices
    estimates_indices = inspector.get_indexes('estimates')
    index_names = [idx['name'] for idx in estimates_indices]
    
    assert 'ix_estimates_date' in index_names
    assert 'ix_estimates_responsible_id' in index_names
    
    # Check users table indices
    users_indices = inspector.get_indexes('users')
    user_index_names = [idx['name'] for idx in users_indices]
    
    assert 'ix_users_username' in user_index_names


def test_schema_idempotence(schema_manager):
    """Test that running schema initialization multiple times is safe"""
    # Initialize schema first time
    result1 = schema_manager.initialize_schema(use_alembic=True)
    assert result1 is True
    
    # Get initial state
    verify1 = schema_manager.verify_schema()
    
    # Initialize again
    result2 = schema_manager.initialize_schema(use_alembic=True)
    assert result2 is True
    
    # Verify state is unchanged
    verify2 = schema_manager.verify_schema()
    
    assert verify1['current_revision'] == verify2['current_revision']
    assert verify1['valid'] == verify2['valid']


def test_migration_history(schema_manager):
    """Test getting migration history"""
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Get migration history
    history = schema_manager.get_migration_history()
    
    assert len(history) > 0
    assert any(rev['is_current'] for rev in history)


def test_foreign_key_constraints(schema_manager, empty_engine):
    """Test that foreign key constraints are enforced"""
    from src.data.models.sqlalchemy_models import User, Person
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import IntegrityError
    
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Create session
    Session = sessionmaker(bind=empty_engine)
    session = Session()
    
    try:
        # Try to create a person with invalid user_id
        person = Person(
            full_name="Test Person",
            user_id=999  # Non-existent user
        )
        session.add(person)
        session.commit()
        
        # Should not reach here
        assert False, "Foreign key constraint not enforced"
        
    except IntegrityError:
        # Expected - foreign key constraint violated
        session.rollback()
        assert True
        
    finally:
        session.close()


def test_unique_constraints(schema_manager, empty_engine):
    """Test that unique constraints are enforced"""
    from src.data.models.sqlalchemy_models import User
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import IntegrityError
    
    # Initialize schema
    schema_manager.initialize_schema(use_alembic=True)
    
    # Create session
    Session = sessionmaker(bind=empty_engine)
    session = Session()
    
    try:
        # Create first user
        user1 = User(
            username="testuser",
            password_hash="hash1",
            role="user"
        )
        session.add(user1)
        session.commit()
        
        # Try to create second user with same username
        user2 = User(
            username="testuser",  # Duplicate
            password_hash="hash2",
            role="user"
        )
        session.add(user2)
        session.commit()
        
        # Should not reach here
        assert False, "Unique constraint not enforced"
        
    except IntegrityError:
        # Expected - unique constraint violated
        session.rollback()
        assert True
        
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
