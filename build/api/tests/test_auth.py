"""
Integration tests for authentication endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings
from src.data.database_manager import DatabaseManager


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    yield


def test_login_success(client, setup_test_db):
    """Test successful login"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] in ["admin", "Администратор"]  # Support both English and Russian


def test_login_invalid_credentials(client, setup_test_db):
    """Test login with invalid credentials"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["success"] is False


def test_login_nonexistent_user(client, setup_test_db):
    """Test login with nonexistent user"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 401


def test_get_current_user(client, setup_test_db):
    """Test getting current user info"""
    # First login
    login_response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] in ["admin", "Администратор"]  # Support both English and Russian
    assert "id" in data


def test_get_current_user_no_token(client, setup_test_db):
    """Test getting current user without token"""
    response = client.get(f"{settings.API_PREFIX}/auth/me")
    assert response.status_code in [401, 403]  # Either unauthorized or forbidden


def test_get_current_user_invalid_token(client, setup_test_db):
    """Test getting current user with invalid token"""
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
