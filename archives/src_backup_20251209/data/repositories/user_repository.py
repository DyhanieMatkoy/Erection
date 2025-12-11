"""User repository"""
from typing import Optional
import logging
from ..database_manager import DatabaseManager
from ..models.user import User
from ..models.sqlalchemy_models import User as UserModel

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username using SQLAlchemy session"""
        try:
            with self.db_manager.session_scope() as session:
                user_model = session.query(UserModel)\
                    .filter(UserModel.username == username)\
                    .filter(UserModel.is_active == True)\
                    .first()
                
                if not user_model:
                    return None
                
                # Convert SQLAlchemy model to dataclass
                return User(
                    id=user_model.id,
                    username=user_model.username,
                    password_hash=user_model.password_hash,
                    role=user_model.role,
                    is_active=user_model.is_active
                )
                
        except Exception as e:
            logger.error(f"Failed to find user by username '{username}': {e}")
            return None
