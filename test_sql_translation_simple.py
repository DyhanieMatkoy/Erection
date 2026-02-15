#!/usr/bin/env python3
"""Simple test for SQL translation functionality"""

import logging
from sql_dialect_translator import SQLDialectTranslator, SQLDialect

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("SQLTranslationTest")

def test_date_translation():
    """Test DATE type translation to SQLite"""
    
    translator = SQLDialectTranslator(logger)
    
    # Test SQL with DATE type
    test_sql = """CREATE TABLE IF NOT EXISTS estimates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        date DATE NOT NULL,
        customer_id INTEGER REFERENCES counterparties(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    
    print("Original SQL:")
    print(test_sql)
    print("\n" + "="*50 + "\n")
    
    # Translate using universal rules
    translated_sql = translator.translate_sql(test_sql, 'any', SQLDialect.SQLITE)
    
    print("Translated SQL (any → SQLite):")
    print(translated_sql)
    print("\n" + "="*50 + "\n")
    
    # Check if DATE was translated to TEXT
    if "date TEXT NOT NULL" in translated_sql:
        print("✅ SUCCESS: DATE was correctly translated to TEXT")
        return True
    else:
        print("❌ FAILED: DATE was not translated correctly")
        print(f"Expected: 'date TEXT NOT NULL'")
        print(f"Found in result: {translated_sql}")
        return False

if __name__ == "__main__":
    success = test_date_translation()
    exit(0 if success else 1)