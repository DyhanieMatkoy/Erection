"""Insert units into database"""
import sqlite3

conn = sqlite3.connect('construction.db')
cur = conn.cursor()

units = [
    ('м', 'Метр'),
    ('м²', 'Квадратный метр'),
    ('м³', 'Кубический метр'),
    ('кг', 'Килограмм'),
    ('т', 'Тонна'),
    ('шт', 'Штука'),
    ('л', 'Литр'),
    ('компл', 'Комплект'),
    ('час', 'Час'),
    ('смена', 'Смена'),
    ('м.п.', 'Метр погонный')
]

for name, description in units:
    cur.execute("""
        INSERT OR IGNORE INTO units (name, description) 
        VALUES (?, ?)
    """, (name, description))

conn.commit()
print(f"✓ Inserted {cur.rowcount} units")

# Verify
cur.execute("SELECT COUNT(*) FROM units")
count = cur.fetchone()[0]
print(f"✓ Total units in database: {count}")

conn.close()
