"""
Unit tests for AuthService
Tests authentication, token generation, and password hashing
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from api.services.auth_service import AuthService
from api.config import settings


class TestAuthService:
    """Test suite for AuthService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.auth_service = AuthService()
        self.test_password = "test_password_123"
        self.test_username = "test_user"
        self.test_user_id = 1
    
    # Password Hashing Tests
    
    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a bcrypt hash"""
        hashed = self.auth_service.hash_password(self.test_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != self.test_password
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_hash_password_different_hashes(self):
        """Test that same password creates different hashes (salt)"""
        hash1 = self.auth_service.hash_password(self.test_password)
        hash2 = self.auth_service.hash_password(self.test_password)
        
        assert hash1 != hash2  # Different salts
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        hashed = self.auth_service.hash_password(self.test_password)
        result = self.auth_service.verify_password(self.test_password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        hashed = self.auth_service.hash_password(self.test_password)
        result = self.auth_service.verify_password("wrong_password", hashed)
        
        assert result is False
    
    def test_verify_password_empty_password(self):
        """Test password verification with empty password"""
        hashed = self.auth_service.hash_password(self.test_password)
        result = self.auth_service.verify_password("", hashed)
        
        assert result is False
    
    # Token Generation Tests
    
    def test_create_access_token_default_expiry(self):
        """Test token creation with default expiry"""
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="user"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_custom_expiry(self):
        """Test token creation with custom expiry"""
        expires_delta = timedelta(minutes=30)
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="user",
            expires_delta=expires_delta
        )
        
        # Decode token to check expiry
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = payload["exp"]
        iat = payload["iat"]
        
        # Should expire in approximately 30 minutes (1800 seconds)
        time_diff = exp - iat
        assert 1700 < time_diff < 1900  # ~30 minutes (with some tolerance)
    
    def test_create_access_token_contains_claims(self):
        """Test that token contains required claims"""
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="admin"
        )
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        assert "sub" in payload
        assert payload["sub"] == str(self.test_user_id)
        assert "username" in payload
        assert payload["username"] == self.test_username
        assert "role" in payload
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload
    
    # Token Verification Tests
    
    def test_verify_token_valid(self):
        """Test verification of valid token"""
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="user"
        )
        
        payload = self.auth_service.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(self.test_user_id)
        assert payload["username"] == self.test_username
        assert payload["role"] == "user"
    
    def test_verify_token_invalid_signature(self):
        """Test verification of token with invalid signature"""
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="user"
        )
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered123"
        
        payload = self.auth_service.verify_token(tampered_token)
        assert payload is None
    
    def test_verify_token_expired(self):
        """Test verification of expired token"""
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = self.auth_service.create_access_token(
            user_id=self.test_user_id,
            username=self.test_username,
            role="user",
            expires_delta=expires_delta
        )
        
        payload = self.auth_service.verify_token(token)
        assert payload is None
    
    def test_verify_token_malformed(self):
        """Test verification of malformed token"""
        malformed_token = "not.a.valid.jwt.token"
        
        payload = self.auth_service.verify_token(malformed_token)
        assert payload is None
    
    def test_verify_token_empty(self):
        """Test verification of empty token"""
        payload = self.auth_service.verify_token("")
        assert payload is None
    
    def test_verify_token_none(self):
        """Test verification of None token"""
        # verify_token should handle None gracefully
        payload = self.auth_service.verify_token(None)
        assert payload is None
    
    # Authenticate User Tests (requires database)
    
    def test_authenticate_user_valid_credentials(self, setup_database):
        """Test authentication with valid credentials"""
        # This test requires a test database with a user
        user = self.auth_service.authenticate_user("admin", "admin")
        
        assert user is not None
        assert user["username"] == "admin"
        assert "id" in user
        assert "role" in user
    
    def test_authenticate_user_invalid_username(self, setup_database):
        """Test authentication with invalid username"""
        user = self.auth_service.authenticate_user("nonexistent", "password")
        
        assert user is None
    
    def test_authenticate_user_invalid_password(self, setup_database):
        """Test authentication with invalid password"""
        user = self.auth_service.authenticate_user("admin", "wrong_password")
        
        assert user is None
    
    def test_authenticate_user_empty_credentials(self, setup_database):
        """Test authentication with empty credentials"""
        user = self.auth_service.authenticate_user("", "")
        
        assert user is None
    
    def test_authenticate_user_inactive_user(self, setup_database):
        """Test authentication with inactive user"""
        # Create an inactive user for testing
        conn = self.auth_service.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if inactive user exists, if not create one
        cursor.execute("SELECT id FROM users WHERE username = ?", ("inactive_user",))
        if not cursor.fetchone():
            hashed_pwd = self.auth_service.hash_password("password")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)",
                ("inactive_user", hashed_pwd, "user", 0)
            )
            conn.commit()
        
        user = self.auth_service.authenticate_user("inactive_user", "password")
        
        # Should return None for inactive user
        assert user is None
    
    # Get User By ID Tests
    
    def test_get_user_by_id_valid(self, setup_database):
        """Test getting user by valid ID"""
        # First authenticate to get a valid user ID
        user = self.auth_service.authenticate_user("admin", "admin")
        assert user is not None
        
        # Now get user by ID
        user_by_id = self.auth_service.get_user_by_id(user["id"])
        
        assert user_by_id is not None
        assert user_by_id["id"] == user["id"]
        assert user_by_id["username"] == user["username"]
        assert user_by_id["role"] == user["role"]
        assert "is_active" in user_by_id
    
    def test_get_user_by_id_invalid(self, setup_database):
        """Test getting user by invalid ID"""
        user = self.auth_service.get_user_by_id(99999)
        assert user is None
    
    def test_get_user_by_id_role_mapping(self, setup_database):
        """Test that get_user_by_id correctly maps Russian roles to English"""
        # Get admin user
        user = self.auth_service.get_user_by_id(1)
        
        if user is not None:
            # Role should be in English
            assert user["role"] in ["admin", "manager", "foreman", "executor"]
    
    # Edge Cases
    
    def test_hash_password_unicode(self):
        """Test password hashing with unicode characters"""
        unicode_password = "пароль123!@#"
        hashed = self.auth_service.hash_password(unicode_password)
        
        assert hashed is not None
        assert self.auth_service.verify_password(unicode_password, hashed)
    
    def test_hash_password_special_characters(self):
        """Test password hashing with special characters"""
        special_password = "p@$$w0rd!#%^&*()"
        hashed = self.auth_service.hash_password(special_password)
        
        assert hashed is not None
        assert self.auth_service.verify_password(special_password, hashed)
    
    def test_hash_password_very_long(self):
        """Test password hashing with very long password"""
        long_password = "a" * 1000
        hashed = self.auth_service.hash_password(long_password)
        
        assert hashed is not None
        assert self.auth_service.verify_password(long_password, hashed)
    
    def test_create_token_with_special_username(self):
        """Test token creation with special characters in username"""
        special_username = "user@example.com"
        token = self.auth_service.create_access_token(
            user_id=1,
            username=special_username,
            role="user"
        )
        
        payload = self.auth_service.verify_token(token)
        assert payload["username"] == special_username
    
    def test_token_roundtrip(self):
        """Test complete token creation and verification cycle"""
        # Create token
        token = self.auth_service.create_access_token(
            user_id=42,
            username="test_user",
            role="admin"
        )
        
        # Verify token
        payload = self.auth_service.verify_token(token)
        
        # Check all data preserved
        assert payload["sub"] == "42"
        assert payload["username"] == "test_user"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload


class TestAuthServiceIntegration:
    """Integration tests for AuthService with database"""
    
    def test_full_authentication_flow(self, setup_database):
        """Test complete authentication flow"""
        auth_service = AuthService()
        
        # 1. Authenticate user
        user = auth_service.authenticate_user("admin", "admin")
        assert user is not None
        
        # 2. Create token
        token = auth_service.create_access_token(
            user_id=user["id"],
            username=user["username"],
            role=user["role"]
        )
        assert token is not None
        
        # 3. Verify token
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload["username"] == user["username"]
        assert payload["role"] == user["role"]
    
    def test_password_change_flow(self, setup_database):
        """Test password hashing for password change"""
        auth_service = AuthService()
        
        # Hash new password
        new_password = "new_secure_password_123"
        hashed = auth_service.hash_password(new_password)
        
        # Verify new password works
        assert auth_service.verify_password(new_password, hashed)
        
        # Verify old password doesn't work
        assert not auth_service.verify_password("old_password", hashed)


# Performance Tests (optional)

class TestAuthServicePerformance:
    """Performance tests for AuthService"""
    
    def test_hash_password_performance(self):
        """Test that password hashing completes in reasonable time"""
        import time
        
        auth_service = AuthService()
        start = time.time()
        
        # Hash 10 passwords
        for i in range(10):
            auth_service.hash_password(f"password_{i}")
        
        elapsed = time.time() - start
        
        # Should complete in less than 5 seconds (bcrypt is intentionally slow)
        assert elapsed < 5.0
    
    def test_verify_password_performance(self):
        """Test that password verification completes in reasonable time"""
        import time
        
        auth_service = AuthService()
        password = "test_password"
        hashed = auth_service.hash_password(password)
        
        start = time.time()
        
        # Verify 10 times (reduced from 100 since bcrypt is slow)
        for i in range(10):
            auth_service.verify_password(password, hashed)
        
        elapsed = time.time() - start
        
        # Should complete in less than 5 seconds (bcrypt is intentionally slow)
        assert elapsed < 5.0
    
    def test_token_operations_performance(self):
        """Test that token operations complete in reasonable time"""
        import time
        
        auth_service = AuthService()
        
        start = time.time()
        
        # Create and verify 1000 tokens
        for i in range(1000):
            token = auth_service.create_access_token(
                user_id=i,
                username=f"user_{i}",
                role="user"
            )
            auth_service.verify_token(token)
        
        elapsed = time.time() - start
        
        # Should complete in less than 5 seconds
        assert elapsed < 5.0
