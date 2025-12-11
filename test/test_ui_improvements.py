"""Test UI improvements"""
import sys
from PyQt6.QtWidgets import QApplication
from src.views.main_window import MainWindow
from src.data.database_manager import DatabaseManager


def test_ui_improvements():
    """Test UI improvements"""
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    # Create main window
    window = MainWindow()
    window.show()
    
    print("Тест улучшений пользовательского интерфейса")
    print("=" * 60)
    print("\n1. БЫСТРАЯ НАВИГАЦИЯ ПРИ ЗАПУСКЕ")
    print("   - Окно быстрой навигации должно открыться автоматически")
    print("   - Попробуйте ввести 'смет' для поиска")
    print("   - Используйте стрелки для навигации")
    print("   - Нажмите Enter для открытия формы")
    print("   - Нажмите Escape для закрытия")
    print("\n2. СТАТУСНАЯ СТРОКА")
    print("   - Откройте смету (Документы -> Сметы)")
    print("   - Создайте новую или откройте существующую")
    print("   - Внесите изменения и сохраните (Ctrl+S)")
    print("   - Проверьте сообщение в статусной строке внизу окна")
    print("   - Сообщение должно исчезнуть через 3 секунды")
    print("   - Проведите документ (Ctrl+K)")
    print("   - Проверьте сообщение 'Документ проведен'")
    print("\n3. ВЫБОР СМЕТЫ ЧЕРЕЗ ФОРМУ СПИСКА")
    print("   - Откройте ежедневный отчет (Документы -> Ежедневные отчеты)")
    print("   - Создайте новый отчет")
    print("   - Нажмите кнопку '...' рядом с полем 'Смета'")
    print("   - Должна открыться форма списка смет")
    print("   - Выберите смету и нажмите 'Выбрать'")
    print("   - Смета должна установиться в форме отчета")
    print("\n4. ГОРЯЧИЕ КЛАВИШИ")
    print("   - Ctrl+K - быстрая навигация (в любой момент)")
    print("   - Ctrl+S - сохранить документ")
    print("   - Ctrl+Shift+S - сохранить и закрыть")
    print("   - Ctrl+K (в документе) - провести")
    print("   - Ctrl+P - печать")
    print("   - Esc - закрыть форму")
    print("\nПримечание: Сообщения об ошибках по-прежнему")
    print("отображаются в модальных окнах.")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    test_ui_improvements()
