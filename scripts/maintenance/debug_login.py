"""Debug login issue"""
import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get admin hash
conn = sqlite3.connect('construction.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username=?', ('admin',))
row = cursor.fetchone()

if row:
    username = row[0]
    stored_hash = row[1]
    
    print(f'Username: {username}')
    print(f'Stored hash length: {len(stored_hash)} bytes')
    print(f'Stored hash: {stored_hash}')
    print()
    
    # Test password
    test_password = 'admin'
    print(f'Test password: "{test_password}"')
    print(f'Test password length: {len(test_password)} bytes')
    print()
    
    # Truncate password
    password_bytes = test_password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    print(f'Truncated password: "{password_truncated}"')
    print(f'Truncated password length: {len(password_truncated)} bytes')
    print()
    
    # Try to verify
    print('Attempting verification...')
    try:
        result = pwd_context.verify(password_truncated, stored_hash)
        print(f'SUCCESS: Verification result = {result}')
    except Exception as e:
        print(f'ERROR: {e}')
        print(f'Error type: {type(e).__name__}')
        
        # Check if hash is being passed as password
        print()
        print('Checking if hash is too long...')
        print(f'Hash length: {len(stored_hash)}')
        if len(stored_hash) > 72:
            print('WARNING: Hash is longer than 72 bytes!')
            print('This suggests the hash might be passed as password somewhere')
else:
    print('Admin user not found')

conn.close()
