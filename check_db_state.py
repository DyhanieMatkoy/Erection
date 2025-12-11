import sqlite3

conn = sqlite3.connect('construction.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("Existing tables:")
for table in tables:
    print(f"  - {table[0]}")

# Check if units table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='units'")
units_exists = cursor.fetchone()
print(f"\nUnits table exists: {units_exists is not None}")

# Check if cost_item_materials has work_id
if units_exists:
    cursor.execute("PRAGMA table_info(cost_item_materials)")
    columns = cursor.fetchall()
    print("\ncost_item_materials columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    has_work_id = any(col[1] == 'work_id' for col in columns)
    print(f"\nHas work_id column: {has_work_id}")

conn.close()
