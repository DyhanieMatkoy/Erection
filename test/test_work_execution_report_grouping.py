"""Test work execution report with 2-level grouping"""
import sys
from PyQt6.QtWidgets import QApplication
from src.views.work_execution_report_form import WorkExecutionReportForm
from src.data.database_manager import DatabaseManager


def test_work_execution_report():
    """Test work execution report form with hierarchical grouping"""
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    # Create and show form
    form = WorkExecutionReportForm()
    form.show()
    
    print("Тест отчета 'Выполнение работ' с 2 уровнями группировки")
    print("=" * 60)
    print("\nФункциональность:")
    print("1. Группировка 1 - первый уровень иерархии")
    print("2. Группировка 2 - второй уровень иерархии (вложенный)")
    print("3. Итоги по группам первого уровня (жирным шрифтом, голубой фон)")
    print("4. Детализация по группам второго уровня (с отступом)")
    print("\nПримеры комбинаций группировок:")
    print("- По объектам -> По сметам")
    print("- По сметам -> По работам")
    print("- По датам -> По работам")
    print("- По объектам -> По датам")
    print("\nИнструкция:")
    print("1. Выберите период отчета")
    print("2. Выберите фильтры (опционально)")
    print("3. Выберите Группировку 1 (первый уровень)")
    print("4. Выберите Группировку 2 (второй уровень)")
    print("5. Нажмите 'Сформировать'")
    print("\nПримечание: Группировки должны быть разными")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    test_work_execution_report()
