#!/usr/bin/env python3
"""SQL Dialect Translator

Translates SQL statements between different database dialects:
SQLite ↔ PostgreSQL ↔ MySQL
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum


class SQLDialect(Enum):
    """Supported SQL dialects"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class SQLDialectTranslator:
    """Translates SQL between different database dialects"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize SQL dialect translator
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Translation rules for data types
        self.type_mappings = {
            # SQLite → PostgreSQL
            (SQLDialect.SQLITE, SQLDialect.POSTGRESQL): {
                r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b': 'SERIAL PRIMARY KEY',
                r'\bINTEGER\s+AUTOINCREMENT\b': 'SERIAL',
                r'\bINTEGER\b': 'INTEGER',
                r'\bTEXT\b': 'VARCHAR(255)',
                r'\bREAL\b': 'REAL',
                r'\bBLOB\b': 'BYTEA',
                r'\bDATETIME\b': 'TIMESTAMP',
                r'\bTIMESTAMP\b': 'TIMESTAMP',
                r'\bBOOLEAN\b': 'BOOLEAN',
            },
            
            # SQLite → MySQL
            (SQLDialect.SQLITE, SQLDialect.MYSQL): {
                r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b': 'INT AUTO_INCREMENT PRIMARY KEY',
                r'\bINTEGER\s+AUTOINCREMENT\b': 'INT AUTO_INCREMENT',
                r'\bINTEGER\b': 'INT',
                r'\bTEXT\b': 'VARCHAR(255)',
                r'\bREAL\b': 'DECIMAL(10,2)',
                r'\bBLOB\b': 'LONGBLOB',
                r'\bDATETIME\b': 'DATETIME',
                r'\bTIMESTAMP\b': 'TIMESTAMP',
                r'\bBOOLEAN\b': 'TINYINT(1)',
            },
            
            # PostgreSQL → SQLite
            (SQLDialect.POSTGRESQL, SQLDialect.SQLITE): {
                r'\bSERIAL\s+PRIMARY\s+KEY\b': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                r'\bSERIAL\b': 'INTEGER AUTOINCREMENT',
                r'\bVARCHAR\(\d+\)': 'TEXT',
                r'\bTIMESTAMP\b': 'TIMESTAMP',
                r'\bDATE\b': 'TEXT',
                r'\bBYTEA\b': 'BLOB',
            },
            
            # MySQL → SQLite  
            (SQLDialect.MYSQL, SQLDialect.SQLITE): {
                r'\bINT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY\b': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                r'\bINT\s+AUTO_INCREMENT\b': 'INTEGER AUTOINCREMENT',
                r'\bINT\b': 'INTEGER',
                r'\bVARCHAR\(\d+\)': 'TEXT',
                r'\bDECIMAL\(\d+,\d+\)': 'REAL',
                r'\bLONGBLOB\b': 'BLOB',
                r'\bDATETIME\b': 'TIMESTAMP',
                r'\bDATE\b': 'TEXT',
                r'\bTINYINT\(1\)': 'BOOLEAN',
            },
            
            # PostgreSQL → MySQL
            (SQLDialect.POSTGRESQL, SQLDialect.MYSQL): {
                r'\bSERIAL\s+PRIMARY\s+KEY\b': 'INT AUTO_INCREMENT PRIMARY KEY',
                r'\bSERIAL\b': 'INT AUTO_INCREMENT',
                r'\bTIMESTAMP\b': 'DATETIME',
                r'\bDATE\b': 'DATE',
                r'\bBYTEA\b': 'LONGBLOB',
                r'\bBOOLEAN\b': 'TINYINT(1)',
            },
            
            # MySQL → PostgreSQL
            (SQLDialect.MYSQL, SQLDialect.POSTGRESQL): {
                r'\bINT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY\b': 'SERIAL PRIMARY KEY',
                r'\bINT\s+AUTO_INCREMENT\b': 'SERIAL',
                r'\bINT\b': 'INTEGER',
                r'\bDECIMAL\(\d+,\d+\)': 'REAL',
                r'\bLONGBLOB\b': 'BYTEA',
                r'\bDATETIME\b': 'TIMESTAMP',
                r'\bDATE\b': 'DATE',
                r'\bTINYINT\(1\)': 'BOOLEAN',
            },
            
            # Универсальные правила для SQLite (обрабатывают DATE из любого источника)
            ('any', SQLDialect.SQLITE): {
                r'(\w+)\s+DATE\s+NOT\s+NULL': r'\1 TEXT NOT NULL',
                r'(\w+)\s+DATE\b': r'\1 TEXT',
            }
        }
        
        # SQL syntax mappings
        self.syntax_mappings = {
            # SQLite → PostgreSQL
            (SQLDialect.SQLITE, SQLDialect.POSTGRESQL): {
                r'\bINSERT\s+OR\s+REPLACE\b': 'INSERT ... ON CONFLICT DO UPDATE',
                r'\bINSERT\s+OR\s+IGNORE\b': 'INSERT ... ON CONFLICT DO NOTHING',
                r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b': r'LIMIT \1 OFFSET \2',
            },
            
            # SQLite → MySQL
            (SQLDialect.SQLITE, SQLDialect.MYSQL): {
                r'\bINSERT\s+OR\s+REPLACE\b': 'REPLACE',
                r'\bINSERT\s+OR\s+IGNORE\b': 'INSERT IGNORE',
                r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b': r'LIMIT \2, \1',
            },
            
            # PostgreSQL → SQLite
            (SQLDialect.POSTGRESQL, SQLDialect.SQLITE): {
                r'\bINSERT\s+.*\s+ON\s+CONFLICT\s+DO\s+UPDATE\b': 'INSERT OR REPLACE',
                r'\bINSERT\s+.*\s+ON\s+CONFLICT\s+DO\s+NOTHING\b': 'INSERT OR IGNORE',
            },
            
            # MySQL → SQLite
            (SQLDialect.MYSQL, SQLDialect.SQLITE): {
                r'\bREPLACE\s+INTO\b': 'INSERT OR REPLACE INTO',
                r'\bINSERT\s+IGNORE\b': 'INSERT OR IGNORE',
                r'\bLIMIT\s+(\d+),\s*(\d+)\b': r'LIMIT \2 OFFSET \1',
            }
        }
        
        self.logger.info("SQL dialect translator initialized")
    
    def translate_sql(self, sql: str, from_dialect, to_dialect: SQLDialect) -> str:
        """Translate SQL from one dialect to another
        
        Args:
            sql: SQL statement to translate
            from_dialect: Source SQL dialect (can be SQLDialect enum or 'any' string)
            to_dialect: Target SQL dialect
            
        Returns:
            Translated SQL statement
        """
        # Handle 'any' source dialect for universal rules
        if from_dialect == 'any':
            try:
                self.logger.debug(f"Applying universal rules for target dialect: {to_dialect.value}")
                
                translated_sql = sql
                
                # Apply universal rules (for any source to specific target)
                universal_key = ('any', to_dialect)
                if universal_key in self.type_mappings:
                    for pattern, replacement in self.type_mappings[universal_key].items():
                        translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
                
                self.logger.debug(f"Universal translation completed: {len(sql)} → {len(translated_sql)} chars")
                return translated_sql
                
            except Exception as e:
                self.logger.error(f"Universal SQL translation failed: {e}")
                return sql  # Return original on error
        
        # Handle normal dialect-to-dialect translation
        if from_dialect == to_dialect:
            return sql
        
        try:
            self.logger.debug(f"Translating SQL from {from_dialect.value} to {to_dialect.value}")
            
            translated_sql = sql
            translation_key = (from_dialect, to_dialect)
            
            # Apply universal rules first (for any source to specific target)
            universal_key = ('any', to_dialect)
            if universal_key in self.type_mappings:
                for pattern, replacement in self.type_mappings[universal_key].items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
            
            # Apply specific dialect mappings
            if translation_key in self.type_mappings:
                for pattern, replacement in self.type_mappings[translation_key].items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
            
            # Apply syntax mappings
            if translation_key in self.syntax_mappings:
                for pattern, replacement in self.syntax_mappings[translation_key].items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
            
            # Handle special cases
            translated_sql = self._handle_special_cases(translated_sql, from_dialect, to_dialect)
            
            self.logger.debug(f"Translation completed: {len(sql)} → {len(translated_sql)} chars")
            return translated_sql
            
        except Exception as e:
            self.logger.error(f"SQL translation failed: {e}")
            return sql  # Return original on error
    
    def _handle_special_cases(self, sql: str, from_dialect: SQLDialect, to_dialect: SQLDialect) -> str:
        """Handle special translation cases
        
        Args:
            sql: SQL to process
            from_dialect: Source dialect
            to_dialect: Target dialect
            
        Returns:
            Processed SQL
        """
        # Handle INSERT OR REPLACE for PostgreSQL
        if from_dialect == SQLDialect.SQLITE and to_dialect == SQLDialect.POSTGRESQL:
            sql = self._convert_insert_or_replace_postgresql(sql)
        
        # Handle LIMIT/OFFSET for MySQL
        if from_dialect == SQLDialect.SQLITE and to_dialect == SQLDialect.MYSQL:
            sql = self._convert_limit_offset_mysql(sql)
        
        # Handle quotes
        sql = self._convert_quotes(sql, from_dialect, to_dialect)
        
        return sql
    
    def _convert_insert_or_replace_postgresql(self, sql: str) -> str:
        """Convert INSERT OR REPLACE to PostgreSQL ON CONFLICT syntax"""
        # This is a simplified conversion - real implementation would need
        # to parse the table schema to determine conflict columns
        pattern = r'INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\)'
        
        def replace_func(match):
            table = match.group(1)
            columns = match.group(2)
            values = match.group(3)
            
            # Assume first column is primary key for conflict resolution
            first_col = columns.split(',')[0].strip()
            
            return f"""INSERT INTO {table} ({columns}) VALUES ({values}) 
                      ON CONFLICT ({first_col}) DO UPDATE SET 
                      {', '.join([f"{col.strip()} = EXCLUDED.{col.strip()}" 
                                 for col in columns.split(',')[1:]])}"""
        
        return re.sub(pattern, replace_func, sql, flags=re.IGNORECASE | re.DOTALL)
    
    def _convert_limit_offset_mysql(self, sql: str) -> str:
        """Convert LIMIT OFFSET to MySQL LIMIT syntax"""
        pattern = r'LIMIT\s+(\d+)\s+OFFSET\s+(\d+)'
        return re.sub(pattern, r'LIMIT \2, \1', sql, flags=re.IGNORECASE)
    
    def _convert_quotes(self, sql: str, from_dialect: SQLDialect, to_dialect: SQLDialect) -> str:
        """Convert identifier quotes between dialects"""
        if to_dialect == SQLDialect.MYSQL:
            # MySQL uses backticks for identifiers
            sql = re.sub(r'"([^"]+)"', r'`\1`', sql)
        elif to_dialect == SQLDialect.POSTGRESQL:
            # PostgreSQL uses double quotes
            sql = re.sub(r'`([^`]+)`', r'"\1"', sql)
        elif to_dialect == SQLDialect.SQLITE:
            # SQLite accepts both, prefer double quotes
            sql = re.sub(r'`([^`]+)`', r'"\1"', sql)
        
        return sql
    
    def translate_create_table(self, create_sql: str, from_dialect: SQLDialect, to_dialect: SQLDialect) -> str:
        """Translate CREATE TABLE statement between dialects
        
        Args:
            create_sql: CREATE TABLE SQL statement
            from_dialect: Source dialect
            to_dialect: Target dialect
            
        Returns:
            Translated CREATE TABLE statement
        """
        try:
            self.logger.debug(f"Translating CREATE TABLE from {from_dialect.value} to {to_dialect.value}")
            
            translated = self.translate_sql(create_sql, from_dialect, to_dialect)
            
            # Handle dialect-specific CREATE TABLE options
            if to_dialect == SQLDialect.MYSQL:
                # Add MySQL engine and charset
                if 'ENGINE=' not in translated.upper():
                    translated = translated.rstrip(';') + ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'
            
            elif to_dialect == SQLDialect.POSTGRESQL:
                # Remove MySQL-specific options
                translated = re.sub(r'\s+ENGINE=\w+', '', translated, flags=re.IGNORECASE)
                translated = re.sub(r'\s+DEFAULT\s+CHARSET=\w+', '', translated, flags=re.IGNORECASE)
            
            return translated
            
        except Exception as e:
            self.logger.error(f"CREATE TABLE translation failed: {e}")
            return create_sql
    
    def get_dialect_from_connection_string(self, connection_string: str) -> SQLDialect:
        """Determine SQL dialect from connection string
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Detected SQL dialect
        """
        connection_string = connection_string.lower()
        
        if connection_string.startswith('sqlite'):
            return SQLDialect.SQLITE
        elif connection_string.startswith('postgresql') or 'postgres' in connection_string:
            return SQLDialect.POSTGRESQL
        elif connection_string.startswith('mysql') or 'pymysql' in connection_string:
            return SQLDialect.MYSQL
        else:
            # Default to SQLite
            self.logger.warning(f"Unknown connection string format: {connection_string}")
            return SQLDialect.SQLITE
    
    def create_dialect_specific_migration(self, base_migration: str, target_dialect: SQLDialect, 
                                        source_dialect: SQLDialect = SQLDialect.SQLITE) -> str:
        """Create dialect-specific migration from base migration
        
        Args:
            base_migration: Base migration content (usually SQLite)
            target_dialect: Target SQL dialect
            source_dialect: Source SQL dialect
            
        Returns:
            Dialect-specific migration content
        """
        try:
            self.logger.info(f"Creating {target_dialect.value} migration from {source_dialect.value}")
            
            # Split migration into upgrade and downgrade parts
            parts = base_migration.split('def downgrade()')
            upgrade_part = parts[0]
            downgrade_part = parts[1] if len(parts) > 1 else ""
            
            # Translate SQL in upgrade part
            upgrade_translated = self._translate_migration_part(upgrade_part, source_dialect, target_dialect)
            
            # Translate SQL in downgrade part
            downgrade_translated = ""
            if downgrade_part:
                downgrade_translated = self._translate_migration_part(downgrade_part, source_dialect, target_dialect)
                downgrade_translated = "def downgrade()" + downgrade_translated
            
            return upgrade_translated + downgrade_translated
            
        except Exception as e:
            self.logger.error(f"Migration translation failed: {e}")
            return base_migration
    
    def _translate_migration_part(self, migration_part: str, source_dialect: SQLDialect, 
                                target_dialect: SQLDialect) -> str:
        """Translate SQL statements in migration part"""
        # Find SQL statements in op.execute() calls
        sql_pattern = r'op\.execute\([\'\"](.*?)[\'\"]'
        
        def translate_match(match):
            sql = match.group(1)
            translated_sql = self.translate_sql(sql, source_dialect, target_dialect)
            return f'op.execute("{translated_sql}"'
        
        return re.sub(sql_pattern, translate_match, migration_part, flags=re.DOTALL)


def main():
    """Test SQL dialect translator"""
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='SQL Dialect Translator')
    parser.add_argument('--sql', required=True, help='SQL statement to translate')
    parser.add_argument('--from', dest='from_dialect', required=True, 
                       choices=['sqlite', 'postgresql', 'mysql'], help='Source dialect')
    parser.add_argument('--to', dest='to_dialect', required=True,
                       choices=['sqlite', 'postgresql', 'mysql'], help='Target dialect')
    
    args = parser.parse_args()
    
    translator = SQLDialectTranslator(logger)
    
    from_dialect = SQLDialect(args.from_dialect)
    to_dialect = SQLDialect(args.to_dialect)
    
    translated = translator.translate_sql(args.sql, from_dialect, to_dialect)
    
    print(f"Original ({from_dialect.value}):")
    print(args.sql)
    print(f"\nTranslated ({to_dialect.value}):")
    print(translated)


if __name__ == '__main__':
    main()