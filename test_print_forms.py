"""Test script for print forms"""
import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.services.estimate_service import EstimateService
from src.services.daily_report_service import DailyReportService


# Initialize database
db = DatabaseManager()
if not db.initialize('construction.db'):
    print("Failed to initialize database")
    sys.exit(1)


def test_estimate_print_form():
    """Test estimate print form generation"""
    print("Testing estimate print form...")
    
    service = EstimateService()
    
    # Try to generate print form for estimate ID 1
    pdf_content = service.generate_print_form(1)
    
    if pdf_content:
        # Save to file
        with open('test_estimate.pdf', 'wb') as f:
            f.write(pdf_content)
        print(f"✓ Estimate print form generated successfully ({len(pdf_content)} bytes)")
        print("  Saved to: test_estimate.pdf")
        return True
    else:
        print("✗ Failed to generate estimate print form (estimate not found?)")
        return False


def test_daily_report_print_form():
    """Test daily report print form generation"""
    print("\nTesting daily report print form...")
    
    service = DailyReportService()
    
    # Try to generate print form for report ID 1
    pdf_content = service.generate_print_form(1)
    
    if pdf_content:
        # Save to file
        with open('test_daily_report.pdf', 'wb') as f:
            f.write(pdf_content)
        print(f"✓ Daily report print form generated successfully ({len(pdf_content)} bytes)")
        print("  Saved to: test_daily_report.pdf")
        return True
    else:
        print("✗ Failed to generate daily report print form (report not found?)")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Print Forms Test")
    print("=" * 60)
    
    try:
        result1 = test_estimate_print_form()
        result2 = test_daily_report_print_form()
        
        print("\n" + "=" * 60)
        if result1 or result2:
            print("Test completed - check generated PDF files")
        else:
            print("No test data found - please run load_test_data.py first")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
