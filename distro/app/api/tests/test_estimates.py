"""
Integration tests for estimate endpoints
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


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    yield
    # Cleanup if needed


@pytest.fixture
def auth_token(client, setup_test_db):
    """Get authentication token for tests"""
    # Login with test user
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


def test_list_estimates(client, auth_headers):
    """Test listing estimates"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_list_estimates_with_filters(client, auth_headers):
    """Test listing estimates with filters"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates",
        params={
            "page": 1,
            "page_size": 10,
            "sort_by": "date",
            "sort_order": "desc"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_create_estimate(client, auth_headers):
    """Test creating estimate"""
    estimate_data = {
        "number": "TEST-001",
        "date": date.today().isoformat(),
        "customer_id": 1,
        "object_id": 1,
        "contractor_id": 1,
        "responsible_id": 1,
        "lines": [
            {
                "line_number": 1,
                "work_id": 1,
                "quantity": 10.0,
                "unit": "м2",
                "price": 100.0,
                "labor_rate": 0.5,
                "sum": 1000.0,
                "planned_labor": 5.0,
                "is_group": False
            }
        ]
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/estimates",
        json=estimate_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["number"] == "TEST-001"
    assert data["data"]["total_sum"] == 1000.0
    assert data["data"]["total_labor"] == 5.0
    assert len(data["data"]["lines"]) == 1
    
    return data["data"]["id"]


def test_get_estimate(client, auth_headers):
    """Test getting estimate by ID"""
    # First create an estimate
    estimate_id = test_create_estimate(client, auth_headers)
    
    # Get the estimate
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates/{estimate_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == estimate_id
    assert "lines" in data["data"]
    assert "customer_name" in data["data"]
    assert "object_name" in data["data"]


def test_update_estimate(client, auth_headers):
    """Test updating estimate"""
    # First create an estimate
    estimate_id = test_create_estimate(client, auth_headers)
    
    # Update the estimate
    update_data = {
        "number": "TEST-001-UPDATED",
        "date": date.today().isoformat(),
        "customer_id": 1,
        "object_id": 1,
        "contractor_id": 1,
        "responsible_id": 1,
        "lines": [
            {
                "line_number": 1,
                "work_id": 1,
                "quantity": 20.0,
                "unit": "м2",
                "price": 100.0,
                "labor_rate": 0.5,
                "sum": 2000.0,
                "planned_labor": 10.0,
                "is_group": False
            }
        ]
    }
    
    response = client.put(
        f"{settings.API_PREFIX}/documents/estimates/{estimate_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["number"] == "TEST-001-UPDATED"
    assert data["data"]["total_sum"] == 2000.0
    assert data["data"]["total_labor"] == 10.0


def test_delete_estimate(client, auth_headers):
    """Test deleting estimate"""
    # First create an estimate
    estimate_id = test_create_estimate(client, auth_headers)
    
    # Delete the estimate
    response = client.delete(
        f"{settings.API_PREFIX}/documents/estimates/{estimate_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify it's marked as deleted
    response = client.get(
        f"{settings.API_PREFIX}/documents/estimates/{estimate_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_create_estimate_with_groups(client, auth_headers):
    """Test creating estimate with hierarchical groups"""
    estimate_data = {
        "number": "TEST-002",
        "date": date.today().isoformat(),
        "customer_id": 1,
        "object_id": 1,
        "contractor_id": 1,
        "responsible_id": 1,
        "lines": [
            {
                "line_number": 1,
                "is_group": True,
                "group_name": "Группа 1",
                "quantity": 0,
                "unit": "",
                "price": 0,
                "labor_rate": 0,
                "sum": 0,
                "planned_labor": 0
            },
            {
                "line_number": 2,
                "work_id": 1,
                "parent_group_id": 1,
                "quantity": 10.0,
                "unit": "м2",
                "price": 100.0,
                "labor_rate": 0.5,
                "sum": 1000.0,
                "planned_labor": 5.0,
                "is_group": False
            }
        ]
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/estimates",
        json=estimate_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["lines"]) == 2
    # SQLite returns 1/0 for boolean, so check for truthy value
    assert data["data"]["lines"][0]["is_group"] in (True, 1)
    assert data["data"]["lines"][1]["parent_group_id"] is not None


def test_unauthorized_access(client):
    """Test that endpoints require authentication"""
    response = client.get(f"{settings.API_PREFIX}/documents/estimates")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
