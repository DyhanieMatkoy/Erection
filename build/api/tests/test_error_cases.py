"""
Integration tests for error cases (401, 404, 422, 500)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from datetime import date
from api.main import app
from api.config import settings
from src.data.database_manager import DatabaseManager


client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    yield


@pytest.fixture
def auth_token(setup_test_db):
    """Get authentication token for tests"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


# 401 Unauthorized tests
def test_401_no_token():
    """Test 401 when no token provided"""
    response = client.get(f"{settings.API_PREFIX}/auth/me")
    assert response.status_code == 401


def test_401_invalid_token():
    """Test 401 when invalid token provided"""
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_401_malformed_token():
    """Test 401 when malformed token provided"""
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": "InvalidFormat"}
    )
    assert response.status_code == 401


def test_401_wrong_credentials():
    """Test 401 when wrong credentials provided"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


# 404 Not Found tests
def test_404_nonexistent_estimate(auth_headers):
    """Test 404 when estimate not found"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_daily_report(auth_headers):
    """Test 404 when daily report not found"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/daily-reports/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_counterparty(auth_headers):
    """Test 404 when counterparty not found"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_object(auth_headers):
    """Test 404 when object not found"""
    response = client.get(
        f"{settings.API_PREFIX}/references/objects/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_work(auth_headers):
    """Test 404 when work not found"""
    response = client.get(
        f"{settings.API_PREFIX}/references/works/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_person(auth_headers):
    """Test 404 when person not found"""
    response = client.get(
        f"{settings.API_PREFIX}/references/persons/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_404_nonexistent_organization(auth_headers):
    """Test 404 when organization not found"""
    response = client.get(
        f"{settings.API_PREFIX}/references/organizations/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


# 422 Validation Error tests
def test_422_invalid_estimate_data(auth_headers):
    """Test 422 when invalid estimate data provided"""
    invalid_data = {
        "number": "",  # Empty number
        "date": "invalid-date",  # Invalid date format
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/estimates",
        json=invalid_data,
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_missing_required_fields(auth_headers):
    """Test 422 when required fields are missing"""
    incomplete_data = {
        "number": "TEST-001"
        # Missing date and other required fields
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/estimates",
        json=incomplete_data,
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_invalid_pagination_params(auth_headers):
    """Test 422 when invalid pagination parameters provided"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates",
        params={"page": 0, "page_size": -1},  # Invalid values
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_invalid_sort_order(auth_headers):
    """Test 422 when invalid sort order provided"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties",
        params={"sort_order": "invalid"},  # Should be asc or desc
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_invalid_group_by(auth_headers):
    """Test 422 when invalid group_by parameter provided"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={"group_by": "invalid"},  # Should be object, estimate, work, or period
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_invalid_daily_report_data(auth_headers):
    """Test 422 when invalid daily report data provided"""
    invalid_data = {
        "date": "invalid-date",
        "estimate_id": "not-a-number",  # Should be integer
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/daily-reports",
        json=invalid_data,
        headers=auth_headers
    )
    assert response.status_code == 422


def test_422_invalid_reference_data(auth_headers):
    """Test 422 when invalid reference data provided"""
    invalid_data = {
        "name": "",  # Empty name
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/counterparties",
        json=invalid_data,
        headers=auth_headers
    )
    assert response.status_code == 422


# Additional error case tests
def test_invalid_endpoint():
    """Test accessing invalid endpoint"""
    response = client.get(f"{settings.API_PREFIX}/invalid/endpoint")
    assert response.status_code == 404


def test_method_not_allowed(auth_headers):
    """Test using wrong HTTP method"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/me",  # Should be GET
        headers=auth_headers
    )
    assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
