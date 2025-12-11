"""
Shared pytest fixtures for API integration tests
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings
from src.data.database_manager import DatabaseManager


@pytest.fixture(scope="session")
def test_client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture(scope="session")
def setup_database():
    """Setup test database once for all tests"""
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    
    # Ensure admin user has a person record for timesheet tests
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Get admin user ID
    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    admin_row = cursor.fetchone()
    
    if admin_row:
        admin_id = admin_row[0]
        
        # Check if person record exists for admin
        cursor.execute("SELECT id FROM persons WHERE user_id = ?", (admin_id,))
        if not cursor.fetchone():
            # Create person record for admin
            cursor.execute("""
                INSERT INTO persons (full_name, position, user_id, marked_for_deletion)
                VALUES (?, ?, ?, ?)
            """, ("Admin User", "Administrator", admin_id, 0))
            conn.commit()
    
    yield db_manager
    # Cleanup if needed


@pytest.fixture(scope="function")
def db_connection(setup_database):
    """Get database connection for each test"""
    return setup_database.get_connection()


@pytest.fixture(scope="function")
def admin_token(test_client):
    """Get admin authentication token"""
    response = test_client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Get authorization headers for admin user"""
    return {"Authorization": f"Bearer {admin_token}"}
