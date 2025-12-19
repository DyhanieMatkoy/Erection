"""
Authentication service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
from sqlalchemy.orm import Session
from api.config import settings
from src.data.models.sqlalchemy_models import User as UserModel


# TEMPORARY: Using SHA256 for debugging (no bcrypt issues)
# TODO: Switch back to bcrypt after fixing the issue
USE_SIMPLE_HASH = True

# Role mapping from Russian to English
ROLE_MAPPING = {
    "Администратор": "admin",
    "Руководитель": "manager",
    "Бригадир": "foreman",
    "Исполнитель": "executor"
}

# Reverse mapping
ROLE_MAPPING_REVERSE = {v: k for k, v in ROLE_MAPPING.items()}


def simple_hash(password: str) -> str:
    """Simple SHA256 hash for debugging (no salt, not secure for production)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def simple_verify(password: str, hashed: str) -> bool:
    """Verify password against SHA256 hash"""
    return simple_hash(password) == hashed


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize auth service
        
        Args:
            db: Optional SQLAlchemy session. If not provided, will use legacy connection.
        """
        self.db = db
        self._db_manager = None
    
    @property
    def db_manager(self):
        """Get database manager for legacy tests"""
        if self._db_manager is None:
            from src.data.database_manager import DatabaseManager
            self._db_manager = DatabaseManager()
            if not self._db_manager._connection:
                self._db_manager.initialize(settings.DATABASE_PATH)
        return self._db_manager
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        if USE_SIMPLE_HASH:
            return simple_verify(plain_password, hashed_password)
        else:
            # Bcrypt path (for later)
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        if USE_SIMPLE_HASH:
            return simple_hash(password)
        else:
            # Bcrypt path (for later)
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str, db: Optional[Session] = None) -> Optional[dict]:
        """
        Authenticate a user by username and password
        Returns user dict if successful, None otherwise
        
        Args:
            username: Username to authenticate
            password: Plain text password
            db: Optional SQLAlchemy session
        """
        session = db or self.db
        
        if session:
            # Use SQLAlchemy
            user = session.query(UserModel).filter_by(username=username).first()
            
            if not user:
                return None
            
            user_dict = {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role,
                "is_active": user.is_active
            }
        else:
            # Fall back to legacy connection
            from src.data.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            if not db_manager._connection:
                db_manager.initialize(settings.DATABASE_PATH)
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, password_hash, role, is_active FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return None
            
            user_dict = {
                "id": user[0],
                "username": user[1],
                "password_hash": user[2],
                "role": user[3],
                "is_active": bool(user[4])
            }
        
        # Check if user is active
        if not user_dict["is_active"]:
            return None
        
        # Verify password
        if not self.verify_password(password, user_dict["password_hash"]):
            return None
        
        # Map role to English
        if user_dict["role"] in ROLE_MAPPING:
            user_dict["role"] = ROLE_MAPPING[user_dict["role"]]
        
        # Remove password hash from return value
        del user_dict["password_hash"]
        return user_dict
    
    def create_access_token(self, user_id: int, username: str, role: str, 
                           expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        to_encode = {
            "sub": str(user_id),  # JWT standard requires sub to be a string
            "username": username,
            "role": role,
            "exp": expire,
            "iat": now
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token
        Returns token payload if valid, None otherwise
        """
        if not token:
            return None
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    def get_user_by_id(self, user_id: int, db: Optional[Session] = None) -> Optional[dict]:
        """Get user by ID
        
        Args:
            user_id: User ID to retrieve
            db: Optional SQLAlchemy session
        """
        session = db or self.db
        
        if session:
            # Use SQLAlchemy
            user = session.query(UserModel).filter_by(id=user_id).first()
            
            if not user:
                return None
            
            role = user.role
            # Map role to English
            if role in ROLE_MAPPING:
                role = ROLE_MAPPING[role]
            
            return {
                "id": user.id,
                "username": user.username,
                "role": role,
                "is_active": user.is_active
            }
        else:
            # Fall back to legacy connection
            from src.data.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            if not db_manager._connection:
                db_manager.initialize(settings.DATABASE_PATH)
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, role, is_active FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return None
            
            role = user[2]
            # Map role to English
            if role in ROLE_MAPPING:
                role = ROLE_MAPPING[role]
            
            return {
                "id": user[0],
                "username": user[1],
                "role": role,
                "is_active": bool(user[3])
            }

    def has_permission(self, role: str, action: str, resource: str = None) -> bool:
        """
        Check if user role has permission for an action
        
        Args:
            role: User role (admin, manager, foreman, executor)
            action: Action to check (create_general, create_plan, modify_hierarchy, etc.)
            resource: Resource type (estimate, daily_report)
        """
        # Admin has full access
        if role == 'admin':
            return True
            
        # Manager has full access to estimates
        if role == 'manager':
            if resource == 'estimate':
                return True
            return True
            
        # Foreman permissions
        if role == 'foreman':
            if resource == 'estimate':
                if action == 'create_plan':
                    return True
                if action in ['view', 'create']: # Basic create might refer to plan?
                    return True
                if action in ['create_general', 'modify_hierarchy']:
                    return False
            return False
            
        # Executor permissions
        if role == 'executor':
            if action == 'view':
                return True
            return False
            
        return False

