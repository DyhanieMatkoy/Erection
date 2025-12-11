"""Quick script to reset admin password"""
import sqlite3
import hashlib

# TEMPORARY: Using SHA256 for debugging (no bcrypt issues)
USE_SIMPLE_HASH = True

def hash_password(password: str) -> str:
    """Hash password - using simple SHA256 for debugging"""
    if USE_SIMPLE_HASH:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    else:
        # Bcrypt path (for later)
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

# Reset admin password to "admin"
conn = sqlite3.connect('construction.db')
cursor = conn.cursor()

password_hash = hash_password("admin")

cursor.execute("""
    UPDATE users 
    SET password_hash = ?
    WHERE username = 'admin'
""", (password_hash,))

if cursor.rowcount > 0:
    conn.commit()
    print("✓ Admin password reset to 'admin'")
else:
    print("✗ Admin user not found")

conn.close()
