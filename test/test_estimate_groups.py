"""Test estimate print form with groups and text wrapping"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.services.estimate_print_form import EstimatePrintForm

# Initialize database
db_manager = DatabaseManager()
if not db_manager.initialize('construction.db'):
    print("Failed to initialize database")
    sys.exit(1)

def create_test_estimate_with_groups():
    """Create test estimate with groups"""
    db = db_manager.get_connection()
    cursor = db.cursor()
    
    # Check if estimate with groups already exists
    cursor.execute("SELECT id FROM estimates WHERE number = 'TEST-GROUPS'")
    existing = cursor.fetchone()
    
    if existing:
        estimate_id = existing['id']
        print(f"Using existing estimate ID: {estimate_id}")
    else:
        # Create new estimate
        cursor.execute("""
            INSERT INTO estimates (number, date, total_sum, total_labor)
            VALUES ('TEST-GROUPS', date('now'), 500000, 200)
        """)
        estimate_id = cursor.lastrowid
        print(f"Created new estimate ID: {estimate_id}")
        
        # Add lines with groups
        lines = [
            # Group 1
            (1, True, "РАЗДЕЛ 1. ЗЕМЛЯНЫЕ РАБОТЫ", "", 0, "", 0, 0, 0, 0),
            (2, False, "Разработка грунта экскаватором с погрузкой на автомобили-самосвалы", "01-01-001", 100, "м3", 250, 50, 25000, 5000),
            (3, False, "Обратная засыпка траншей и котлованов бульдозерами мощностью 59 кВт", "01-02-061", 80, "м3", 180, 35, 14400, 2800),
            
            # Group 2
            (4, True, "РАЗДЕЛ 2. БЕТОННЫЕ И ЖЕЛЕЗОБЕТОННЫЕ КОНСТРУКЦИИ МОНОЛИТНЫЕ", "", 0, "", 0, 0, 0, 0),
            (5, False, "Устройство бетонной подготовки", "06-01-001", 50, "м3", 3500, 280, 175000, 14000),
            (6, False, "Укладка бетонной смеси в фундаменты при помощи автобетононасоса", "06-01-024", 120, "м3", 4200, 350, 504000, 42000),
            
            # Group 3
            (7, True, "РАЗДЕЛ 3. КОНСТРУКЦИИ ИЗ КИРПИЧА И БЛОКОВ", "", 0, "", 0, 0, 0, 0),
            (8, False, "Кладка стен наружных толщиной 510 мм из кирпича керамического пустотелого", "08-01-001", 200, "м3", 5800, 450, 1160000, 90000),
        ]
        
        for line_num, is_group, name, code, qty, unit, price, labor, total, labor_total in lines:
            if is_group:
                cursor.execute("""
                    INSERT INTO estimate_lines 
                    (estimate_id, line_number, is_group, group_name, quantity, unit, price, labor_rate, sum, planned_labor)
                    VALUES (?, ?, 1, ?, 0, '', 0, 0, 0, 0)
                """, (estimate_id, line_num, name))
            else:
                cursor.execute("""
                    INSERT INTO estimate_lines 
                    (estimate_id, line_number, is_group, quantity, unit, price, labor_rate, sum, planned_labor)
                    VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?)
                """, (estimate_id, line_num, qty, unit, price, labor, total, labor_total))
                
                # Update work name directly in estimate_lines
                cursor.execute("""
                    UPDATE estimate_lines 
                    SET work_id = (SELECT id FROM works WHERE code = ? LIMIT 1)
                    WHERE estimate_id = ? AND line_number = ?
                """, (code, estimate_id, line_num))
        
        # Update totals
        cursor.execute("""
            UPDATE estimates 
            SET total_sum = (SELECT SUM(sum) FROM estimate_lines WHERE estimate_id = ? AND is_group = 0),
                total_labor = (SELECT SUM(planned_labor) FROM estimate_lines WHERE estimate_id = ? AND is_group = 0)
            WHERE id = ?
        """, (estimate_id, estimate_id, estimate_id))
        
        db.commit()
        print("Test data created")
    
    return estimate_id

def test_print_with_groups():
    """Test print form with groups"""
    print("=" * 60)
    print("Testing estimate print form with groups and text wrapping")
    print("=" * 60)
    
    # Create test data
    estimate_id = create_test_estimate_with_groups()
    
    # Generate PDF
    generator = EstimatePrintForm()
    pdf_content = generator.generate(estimate_id)
    
    if pdf_content:
        output_file = "test_estimate_groups.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_content)
        print(f"\n✓ PDF generated: {output_file}")
        print(f"  Size: {len(pdf_content)} bytes")
        print("\nФункции:")
        print("- Группы отображаются как объединенные ячейки на всю ширину")
        print("- Группы выделены серым фоном и жирным шрифтом")
        print("- Текст в колонке 'Наименование' переносится по словам")
        print("- Высота строк автоматически увеличивается при переносе")
        return True
    else:
        print("✗ Failed to generate PDF")
        return False

if __name__ == "__main__":
    success = test_print_with_groups()
    sys.exit(0 if success else 1)
