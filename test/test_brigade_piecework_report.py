"""Test brigade piecework report generation"""
import sys
from datetime import datetime, timedelta
from src.data.database_manager import DatabaseManager
from src.services.excel_brigade_piecework_report import ExcelBrigadePieceworkReport


def test_brigade_piecework_report():
    """Test brigade piecework report generation"""
    print("Testing brigade piecework report generation...")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    # Set date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    period_start = start_date.strftime('%Y-%m-%d')
    period_end = end_date.strftime('%Y-%m-%d')
    
    print(f"Period: {period_start} to {period_end}")
    
    # Test without filters
    print("\n1. Testing without filters...")
    generator = ExcelBrigadePieceworkReport()
    excel_bytes = generator.generate(period_start, period_end)
    
    if excel_bytes:
        output_file = f"test_brigade_piecework_{period_start}_{period_end}.xlsx"
        with open(output_file, 'wb') as f:
            f.write(excel_bytes)
        print(f"✓ Report generated successfully: {output_file}")
        print(f"  File size: {len(excel_bytes)} bytes")
    else:
        print("✗ No data found for report")
    
    # Test with object filter
    print("\n2. Testing with object filter...")
    filters = {'object_id': 1}
    excel_bytes = generator.generate(period_start, period_end, filters)
    
    if excel_bytes:
        output_file = f"test_brigade_piecework_object_{period_start}_{period_end}.xlsx"
        with open(output_file, 'wb') as f:
            f.write(excel_bytes)
        print(f"✓ Report with object filter generated: {output_file}")
    else:
        print("✗ No data found for object filter")
    
    # Test with executor filter
    print("\n3. Testing with executor filter...")
    filters = {'executor_id': 1}
    excel_bytes = generator.generate(period_start, period_end, filters)
    
    if excel_bytes:
        output_file = f"test_brigade_piecework_executor_{period_start}_{period_end}.xlsx"
        with open(output_file, 'wb') as f:
            f.write(excel_bytes)
        print(f"✓ Report with executor filter generated: {output_file}")
    else:
        print("✗ No data found for executor filter")
    
    print("\n✓ All tests completed!")


if __name__ == '__main__':
    try:
        test_brigade_piecework_report()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
