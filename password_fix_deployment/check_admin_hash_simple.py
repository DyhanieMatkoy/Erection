import sqlite3
import hashlib

conn = sqlite3.connect('construction.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username = "admin"')
result = cursor.fetchone()

if result:
    username, hash_value = result
    print(f"Username: {username}")
    print(f"Hash: {hash_value}")
    print(f"Hash length: {len(hash_value)}")
    
    # Check if it's SHA256 (64 hex chars)
    if len(hash_value) == 64:
        print("✓ This is a SHA256 hash")
        
        # Verify it matches "admin"
        expected = hashlib.sha256("admin".encode('utf-8')).hexdigest()
        if hash_value == expected:
            print("✓ Hash matches password 'admin'")
        else:
            print("✗ Hash does NOT match password 'admin'")
    else:
        print("✗ This is NOT a SHA256 hash (probably bcrypt)")

conn.close()
