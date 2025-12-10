"""Database manager for SQLite operations"""
import sqlite3
from typing import Optional


class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
        return cls._instance
    
    def initialize(self, db_path: str) -> bool:
        """Initialize database connection and create tables"""
        try:
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._create_tables()
            self._create_indices()
            return True
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return False
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return self._connection
    
    def _create_tables(self):
        """Create all database tables"""
        cursor = self._connection.cursor()
        
        tables = [
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )""",
            
            # Persons
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Organizations
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                default_responsible_id INTEGER REFERENCES persons(id),
                parent_id INTEGER REFERENCES organizations(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Counterparties
            """CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                contact_person TEXT,
                phone TEXT,
                parent_id INTEGER REFERENCES counterparties(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Objects
            """CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES counterparties(id),
                address TEXT,
                parent_id INTEGER REFERENCES objects(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Works
            """CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                parent_id INTEGER REFERENCES works(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",
            
            # Estimates
            """CREATE TABLE IF NOT EXISTS estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                customer_id INTEGER REFERENCES counterparties(id),
                object_id INTEGER REFERENCES objects(id),
                contractor_id INTEGER REFERENCES organizations(id),
                responsible_id INTEGER REFERENCES persons(id),
                total_sum REAL DEFAULT 0,
                total_labor REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Estimate Lines
            """CREATE TABLE IF NOT EXISTS estimate_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
                line_number INTEGER,
                work_id INTEGER REFERENCES works(id),
                quantity REAL,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                sum REAL,
                planned_labor REAL,
                is_group INTEGER DEFAULT 0,
                group_name TEXT,
                parent_group_id INTEGER REFERENCES estimate_lines(id),
                is_collapsed INTEGER DEFAULT 0
            )""",
            
            # Daily Reports
            """CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Daily Report Lines
            """CREATE TABLE IF NOT EXISTS daily_report_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
                line_number INTEGER,
                work_id INTEGER REFERENCES works(id),
                planned_labor REAL,
                actual_labor REAL,
                deviation_percent REAL,
                is_group INTEGER DEFAULT 0,
                group_name TEXT,
                parent_group_id INTEGER REFERENCES daily_report_lines(id),
                is_collapsed INTEGER DEFAULT 0
            )""",
            
            # Daily Report Executors
            """CREATE TABLE IF NOT EXISTS daily_report_executors (
                report_line_id INTEGER REFERENCES daily_report_lines(id) ON DELETE CASCADE,
                executor_id INTEGER REFERENCES persons(id),
                PRIMARY KEY (report_line_id, executor_id)
            )""",
            
            # User Settings
            """CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER REFERENCES users(id),
                form_name TEXT,
                setting_key TEXT,
                setting_value TEXT,
                PRIMARY KEY (user_id, form_name, setting_key)
            )""",
            
            # Constants
            """CREATE TABLE IF NOT EXISTS constants (
                key TEXT PRIMARY KEY,
                value TEXT
            )""",
            
            # Work Execution Register (Регистр накопления ВыполнениеРабот)
            """CREATE TABLE IF NOT EXISTS work_execution_register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorder_type TEXT NOT NULL,
                recorder_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                period DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                work_id INTEGER REFERENCES works(id),
                quantity_income REAL DEFAULT 0,
                quantity_expense REAL DEFAULT 0,
                sum_income REAL DEFAULT 0,
                sum_expense REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # Add posting fields to documents if they don't exist
        self._add_posting_fields()
        
        self._connection.commit()
    
    def _add_posting_fields(self):
        """Add posting fields to documents (migration)"""
        cursor = self._connection.cursor()
        
        # Check if fields exist in estimates
        cursor.execute("PRAGMA table_info(estimates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_posted' not in columns:
            cursor.execute("ALTER TABLE estimates ADD COLUMN is_posted INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE estimates ADD COLUMN posted_at TIMESTAMP")
        
        # Check if fields exist in daily_reports
        cursor.execute("PRAGMA table_info(daily_reports)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_posted' not in columns:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN is_posted INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN posted_at TIMESTAMP")
        
        # Add code field to works if it doesn't exist
        cursor.execute("PRAGMA table_info(works)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'code' not in columns:
            cursor.execute("ALTER TABLE works ADD COLUMN code TEXT")
        
        # Add grouping fields to estimate_lines if they don't exist
        cursor.execute("PRAGMA table_info(estimate_lines)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_group' not in columns:
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN is_group INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN group_name TEXT")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN parent_group_id INTEGER REFERENCES estimate_lines(id)")
            cursor.execute("ALTER TABLE estimate_lines ADD COLUMN is_collapsed INTEGER DEFAULT 0")
        
        # Add grouping fields to daily_report_lines if they don't exist
        cursor.execute("PRAGMA table_info(daily_report_lines)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_group' not in columns:
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN is_group INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN group_name TEXT")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN parent_group_id INTEGER REFERENCES daily_report_lines(id)")
            cursor.execute("ALTER TABLE daily_report_lines ADD COLUMN is_collapsed INTEGER DEFAULT 0")
        
        # Add parent_id and is_group fields to references if they don't exist
        for table in ['persons', 'counterparties', 'objects', 'organizations', 'works']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'parent_id' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN parent_id INTEGER REFERENCES {table}(id)")
            
            if 'is_group' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_group INTEGER DEFAULT 0")
    
    def _create_indices(self):
        """Create database indices"""
        cursor = self._connection.cursor()
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",
            "CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date)",
            "CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)",
            # Register indices
            "CREATE INDEX IF NOT EXISTS idx_register_recorder ON work_execution_register(recorder_type, recorder_id)",
            "CREATE INDEX IF NOT EXISTS idx_register_dimensions ON work_execution_register(period, object_id, estimate_id, work_id)"
        ]
        
        for index_sql in indices:
            cursor.execute(index_sql)
        
        self._connection.commit()
