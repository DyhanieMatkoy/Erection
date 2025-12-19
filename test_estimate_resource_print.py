"""Test estimate resource print form functionality"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.estimate_resource_print_form import EstimateResourcePrintForm
from src.services.excel_estimate_resource_print_form import ExcelEstimateResourcePrintForm
from src.services.print_form_service import PrintFormService
from src.data.database_manager import DatabaseManager


def test_pdf_estimate_resource_print():
    """Test PDF estimate resource print form generation"""
    print("Testing PDF estimate resource print form...")
    
    generator = EstimateResourcePrintForm()
    
    # Generate PDF for estimate ID 1
    pdf_content = generator.generate(1)
    
    if pdf_content:
        output_file = 'test_estimate_resource.pdf'
        with open(output_file, 'wb') as f:
            f.write(pdf_content)
        print(f"✓ PDF estimate resource print form generated: {output_file}")
        print(f"  Size: {len(pdf_content)} bytes")
        return True
    else:
        print("✗ Failed to generate PDF estimate resource print form")
        return False


def test_excel_estimate_resource_print():
    """Test Excel estimate resource print form generation"""
    print("Testing Excel estimate resource print form...")
    
    generator = ExcelEstimateResourcePrintForm()
    
    # Generate Excel for estimate ID 1
    excel_content = generator.generate(1)
    
    if excel_content:
        output_file = 'test_estimate_resource.xlsx'
        with open(output_file, 'wb') as f:
            f.write(excel_content)
        print(f"✓ Excel estimate resource print form generated: {output_file}")
        print(f"  Size: {len(excel_content)} bytes")
        return True
    else:
        print("✗ Failed to generate Excel estimate resource print form")
        return False


def test_print_service_variants():
    """Test print service with different variants"""
    print("Testing print service with variants...")
    
    service = PrintFormService()
    
    # Test standard variant
    print("  Testing STANDARD variant...")
    result_standard = service.generate_estimate(1, 'STANDARD')
    if result_standard:
        content, ext = result_standard
        output_file = f'test_estimate_standard.{ext}'
        with open(output_file, 'wb') as f:
            f.write(content)
        print(f"    ✓ Standard variant generated: {output_file} ({len(content)} bytes)")
    else:
        print("    ✗ Failed to generate standard variant")
        return False
    
    # Test resource variant
    print("  Testing RESOURCE variant...")
    result_resource = service.generate_estimate(1, 'RESOURCE')
    if result_resource:
        content, ext = result_resource
        output_file = f'test_estimate_resource_service.{ext}'
        with open(output_file, 'wb') as f:
            f.write(content)
        print(f"    ✓ Resource variant generated: {output_file} ({len(content)} bytes)")
    else:
        print("    ✗ Failed to generate resource variant")
        return False
    
    return True


def test_configuration():
    """Test configuration methods"""
    print("Testing configuration methods...")
    
    service = PrintFormService()
    
    # Test getting current variant
    current_variant = service.get_estimate_print_variant()
    print(f"  Current estimate variant: {current_variant}")
    
    # Test setting variant
    success = service.set_estimate_print_variant('RESOURCE')
    if success:
        print("  ✓ Successfully set variant to RESOURCE")
        
        # Verify it was set
        new_variant = service.get_estimate_print_variant()
        if new_variant == 'RESOURCE':
            print("  ✓ Variant correctly saved and retrieved")
        else:
            print(f"  ✗ Variant not saved correctly: {new_variant}")
            return False
        
        # Reset to original
        service.set_estimate_print_variant(current_variant)
        print(f"  ✓ Reset variant to original: {current_variant}")
    else:
        print("  ✗ Failed to set variant")
        return False
    
    return True


def test_template_creation():
    """Test template creation for resource variant"""
    print("Testing template creation...")
    
    generator = ExcelEstimateResourcePrintForm()
    
    # Create template
    success = generator.create_template()
    if success:
        print("  ✓ Excel resource template created successfully")
        
        # Check if template file exists
        template_path = generator.get_template_path(generator.TEMPLATE_NAME)
        if os.path.exists(template_path):
            print(f"  ✓ Template file exists: {template_path}")
            file_size = os.path.getsize(template_path)
            print(f"    Size: {file_size} bytes")
        else:
            print(f"  ✗ Template file not found: {template_path}")
            return False
    else:
        print("  ✗ Failed to create Excel resource template")
        return False
    
    return True


def check_database_data():
    """Check if we have test data in database"""
    print("Checking database data...")
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize('construction.db')
        
        with db_manager.get_session() as session:
            from src.data.models.sqlalchemy_models import (
                Estimate, EstimateLine, Material, CostItemMaterial
            )
            
            # Check estimates
            estimate_count = session.query(Estimate).count()
            print(f"  Estimates in database: {estimate_count}")
            
            if estimate_count == 0:
                print("  ✗ No estimates found in database")
                return False
            
            # Check estimate lines
            lines_count = session.query(EstimateLine).filter(EstimateLine.estimate_id == 1).count()
            print(f"  Estimate lines for estimate 1: {lines_count}")
            
            # Check materials
            materials_count = session.query(Material).count()
            print(f"  Materials in database: {materials_count}")
            
            # Check cost_item_materials
            cim_count = session.query(CostItemMaterial).filter(CostItemMaterial.material_id.isnot(None)).count()
            print(f"  Material associations: {cim_count}")
            
            if materials_count == 0 or cim_count == 0:
                print("  ⚠ Warning: No materials or material associations found")
                print("    Resource statement will be empty")
            
            return True
            
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Estimate Resource Print Forms")
    print("=" * 60)
    
    results = []
    
    # Check database first
    results.append(("Database Check", check_database_data()))
    
    # Test configuration
    results.append(("Configuration", test_configuration()))
    
    # Test template creation
    results.append(("Template Creation", test_template_creation()))
    
    # Test PDF generation
    results.append(("PDF Resource Print", test_pdf_estimate_resource_print()))
    
    # Test Excel generation
    results.append(("Excel Resource Print", test_excel_estimate_resource_print()))
    
    # Test print service
    results.append(("Print Service Variants", test_print_service_variants()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:25} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nGenerated files:")
        print("- test_estimate_resource.pdf")
        print("- test_estimate_resource.xlsx")
        print("- test_estimate_standard.pdf (or .xlsx)")
        print("- test_estimate_resource_service.pdf (or .xlsx)")
    else:
        print("✗ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)