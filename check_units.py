"""Check units in database"""
import sqlite3

conn = sqlite3.connect('construction.db')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM units')
count = cur.fetchone()[0]
print(f'Total units: {count}')

cur.execute('SELECT name, description FROM units')
print('\nAll units:')
for row in cur.fetchall():
    print(f'  {row[0]:10} - {row[1]}')

conn.close()
