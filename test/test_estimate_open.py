"""Test opening estimate multiple times"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager


def test_open_estimate_multiple_times():
    """Test opening estimate form multiple times"""
    print("=" * 60)
    print("Testing opening estimate multiple times")
    print("=" * 60)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    # Get first estimate ID
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM estimates ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("✗ No estimates found in database")
        return False
    
    estimate_id = row[0]
    print(f"Testing with estimate ID: {estimate_id}")
    
    # Try opening 3 times
    for i in range(1, 4):
        print(f"\n--- Attempt {i} ---")
        try:
            from src.views.estimate_document_form import EstimateDocumentForm
            
            print(f"Creating form...")
            form = EstimateDocumentForm(estimate_id)
            print(f"✓ Form created successfully")
            
            # Check data
            number = form.number_edit.text()
            rows = form.table_part.rowCount()
            print(f"✓ Number: {number}")
            print(f"✓ Rows: {rows}")
            
            print(f"Closing form...")
            form.close()
            print(f"✓ Form closed")
            
            # Force cleanup
            del form
            
        except Exception as e:
            print(f"✗ Error on attempt {i}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✓ All attempts successful!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    success = test_open_estimate_multiple_times()
    sys.exit(0 if success else 1)
