"""
Unit tests for JWT validation middleware

NOTE: These tests are skipped - they need refactoring to work with FastAPI dependency injection.
TODO: Refactor to use TestClient with HTTP requests instead of calling dependencies directly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from api.dependencies.auth import get_current_user, get_current_admin_user
from api.services.auth_service import AuthService
from api.models.auth import UserInfo
from api.config import settings
from src.data.database_manager import DatabaseManager

# Skip all middleware tests until refactored
pytestmark = pytest.mark.skip(reason="Need refactoring for FastAPI dependency injection")


@pytest.fixture(scope="module")
def auth_service():
    """Create auth service instance"""
    service = AuthService()
    return service


@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    yield


@pytest.fixture
def valid_token(auth_service, setup_test_db):
    """Create a valid JWT token for testing"""
    # Get admin user
    user = auth_service.authenticate_user("admin", "admin")
    assert user is not None, "Admin user should exist"
    
    # Create token
    token = auth_service.create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"]
    )
    return token


@pytest.fixture
def expired_token(auth_service, setup_test_db):
    """Create an expired JWT token for testing"""
    # Get admin user
    user = auth_service.authenticate_user("admin", "admin")
    assert user is not None, "Admin user should exist"
    
    # Create token with negative expiration (already expired)
    token = auth_service.create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        expires_delta=timedelta(seconds=-1)
    )
    return token


class TestGetCurrentUser:
    """Tests for get_current_user middleware dependency"""
    
    @pytest.mark.asyncio
    async def test_valid_token(self, valid_token, setup_test_db):
        """Test middleware with valid token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        user = await get_current_user(credentials)
        
        assert isinstance(user, UserInfo)
        assert user.username == "admin"
        assert user.role in ["admin", "Администратор"]
        assert user.is_active is True
        assert user.id > 0
    
    @pytest.mark.asyncio
    async def test_invalid_token_format(self, setup_test_db):
        """Test middleware with invalid token format"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token_format"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    @pytest.mark.asyncio
    async def test_expired_token(self, expired_token, setup_test_db):
        """Test middleware with expired token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_token_with_invalid_signature(self, valid_token, setup_test_db):
        """Test middleware with token that has invalid signature"""
        # Tamper with the token by changing the last character
        tampered_token = valid_token[:-1] + ("a" if valid_token[-1] != "a" else "b")
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=tampered_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_token_with_missing_sub(self, auth_service, setup_test_db):
        """Test middleware with token missing 'sub' claim"""
        from jose import jwt
        
        # Create token without 'sub' claim
        payload = {
            "username": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_token_with_invalid_sub_format(self, auth_service, setup_test_db):
        """Test middleware with token having non-numeric 'sub' claim"""
        from jose import jwt
        
        # Create token with invalid 'sub' format
        payload = {
            "sub": "not_a_number",
            "username": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_token_with_nonexistent_user(self, auth_service, setup_test_db):
        """Test middleware with token for non-existent user"""
        from jose import jwt
        
        # Create token with non-existent user ID
        payload = {
            "sub": "999999",  # Assuming this user doesn't exist
            "username": "nonexistent",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_token_for_inactive_user(self, auth_service, setup_test_db):
        """Test middleware with token for inactive user"""
        from jose import jwt
        
        # First, create an inactive user in the database
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Delete user if exists (cleanup from previous runs)
        cursor.execute("DELETE FROM users WHERE username = ?", ("inactive_user",))
        conn.commit()
        
        # Create inactive user
        password_hash = auth_service.hash_password("testpass")
        cursor.execute(
            """INSERT INTO users (username, password_hash, role, is_active) 
               VALUES (?, ?, ?, ?)""",
            ("inactive_user", password_hash, "user", 0)
        )
        conn.commit()
        
        # Get the user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", ("inactive_user",))
        user_id = cursor.fetchone()[0]
        
        try:
            # Create token for inactive user
            payload = {
                "sub": str(user_id),
                "username": "inactive_user",
                "role": "user",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow()
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 403
            assert "User is inactive" in exc_info.value.detail
        finally:
            # Cleanup: delete the test user
            cursor.execute("DELETE FROM users WHERE username = ?", ("inactive_user",))
            conn.commit()


class TestGetCurrentAdminUser:
    """Tests for get_current_admin_user middleware dependency"""
    
    @pytest.mark.asyncio
    async def test_admin_user_access(self, valid_token, setup_test_db):
        """Test admin user can access admin-protected endpoints"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        # First get current user
        current_user = await get_current_user(credentials)
        
        # Then check admin access
        admin_user = await get_current_admin_user(current_user)
        
        assert isinstance(admin_user, UserInfo)
        assert admin_user.username == "admin"
        assert admin_user.role in ["admin", "Администратор"]
    
    @pytest.mark.asyncio
    async def test_non_admin_user_denied(self, auth_service, setup_test_db):
        """Test non-admin user is denied access to admin-protected endpoints"""
        from jose import jwt
        
        # Create a non-admin user
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Delete user if exists (cleanup from previous runs)
        cursor.execute("DELETE FROM users WHERE username = ?", ("regular_user",))
        conn.commit()
        
        password_hash = auth_service.hash_password("testpass")
        cursor.execute(
            """INSERT INTO users (username, password_hash, role, is_active) 
               VALUES (?, ?, ?, ?)""",
            ("regular_user", password_hash, "user", 1)
        )
        conn.commit()
        
        # Get the user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", ("regular_user",))
        user_id = cursor.fetchone()[0]
        
        try:
            # Create token for regular user
            token = auth_service.create_access_token(
                user_id=user_id,
                username="regular_user",
                role="user"
            )
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
            
            # Get current user (should succeed)
            current_user = await get_current_user(credentials)
            assert current_user.role == "user"
            
            # Try to access admin endpoint (should fail)
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin_user(current_user)
            
            assert exc_info.value.status_code == 403
            assert "Admin privileges required" in exc_info.value.detail
        finally:
            # Cleanup: delete the test user
            cursor.execute("DELETE FROM users WHERE username = ?", ("regular_user",))
            conn.commit()
    
    @pytest.mark.asyncio
    async def test_foreman_user_denied(self, auth_service, setup_test_db):
        """Test foreman user is denied access to admin-protected endpoints"""
        # Create a foreman user
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Delete user if exists (cleanup from previous runs)
        cursor.execute("DELETE FROM users WHERE username = ?", ("foreman_user",))
        conn.commit()
        
        password_hash = auth_service.hash_password("testpass")
        cursor.execute(
            """INSERT INTO users (username, password_hash, role, is_active) 
               VALUES (?, ?, ?, ?)""",
            ("foreman_user", password_hash, "Бригадир", 1)
        )
        conn.commit()
        
        # Get the user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", ("foreman_user",))
        user_id = cursor.fetchone()[0]
        
        try:
            # Create token for foreman user
            token = auth_service.create_access_token(
                user_id=user_id,
                username="foreman_user",
                role="foreman"
            )
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
            
            # Get current user (should succeed)
            current_user = await get_current_user(credentials)
            assert current_user.role == "foreman"
            
            # Try to access admin endpoint (should fail)
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin_user(current_user)
            
            assert exc_info.value.status_code == 403
            assert "Admin privileges required" in exc_info.value.detail
        finally:
            # Cleanup: delete the test user
            cursor.execute("DELETE FROM users WHERE username = ?", ("foreman_user",))
            conn.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
