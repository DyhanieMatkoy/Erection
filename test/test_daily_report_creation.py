"""Test daily report creation from estimate"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.data.database_manager import DatabaseManager
from src.services.auth_service import AuthService

def test_estimate_list():
    """Test estimate list form with create daily report button"""
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
    # Login first
    auth_service = AuthService()
    
    # Try to login as admin
    success, message = auth_service.login("admin", "admin")
    if not success:
        QMessageBox.critical(None, "Ошибка", f"Не удалось войти: {message}")
        return
    
    # Import after login to ensure auth context is set
    from src.views.estimate_list_form import EstimateListForm
    
    # Create estimate list form
    form = EstimateListForm()
    form.show()
    
    print("Форма списка смет открыта")
    print("Проверьте:")
    print("1. Кнопка 'Создать Ежедневный отчёт' присутствует")
    print("2. При выборе сметы и нажатии кнопки открывается форма ежедневного отчёта")
    print("3. В форме отчёта смета уже выбрана")
    print("4. Можно выбрать бригадира через кнопку '...'")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_estimate_list()
