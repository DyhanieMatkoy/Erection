"""
Модуль для создания начальных данных при первом запуске приложения
"""
import sqlite3
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def simple_hash(password: str) -> str:
    """Simple SHA256 hash for admin user (matches auth_service.py)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_initial_admin_user(db_path: str) -> bool:
    """
    Создает пользователя admin при первом запуске
    
    Args:
        db_path: Путь к базе данных SQLite
        
    Returns:
        True если пользователь создан или уже существует, False при ошибке
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь admin
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            logger.info("Пользователь admin уже существует")
            conn.close()
            return True
        
        # Создаем пользователя admin
        admin_password_hash = simple_hash("admin")
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?)
        """, ("admin", admin_password_hash, "Администратор", 1))
        
        admin_id = cursor.lastrowid
        
        # Создаем запись в persons для пользователя admin
        cursor.execute("""
            INSERT INTO persons (full_name, position, user_id, marked_for_deletion)
            VALUES (?, ?, ?, ?)
        """, ("Администратор системы", "Администратор", admin_id, 0))
        
        conn.commit()
        conn.close()
        
        logger.info("Пользователь admin создан успешно")
        print("✓ Создан пользователь admin (логин: admin, пароль: admin)")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания пользователя admin: {e}")
        print(f"✗ Ошибка создания пользователя admin: {e}")
        return False


def create_initial_data(db_path: str) -> bool:
    """
    Создает все начальные данные при первом запуске
    
    Args:
        db_path: Путь к базе данных SQLite
        
    Returns:
        True если данные созданы успешно, False при ошибке
    """
    try:
        # Создаем пользователя admin
        if not create_initial_admin_user(db_path):
            return False
        
        # Здесь можно добавить создание других начальных данных
        # например, базовые справочники, настройки по умолчанию и т.д.
        
        logger.info("Начальные данные созданы успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания начальных данных: {e}")
        return False


def ensure_admin_user_exists(db_path: str) -> bool:
    """
    Проверяет существование пользователя admin и создает его при необходимости
    Эта функция вызывается при каждом запуске приложения
    
    Args:
        db_path: Путь к базе данных SQLite
        
    Returns:
        True если пользователь admin существует или создан, False при ошибке
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы users
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            logger.warning("Таблица users не существует")
            conn.close()
            return False
        
        # Проверяем существование пользователя admin
        cursor.execute("SELECT id, password_hash FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            # Проверяем, что пароль корректный (может быть поврежден)
            admin_id, current_hash = admin_user
            expected_hash = simple_hash("admin")
            
            if current_hash != expected_hash:
                logger.info("Обновляем пароль пользователя admin")
                cursor.execute("""
                    UPDATE users SET password_hash = ? WHERE id = ?
                """, (expected_hash, admin_id))
                conn.commit()
                print("✓ Пароль пользователя admin обновлен")
            
            conn.close()
            return True
        
        # Создаем пользователя admin
        logger.info("Создаем пользователя admin")
        return create_initial_admin_user(db_path)
        
    except Exception as e:
        logger.error(f"Ошибка проверки пользователя admin: {e}")
        return False