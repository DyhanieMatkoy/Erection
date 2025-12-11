"""
Setup test database with proper password hashing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from passlib.context import CryptContext
from src.data.database_manager import DatabaseManager
from api.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_test_users():
    """Setup test users with properly hashed passwords"""
    db_manager = DatabaseManager()
    db_manager.initialize(settings.DATABASE_PATH)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if admin user exists
        cursor.execute("SELECT id, password_hash FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            # Re-hash the password
            hashed = pwd_context.hash("admin")
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hashed, admin[0])
            )
            conn.commit()
            print(f"Updated admin user password hash: {hashed[:20]}...")
        else:
            # Create admin user
            hashed = pwd_context.hash("admin")
            cursor.execute(
                """INSERT INTO users (username, password_hash, role, is_active)
                   VALUES (?, ?, ?, ?)""",
                ("admin", hashed, "admin", 1)
            )
            conn.commit()
            print("Created admin user")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_test_users()
