"""Check admin hash"""
import sqlite3

conn = sqlite3.connect('construction.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username=?', ('admin',))
row = cursor.fetchone()

if row:
    print(f'Username: {row[0]}')
    print(f'Hash length: {len(row[1])}')
    print(f'Hash: {row[1]}')
else:
    print('Admin user not found')

conn.close()
