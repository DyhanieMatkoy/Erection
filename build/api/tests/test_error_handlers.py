"""
Unit tests for custom error handlers
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError, field_validator
from api.main import app, http_exception_handler, validation_exception_handler, general_exception_handler
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
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


class TestHTTPExceptionHandler:
    """Tests for HTTP exception handler"""
    
    def test_404_error_format(self):
        """Test 404 error returns consistent JSON format"""
        response = client.get(f"{settings.API_PREFIX}/nonexistent/endpoint")
        
        assert response.status_code == 404
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        
        # Check error structure
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "path" in error
        
        # Check error values
        assert error["code"] == "HTTP_404"
        assert "path" in error
    
    def test_401_error_format(self):
        """Test 401 error returns consistent JSON format"""
        # Use invalid token to get 401
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "HTTP_401"
        assert "message" in data["error"]
        assert "path" in data["error"]
    
    def test_403_error_format(self, setup_test_db):
        """Test 403 error returns consistent JSON format"""
        # Test with no credentials (HTTPBearer now returns 401)
        response = client.get(f"{settings.API_PREFIX}/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "HTTP_401"
        assert "message" in data["error"]
    
    def test_405_error_format(self):
        """Test 405 Method Not Allowed error format"""
        # Try POST on a GET-only endpoint
        response = client.post(f"{settings.API_PREFIX}/auth/me")
        
        assert response.status_code == 405
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "HTTP_405"


class TestValidationExceptionHandler:
    """Tests for validation exception handler"""
    
    def test_validation_error_format(self, auth_headers):
        """Test validation error returns detailed field information"""
        # Send invalid data to create estimate
        invalid_data = {
            "number": "",  # Empty string
            "date": "invalid-date",  # Invalid date format
        }
        
        response = client.post(
            f"{settings.API_PREFIX}/documents/estimates",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert "error" in data
        
        # Check error structure
        error = data["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "Validation failed"
        assert "details" in error
        
        # Check details is a list
        assert isinstance(error["details"], list)
        assert len(error["details"]) > 0
        
        # Check each detail has required fields
        for detail in error["details"]:
            assert "field" in detail
            assert "message" in detail
            assert "type" in detail
    
    def test_missing_required_field_validation(self, auth_headers):
        """Test validation error for missing required fields"""
        # Missing required fields
        incomplete_data = {
            "number": "TEST-001"
            # Missing date
        }
        
        response = client.post(
            f"{settings.API_PREFIX}/documents/estimates",
            json=incomplete_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert len(data["error"]["details"]) > 0
        
        # Check that date field is mentioned in errors
        fields = [detail["field"] for detail in data["error"]["details"]]
        assert any("date" in field for field in fields)
    
    def test_invalid_type_validation(self, auth_headers):
        """Test validation error for invalid field types"""
        # Invalid types
        invalid_data = {
            "number": "TEST-001",
            "date": "2024-01-01",
            "customer_id": "not-a-number",  # Should be int
            "lines": []
        }
        
        response = client.post(
            f"{settings.API_PREFIX}/documents/estimates",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        details = data["error"]["details"]
        
        # Check that customer_id is mentioned
        fields = [detail["field"] for detail in details]
        assert any("customer_id" in field for field in fields)
    
    def test_invalid_query_parameter_validation(self, auth_headers):
        """Test validation error for invalid query parameters"""
        # Invalid query parameters
        response = client.get(
            f"{settings.API_PREFIX}/documents/estimates",
            params={"page": -1, "page_size": 0},  # Invalid values
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert len(data["error"]["details"]) > 0


class TestGeneralExceptionHandler:
    """Tests for general exception handler"""
    
    def test_general_exception_format(self):
        """Test that unexpected exceptions return 500 with consistent format"""
        # This is harder to test without creating a route that raises an exception
        # We'll test the handler function directly
        
        from starlette.requests import Request
        from starlette.datastructures import URL
        
        # Create a mock request
        class MockRequest:
            def __init__(self):
                self.url = type('obj', (object,), {'path': '/test/path'})()
        
        request = MockRequest()
        exc = Exception("Test exception")
        
        # Call handler
        import asyncio
        response = asyncio.run(general_exception_handler(request, exc))
        
        # Check response
        assert response.status_code == 500
        
        # Parse JSON body
        import json
        body = json.loads(response.body.decode())
        
        assert body["success"] is False
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert body["error"]["message"] == "An unexpected error occurred"
        assert "path" in body["error"]


class TestErrorHandlerIntegration:
    """Integration tests for error handlers with actual endpoints"""
    
    def test_authentication_error_flow(self, setup_test_db):
        """Test complete authentication error flow"""
        # No token (returns 401 from HTTPBearer)
        response = client.get(f"{settings.API_PREFIX}/auth/me")
        assert response.status_code == 401
        assert response.json()["success"] is False
        
        # Invalid token
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
        assert response.json()["success"] is False
        
        # Wrong credentials
        response = client.post(
            f"{settings.API_PREFIX}/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401
        assert response.json()["success"] is False
    
    def test_not_found_error_flow(self, auth_headers):
        """Test complete not found error flow"""
        # Test various not found scenarios
        endpoints = [
            f"{settings.API_PREFIX}/documents/estimates/999999",
            f"{settings.API_PREFIX}/documents/daily-reports/999999",
            f"{settings.API_PREFIX}/references/counterparties/999999",
            f"{settings.API_PREFIX}/references/objects/999999",
            f"{settings.API_PREFIX}/references/works/999999",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "HTTP_404"
    
    def test_validation_error_flow(self, auth_headers):
        """Test complete validation error flow"""
        # Test various validation scenarios
        test_cases = [
            {
                "endpoint": f"{settings.API_PREFIX}/documents/estimates",
                "data": {"number": "", "date": "invalid"},
                "method": "post"
            },
            {
                "endpoint": f"{settings.API_PREFIX}/references/counterparties",
                "data": {"name": ""},
                "method": "post"
            },
        ]
        
        for test_case in test_cases:
            if test_case["method"] == "post":
                response = client.post(
                    test_case["endpoint"],
                    json=test_case["data"],
                    headers=auth_headers
                )
            
            assert response.status_code == 422
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "VALIDATION_ERROR"
            assert "details" in data["error"]


class TestErrorResponseConsistency:
    """Tests to ensure all error responses follow the same format"""
    
    def test_all_errors_have_success_false(self, auth_headers):
        """Test that all error responses have success: false"""
        # Test various error scenarios
        error_responses = [
            client.get(f"{settings.API_PREFIX}/nonexistent"),  # 404
            client.get(f"{settings.API_PREFIX}/auth/me"),  # 403 (no token)
            client.post(f"{settings.API_PREFIX}/auth/me"),  # 405
            client.post(
                f"{settings.API_PREFIX}/documents/estimates",
                json={"invalid": "data"},
                headers=auth_headers
            ),  # 422
        ]
        
        for response in error_responses:
            if response.status_code >= 400:
                data = response.json()
                assert "success" in data
                assert data["success"] is False
                assert "error" in data
    
    def test_all_errors_have_error_object(self, auth_headers):
        """Test that all error responses have an error object with required fields"""
        error_responses = [
            client.get(f"{settings.API_PREFIX}/nonexistent"),
            client.get(f"{settings.API_PREFIX}/auth/me"),
            client.post(
                f"{settings.API_PREFIX}/documents/estimates",
                json={"number": "", "date": "invalid"},
                headers=auth_headers
            ),
        ]
        
        for response in error_responses:
            if response.status_code >= 400:
                data = response.json()
                assert "error" in data
                error = data["error"]
                assert "code" in error
                assert "message" in error
                # Some errors have additional fields like 'details' or 'path'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
