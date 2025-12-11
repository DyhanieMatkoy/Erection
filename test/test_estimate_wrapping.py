"""Test estimate print form with text wrapping on existing data"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.services.estimate_service import EstimateService

# Initialize database
db = DatabaseManager()
if not db.initialize('construction.db'):
    print("Failed to initialize database")
    sys.exit(1)

def test_estimate_wrapping():
    """Test estimate print form with text wrapping"""
    print("=" * 60)
    print("Testing text wrapping in estimate print form")
    print("=" * 60)
    
    service = EstimateService()
    
    # Generate print form for estimate ID 1
    pdf_content = service.generate_print_form(1)
    
    if pdf_content:
        output_file = "test_estimate_wrapping.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_content)
        print(f"\n✓ PDF generated: {output_file}")
        print(f"  Size: {len(pdf_content)} bytes")
        print("\nИзменения:")
        print("- Поля уменьшены с 20мм до 10мм")
        print("- Колонка 'Наименование' расширена с 45мм до 70мм")
        print("- Текст переносится по словам")
        print("- Высота строк автоматически подстраивается")
        return True
    else:
        print("✗ Failed to generate PDF")
        return False

if __name__ == "__main__":
    success = test_estimate_wrapping()
    sys.exit(0 if success else 1)
