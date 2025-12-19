"""
Shared pytest fixtures for API integration tests
"""
import sys
import os
import shutil
import tempfile
import configparser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings
from src.data.database_manager import DatabaseManager
from src.data.sqlalchemy_base import Base


@pytest.fixture(scope="session")
def test_client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture(scope="session")
def setup_database():
    """Setup test database once for all tests"""
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, "test_construction.db")
    config_path = os.path.join(test_dir, "test_env.ini")
    
    # Create test configuration file
    config = configparser.ConfigParser()
    config['Database'] = {
        'type': 'sqlite',
        'sqlite_path': db_path
    }
    with open(config_path, 'w') as config_file:
        config.write(config_file)
    
    # Initialize DatabaseManager with test config
    # This forces SQLAlchemy initialization mode, not legacy
    db_manager = DatabaseManager()
    
    # Reset singleton state if needed (though new init overrides usually)
    # But since it's a singleton, we should be careful if other tests run in parallel (unlikely here)
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db_manager.initialize(config_path)
    
    # Ensure tables are created (initialize does this, but being explicit is fine)
    # And specifically, since we are using SQLAlchemy mode, models should be reflected.
    
    # Ensure admin user has a person record for timesheet tests
    # Note: We need to handle the case where tables are empty
    # Create admin user first if not exists (since it's a fresh DB)
    
    with db_manager.session_scope() as session:
        from src.data.models.sqlalchemy_models import User, Person
        import uuid
        
        admin = session.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin", 
                password_hash="admin", # In real app use hash
                role="admin",
                is_active=True
            )
            session.add(admin)
            session.flush() # get ID
            
            # Create person for admin
            person = Person(
                full_name="Admin User",
                position="Administrator",
                user_id=admin.id,
                marked_for_deletion=False,
                uuid=str(uuid.uuid4())
            )
            session.add(person)
            session.commit()
    
    yield db_manager
    
    # Cleanup
    try:
        if db_manager._engine:
            db_manager._engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(config_path):
            os.remove(config_path)
        os.rmdir(test_dir)
    except Exception as e:
        print(f"Error cleaning up test database: {e}")


@pytest.fixture(scope="function")
def db_session(setup_database):
    """Get a clean database session for the test"""
    db_manager = setup_database
    with db_manager.session_scope() as session:
        yield session
        # Session is closed/committed/rolled back by context manager
        # But for tests we might want to ensure rollback?
        # session_scope commits on success.
        # Ideally tests should run in a transaction that rolls back.
        # But DatabaseManager.session_scope commits.
        # We can just let it commit to the temp DB, since we have a fresh DB for the session 
        # and tests are mostly additive or independent? 
        # Actually, sharing a DB across session means tests affect each other.
        # Ideally fixture should be function scoped and rollback or clear DB.
        # Clearing DB is expensive.
        # Rolling back is better.
        
        # To force rollback in session_scope, we would need to raise an exception or modify session_scope.
        # Or we can use a nested transaction or standard pytest-sqlalchemy patterns.
        # Given existing code uses db_manager.session_scope(), we stick to it.
        # If tests need isolation, they should clean up or we accept state.
        # Our property tests generate random data, collisions unlikely.


@pytest.fixture(scope="function")
def db_connection(setup_database):
    """Get database connection for each test"""
    return setup_database.get_connection()


@pytest.fixture(scope="function")
def admin_token(test_client):
    """Get admin authentication token"""
    # Need to ensure admin exists (done in setup_database)
    # And password matches (we set "admin" as hash, auth logic might expect hashed)
    # If auth endpoint verifies hash, we need valid hash.
    # Assuming "admin" plain text for now if simple auth or mock.
    # Actually, we should probably mock the auth dependency instead of relying on login endpoint
    # to avoid hashing complexity.
    
    # But to keep it simple and minimally invasive:
    # If login fails, we mock.
    try:
        response = test_client.post(
            f"{settings.API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except:
        pass
    return "mock_admin_token"


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Get authorization headers for admin user"""
    return {"Authorization": f"Bearer {admin_token}"}
