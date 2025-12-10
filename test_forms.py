"""Test forms opening and basic operations"""
import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.data.models.estimate import Estimate, EstimateLine
from src.data.models.daily_report import DailyReport, DailyReportLine
from src.services.daily_report_service import DailyReportService


def test_database_connection():
    """Test database connection"""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        success = db_manager.initialize('construction.db')
        
        if success:
            print("✓ Database initialized successfully")
            
            # Check tables
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✓ Found {len(tables)} tables")
            
            # Check for new columns
            cursor.execute("PRAGMA table_info(estimate_lines)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_group' in columns:
                print("✓ Column 'is_group' exists in estimate_lines")
            else:
                print("✗ Column 'is_group' NOT FOUND in estimate_lines")
                return False
            
            if 'group_name' in columns:
                print("✓ Column 'group_name' exists in estimate_lines")
            else:
                print("✗ Column 'group_name' NOT FOUND in estimate_lines")
                return False
            
            return True
        else:
            print("✗ Failed to initialize database")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_estimate_list_form():
    """Test opening estimate list form"""
    print("\n" + "=" * 60)
    print("TEST 2: Estimate List Form")
    print("=" * 60)
    
    try:
        from src.views.estimate_list_form import EstimateListForm
        
        form = EstimateListForm()
        print("✓ EstimateListForm created successfully")
        
        # Check if table is populated
        row_count = form.table_view.rowCount()
        print(f"✓ Table has {row_count} rows")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_estimate_document_form():
    """Test opening estimate document form"""
    print("\n" + "=" * 60)
    print("TEST 3: Estimate Document Form (New)")
    print("=" * 60)
    
    try:
        from src.views.estimate_document_form import EstimateDocumentForm
        
        form = EstimateDocumentForm(0)
        print("✓ EstimateDocumentForm created successfully")
        
        # Check fields
        if form.number_edit:
            print("✓ Number field exists")
        if form.date_edit:
            print("✓ Date field exists")
        if form.table_part:
            print("✓ Table part exists")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_estimate():
    """Test creating and saving estimate"""
    print("\n" + "=" * 60)
    print("TEST 4: Create and Save Estimate")
    print("=" * 60)
    
    try:
        db = DatabaseManager().get_connection()
        cursor = db.cursor()
        
        # Create test data if not exists
        # Check for test counterparty
        cursor.execute("SELECT id FROM counterparties WHERE name = 'Тестовый заказчик' LIMIT 1")
        row = cursor.fetchone()
        if row:
            customer_id = row[0]
            print(f"✓ Using existing test customer (ID: {customer_id})")
        else:
            cursor.execute("INSERT INTO counterparties (name, inn) VALUES ('Тестовый заказчик', '1234567890')")
            customer_id = cursor.lastrowid
            db.commit()
            print(f"✓ Created test customer (ID: {customer_id})")
        
        # Check for test work
        cursor.execute("SELECT id FROM works WHERE name = 'Тестовая работа' LIMIT 1")
        row = cursor.fetchone()
        if row:
            work_id = row[0]
            print(f"✓ Using existing test work (ID: {work_id})")
        else:
            cursor.execute("INSERT INTO works (name, unit, price, labor_rate) VALUES ('Тестовая работа', 'шт', 100.0, 1.5)")
            work_id = cursor.lastrowid
            db.commit()
            print(f"✓ Created test work (ID: {work_id})")
        
        # Create estimate
        estimate = Estimate()
        estimate.number = "TEST-001"
        estimate.date = date.today()
        estimate.customer_id = customer_id
        estimate.total_sum = 1000.0
        estimate.total_labor = 15.0
        
        # Add line
        line = EstimateLine()
        line.line_number = 1
        line.work_id = work_id
        line.quantity = 10.0
        line.unit = "шт"
        line.price = 100.0
        line.labor_rate = 1.5
        line.sum = 1000.0
        line.planned_labor = 15.0
        
        estimate.lines = [line]
        
        # Save
        cursor.execute("""
            INSERT INTO estimates (number, date, customer_id, total_sum, total_labor)
            VALUES (?, ?, ?, ?, ?)
        """, (estimate.number, estimate.date, estimate.customer_id, estimate.total_sum, estimate.total_labor))
        
        estimate_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO estimate_lines 
            (estimate_id, line_number, work_id, quantity, unit, price, labor_rate, sum, planned_labor,
             is_group, group_name, parent_group_id, is_collapsed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (estimate_id, line.line_number, line.work_id, line.quantity, line.unit,
              line.price, line.labor_rate, line.sum, line.planned_labor,
              0, '', None, 0))
        
        db.commit()
        
        print(f"✓ Created estimate (ID: {estimate_id})")
        
        # Verify
        cursor.execute("SELECT * FROM estimates WHERE id = ?", (estimate_id,))
        row = cursor.fetchone()
        if row:
            print(f"✓ Estimate verified: {row['number']}")
        
        cursor.execute("SELECT * FROM estimate_lines WHERE estimate_id = ?", (estimate_id,))
        lines = cursor.fetchall()
        print(f"✓ Estimate has {len(lines)} lines")
        
        return estimate_id
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_daily_report_list_form():
    """Test opening daily report list form"""
    print("\n" + "=" * 60)
    print("TEST 5: Daily Report List Form")
    print("=" * 60)
    
    try:
        from src.views.daily_report_list_form import DailyReportListForm
        
        form = DailyReportListForm()
        print("✓ DailyReportListForm created successfully")
        
        # Check if table is populated
        row_count = form.table_view.rowCount()
        print(f"✓ Table has {row_count} rows")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_report_document_form():
    """Test opening daily report document form"""
    print("\n" + "=" * 60)
    print("TEST 6: Daily Report Document Form (New)")
    print("=" * 60)
    
    try:
        from src.views.daily_report_document_form import DailyReportDocumentForm
        
        form = DailyReportDocumentForm(0)
        print("✓ DailyReportDocumentForm created successfully")
        
        # Check fields
        if form.date_edit:
            print("✓ Date field exists")
        if form.estimate_combo:
            print("✓ Estimate combo exists")
        if form.table_part:
            print("✓ Table part exists")
        if form.fill_button:
            print("✓ Fill button exists")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_daily_report(estimate_id):
    """Test creating and saving daily report"""
    print("\n" + "=" * 60)
    print("TEST 7: Create and Save Daily Report")
    print("=" * 60)
    
    if not estimate_id:
        print("✗ No estimate ID provided")
        return None
    
    try:
        db = DatabaseManager().get_connection()
        cursor = db.cursor()
        
        # Check for test person
        cursor.execute("SELECT id FROM persons WHERE full_name = 'Тестовый бригадир' LIMIT 1")
        row = cursor.fetchone()
        if row:
            foreman_id = row[0]
            print(f"✓ Using existing test foreman (ID: {foreman_id})")
        else:
            cursor.execute("INSERT INTO persons (full_name, position) VALUES ('Тестовый бригадир', 'Бригадир')")
            foreman_id = cursor.lastrowid
            db.commit()
            print(f"✓ Created test foreman (ID: {foreman_id})")
        
        # Create daily report
        service = DailyReportService()
        report = DailyReport()
        report.date = date.today()
        report.estimate_id = estimate_id
        report.foreman_id = foreman_id
        
        # Get estimate lines
        cursor.execute("SELECT id FROM estimate_lines WHERE estimate_id = ? LIMIT 1", (estimate_id,))
        line_row = cursor.fetchone()
        if not line_row:
            print("✗ No estimate lines found")
            return None
        
        # Fill from estimate
        selected_line_ids = [line_row[0]]
        if service.fill_from_estimate(report, selected_line_ids):
            print(f"✓ Filled report from estimate ({len(report.lines)} lines)")
        else:
            print("✗ Failed to fill from estimate")
            return None
        
        # Save report
        if service.save(report):
            print(f"✓ Saved daily report (ID: {report.id})")
            
            # Verify
            cursor.execute("SELECT * FROM daily_reports WHERE id = ?", (report.id,))
            row = cursor.fetchone()
            if row:
                print(f"✓ Report verified: {row['date']}")
            
            cursor.execute("SELECT * FROM daily_report_lines WHERE report_id = ?", (report.id,))
            lines = cursor.fetchall()
            print(f"✓ Report has {len(lines)} lines")
            
            return report.id
        else:
            print("✗ Failed to save report")
            return None
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_load_estimate(estimate_id):
    """Test loading existing estimate"""
    print("\n" + "=" * 60)
    print("TEST 8: Load Existing Estimate")
    print("=" * 60)
    
    if not estimate_id:
        print("✗ No estimate ID provided")
        return False
    
    try:
        from src.views.estimate_document_form import EstimateDocumentForm
        
        form = EstimateDocumentForm(estimate_id)
        print(f"✓ Loaded estimate form (ID: {estimate_id})")
        
        # Check if data is loaded
        if form.number_edit.text():
            print(f"✓ Number loaded: {form.number_edit.text()}")
        
        row_count = form.table_part.rowCount()
        print(f"✓ Table has {row_count} rows")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_daily_report(report_id):
    """Test loading existing daily report"""
    print("\n" + "=" * 60)
    print("TEST 9: Load Existing Daily Report")
    print("=" * 60)
    
    if not report_id:
        print("✗ No report ID provided")
        return False
    
    try:
        from src.views.daily_report_document_form import DailyReportDocumentForm
        
        form = DailyReportDocumentForm(report_id)
        print(f"✓ Loaded daily report form (ID: {report_id})")
        
        # Check if data is loaded
        row_count = form.table_part.rowCount()
        print(f"✓ Table has {row_count} rows")
        
        form.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STARTING COMPREHENSIVE FORM TESTS")
    print("=" * 60)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    results = []
    estimate_id = None
    report_id = None
    
    # Run tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Estimate List Form", test_estimate_list_form()))
    results.append(("Estimate Document Form", test_estimate_document_form()))
    
    estimate_id = test_create_estimate()
    results.append(("Create Estimate", estimate_id is not None))
    
    results.append(("Daily Report List Form", test_daily_report_list_form()))
    results.append(("Daily Report Document Form", test_daily_report_document_form()))
    
    report_id = test_create_daily_report(estimate_id)
    results.append(("Create Daily Report", report_id is not None))
    
    results.append(("Load Estimate", test_load_estimate(estimate_id)))
    results.append(("Load Daily Report", test_load_daily_report(report_id)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
