"""User repository"""
from typing import Optional
from ..database_manager import DatabaseManager
from ..models.user import User


class UserRepository:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = ? AND is_active = 1
        """, (username,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return User(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            role=row['role'],
            is_active=bool(row['is_active'])
        )
