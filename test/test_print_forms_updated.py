"""Test updated print forms based on АРСД format"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.estimate_print_form import EstimatePrintForm
from src.services.daily_report_print_form import DailyReportPrintForm
from src.data.database_manager import DatabaseManager


def initialize_database():
    """Initialize database connection"""
    db_manager = DatabaseManager()
    db_path = "construction.db"
    if not db_manager.initialize(db_path):
        print("Failed to initialize database")
        sys.exit(1)
    print(f"Database initialized: {db_path}\n")


def test_estimate_print_form():
    """Test estimate print form generation"""
    print("Testing estimate print form...")
    
    generator = EstimatePrintForm()
    
    # Generate PDF for estimate ID 1
    pdf_content = generator.generate(1)
    
    if pdf_content:
        # Save to file
        output_file = "test_estimate_arsd.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_content)
        print(f"✓ Estimate print form generated: {output_file}")
        print(f"  Size: {len(pdf_content)} bytes")
        return True
    else:
        print("✗ Failed to generate estimate print form")
        return False


def test_daily_report_print_form():
    """Test daily report print form generation"""
    print("\nTesting daily report print form...")
    
    generator = DailyReportPrintForm()
    
    # Generate PDF for report ID 1
    pdf_content = generator.generate(1)
    
    if pdf_content:
        # Save to file
        output_file = "test_daily_report_arsd.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_content)
        print(f"✓ Daily report print form generated: {output_file}")
        print(f"  Size: {len(pdf_content)} bytes")
        return True
    else:
        print("✗ Failed to generate daily report print form")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Updated Print Forms (АРСД Format)")
    print("=" * 60)
    
    # Initialize database
    initialize_database()
    
    results = []
    
    # Test estimate
    results.append(test_estimate_print_form())
    
    # Test daily report
    results.append(test_daily_report_print_form())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All print forms generated successfully!")
        print("\nGenerated files:")
        print("  - test_estimate_arsd.pdf")
        print("  - test_daily_report_arsd.pdf")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)
