#!/usr/bin/env python3
"""
Скрипт для настройки Desktop клиента для работы по сети
"""
import os
import configparser
import sys
from pathlib import Path


def create_database_config():
    """Создает конфигурационный файл для подключения к удаленной базе данных"""
    
    print("=" * 60)
    print("Настройка Desktop клиента для работы по сети")
    print("=" * 60)
    
    # Выбор типа базы данных
    print("\nВыберите тип базы данных:")
    print("1. PostgreSQL (рекомендуется)")
    print("2. SQL Server")
    print("3. SQLite по сети (не рекомендуется)")
    
    while True:
        choice = input("\nВведите номер (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Неверный выбор. Введите 1, 2 или 3.")
    
    config = configparser.ConfigParser()
    
    if choice == '1':  # PostgreSQL
        print("\n--- Настройка PostgreSQL ---")
        host = input("IP адрес сервера PostgreSQL: ").strip()
        port = input("Порт (по умолчанию 5432): ").strip() or "5432"
        database = input("Имя базы данных (по умолчанию construction): ").strip() or "construction"
        username = input("Имя пользователя (по умолчанию postgres): ").strip() or "postgres"
        password = input("Пароль: ").strip()
        
        config['database'] = {
            'type': 'postgresql',
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password
        }
        
    elif choice == '2':  # SQL Server
        print("\n--- Настройка SQL Server ---")
        host = input("IP адрес сервера SQL Server: ").strip()
        port = input("Порт (по умолчанию 1433): ").strip() or "1433"
        database = input("Имя базы данных (по умолчанию construction): ").strip() or "construction"
        username = input("Имя пользователя (по умолчанию sa): ").strip() or "sa"
        password = input("Пароль: ").strip()
        driver = input("ODBC драйвер (по умолчанию 'ODBC Driver 17 for SQL Server'): ").strip() or "ODBC Driver 17 for SQL Server"
        
        config['database'] = {
            'type': 'mssql',
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password,
            'driver': driver
        }
        
    else:  # SQLite по сети
        print("\n--- Настройка SQLite по сети ---")
        print("⚠️  Внимание: SQLite по сети не рекомендуется для множественного доступа!")
        network_path = input("Сетевой путь к файлу базы данных (например, \\\\server\\share\\construction.db): ").strip()
        
        config['database'] = {
            'type': 'sqlite',
            'path': network_path
        }
    
    # Сохранение конфигурации
    config_path = Path('env.ini')
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"\n✅ Конфигурация сохранена в {config_path}")
    
    # Проверка подключения
    if input("\nПроверить подключение к базе данных? (y/n): ").lower().startswith('y'):
        test_connection(config)


def test_connection(config):
    """Тестирует подключение к базе данных"""
    print("\n--- Тестирование подключения ---")
    
    try:
        # Импортируем необходимые модули
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.data.database_manager import DatabaseManager
        
        # Создаем менеджер базы данных
        db_manager = DatabaseManager()
        
        # Инициализируем подключение
        if config['database']['type'] == 'sqlite':
            db_manager.initialize(config['database']['path'])
        else:
            db_manager.initialize_from_config('env.ini')
        
        # Проверяем подключение
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result:
            print("✅ Подключение успешно!")
            print("Desktop приложение готово к работе по сети.")
        else:
            print("❌ Ошибка: не удалось выполнить тестовый запрос")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\nВозможные причины:")
        print("- Неверные параметры подключения")
        print("- Сервер базы данных недоступен")
        print("- Проблемы с сетью или брандмауэром")
        print("- База данных не существует")


def show_usage_instructions():
    """Показывает инструкции по использованию"""
    print("\n" + "=" * 60)
    print("Инструкции по запуску")
    print("=" * 60)
    print("\n1. Убедитесь, что установлены все зависимости:")
    print("   pip install -r requirements.txt")
    print("\n2. Запустите Desktop приложение:")
    print("   python main.py")
    print("\n3. Если возникают проблемы:")
    print("   - Проверьте настройки в файле env.ini")
    print("   - Убедитесь, что сервер базы данных доступен")
    print("   - Проверьте настройки брандмауэра")
    print("\n4. Для получения подробной информации см.:")
    print("   NETWORK_DESKTOP_SETUP_GUIDE.md")


def main():
    """Главная функция"""
    try:
        create_database_config()
        show_usage_instructions()
        
    except KeyboardInterrupt:
        print("\n\nНастройка прервана пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()