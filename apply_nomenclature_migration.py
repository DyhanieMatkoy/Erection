import sqlite3

# Connect to the database
conn = sqlite3.connect('construction.db')
cursor = conn.cursor()

# Create nomenclatures table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS nomenclatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER REFERENCES nomenclatures(id),
        code VARCHAR(50),
        description VARCHAR(500),
        is_folder BOOLEAN DEFAULT FALSE,
        marked_for_deletion BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Add nomenclature_id column to works table if it doesn't exist
try:
    cursor.execute("ALTER TABLE works ADD COLUMN nomenclature_id INTEGER REFERENCES nomenclatures(id)")
except Exception as e:
    print(f"Error adding column (might already exist): {e}")

# Create index on parent_id for hierarchical queries
cursor.execute("CREATE INDEX IF NOT EXISTS ix_nomenclatures_parent_id ON nomenclatures (parent_id)")

# Update alembic version
cursor.execute("UPDATE alembic_version SET version_num = '20251208_120000'")

conn.commit()
conn.close()

print("Nomenclature migration applied successfully!")