#!/usr/bin/env python3
"""Simple Database Initializer

Упрощенная инициализация базы данных для тестов, которая создает только необходимые таблицы
и использует SQL Dialect Translator для корректного перевода между диалектами.
"""

import logging
from typing import Optional, List
from sqlalchemy import create_engine, text
from sql_dialect_translator import SQLDialectTranslator, SQLDialect


class SimpleDatabaseInitializer:
    """Упрощенная инициализация базы данных для тестов"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize simple database initializer
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.translator = SQLDialectTranslator(logger)
    
    def initialize_test_database(self, connection_string: str) -> bool:
        """Initialize test database with minimal required tables
        
        Args:
            connection_string: Database connection string
            
        Returns:
            True if initialization successful
        """
        try:
            # Determine target dialect
            if connection_string.startswith('sqlite:'):
                target_dialect = SQLDialect.SQLITE
            elif connection_string.startswith('mysql'):
                target_dialect = SQLDialect.MYSQL
            elif connection_string.startswith('postgresql:'):
                target_dialect = SQLDialect.POSTGRESQL
            else:
                raise Exception(f"Unsupported database type in connection string: {connection_string}")
            
            self.logger.info(f"Initializing {target_dialect.value} test database")
            
            # Create engine with appropriate settings
            engine_kwargs = self._get_engine_kwargs(target_dialect)
            engine = create_engine(connection_string, **engine_kwargs)
            
            # Get minimal table definitions
            base_tables = self._get_minimal_table_definitions()
            
            with engine.connect() as conn:
                # Create tables
                for table_name, base_sql in base_tables.items():
                    try:
                        # Translate SQL to target dialect
                        if target_dialect != SQLDialect.SQLITE:
                            translated_sql = self.translator.translate_sql(base_sql, SQLDialect.SQLITE, target_dialect)
                        else:
                            translated_sql = base_sql
                        
                        # Execute SQL
                        conn.execute(text(translated_sql))
                        self.logger.debug(f"Created table: {table_name}")
                        
                    except Exception as e:
                        # Ignore "already exists" errors
                        error_str = str(e).lower()
                        if any(err in error_str for err in ["already exists", "duplicate", "table exists"]):
                            self.logger.debug(f"Table {table_name} already exists, skipping")
                        else:
                            self.logger.warning(f"Failed to create table {table_name}: {e}")
                
                conn.commit()
            
            engine.dispose()
            self.logger.info(f"Test database initialized successfully: {target_dialect.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize test database: {e}")
            return False
    
    def _get_engine_kwargs(self, dialect: SQLDialect) -> dict:
        """Get engine configuration for dialect"""
        if dialect == SQLDialect.SQLITE:
            return {
                'echo': False,
                'poolclass': None,
                'connect_args': {'check_same_thread': False}
            }
        elif dialect == SQLDialect.MYSQL:
            return {
                'echo': False,
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 1800,
                'pool_pre_ping': True,
                'connect_args': {
                    'connect_timeout': 60,
                    'read_timeout': 300,
                    'write_timeout': 300,
                    'charset': 'utf8mb4'
                }
            }
        elif dialect == SQLDialect.POSTGRESQL:
            return {
                'echo': False,
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True
            }
        else:
            return {'echo': False}
    
    def _get_minimal_table_definitions(self) -> dict:
        """Get minimal table definitions in SQLite format (base format)
        
        Returns:
            Dictionary of table_name -> SQL definition
        """
        return {
            # Основные таблицы для синхронизации
            'sync_nodes': """
                CREATE TABLE IF NOT EXISTS sync_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL UNIQUE,
                    entity_type TEXT NOT NULL,
                    entity_uuid TEXT NOT NULL,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            'sync_changes': """
                CREATE TABLE IF NOT EXISTS sync_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_uuid TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    packet_no INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )
            """,
            
            # Пользователи (упрощенная версия)
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Персоны (упрощенная версия)
            'persons': """
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    position TEXT,
                    phone TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Контрагенты (упрощенная версия)
            'counterparties': """
                CREATE TABLE IF NOT EXISTS counterparties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    inn TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Объекты (упрощенная версия)
            'objects': """
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    address TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Работы (упрощенная версия)
            'works': """
                CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    code TEXT,
                    unit TEXT,
                    price REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Сметы (упрощенная версия)
            'estimates': """
                CREATE TABLE IF NOT EXISTS estimates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    number TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total_sum REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Ежедневные отчеты (упрощенная версия)
            'daily_reports': """
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    number TEXT NOT NULL,
                    date TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """,
            
            # Табели (упрощенная версия)
            'timesheets': """
                CREATE TABLE IF NOT EXISTS timesheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    number TEXT NOT NULL,
                    date TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )
            """
        }


def main():
    """Test simple database initializer"""
    logging.basicConfig(level=logging.INFO)
    
    initializer = SimpleDatabaseInitializer()
    
    # Test SQLite
    sqlite_result = initializer.initialize_test_database("sqlite:///test_simple.db")
    print(f"SQLite initialization: {'SUCCESS' if sqlite_result else 'FAILED'}")
    
    # Test MySQL (if available) - first create database, then initialize
    try:
        import pymysql
        
        # Create database first
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='root_password'
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS test_simple")
        conn.commit()
        conn.close()
        print("MySQL database 'test_simple' created")
        
        # Now initialize tables
        mysql_result = initializer.initialize_test_database("mysql+pymysql://root:root_password@localhost:3306/test_simple")
        print(f"MySQL initialization: {'SUCCESS' if mysql_result else 'FAILED'}")
        
    except Exception as e:
        print(f"MySQL initialization: FAILED - {e}")


if __name__ == '__main__':
    main()