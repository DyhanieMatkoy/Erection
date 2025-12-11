"""
Integration tests for reference endpoints
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


@pytest.fixture
def auth_token(client, setup_test_db):
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


# Counterparties tests
def test_list_counterparties(client, auth_headers):
    """Test listing counterparties"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_list_counterparties_with_pagination(client, auth_headers):
    """Test listing counterparties with pagination"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties",
        params={"page": 1, "page_size": 10},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10


def test_list_counterparties_with_search(client, auth_headers):
    """Test listing counterparties with search"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties",
        params={"search": "test"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_list_counterparties_with_sorting(client, auth_headers):
    """Test listing counterparties with sorting"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties",
        params={"sort_by": "name", "sort_order": "desc"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_create_counterparty(client, auth_headers):
    """Test creating counterparty"""
    counterparty_data = {
        "name": "Test Counterparty",
        "parent_id": None
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/counterparties",
        json=counterparty_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Counterparty"
    return data["data"]["id"]


def test_get_counterparty(client, auth_headers):
    """Test getting counterparty by ID"""
    # First create a counterparty
    counterparty_id = test_create_counterparty(client, auth_headers)
    
    # Get the counterparty
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties/{counterparty_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == counterparty_id


def test_get_nonexistent_counterparty(client, auth_headers):
    """Test getting nonexistent counterparty"""
    response = client.get(
        f"{settings.API_PREFIX}/references/counterparties/999999",
        headers=auth_headers
    )
    assert response.status_code == 404


# Objects tests
def test_list_objects(client, auth_headers):
    """Test listing objects"""
    response = client.get(
        f"{settings.API_PREFIX}/references/objects",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_create_object(client, auth_headers):
    """Test creating object"""
    object_data = {
        "name": "Test Object",
        "address": "Test Address",
        "parent_id": None
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/objects",
        json=object_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Object"


# Works tests
def test_list_works(client, auth_headers):
    """Test listing works"""
    response = client.get(
        f"{settings.API_PREFIX}/references/works",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_create_work(client, auth_headers):
    """Test creating work"""
    work_data = {
        "name": "Test Work",
        "unit": "м2",
        "price": 100.0,
        "labor_rate": 0.5,
        "parent_id": None
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/works",
        json=work_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Work"


# Persons tests
def test_list_persons(client, auth_headers):
    """Test listing persons"""
    response = client.get(
        f"{settings.API_PREFIX}/references/persons",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_create_person(client, auth_headers):
    """Test creating person"""
    person_data = {
        "full_name": "Test Person",
        "position": "Worker"
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/persons",
        json=person_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["full_name"] == "Test Person"


# Organizations tests
def test_list_organizations(client, auth_headers):
    """Test listing organizations"""
    response = client.get(
        f"{settings.API_PREFIX}/references/organizations",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_create_organization(client, auth_headers):
    """Test creating organization"""
    org_data = {
        "name": "Test Organization",
        "inn": "1234567890"
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/references/organizations",
        json=org_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Organization"


# Unauthorized access tests
def test_list_counterparties_unauthorized(client):
    """Test that listing counterparties requires authentication"""
    response = client.get(f"{settings.API_PREFIX}/references/counterparties")
    assert response.status_code == 401


def test_create_counterparty_unauthorized(client):
    """Test that creating counterparty requires authentication"""
    response = client.post(
        f"{settings.API_PREFIX}/references/counterparties",
        json={"name": "Test"}
    )
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
