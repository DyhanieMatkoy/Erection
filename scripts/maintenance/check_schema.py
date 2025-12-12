import sqlite3

conn = sqlite3.connect('construction.db')
cursor = conn.cursor()

# Check if nomenclatures table exists
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='nomenclatures'")
nomenclatures_schema = cursor.fetchone()
print("Nomenclatures table schema:")
print(nomenclatures_schema[0] if nomenclatures_schema else "Table not found")

# Check if works table has nomenclature_id column
cursor.execute("PRAGMA table_info(works)")
works_columns = cursor.fetchall()
print("\nWorks table columns:")
for col in works_columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()