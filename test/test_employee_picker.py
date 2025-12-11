"""Test employee picker dialog with brigade filter"""
import sys
from PyQt6.QtWidgets import QApplication
from src.views.employee_picker_dialog import EmployeePickerDialog
from src.data.database_manager import DatabaseManager


def test_employee_picker():
    """Test employee picker dialog"""
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Try to initialize with the default database
    import os
    db_path = "construction.db"
    if not os.path.exists(db_path):
        db_path = "erection.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found. Please run the application first.")
        return
    
    db_manager.initialize(db_path)
    db = db_manager.get_connection()
    cursor = db.cursor()
    
    # Get a foreman for testing (first person with user_id)
    cursor.execute("""
        SELECT p.id, p.full_name
        FROM persons p
        WHERE p.user_id IS NOT NULL
        LIMIT 1
    """)
    
    foreman_row = cursor.fetchone()
    
    if foreman_row:
        foreman_id = foreman_row['id']
        foreman_name = foreman_row['full_name']
        print(f"Testing with foreman: {foreman_name} (ID: {foreman_id})")
    else:
        foreman_id = None
        print("No foreman found, testing without brigade filter")
    
    # Test 1: Show only brigade members
    print("\n=== Test 1: Show only brigade members ===")
    dialog1 = EmployeePickerDialog(foreman_id=foreman_id, show_all=False)
    
    # Count employees shown
    count1 = dialog1.table.rowCount()
    print(f"Employees shown (brigade only): {count1}")
    
    # Show some employees
    for row in range(min(5, count1)):
        name = dialog1.table.item(row, 0).text()
        position = dialog1.table.item(row, 1).text()
        rate = dialog1.table.item(row, 2).text()
        print(f"  - {name} ({position}) - Rate: {rate}")
    
    # Test 2: Show all employees
    print("\n=== Test 2: Show all employees ===")
    dialog2 = EmployeePickerDialog(foreman_id=foreman_id, show_all=True)
    
    # Count employees shown
    count2 = dialog2.table.rowCount()
    print(f"Employees shown (all): {count2}")
    
    # Show some employees
    for row in range(min(5, count2)):
        name = dialog2.table.item(row, 0).text()
        position = dialog2.table.item(row, 1).text()
        rate = dialog2.table.item(row, 2).text()
        print(f"  - {name} ({position}) - Rate: {rate}")
    
    # Test 3: Check filter preference persistence
    print("\n=== Test 3: Filter preference persistence ===")
    
    # Create dialog with show_all=True and save preference
    dialog3 = EmployeePickerDialog(foreman_id=foreman_id, show_all=True)
    dialog3._save_filter_preference(True)
    print("Saved preference: show_all=True")
    
    # Create new dialog without specifying show_all (should load from settings)
    dialog4 = EmployeePickerDialog(foreman_id=foreman_id)
    loaded_preference = dialog4.show_all
    print(f"Loaded preference: show_all={loaded_preference}")
    
    if loaded_preference:
        print("✓ Filter preference persistence works!")
    else:
        print("✗ Filter preference persistence failed!")
    
    # Reset to default
    dialog4._save_filter_preference(False)
    print("Reset preference to default (show_all=False)")
    
    # Test 4: Check hourly_rate field
    print("\n=== Test 4: Check hourly_rate field ===")
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'hourly_rate' in columns:
        print("✓ hourly_rate field exists in persons table")
        
        # Check if any persons have hourly_rate set
        cursor.execute("SELECT COUNT(*) as cnt FROM persons WHERE hourly_rate > 0")
        count = cursor.fetchone()['cnt']
        print(f"  Persons with hourly_rate > 0: {count}")
    else:
        print("✗ hourly_rate field does NOT exist in persons table")
        print("  Run the application once to trigger the migration")
    
    # Test 5: Check user_settings table
    print("\n=== Test 5: Check user_settings table ===")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='user_settings'
    """)
    
    if cursor.fetchone():
        print("✓ user_settings table exists")
        
        # Check saved preference
        cursor.execute("""
            SELECT setting_value FROM user_settings
            WHERE setting_key = 'employee_picker_show_all'
        """)
        row = cursor.fetchone()
        if row:
            print(f"  Saved preference: {row['setting_value']}")
        else:
            print("  No preference saved yet")
    else:
        print("✗ user_settings table does NOT exist")
        print("  It will be created when filter preference is saved")
    
    print("\n=== All tests completed ===")
    print("\nNote: To test the dialog interactively, comment out sys.exit() and run dialog.exec()")


if __name__ == "__main__":
    test_employee_picker()
