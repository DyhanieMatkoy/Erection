"""Test login directly"""
import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with 72-byte truncation"""
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password_truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with 72-byte truncation"""
    plain_password_bytes = plain_password.encode('utf-8')[:72]
    plain_password_truncated = plain_password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password_truncated, hashed_password)

# Get admin hash
conn = sqlite3.connect('construction.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username=?', ('admin',))
row = cursor.fetchone()

if row:
    username = row[0]
    stored_hash = row[1]
    
    print(f'Username: {username}')
    print(f'Hash length: {len(stored_hash)} bytes')
    print(f'Hash starts with: {stored_hash[:20]}')
    
    # Try to verify
    print('\nTrying to verify password "admin"...')
    try:
        result = verify_password('admin', stored_hash)
        print(f'Verification result: {result}')
        print('SUCCESS - No error occurred')
    except Exception as e:
        print(f'Verification error: {e}')
        print(f'Error type: {type(e).__name__}')
        import traceback
        traceback.print_exc()
        
        # Try to identify the hash
        print(f'\nHash info:')
        print(f'  Starts with $2b$: {stored_hash.startswith("$2b$")}')
        print(f'  Starts with $2a$: {stored_hash.startswith("$2a$")}')
        print(f'  Starts with $2y$: {stored_hash.startswith("$2y$")}')
else:
    print('Admin user not found')

conn.close()
