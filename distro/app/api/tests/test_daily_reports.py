"""
Integration tests for daily report endpoints
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


def test_list_daily_reports(client, auth_headers):
    """Test listing daily reports"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/daily-reports",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data


def test_list_daily_reports_with_filters(client, auth_headers):
    """Test listing daily reports with filters"""
    response = client.get(
        f"{settings.API_PREFIX}/documents/daily-reports",
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


def test_create_daily_report(client, auth_headers):
    """Test creating daily report"""
    report_data = {
        "date": date.today().isoformat(),
        "estimate_id": 1,
        "foreman_id": 1,
        "lines": [
            {
                "line_number": 1,
                "work_id": 1,
                "planned_labor": 5.0,
                "actual_labor": 4.5,
                "deviation_percent": -10.0,
                "executor_ids": [1]
            }
        ]
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/daily-reports",
        json=report_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["date"] == date.today().isoformat()
    assert len(data["data"]["lines"]) == 1
    
    return data["data"]["id"]


def test_get_daily_report(client, auth_headers):
    """Test getting daily report by ID"""
    # First create a report
    report_id = test_create_daily_report(client, auth_headers)
    
    # Get the report
    response = client.get(
        f"{settings.API_PREFIX}/documents/daily-reports/{report_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == report_id
    assert "lines" in data["data"]
    assert "estimate_number" in data["data"]
    assert "foreman_name" in data["data"]


def test_update_daily_report(client, auth_headers):
    """Test updating daily report"""
    # First create a report
    report_id = test_create_daily_report(client, auth_headers)
    
    # Update the report
    update_data = {
        "date": date.today().isoformat(),
        "estimate_id": 1,
        "foreman_id": 1,
        "lines": [
            {
                "line_number": 1,
                "work_id": 1,
                "planned_labor": 5.0,
                "actual_labor": 5.5,
                "deviation_percent": 10.0,
                "executor_ids": [1]
            }
        ]
    }
    
    response = client.put(
        f"{settings.API_PREFIX}/documents/daily-reports/{report_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["lines"][0]["actual_labor"] == 5.5


def test_delete_daily_report(client, auth_headers):
    """Test deleting daily report"""
    # First create a report
    report_id = test_create_daily_report(client, auth_headers)
    
    # Delete the report
    response = client.delete(
        f"{settings.API_PREFIX}/documents/daily-reports/{report_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify it's marked as deleted
    response = client.get(
        f"{settings.API_PREFIX}/documents/daily-reports/{report_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_create_daily_report_with_multiple_executors(client, auth_headers):
    """Test creating daily report with multiple executors"""
    report_data = {
        "date": date.today().isoformat(),
        "estimate_id": 1,
        "foreman_id": 1,
        "lines": [
            {
                "line_number": 1,
                "work_id": 1,
                "planned_labor": 10.0,
                "actual_labor": 9.0,
                "deviation_percent": -10.0,
                "executor_ids": [1, 2]
            }
        ]
    }
    
    response = client.post(
        f"{settings.API_PREFIX}/documents/daily-reports",
        json=report_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["lines"][0]["executor_ids"]) == 2


def test_unauthorized_access(client):
    """Test that endpoints require authentication"""
    response = client.get(f"{settings.API_PREFIX}/documents/daily-reports")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
