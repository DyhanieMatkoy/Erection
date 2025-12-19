"""Example of using estimate resource print functionality"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.print_form_service import PrintFormService
from src.services.estimate_service import EstimateService


def demonstrate_estimate_printing():
    """Demonstrate different estimate printing options"""
    print("=" * 60)
    print("Estimate Resource Print Example")
    print("=" * 60)
    
    # Initialize services
    print_service = PrintFormService()
    estimate_service = EstimateService()
    
    # Example estimate ID (adjust as needed)
    estimate_id = 1
    
    print(f"Working with estimate ID: {estimate_id}")
    print()
    
    # 1. Show current configuration
    print("1. Current Configuration:")
    print(f"   Print Format: {print_service.get_print_format()}")
    print(f"   Estimate Variant: {print_service.get_estimate_print_variant()}")
    print()
    
    # 2. Generate standard estimate
    print("2. Generating Standard Estimate:")
    result = estimate_service.generate_print_form(estimate_id, 'STANDARD')
    if result:
        content, ext = result
        filename = f"example_estimate_standard.{ext}"
        with open(filename, 'wb') as f:
            f.write(content)
        print(f"   ✓ Generated: {filename} ({len(content)} bytes)")
    else:
        print("   ✗ Failed to generate standard estimate")
    print()
    
    # 3. Generate estimate with resource statement
    print("3. Generating Estimate with Resource Statement:")
    result = estimate_service.generate_print_form(estimate_id, 'RESOURCE')
    if result:
        content, ext = result
        filename = f"example_estimate_resource.{ext}"
        with open(filename, 'wb') as f:
            f.write(content)
        print(f"   ✓ Generated: {filename} ({len(content)} bytes)")
        print("   📋 This version includes a separate resource statement table")
    else:
        print("   ✗ Failed to generate resource estimate")
    print()
    
    # 4. Change configuration and generate
    print("4. Changing Configuration:")
    original_variant = print_service.get_estimate_print_variant()
    
    # Set to resource variant
    success = print_service.set_estimate_print_variant('RESOURCE')
    if success:
        print("   ✓ Set default variant to RESOURCE")
        
        # Generate using default configuration
        result = estimate_service.generate_print_form(estimate_id)
        if result:
            content, ext = result
            filename = f"example_estimate_default_resource.{ext}"
            with open(filename, 'wb') as f:
                f.write(content)
            print(f"   ✓ Generated with default config: {filename}")
        
        # Restore original configuration
        print_service.set_estimate_print_variant(original_variant)
        print(f"   ✓ Restored original variant: {original_variant}")
    else:
        print("   ✗ Failed to change configuration")
    print()
    
    # 5. Test both formats
    print("5. Testing Both Formats:")
    original_format = print_service.get_print_format()
    
    for format_type in ['PDF', 'EXCEL']:
        print(f"   Testing {format_type} format:")
        print_service.set_print_format(format_type)
        
        # Generate resource variant
        result = print_service.generate_estimate(estimate_id, 'RESOURCE')
        if result:
            content, ext = result
            filename = f"example_estimate_resource_{format_type.lower()}.{ext}"
            with open(filename, 'wb') as f:
                f.write(content)
            print(f"     ✓ Generated: {filename} ({len(content)} bytes)")
        else:
            print(f"     ✗ Failed to generate {format_type} resource estimate")
    
    # Restore original format
    print_service.set_print_format(original_format)
    print(f"   ✓ Restored original format: {original_format}")
    print()
    
    # 6. Create templates
    print("6. Creating Templates:")
    success, message = print_service.create_templates()
    if success:
        print(f"   ✓ {message}")
    else:
        print(f"   ✗ {message}")
    print()
    
    print("=" * 60)
    print("Example completed!")
    print()
    print("Generated files:")
    print("- example_estimate_standard.pdf/xlsx - Standard estimate format")
    print("- example_estimate_resource.pdf/xlsx - Estimate with resource statement")
    print("- example_estimate_default_resource.pdf/xlsx - Using default config")
    print("- example_estimate_resource_pdf.pdf - PDF resource variant")
    print("- example_estimate_resource_excel.xlsx - Excel resource variant")
    print()
    print("Key differences in RESOURCE variant:")
    print("1. Includes the standard estimate on first page/sheet")
    print("2. Adds a separate resource statement (ресурсная ведомость)")
    print("3. Resource statement shows:")
    print("   - Line number")
    print("   - Material code and description")
    print("   - Total quantity needed")
    print("   - Unit price")
    print("   - Total cost")
    print("4. Includes total cost of all materials")


def show_configuration_options():
    """Show available configuration options"""
    print("\n" + "=" * 60)
    print("Configuration Options")
    print("=" * 60)
    
    print("Print Format Options:")
    print("- PDF: Standard PDF format")
    print("- EXCEL: Excel format with multiple sheets")
    print()
    
    print("Estimate Variant Options:")
    print("- STANDARD: Traditional estimate format")
    print("- RESOURCE: Estimate + separate resource statement")
    print()
    
    print("Configuration Methods:")
    print("- print_service.set_print_format('PDF' or 'EXCEL')")
    print("- print_service.set_estimate_print_variant('STANDARD' or 'RESOURCE')")
    print("- estimate_service.generate_print_form(id, variant='RESOURCE')")
    print()
    
    print("Configuration is saved to env.ini file:")
    print("[PrintForms]")
    print("format = PDF")
    print("estimate_variant = RESOURCE")


if __name__ == "__main__":
    try:
        demonstrate_estimate_printing()
        show_configuration_options()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)