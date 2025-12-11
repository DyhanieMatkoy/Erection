"""Test script for document posting functionality"""
import sys
from datetime import date
from src.data.database_manager import DatabaseManager
from src.services.document_posting_service import DocumentPostingService
from src.data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository


def print_separator():
    print("\n" + "="*80 + "\n")


def test_posting():
    """Test document posting"""
    
    # Initialize database
    db_manager = DatabaseManager()
    if not db_manager.initialize("construction.db"):
        print("Failed to initialize database")
        return False
    
    db = db_manager.get_connection()
    posting_service = DocumentPostingService()
    register_repo = WorkExecutionRegisterRepository()
    
    print("Тест проведения документов")
    print_separator()
    
    # Find or create test estimate
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, number, is_posted
        FROM estimates
        ORDER BY id DESC
        LIMIT 1
    """)
    
    estimate = cursor.fetchone()
    if not estimate:
        print("❌ Нет смет в базе данных. Создайте смету через интерфейс.")
        return False
    
    estimate_id = estimate['id']
    estimate_number = estimate['number']
    is_posted = estimate['is_posted']
    
    print(f"Найдена смета: {estimate_number} (ID: {estimate_id})")
    print(f"Статус проведения: {'Проведена' if is_posted else 'Не проведена'}")
    
    # Check if estimate has required fields
    cursor.execute("SELECT object_id, customer_id FROM estimates WHERE id = ?", (estimate_id,))
    est_data = cursor.fetchone()
    
    if not est_data['object_id']:
        print("\n⚠ У сметы не заполнен объект. Заполняем...")
        # Find or create object
        cursor.execute("SELECT id FROM objects WHERE marked_for_deletion = 0 LIMIT 1")
        obj = cursor.fetchone()
        if obj:
            cursor.execute("UPDATE estimates SET object_id = ? WHERE id = ?", (obj['id'], estimate_id))
            db.commit()
            print(f"✓ Установлен объект ID: {obj['id']}")
        else:
            print("❌ Нет объектов в базе. Создайте объект через интерфейс.")
            return False
    
    if not est_data['customer_id']:
        print("\n⚠ У сметы не заполнен заказчик. Заполняем...")
        # Find or create counterparty
        cursor.execute("SELECT id FROM counterparties WHERE marked_for_deletion = 0 LIMIT 1")
        cp = cursor.fetchone()
        if cp:
            cursor.execute("UPDATE estimates SET customer_id = ? WHERE id = ?", (cp['id'], estimate_id))
            db.commit()
            print(f"✓ Установлен заказчик ID: {cp['id']}")
        else:
            print("❌ Нет контрагентов в базе. Создайте контрагента через интерфейс.")
            return False
    
    # If already posted, unpost first
    if is_posted:
        print("\nОтменяем проведение...")
        success, error = posting_service.unpost_estimate(estimate_id)
        if not success:
            print(f"❌ Ошибка при отмене проведения: {error}")
            return False
        print("✓ Проведение отменено")
    
    print_separator()
    
    # Test posting estimate
    print("Тест 1: Проведение сметы")
    print("-" * 40)
    
    success, error = posting_service.post_estimate(estimate_id)
    if not success:
        print(f"❌ Ошибка при проведении: {error}")
        return False
    
    print("✓ Смета проведена успешно")
    
    # Check movements
    movements = register_repo.get_movements('estimate', estimate_id)
    print(f"✓ Создано движений: {len(movements)}")
    
    if movements:
        print("\nПример движения:")
        m = movements[0]
        print(f"  - Работа ID: {m['work_id']}")
        print(f"  - Приход количества: {m['quantity_income']}")
        print(f"  - Приход суммы: {m['sum_income']}")
    
    print_separator()
    
    # Test balance
    print("Тест 2: Проверка остатков")
    print("-" * 40)
    
    balance = register_repo.get_balance(
        filters={'estimate_id': estimate_id},
        grouping=['work']
    )
    
    print(f"✓ Получено строк остатков: {len(balance)}")
    
    if balance:
        print("\nПример остатка:")
        b = balance[0]
        print(f"  - Работа: {b.get('work_name', 'N/A')}")
        print(f"  - План количество: {b['quantity_income']}")
        print(f"  - Факт количество: {b['quantity_expense']}")
        print(f"  - Остаток количество: {b['quantity_balance']}")
        print(f"  - План сумма: {b['sum_income']:.2f}")
        print(f"  - Факт сумма: {b['sum_expense']:.2f}")
        print(f"  - Остаток сумма: {b['sum_balance']:.2f}")
    
    print_separator()
    
    # Find daily report for this estimate
    cursor.execute("""
        SELECT id, date, is_posted
        FROM daily_reports
        WHERE estimate_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (estimate_id,))
    
    report = cursor.fetchone()
    
    if report:
        report_id = report['id']
        report_date = report['date']
        is_posted = report['is_posted']
        
        print(f"Найден ежедневный отчет от {report_date} (ID: {report_id})")
        print(f"Статус проведения: {'Проведен' if is_posted else 'Не проведен'}")
        
        # If already posted, unpost first
        if is_posted:
            print("\nОтменяем проведение...")
            success, error = posting_service.unpost_daily_report(report_id)
            if not success:
                print(f"❌ Ошибка при отмене проведения: {error}")
                return False
            print("✓ Проведение отменено")
        
        print_separator()
        
        # Test posting daily report
        print("Тест 3: Проведение ежедневного отчета")
        print("-" * 40)
        
        success, error = posting_service.post_daily_report(report_id)
        if not success:
            print(f"❌ Ошибка при проведении: {error}")
            return False
        
        print("✓ Отчет проведен успешно")
        
        # Check movements
        movements = register_repo.get_movements('daily_report', report_id)
        print(f"✓ Создано движений: {len(movements)}")
        
        if movements:
            print("\nПример движения:")
            m = movements[0]
            print(f"  - Работа ID: {m['work_id']}")
            print(f"  - Расход количества: {m['quantity_expense']}")
            print(f"  - Расход суммы: {m['sum_expense']}")
        
        print_separator()
        
        # Test balance after report
        print("Тест 4: Проверка остатков после отчета")
        print("-" * 40)
        
        balance = register_repo.get_balance(
            filters={'estimate_id': estimate_id},
            grouping=['work']
        )
        
        print(f"✓ Получено строк остатков: {len(balance)}")
        
        if balance:
            print("\nПример остатка:")
            b = balance[0]
            print(f"  - Работа: {b.get('work_name', 'N/A')}")
            print(f"  - План количество: {b['quantity_income']}")
            print(f"  - Факт количество: {b['quantity_expense']}")
            print(f"  - Остаток количество: {b['quantity_balance']}")
            print(f"  - План сумма: {b['sum_income']:.2f}")
            print(f"  - Факт сумма: {b['sum_expense']:.2f}")
            print(f"  - Остаток сумма: {b['sum_balance']:.2f}")
            
            # Calculate percentage
            if b['quantity_income'] > 0:
                percent = (b['quantity_expense'] / b['quantity_income']) * 100
                print(f"  - Процент выполнения: {percent:.1f}%")
        
        print_separator()
        
        # Test unposting
        print("Тест 5: Отмена проведения")
        print("-" * 40)
        
        print("Отменяем проведение отчета...")
        success, error = posting_service.unpost_daily_report(report_id)
        if not success:
            print(f"❌ Ошибка: {error}")
            return False
        print("✓ Проведение отчета отменено")
        
        # Check movements deleted
        movements = register_repo.get_movements('daily_report', report_id)
        if len(movements) == 0:
            print("✓ Движения отчета удалены")
        else:
            print(f"❌ Движения не удалены (осталось {len(movements)})")
            return False
        
        print("\nОтменяем проведение сметы...")
        success, error = posting_service.unpost_estimate(estimate_id)
        if not success:
            print(f"❌ Ошибка: {error}")
            return False
        print("✓ Проведение сметы отменено")
        
        # Check movements deleted
        movements = register_repo.get_movements('estimate', estimate_id)
        if len(movements) == 0:
            print("✓ Движения сметы удалены")
        else:
            print(f"❌ Движения не удалены (осталось {len(movements)})")
            return False
    
    else:
        print("⚠ Нет ежедневных отчетов для этой сметы")
        print("Создайте отчет через интерфейс для полного тестирования")
    
    print_separator()
    print("✅ Все тесты пройдены успешно!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_posting()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении тестов: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
