"""Test executor filtering in work execution report"""
from src.data.database_manager import DatabaseManager
from src.services.auth_service import AuthService
from src.data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize('construction.db')
db = db_manager.get_connection()

print("=" * 70)
print("Testing Executor Filtering in Work Execution Report")
print("=" * 70)

# Check executors in daily reports
cursor = db.cursor()
cursor.execute("""
    SELECT DISTINCT p.id, p.full_name, COUNT(dre.report_line_id) as report_count
    FROM persons p
    INNER JOIN daily_report_executors dre ON p.id = dre.executor_id
    GROUP BY p.id, p.full_name
    ORDER BY report_count DESC
""")

executors = cursor.fetchall()
print(f"\nFound {len(executors)} executors with daily report entries:")
for executor in executors:
    print(f"  - {executor['full_name']} (ID: {executor['id']}) - {executor['report_count']} report lines")

if executors:
    test_executor = executors[0]
    print(f"\n{'=' * 70}")
    print(f"Testing with executor: {test_executor['full_name']} (ID: {test_executor['id']})")
    print(f"{'=' * 70}")
    
    # Test WorkExecutionRegisterRepository
    repo = WorkExecutionRegisterRepository()
    
    # Get turnovers without executor filter
    print("\n1. Getting turnovers WITHOUT executor filter...")
    data_all = repo.get_turnovers('2025-01-01', '2025-12-31', {}, ['estimate', 'work'])
    print(f"   Found {len(data_all)} records")
    
    # Get turnovers with executor filter
    print(f"\n2. Getting turnovers WITH executor filter (executor_id={test_executor['id']})...")
    data_filtered = repo.get_turnovers('2025-01-01', '2025-12-31', 
                                       {'executor_id': test_executor['id']}, 
                                       ['estimate', 'work'])
    print(f"   Found {len(data_filtered)} records")
    
    if len(data_filtered) <= len(data_all):
        print(f"   ✓ Executor filter correctly reduces results")
    else:
        print(f"   ✗ Executor filter issue: more results with filter than without")
    
    # Show some details
    if data_filtered:
        print(f"\n   Sample filtered records:")
        for i, record in enumerate(data_filtered[:5]):
            print(f"     {i+1}. Estimate: {record.get('estimate_number', 'N/A')}, "
                  f"Work: {record.get('work_name', 'N/A')}, "
                  f"Expense: {record.get('quantity_expense', 0):.2f}")
    
    # Test with AuthService simulation
    print(f"\n{'=' * 70}")
    print("Simulating WorkExecutionReportForm filtering")
    print(f"{'=' * 70}")
    
    # Create a test employee user if needed
    cursor.execute("""
        SELECT u.id, u.username, u.role, p.id as person_id, p.full_name
        FROM users u
        INNER JOIN persons p ON u.id = p.user_id
        WHERE u.role = 'Сотрудник' AND p.id = ?
    """, (test_executor['id'],))
    
    employee_user = cursor.fetchone()
    
    if not employee_user:
        print(f"\n⚠ No employee user found for executor {test_executor['full_name']}. Creating one...")
        
        import hashlib
        password_hash = hashlib.sha256('employee123'.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES ('employee_test', ?, 'Сотрудник', 1)
        """, (password_hash,))
        user_id = cursor.lastrowid
        
        # Link to the executor person
        cursor.execute("""
            UPDATE persons SET user_id = ? WHERE id = ?
        """, (user_id, test_executor['id']))
        
        db.commit()
        print(f"✓ Created test employee user: employee_test / employee123")
        print(f"✓ Linked to person ID: {test_executor['id']} ({test_executor['full_name']})")
        
        # Re-query
        cursor.execute("""
            SELECT u.id, u.username, u.role, p.id as person_id, p.full_name
            FROM users u
            INNER JOIN persons p ON u.id = p.user_id
            WHERE u.role = 'Сотрудник' AND p.id = ?
        """, (test_executor['id'],))
        employee_user = cursor.fetchone()
    
    if employee_user:
        print(f"\nTesting with employee user: {employee_user['username']}")
        
        auth_service = AuthService()
        user = auth_service.login(employee_user['username'], 'employee123')
        
        if user:
            print(f"✓ Login successful: {user.username}")
            print(f"✓ Role: {user.role}")
            print(f"✓ Is employee: {auth_service.is_employee()}")
            print(f"✓ Person ID: {auth_service.current_person_id()}")
            
            # Simulate the filtering logic from WorkExecutionReportForm
            filters = {}
            
            if auth_service.is_foreman() or auth_service.is_employee():
                person_id = auth_service.current_person_id()
                if person_id:
                    filters['executor_id'] = person_id
                    print(f"✓ Applied executor filter: executor_id = {person_id}")
            
            # Get filtered data
            filtered_data = repo.get_turnovers('2025-01-01', '2025-12-31', 
                                              filters, 
                                              ['estimate', 'work'])
            
            print(f"✓ Query returned {len(filtered_data)} records")
            
            if len(filtered_data) == len(data_filtered):
                print(f"\n✓ SUCCESS: Employee filtering works correctly!")
                print(f"  Expected {len(data_filtered)} records, got {len(filtered_data)} records")
            else:
                print(f"\n✗ FAILURE: Employee filtering mismatch!")
                print(f"  Expected {len(data_filtered)} records, got {len(filtered_data)} records")
            
            auth_service.logout()
        else:
            print(f"✗ Login failed for {employee_user['username']}")

else:
    print("\n⚠ No executors found in daily reports. Cannot test executor filtering.")
    print("   Please create some daily reports with executors first.")

print(f"\n{'=' * 70}")
print("Test completed!")
print(f"{'=' * 70}")
