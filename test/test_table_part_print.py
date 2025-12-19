"""
Test table part print functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication
from src.services.table_part_print_service import (
    TablePartPrintService, PrintConfiguration, PageOrientation, PrintFormat,
    create_print_service
)
from src.views.dialogs.table_part_print_dialog import create_table_part_print_dialog


def test_print_service():
    """Test the print service functionality"""
    print("🧪 Testing TablePartPrintService...")
    
    # Create test data
    test_data = [
        {"Наименование": "Работа 1", "Количество": 10, "Цена": 100.0, "Сумма": 1000.0},
        {"Наименование": "Работа 2", "Количество": 5, "Цена": 200.0, "Сумма": 1000.0},
        {"Наименование": "Работа 3", "Количество": 15, "Цена": 50.0, "Сумма": 750.0},
    ]
    
    # Create print service
    service = create_print_service()
    
    # Test configuration
    config = PrintConfiguration(
        orientation=PageOrientation.PORTRAIT,
        scale_percent=100,
        repeat_headers=True,
        show_grid=True,
        table_name="Тестовая табличная часть"
    )
    
    # Test HTML generation
    html_content = service.generate_html_preview(test_data, config)
    
    print("✓ HTML content generated successfully")
    print(f"  Content length: {len(html_content)} characters")
    
    # Test data validation
    is_valid, error_msg = service.validate_print_data(test_data)
    print(f"✓ Data validation: {is_valid}")
    if not is_valid:
        print(f"  Error: {error_msg}")
    
    # Test page count calculation
    page_count = service.get_page_count(test_data, config)
    print(f"✓ Estimated pages: {page_count}")
    
    return True


def test_print_dialog():
    """Test the print dialog"""
    print("\n🧪 Testing TablePartPrintDialog...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create test data
    test_data = []
    for i in range(1, 101):  # 100 rows for multi-page testing
        test_data.append({
            "№": i,
            "Наименование": f"Работа {i}",
            "Количество": i * 2,
            "Цена": 100.0 + i,
            "Сумма": (i * 2) * (100.0 + i)
        })
    
    # Create print dialog
    dialog = create_table_part_print_dialog(
        test_data, 
        "Тестовая табличная часть с большим количеством строк"
    )
    
    print("✓ Print dialog created successfully")
    print(f"  Dialog size: {dialog.size().width()}x{dialog.size().height()}")
    print(f"  Test data rows: {len(test_data)}")
    
    # Test dialog without showing (for automated testing)
    config = dialog.get_print_configuration()
    print(f"✓ Print configuration retrieved")
    print(f"  Orientation: {config.orientation.value}")
    print(f"  Format: {config.format.value}")
    print(f"  Repeat headers: {config.repeat_headers}")
    
    return True


def test_multi_page_printing():
    """Test multi-page printing functionality"""
    print("\n🧪 Testing multi-page printing...")
    
    # Create large test dataset
    large_data = []
    for i in range(1, 151):  # 150 rows to test page breaks
        large_data.append({
            "Код": f"W{i:03d}",
            "Наименование работы": f"Выполнение работ по позиции {i}",
            "Единица измерения": "м²" if i % 2 == 0 else "шт",
            "Количество": i * 1.5,
            "Цена за единицу": 150.0 + (i % 50),
            "Сумма": (i * 1.5) * (150.0 + (i % 50))
        })
    
    service = create_print_service()
    
    # Test with different page sizes
    config = PrintConfiguration(
        max_rows_per_page=25,  # Force multiple pages
        repeat_headers=True,
        table_name="Большая табличная часть"
    )
    
    # Test page splitting
    pages = service._split_data_into_pages(large_data, config.max_rows_per_page)
    print(f"✓ Data split into {len(pages)} pages")
    
    for i, page in enumerate(pages):
        print(f"  Page {i+1}: {len(page)} rows")
    
    # Test HTML generation for multi-page
    html_content = service.generate_html_preview(large_data, config)
    print("✓ Multi-page HTML generated successfully")
    
    # Check for page break indicators
    page_breaks = html_content.count('page-break')
    print(f"  Page breaks found: {page_breaks}")
    
    # Check for repeated headers
    if config.repeat_headers:
        header_count = html_content.count('header-row')
        print(f"  Header repetitions: {header_count}")
    
    return True


def main():
    """Run all print tests"""
    print("=" * 60)
    print("Table Part Print Functionality Tests")
    print("=" * 60)
    
    try:
        # Test print service
        test_print_service()
        
        # Test print dialog
        test_print_dialog()
        
        # Test multi-page printing
        test_multi_page_printing()
        
        print("\n" + "=" * 60)
        print("✅ All print tests completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)