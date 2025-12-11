"""
Integration tests for register endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
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


def test_get_work_execution_register(auth_headers):
    """Test getting work execution register"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


def test_get_work_execution_register_with_period(auth_headers):
    """Test getting work execution register with period filter"""
    today = date.today()
    period_from = (today - timedelta(days=30)).isoformat()
    period_to = today.isoformat()
    
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={
            "period_from": period_from,
            "period_to": period_to
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_register_with_object_filter(auth_headers):
    """Test getting work execution register with object filter"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={"object_id": 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_register_with_estimate_filter(auth_headers):
    """Test getting work execution register with estimate filter"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={"estimate_id": 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_register_with_work_filter(auth_headers):
    """Test getting work execution register with work filter"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={"work_id": 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_register_with_grouping(auth_headers):
    """Test getting work execution register with grouping"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={"group_by": "object"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_register_with_pagination(auth_headers):
    """Test getting work execution register with pagination"""
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={
            "page": 1,
            "page_size": 10
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data


def test_get_work_execution_register_with_all_filters(auth_headers):
    """Test getting work execution register with all filters"""
    today = date.today()
    period_from = (today - timedelta(days=30)).isoformat()
    period_to = today.isoformat()
    
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution",
        params={
            "period_from": period_from,
            "period_to": period_to,
            "object_id": 1,
            "estimate_id": 1,
            "work_id": 1,
            "group_by": "work",
            "page": 1,
            "page_size": 20
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_work_execution_movements(auth_headers):
    """Test getting detailed work execution movements"""
    today = date.today()
    period_from = (today - timedelta(days=30)).isoformat()
    period_to = today.isoformat()
    
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution/movements",
        params={
            "period_from": period_from,
            "period_to": period_to
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_get_work_execution_movements_with_filters(auth_headers):
    """Test getting detailed work execution movements with filters"""
    today = date.today()
    period_from = (today - timedelta(days=30)).isoformat()
    period_to = today.isoformat()
    
    response = client.get(
        f"{settings.API_PREFIX}/registers/work-execution/movements",
        params={
            "period_from": period_from,
            "period_to": period_to,
            "object_id": 1,
            "estimate_id": 1,
            "work_id": 1
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_unauthorized_access():
    """Test that endpoints require authentication"""
    response = client.get(f"{settings.API_PREFIX}/registers/work-execution")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
