#!/usr/bin/env python3
"""Test estimates table translation specifically"""

import logging
import sqlite3
from sql_dialect_translator import SQLDialectTranslator, SQLDialect

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("EstimatesTableTest")

def test_estimates_table():
    """Test estimates table creation with DATE translation"""
    
    translator = SQLDialectTranslator(logger)
    
    # Test SQL from database_manager.py
    estimates_sql = """CREATE TABLE IF NOT EXISTS estimates (
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
            )"""
    
    print("Original estimates table SQL:")
    print(estimates_sql)
    print("\n" + "="*50 + "\n")
    
    # Translate using universal rules
    translated_sql = translator.translate_sql(estimates_sql, 'any', SQLDialect.SQLITE)
    
    print("Translated estimates table SQL:")
    print(translated_sql)
    print("\n" + "="*50 + "\n")
    
    # Test creating the table in SQLite
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        cursor.execute(translated_sql)
        print("✅ Table created successfully")
        
        # Check table schema
        cursor.execute("PRAGMA table_info(estimates)")
        columns = cursor.fetchall()
        
        print("Table schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else ''}")
        
        # Test index creation
        index_sql = "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)"
        print(f"\nTesting index: {index_sql}")
        
        cursor.execute(index_sql)
        print("✅ Index created successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_estimates_table()
    exit(0 if success else 1)