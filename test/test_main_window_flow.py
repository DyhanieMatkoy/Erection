"""Test opening estimates through main window flow"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.data.database_manager import DatabaseManager


def test_main_window_flow():
    """Test opening estimate list and documents"""
    print("=" * 60)
    print("Testing Main Window Flow")
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
    
    try:
        # Step 1: Open estimate list
        print("\n--- Step 1: Open Estimate List ---")
        from src.views.estimate_list_form import EstimateListForm
        
        list_form = EstimateListForm()
        print("✓ Estimate list form created")
        
        row_count = list_form.table_view.rowCount()
        print(f"✓ List has {row_count} rows")
        
        # Step 2: Open first estimate
        print("\n--- Step 2: Open First Estimate ---")
        from src.views.estimate_document_form import EstimateDocumentForm
        
        doc_form1 = EstimateDocumentForm(estimate_id)
        print("✓ First document form created")
        print(f"✓ Number: {doc_form1.number_edit.text()}")
        print(f"✓ Rows: {doc_form1.table_part.rowCount()}")
        
        # Step 3: Close first estimate
        print("\n--- Step 3: Close First Estimate ---")
        doc_form1.close()
        del doc_form1
        print("✓ First document form closed")
        
        # Step 4: Open same estimate again
        print("\n--- Step 4: Open Same Estimate Again ---")
        doc_form2 = EstimateDocumentForm(estimate_id)
        print("✓ Second document form created")
        print(f"✓ Number: {doc_form2.number_edit.text()}")
        print(f"✓ Rows: {doc_form2.table_part.rowCount()}")
        
        # Step 5: Close second estimate
        print("\n--- Step 5: Close Second Estimate ---")
        doc_form2.close()
        del doc_form2
        print("✓ Second document form closed")
        
        # Step 6: Open third time
        print("\n--- Step 6: Open Third Time ---")
        doc_form3 = EstimateDocumentForm(estimate_id)
        print("✓ Third document form created")
        print(f"✓ Number: {doc_form3.number_edit.text()}")
        print(f"✓ Rows: {doc_form3.table_part.rowCount()}")
        
        # Cleanup
        doc_form3.close()
        del doc_form3
        list_form.close()
        del list_form
        
        print("\n" + "=" * 60)
        print("✓ All steps successful!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    success = test_main_window_flow()
    sys.exit(0 if success else 1)
