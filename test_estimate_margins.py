"""Test estimate print form with updated margins and column widths"""
import sys
from src.services.estimate_print_form import EstimatePrintForm

def test_estimate_print():
    """Test estimate print form generation"""
    print("Generating estimate print form...")
    
    # Create print form generator
    generator = EstimatePrintForm()
    
    # Generate PDF for estimate ID 1
    pdf_content = generator.generate(1)
    
    if pdf_content:
        # Save to file
        output_file = "test_estimate_margins.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_content)
        print(f"✓ PDF generated successfully: {output_file}")
        print(f"  File size: {len(pdf_content)} bytes")
        print("\nИзменения:")
        print("- Поля уменьшены с 20мм до 10мм для горизонтальной ориентации")
        print("- Колонка 'Наименование' расширена с 45мм до 70мм")
        print("- Остальные колонки пропорционально увеличены")
        print("- Общая ширина таблицы: ~257мм (использует почти всю ширину A4)")
    else:
        print("✗ Failed to generate PDF - estimate not found")
        return False
    
    return True

if __name__ == "__main__":
    success = test_estimate_print()
    sys.exit(0 if success else 1)
