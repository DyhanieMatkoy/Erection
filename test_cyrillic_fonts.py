"""Test Cyrillic fonts in print forms"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.print_form_generator import PrintFormGenerator
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph

def test_cyrillic():
    """Test Cyrillic text rendering"""
    print("Testing Cyrillic font support...")
    
    # Create generator
    generator = PrintFormGenerator()
    
    print(f"Using font: {generator.font_name}")
    print(f"Using bold font: {generator.font_name_bold}")
    
    # Create test document
    elements = []
    
    # Test various Cyrillic texts
    elements.append(generator.create_title("ТЕСТОВЫЙ ДОКУМЕНТ"))
    elements.append(generator.create_spacer(10))
    elements.append(generator.create_subtitle("Проверка кириллицы"))
    elements.append(generator.create_spacer(10))
    elements.append(generator.create_paragraph("Это тестовый текст на русском языке."))
    elements.append(generator.create_paragraph("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"))
    elements.append(generator.create_paragraph("абвгдеёжзийклмнопрстуфхцчшщъыьэюя"))
    elements.append(generator.create_spacer(10))
    
    # Test table with Cyrillic
    table_data = [
        ["№", "Наименование", "Количество"],
        ["1", "Работа первая", "10.5"],
        ["2", "Работа вторая", "20.3"],
        ["3", "Работа третья", "15.7"]
    ]
    
    from reportlab.lib.units import mm
    col_widths = [20 * mm, 100 * mm, 40 * mm]
    table = generator.create_table(table_data, col_widths)
    elements.append(table)
    
    # Generate PDF
    try:
        pdf_content = generator.create_pdf(elements)
        
        # Save to file
        output_file = "test_cyrillic_output.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_content)
        
        print(f"\n✓ PDF created successfully: {output_file}")
        print(f"  File size: {len(pdf_content)} bytes")
        print("\nPlease open the PDF file to verify Cyrillic text is displayed correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cyrillic()
    sys.exit(0 if success else 1)
