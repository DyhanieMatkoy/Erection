"""Check users and their person associations"""
from src.data.database_manager import DatabaseManager

db = DatabaseManager()
db.initialize('construction.db')
cursor = db.get_connection().cursor()

print("Users and their person associations:")
print("-" * 60)
cursor.execute("""
    SELECT u.username, u.role, p.id as person_id, p.full_name 
    FROM users u 
    LEFT JOIN persons p ON u.id = p.user_id
""")

for row in cursor.fetchall():
    print(f"User: {row['username']:15} Role: {row['role']:15} Person ID: {row['person_id']}, Name: {row['full_name']}")

print("\nDaily reports and their foremen:")
print("-" * 60)
cursor.execute("""
    SELECT dr.id, dr.date, p.full_name as foreman, p.id as foreman_id
    FROM daily_reports dr
    LEFT JOIN persons p ON dr.foreman_id = p.id
    WHERE dr.marked_for_deletion = 0
    ORDER BY dr.date DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"Report ID: {row['id']:3} Date: {row['date']:12} Foreman: {row['foreman']:20} (ID: {row['foreman_id']})")
