"""Test foreman filtering in detail"""
from src.data.database_manager import DatabaseManager
from src.services.auth_service import AuthService

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize('construction.db')
db = db_manager.get_connection()

print("=" * 70)
print("Testing Foreman Filtering Implementation")
print("=" * 70)

# Check if we have any foreman users
cursor = db.cursor()
cursor.execute("""
    SELECT u.id, u.username, u.role, p.id as person_id, p.full_name
    FROM users u
    INNER JOIN persons p ON u.id = p.user_id
    WHERE u.role = 'Бригадир'
""")

foreman_users = cursor.fetchall()
print(f"\nFound {len(foreman_users)} foreman users in database:")
for user in foreman_users:
    print(f"  - {user['username']} (Person ID: {user['person_id']}, Name: {user['full_name']})")

if not foreman_users:
    print("\n⚠ No foreman users found. Creating a test foreman user...")
    
    # Create a test foreman user
    import hashlib
    password_hash = hashlib.sha256('foreman123'.encode()).hexdigest()
    
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, is_active)
        VALUES ('foreman_test', ?, 'Бригадир', 1)
    """, (password_hash,))
    user_id = cursor.lastrowid
    
    # Link to person ID 7 (Тестовый бригадир)
    cursor.execute("""
        UPDATE persons SET user_id = ? WHERE id = 7
    """, (user_id,))
    
    db.commit()
    print(f"✓ Created test foreman user: foreman_test / foreman123")
    print(f"✓ Linked to person ID: 7 (Тестовый бригадир)")
    
    # Re-query
    cursor.execute("""
        SELECT u.id, u.username, u.role, p.id as person_id, p.full_name
        FROM users u
        INNER JOIN persons p ON u.id = p.user_id
        WHERE u.role = 'Бригадир'
    """)
    foreman_users = cursor.fetchall()

# Test with first foreman user
if foreman_users:
    test_user = foreman_users[0]
    print(f"\n{'=' * 70}")
    print(f"Testing with user: {test_user['username']} (Person ID: {test_user['person_id']})")
    print(f"{'=' * 70}")
    
    # Get all daily reports
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM daily_reports 
        WHERE marked_for_deletion = 0
    """)
    total_reports = cursor.fetchone()['count']
    print(f"\nTotal daily reports in database: {total_reports}")
    
    # Get reports for this foreman
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM daily_reports 
        WHERE marked_for_deletion = 0 AND foreman_id = ?
    """, (test_user['person_id'],))
    foreman_reports = cursor.fetchone()['count']
    print(f"Daily reports for this foreman: {foreman_reports}")
    
    # Show the reports
    cursor.execute("""
        SELECT dr.id, dr.date, e.number as estimate_number
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        WHERE dr.marked_for_deletion = 0 AND dr.foreman_id = ?
        ORDER BY dr.date DESC
    """, (test_user['person_id'],))
    
    print(f"\nReports visible to foreman {test_user['full_name']}:")
    for report in cursor.fetchall():
        print(f"  - Report ID: {report['id']}, Date: {report['date']}, Estimate: {report['estimate_number']}")
    
    # Test AuthService
    print(f"\n{'=' * 70}")
    print("Testing AuthService")
    print(f"{'=' * 70}")
    
    auth_service = AuthService()
    user = auth_service.login(test_user['username'], 'foreman123')
    
    if user:
        print(f"✓ Login successful: {user.username}")
        print(f"✓ Role: {user.role}")
        print(f"✓ Is foreman: {auth_service.is_foreman()}")
        print(f"✓ Person ID: {auth_service.current_person_id()}")
        
        if auth_service.current_person_id() == test_user['person_id']:
            print(f"✓ Person ID matches expected value")
        else:
            print(f"✗ Person ID mismatch! Expected {test_user['person_id']}, got {auth_service.current_person_id()}")
        
        # Simulate the filtering logic from DailyReportListForm
        print(f"\n{'=' * 70}")
        print("Simulating DailyReportListForm filtering")
        print(f"{'=' * 70}")
        
        where_clauses = ["(dr.marked_for_deletion = 0 OR dr.marked_for_deletion IS NULL)"]
        params = []
        
        if auth_service.is_foreman():
            person_id = auth_service.current_person_id()
            if person_id:
                where_clauses.append("dr.foreman_id = ?")
                params.append(person_id)
                print(f"✓ Applied foreman filter: foreman_id = {person_id}")
        
        where_clause = " AND ".join(where_clauses)
        query = f"""
            SELECT dr.id, dr.date, 
                   e.number as estimate_number,
                   p.full_name as foreman_name
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            LEFT JOIN persons p ON dr.foreman_id = p.id
            WHERE {where_clause}
            ORDER BY dr.date DESC
        """
        
        cursor.execute(query, params)
        filtered_reports = cursor.fetchall()
        
        print(f"✓ Query returned {len(filtered_reports)} reports")
        print(f"\nFiltered reports:")
        for report in filtered_reports:
            print(f"  - Report ID: {report['id']}, Date: {report['date']}, Estimate: {report['estimate_number']}, Foreman: {report['foreman_name']}")
        
        if len(filtered_reports) == foreman_reports:
            print(f"\n✓ SUCCESS: Filtering works correctly!")
            print(f"  Expected {foreman_reports} reports, got {len(filtered_reports)} reports")
        else:
            print(f"\n✗ FAILURE: Filtering mismatch!")
            print(f"  Expected {foreman_reports} reports, got {len(filtered_reports)} reports")
        
        auth_service.logout()
    else:
        print(f"✗ Login failed for {test_user['username']}")

print(f"\n{'=' * 70}")
print("Test completed!")
print(f"{'=' * 70}")
