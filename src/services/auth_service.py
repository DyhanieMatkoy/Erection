"""Authentication service"""
import hashlib
from typing import Optional
from ..data.repositories.user_repository import UserRepository
from ..data.models.user import User


class AuthService:
    _instance = None
    _current_user: Optional[User] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def login(self, username: str, password: str) -> Optional[User]:
        """Login user"""
        repo = UserRepository()
        user = repo.find_by_username(username)
        
        if not user:
            return None
        
        password_hash = self._hash_password(password)
        if user.password_hash != password_hash:
            return None
        
        self._current_user = user
        return user
    
    def logout(self):
        """Logout current user"""
        self._current_user = None
    
    def current_user(self) -> Optional[User]:
        """Get current user"""
        return self._current_user
    
    def has_permission(self, action: str) -> bool:
        """Check if current user has permission"""
        if not self._current_user:
            return False
        
        role = self._current_user.role
        if role in ["Администратор", "Руководитель"]:
            return True
        
        return False
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
