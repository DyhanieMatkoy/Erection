"""Check admin password hash"""
import sqlite3

conn = sqlite3.connect('construction.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username=?', ('admin',))
row = cursor.fetchone()

if row:
    username = row[0]
    stored_hash = row[1]
    
    print(f'Username: {username}')
    print(f'Hash length: {len(stored_hash)} bytes')
    print(f'Hash type: {type(stored_hash)}')
    print(f'Hash starts with: {stored_hash[:30]}')
    print(f'Hash ends with: {stored_hash[-30:]}')
    
    # Check if it's a valid bcrypt hash format
    if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$') or stored_hash.startswith('$2y$'):
        print('Hash format: Valid bcrypt format')
    else:
        print('Hash format: INVALID - not a bcrypt hash!')
        print(f'Full hash: {stored_hash}')
else:
    print('Admin user not found')

conn.close()
