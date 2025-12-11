"""Tests for SQLite backward compatibility

This test suite verifies that the enhanced DatabaseManager maintains
full backward compatibility with existing SQLite databases.

Requirements tested:
- 5.1: Default to SQLite when no configuration specified
- 5.2: Connect to existing SQLite database without migration
- 5.3: Maintain all existing functionality without regression
- 5.5: Same API interface for all database operations
"""
import pytest
import os
import shutil
import tempfile
from pathlib import Path

from src.data.database_manager import DatabaseManager
from src.data.repositories.estimate_repository import EstimateRepository
from src.data.repositories.reference_repository import ReferenceRepository
from src.data.repositories.user_repository import UserRepository
from src.data.models.sqlalchemy_models import (
    User, Person, Organization, Counterparty, Object as ObjectModel,
    Work, Estimate, EstimateLine
)


class TestSQLiteBackwardCompatibility:
    """Test SQLite backward compatibility"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Reset singleton instance
        DatabaseManager._instance = None
        
    def teardown_method(self):
        """Clean up after tests"""
        db_manager = DatabaseManager._instance
        if db_manager:
            if db_manager._connection:
                try:
                    db_manager._connection.close()
                except:
                    pass
            if db_manager._engine:
                try:
                    db_manager._engine.dispose()
                except:
                    pass
        DatabaseManager._instance = None
    
    def test_default_configuration_uses_sqlite(self):
        """Test that default configuration uses SQLite
        
        Requirement 5.1: WHEN no database configuration is specified 
        THEN the system SHALL use SQLite with the existing database file
        """
        # Create a minimal config without database section
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[Auth]\n')
            f.write('login = admin\n')
            f.write('password = admin\n')
            config_path = f.name
        
        try:
            db_manager = DatabaseManager()
            result = db_manager.initialize(config_path)
            
            assert result is True, "DatabaseManager should initialize successfully"
            assert db_manager._config is not None
            assert db_manager._config.is_sqlite(), "Should default to SQLite"
            assert db_manager._engine is not None
            assert db_manager._session_factory is not None
            
        finally:
            os.unlink(config_path)
    
    def test_existing_sqlite_database_connection(self):
        """Test connection to existing SQLite database without migration
        
        Requirement 5.2: WHEN the system detects an existing SQLite database 
        THEN the Database Manager SHALL connect to it without requiring migration
        """
        # Use the actual construction.db file if it exists
        if os.path.exists('construction.db'):
            db_manager = DatabaseManager()
            result = db_manager.initialize('env.ini')
            
            assert result is True, "Should connect to existing database"
            assert db_manager._connection is not None
            assert db_manager._engine is not None
            
            # Verify we can query the database
            with db_manager.session_scope() as session:
                # Try to query users table (should exist in construction.db)
                users = session.query(User).all()
                # Should not raise an error, even if empty
                assert isinstance(users, list)
    
    def test_legacy_initialization_method(self):
        """Test backward compatibility with legacy initialization
        
        Requirement 5.3: WHEN SQLite is configured THEN the system SHALL 
        maintain all existing functionality without regression
        """
        # Test the old way of initializing with just a database path
        db_manager = DatabaseManager()
        result = db_manager.initialize('test_legacy_compat.db')
        
        try:
            assert result is True
            assert db_manager._connection is not None
            assert db_manager._engine is not None
            
            # Test that get_connection() still works (legacy API)
            connection = db_manager.get_connection()
            assert connection is not None
            
            # Test that we can execute queries using legacy connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 1
            
        finally:
            if os.path.exists('test_legacy_compat.db'):
                try:
                    os.unlink('test_legacy_compat.db')
                except PermissionError:
                    pass
    
    def test_repository_operations_with_sqlite(self):
        """Test that repository operations work with SQLite
        
        Requirement 5.3: Maintain all existing functionality without regression
        """
        # Create a test database with unique name
        import uuid
        test_db = f'test_repo_compat_{uuid.uuid4().hex[:8]}.db'
        
        try:
            # Clean up if exists
            if os.path.exists(test_db):
                os.unlink(test_db)
            
            db_manager = DatabaseManager()
            db_manager.initialize(test_db)
            
            # Initialize schema
            from src.data.schema_manager import SchemaManager
            engine = db_manager.get_engine()
            schema_manager = SchemaManager(engine)
            schema_manager.initialize_schema()
            
            # Test UserRepository
            user_repo = UserRepository()
            
            # Create a test user with unique username
            unique_username = f'test_compat_user_{uuid.uuid4().hex[:8]}'
            test_user = User(
                username=unique_username,
                password_hash='test_hash',
                role='user',
                is_active=True
            )
            
            with db_manager.session_scope() as session:
                session.add(test_user)
                session.commit()
                user_id = test_user.id
            
            # Verify we can find the user
            found_user = user_repo.find_by_username(unique_username)
            assert found_user is not None
            assert found_user.username == unique_username
            
            # Test ReferenceRepository
            ref_repo = ReferenceRepository()
            
            # Create a test person
            test_person = Person(
                full_name='Test Person',
                position='Tester',
                hourly_rate=100.0,
                marked_for_deletion=False
            )
            
            with db_manager.session_scope() as session:
                session.add(test_person)
                session.commit()
                person_id = test_person.id
            
            # Verify we can use reference repository methods
            can_delete, usages = ref_repo.can_delete_person(person_id)
            assert can_delete is True  # Should be deletable since not used anywhere
            
        finally:
            if os.path.exists(test_db):
                try:
                    os.unlink(test_db)
                except PermissionError:
                    pass
    
    def test_no_schema_changes_required(self):
        """Test that existing databases work without schema changes
        
        Requirement 5.2: Connect to existing SQLite database without requiring migration
        """
        # Create a database with the old schema (simulated)
        test_db = 'test_no_migration.db'
        
        try:
            # First, create a database with schema
            db_manager = DatabaseManager()
            db_manager.initialize(test_db)
            
            from src.data.schema_manager import SchemaManager
            engine = db_manager.get_engine()
            schema_manager = SchemaManager(engine)
            schema_manager.initialize_schema()
            
            # Close and reinitialize
            if db_manager._connection:
                db_manager._connection.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            DatabaseManager._instance = None
            
            # Now reconnect - should work without migration
            db_manager = DatabaseManager()
            result = db_manager.initialize(test_db)
            
            assert result is True
            
            # Verify schema is still valid
            engine = db_manager.get_engine()
            schema_manager = SchemaManager(engine)
            schema_info = schema_manager.verify_schema()
            # Schema should be valid (no missing or extra tables)
            assert schema_info['missing_tables'] == []
            assert schema_info['extra_tables'] == []
            
        finally:
            if os.path.exists(test_db):
                try:
                    os.unlink(test_db)
                except PermissionError:
                    pass
    
    def test_api_interface_consistency(self):
        """Test that API interface is consistent across operations
        
        Requirement 5.5: THE system SHALL maintain the same API interface 
        for all database operations regardless of backend
        """
        test_db = 'test_api_consistency.db'
        
        try:
            db_manager = DatabaseManager()
            db_manager.initialize(test_db)
            
            # Test that all expected methods exist and work
            
            # 1. get_connection() - legacy method
            connection = db_manager.get_connection()
            assert connection is not None
            
            # 2. get_engine() - new SQLAlchemy method
            engine = db_manager.get_engine()
            assert engine is not None
            
            # 3. get_session() - new SQLAlchemy method
            session = db_manager.get_session()
            assert session is not None
            session.close()
            
            # 4. session_scope() - new context manager
            with db_manager.session_scope() as session:
                assert session is not None
            
            # All methods should work without errors
            
        finally:
            if os.path.exists(test_db):
                try:
                    os.unlink(test_db)
                except PermissionError:
                    pass
    
    def test_existing_construction_db_functionality(self):
        """Test that existing construction.db works with all functionality
        
        Comprehensive test of backward compatibility with real database
        """
        if not os.path.exists('construction.db'):
            pytest.skip("construction.db not found - skipping real database test")
        
        # Make a backup first
        backup_path = 'construction.db.backup_test'
        if os.path.exists(backup_path):
            os.unlink(backup_path)
        shutil.copy2('construction.db', backup_path)
        
        try:
            db_manager = DatabaseManager()
            result = db_manager.initialize('env.ini')
            
            assert result is True
            
            # Test that we can query all major tables
            with db_manager.session_scope() as session:
                # Users
                users = session.query(User).all()
                assert isinstance(users, list)
                
                # Persons
                persons = session.query(Person).all()
                assert isinstance(persons, list)
                
                # Organizations
                orgs = session.query(Organization).all()
                assert isinstance(orgs, list)
                
                # Counterparties
                counterparties = session.query(Counterparty).all()
                assert isinstance(counterparties, list)
                
                # Objects
                objects = session.query(ObjectModel).all()
                assert isinstance(objects, list)
                
                # Works
                works = session.query(Work).all()
                assert isinstance(works, list)
                
                # Estimates
                estimates = session.query(Estimate).all()
                assert isinstance(estimates, list)
            
            # Test repository operations
            user_repo = UserRepository()
            # Test find_by_username instead of get_all_users
            # Query users within a session to avoid detached instance errors
            with db_manager.session_scope() as session:
                active_users = session.query(User).filter(User.is_active == True).all()
                if len(active_users) > 0:
                    username = active_users[0].username
                    # Now test outside the session
                    test_user = user_repo.find_by_username(username)
                    assert test_user is not None
            
            # Test ReferenceRepository
            ref_repo = ReferenceRepository()
            # Query persons within a session
            with db_manager.session_scope() as session:
                all_persons = session.query(Person).all()
                if len(all_persons) > 0:
                    person_id = all_persons[0].id
                    # Test reference repository method
                    can_delete, usages = ref_repo.can_delete_person(person_id)
                    assert isinstance(can_delete, bool)
                    assert isinstance(usages, list)
            
        finally:
            # Close connections before restoring backup
            if db_manager._connection:
                try:
                    db_manager._connection.close()
                except:
                    pass
            if db_manager._engine:
                try:
                    db_manager._engine.dispose()
                except:
                    pass
            
            # Restore backup
            if os.path.exists(backup_path):
                try:
                    if os.path.exists('construction.db'):
                        os.unlink('construction.db')
                    shutil.move(backup_path, 'construction.db')
                except PermissionError:
                    # If file is locked, just keep the backup
                    pass
    
    def test_sqlite_specific_features(self):
        """Test SQLite-specific features still work
        
        Requirement 5.3: Maintain all existing functionality
        """
        import uuid
        test_db = f'test_sqlite_features_{uuid.uuid4().hex[:8]}.db'
        
        try:
            # Clean up if exists
            if os.path.exists(test_db):
                os.unlink(test_db)
            
            db_manager = DatabaseManager()
            db_manager.initialize(test_db)
            
            # Test AUTOINCREMENT for primary keys
            from src.data.schema_manager import SchemaManager
            engine = db_manager.get_engine()
            schema_manager = SchemaManager(engine)
            schema_manager.initialize_schema()
            
            # Insert multiple records and verify auto-increment
            unique_id = uuid.uuid4().hex[:8]
            with db_manager.session_scope() as session:
                user1 = User(username=f'user1_{unique_id}', password_hash='hash1', role='user')
                user2 = User(username=f'user2_{unique_id}', password_hash='hash2', role='user')
                session.add(user1)
                session.add(user2)
                session.commit()
                
                # IDs should be auto-generated and sequential
                assert user1.id is not None
                assert user2.id is not None
                assert user2.id > user1.id
            
        finally:
            if os.path.exists(test_db):
                try:
                    os.unlink(test_db)
                except PermissionError:
                    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
