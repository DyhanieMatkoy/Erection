"""Test Excel print forms"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.print_form_service import PrintFormService
from src.services.excel_estimate_print_form import ExcelEstimatePrintForm
from src.services.excel_daily_report_print_form import ExcelDailyReportPrintForm


def test_print_service():
    """Test print form service"""
    print("Testing Print Form Service...")
    
    service = PrintFormService()
    
    # Test get format
    format_type = service.get_print_format()
    print(f"Current format: {format_type}")
    
    # Test set format
    print("\nSetting format to Excel...")
    success = service.set_print_format('EXCEL')
    print(f"Set format success: {success}")
    
    format_type = service.get_print_format()
    print(f"New format: {format_type}")
    
    # Test templates path
    templates_path = service.get_templates_path()
    print(f"\nTemplates path: {templates_path}")
    
    # Test create templates
    print("\nCreating templates...")
    success, message = service.create_templates()
    print(f"Create templates: {success}")
    print(f"Message: {message}")
    
    # Check if templates exist
    templates_exist = service.templates_exist()
    print(f"\nTemplates exist: {templates_exist}")
    
    # Reset to PDF
    print("\nResetting format to PDF...")
    service.set_print_format('PDF')
    format_type = service.get_print_format()
    print(f"Format reset to: {format_type}")
    
    print("\n✓ Print Form Service test completed!")


def test_excel_generators():
    """Test Excel generators"""
    print("\n" + "="*50)
    print("Testing Excel Generators...")
    
    # Test estimate generator
    print("\nTesting Estimate Generator...")
    estimate_gen = ExcelEstimatePrintForm()
    print(f"Template exists: {estimate_gen.template_exists(estimate_gen.TEMPLATE_NAME)}")
    print(f"Template path: {estimate_gen.get_template_path(estimate_gen.TEMPLATE_NAME)}")
    
    # Test daily report generator
    print("\nTesting Daily Report Generator...")
    report_gen = ExcelDailyReportPrintForm()
    print(f"Template exists: {report_gen.template_exists(report_gen.TEMPLATE_NAME)}")
    print(f"Template path: {report_gen.get_template_path(report_gen.TEMPLATE_NAME)}")
    
    print("\n✓ Excel Generators test completed!")


def test_template_creation():
    """Test template creation"""
    print("\n" + "="*50)
    print("Testing Template Creation...")
    
    # Create estimate template
    print("\nCreating estimate template...")
    estimate_gen = ExcelEstimatePrintForm()
    success = estimate_gen.create_template()
    print(f"Estimate template created: {success}")
    
    if success:
        template_path = estimate_gen.get_template_path(estimate_gen.TEMPLATE_NAME)
        print(f"Template saved to: {template_path}")
        print(f"File exists: {os.path.exists(template_path)}")
    
    # Create daily report template
    print("\nCreating daily report template...")
    report_gen = ExcelDailyReportPrintForm()
    success = report_gen.create_template()
    print(f"Daily report template created: {success}")
    
    if success:
        template_path = report_gen.get_template_path(report_gen.TEMPLATE_NAME)
        print(f"Template saved to: {template_path}")
        print(f"File exists: {os.path.exists(template_path)}")
    
    print("\n✓ Template Creation test completed!")


if __name__ == '__main__':
    print("="*50)
    print("Excel Print Forms Test Suite")
    print("="*50)
    
    try:
        test_print_service()
        test_excel_generators()
        test_template_creation()
        
        print("\n" + "="*50)
        print("✓ All tests completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
