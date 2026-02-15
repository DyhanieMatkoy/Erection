#!/usr/bin/env python3
"""
Правильное исправление проблемы с созданием индексов в DatabaseManager
"""

import os
import sys
from pathlib import Path

def fix_database_manager():
    """Исправляет метод _create_indices в DatabaseManager"""
    
    print("🔧 Исправление метода _create_indices в DatabaseManager...")
    
    db_manager_path = Path("src/data/database_manager.py")
    
    if not db_manager_path.exists():
        print(f"❌ Файл не найден: {db_manager_path}")
        return False
    
    # Читаем содержимое файла
    with open(db_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и заменяем проблемный метод _create_indices
    old_method = '''    def _create_indices(self):
        """Create database indices with automatic SQL translation for multi-database support"""
        cursor = self._connection.cursor()
        
        # Determine target SQL dialect based on current database configuration
        target_dialect = self._get_current_sql_dialect()
        
        # Проверяем, что все необходимые таблицы существуют перед созданием индексов
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
            if not cursor.fetchone():
                logger.warning("Table 'estimates' does not exist, skipping index creation")
                return
                
            cursor.execute("PRAGMA table_info(estimates)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'date' not in columns:
                logger.warning("Column 'date' does not exist in estimates table, skipping date index")
                # Создаем индексы без проблемного индекса на date
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)",
                    "CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)",
                    # Audit Logs
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
                ]
            else:
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",'''
    
    new_method = '''    def _create_indices(self):
        """Create database indices with automatic SQL translation for multi-database support"""
        cursor = self._connection.cursor()
        
        # Determine target SQL dialect based on current database configuration
        target_dialect = self._get_current_sql_dialect()
        
        # Проверяем, что таблица estimates существует и имеет колонку date
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
            if not cursor.fetchone():
                logger.warning("Table 'estimates' does not exist, skipping index creation")
                return
                
            cursor.execute("PRAGMA table_info(estimates)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Создаем список индексов в зависимости от наличия колонок
            indices = []
            
            # Индекс на date только если колонка существует
            if 'date' in columns:
                indices.append("CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)")
            else:
                logger.warning("Column 'date' does not exist in estimates table, skipping date index")
            
            # Остальные индексы
            if 'responsible_id' in columns:
                indices.append("CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)")
            
            # Проверяем таблицу daily_reports
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_reports'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(daily_reports)")
                dr_columns = [row[1] for row in cursor.fetchall()]
                if 'date' in dr_columns:
                    indices.append("CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date)")
                if 'estimate_id' in dr_columns:
                    indices.append("CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)")
            
            # Базовые индексы для других таблиц
            indices.extend([
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
                "CREATE INDEX IF NOT EXISTS idx_register_recorder ON work_execution_register(recorder_type, recorder_id)",
                "CREATE INDEX IF NOT EXISTS idx_register_dimensions ON work_execution_register(period, object_id, estimate_id, work_id)",
                "CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)",
                "CREATE INDEX IF NOT EXISTS idx_timesheets_foreman ON timesheets(foreman_id)",
                "CREATE INDEX IF NOT EXISTS idx_timesheets_object ON timesheets(object_id)",
                "CREATE INDEX IF NOT EXISTS idx_timesheets_estimate ON timesheets(estimate_id)",
                "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_timesheet ON timesheet_lines(timesheet_id)",
                "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_employee ON timesheet_lines(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_recorder ON payroll_register(recorder_type, recorder_id)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_dimensions ON payroll_register(period, object_id, estimate_id, employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_date ON payroll_register(work_date)"
            ])
            
        except Exception as check_error:
            logger.error(f"Error checking table structure: {check_error}")
            # Fallback: создаем только безопасные индексы
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)"
            ]'''
    
    # Заменяем старый метод
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # Записываем исправленный файл
        with open(db_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Метод _create_indices исправлен")
        return True
    else:
        print("⚠️ Не удалось найти метод для исправления, попробуем другой подход")
        
        # Альтернативный подход - заменяем весь файл
        return fix_entire_method(content, db_manager_path)

def fix_entire_method(content, db_manager_path):
    """Исправляет весь метод _create_indices"""
    
    # Ищем начало метода
    method_start = content.find("def _create_indices(self):")
    if method_start == -1:
        print("❌ Не удалось найти метод _create_indices")
        return False
    
    # Ищем конец метода (следующий def или конец класса)
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = content.find("\nclass ", method_start + 1)
    if method_end == -1:
        method_end = len(content)
    
    # Новый метод
    new_method = '''    def _create_indices(self):
        """Create database indices with automatic SQL translation for multi-database support"""
        cursor = self._connection.cursor()
        
        # Determine target SQL dialect based on current database configuration
        target_dialect = self._get_current_sql_dialect()
        
        # Безопасное создание индексов с проверкой существования таблиц и колонок
        try:
            # Проверяем таблицу estimates
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(estimates)")
                est_columns = [row[1] for row in cursor.fetchall()]
                
                # Создаем индексы только для существующих колонок
                if 'date' in est_columns:
                    try:
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)")
                    except Exception as e:
                        logger.warning(f"Failed to create estimates date index: {e}")
                
                if 'responsible_id' in est_columns:
                    try:
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)")
                    except Exception as e:
                        logger.warning(f"Failed to create estimates responsible index: {e}")
            
            # Проверяем таблицу daily_reports
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_reports'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(daily_reports)")
                dr_columns = [row[1] for row in cursor.fetchall()]
                
                if 'date' in dr_columns:
                    try:
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date)")
                    except Exception as e:
                        logger.warning(f"Failed to create daily_reports date index: {e}")
                
                if 'estimate_id' in dr_columns:
                    try:
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)")
                    except Exception as e:
                        logger.warning(f"Failed to create daily_reports estimate index: {e}")
            
            # Создаем остальные индексы с обработкой ошибок
            other_indices = [
                ("audit_logs", "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"),
                ("audit_logs", "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)"),
                ("work_execution_register", "CREATE INDEX IF NOT EXISTS idx_register_recorder ON work_execution_register(recorder_type, recorder_id)"),
                ("work_execution_register", "CREATE INDEX IF NOT EXISTS idx_register_dimensions ON work_execution_register(period, object_id, estimate_id, work_id)"),
                ("timesheets", "CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)"),
                ("timesheets", "CREATE INDEX IF NOT EXISTS idx_timesheets_foreman ON timesheets(foreman_id)"),
                ("timesheets", "CREATE INDEX IF NOT EXISTS idx_timesheets_object ON timesheets(object_id)"),
                ("timesheets", "CREATE INDEX IF NOT EXISTS idx_timesheets_estimate ON timesheets(estimate_id)"),
                ("timesheet_lines", "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_timesheet ON timesheet_lines(timesheet_id)"),
                ("timesheet_lines", "CREATE INDEX IF NOT EXISTS idx_timesheet_lines_employee ON timesheet_lines(employee_id)"),
                ("payroll_register", "CREATE INDEX IF NOT EXISTS idx_payroll_recorder ON payroll_register(recorder_type, recorder_id)"),
                ("payroll_register", "CREATE INDEX IF NOT EXISTS idx_payroll_dimensions ON payroll_register(period, object_id, estimate_id, employee_id)"),
                ("payroll_register", "CREATE INDEX IF NOT EXISTS idx_payroll_date ON payroll_register(work_date)")
            ]
            
            for table_name, index_sql in other_indices:
                try:
                    # Проверяем существование таблицы
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    if cursor.fetchone():
                        cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Failed to create index for {table_name}: {e}")
            
            self._connection.commit()
            logger.info("Database indices created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indices: {e}")
            # Не поднимаем исключение, чтобы не прерывать инициализацию БД

'''
    
    # Заменяем метод
    new_content = content[:method_start] + new_method + content[method_end:]
    
    # Записываем исправленный файл
    with open(db_manager_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Метод _create_indices полностью переписан")
    return True

def main():
    """Главная функция"""
    
    print("🚀 Исправление проблемы с созданием индексов в DatabaseManager")
    print("=" * 60)
    
    if fix_database_manager():
        print("\n✅ Исправление успешно применено!")
        print("Теперь можно запускать тесты синхронизации.")
    else:
        print("\n❌ Не удалось применить исправление")

if __name__ == "__main__":
    main()