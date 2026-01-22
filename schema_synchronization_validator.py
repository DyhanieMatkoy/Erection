"""Schema Synchronization Validator

This module validates schema consistency across different database types
and provides detailed schema comparison and analysis capabilities.
"""

import os
import sys
import logging
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_configuration_manager import DatabaseConfig, DatabaseType


@dataclass
class TableSchema:
    """Table schema information"""
    name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    primary_key: Optional[List[str]] = None


@dataclass
class SchemaSnapshot:
    """Database schema snapshot"""
    database_type: DatabaseType
    schema_version: Optional[str]
    tables: Dict[str, TableSchema]
    captured_at: datetime


class SchemaSynchronizationValidator:
    """Validates schema consistency across different database types"""
    
    def __init__(self, database_configs: Dict[str, DatabaseConfig], logger: logging.Logger):
        """Initialize schema synchronization validator
        
        Args:
            database_configs: Dictionary of database configurations
            logger: Logger instance
        """
        self.db_configs = database_configs
        self.logger = logger
        
        # Schema snapshots cache
        self.schema_cache: Dict[str, SchemaSnapshot] = {}
        
        # Data type mappings for cross-database comparison
        self.type_mappings = self._initialize_type_mappings()
        
        self.logger.info("Schema synchronization validator initialized")
    
    def _initialize_type_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize data type mappings between database types
        
        Returns:
            Dictionary of type mappings
        """
        return {
            'postgresql_to_sqlite': {
                'integer': 'integer',
                'bigint': 'integer',
                'serial': 'integer',
                'bigserial': 'integer',
                'varchar': 'text',
                'text': 'text',
                'char': 'text',
                'boolean': 'integer',
                'timestamp': 'text',
                'timestamptz': 'text',
                'date': 'text',
                'time': 'text',
                'decimal': 'real',
                'numeric': 'real',
                'real': 'real',
                'double precision': 'real'
            },
            'mysql_to_sqlite': {
                'int': 'integer',
                'integer': 'integer',
                'bigint': 'integer',
                'tinyint': 'integer',
                'smallint': 'integer',
                'mediumint': 'integer',
                'varchar': 'text',
                'text': 'text',
                'char': 'text',
                'longtext': 'text',
                'mediumtext': 'text',
                'tinytext': 'text',
                'boolean': 'integer',
                'bool': 'integer',
                'datetime': 'text',
                'timestamp': 'text',
                'date': 'text',
                'time': 'text',
                'decimal': 'real',
                'numeric': 'real',
                'float': 'real',
                'double': 'real'
            },
            'sqlite_to_postgresql': {
                'integer': 'integer',
                'text': 'varchar',
                'real': 'decimal',
                'blob': 'bytea'
            },
            'sqlite_to_mysql': {
                'integer': 'int',
                'text': 'varchar(255)',
                'real': 'decimal(10,2)',
                'blob': 'longblob'
            },
            'postgresql_to_mysql': {
                'integer': 'int',
                'bigint': 'bigint',
                'serial': 'int auto_increment',
                'bigserial': 'bigint auto_increment',
                'varchar': 'varchar',
                'text': 'text',
                'char': 'char',
                'boolean': 'tinyint(1)',
                'timestamp': 'datetime',
                'timestamptz': 'datetime',
                'date': 'date',
                'time': 'time',
                'decimal': 'decimal',
                'numeric': 'decimal',
                'real': 'float',
                'double precision': 'double'
            },
            'mysql_to_postgresql': {
                'int': 'integer',
                'integer': 'integer',
                'bigint': 'bigint',
                'tinyint': 'smallint',
                'smallint': 'smallint',
                'mediumint': 'integer',
                'varchar': 'varchar',
                'text': 'text',
                'char': 'char',
                'longtext': 'text',
                'mediumtext': 'text',
                'tinytext': 'varchar',
                'boolean': 'boolean',
                'bool': 'boolean',
                'datetime': 'timestamp',
                'timestamp': 'timestamp',
                'date': 'date',
                'time': 'time',
                'decimal': 'decimal',
                'numeric': 'decimal',
                'float': 'real',
                'double': 'double precision'
            }
        }
    
    def capture_schema_snapshot(self, db_config: DatabaseConfig, config_id: str) -> SchemaSnapshot:
        """Capture current schema state for comparison
        
        Args:
            db_config: Database configuration
            config_id: Configuration identifier
            
        Returns:
            SchemaSnapshot instance
        """
        try:
            self.logger.info(f"Capturing schema snapshot for {config_id} ({db_config.db_type.value})")
            
            if db_config.db_type == DatabaseType.SQLITE:
                snapshot = self._capture_sqlite_schema(db_config)
            elif db_config.db_type == DatabaseType.POSTGRESQL:
                snapshot = self._capture_postgresql_schema(db_config)
            elif db_config.db_type == DatabaseType.MYSQL:
                snapshot = self._capture_mysql_schema(db_config)
            else:
                raise ValueError(f"Unsupported database type: {db_config.db_type}")
            
            # Cache the snapshot
            self.schema_cache[config_id] = snapshot
            
            self.logger.info(f"Schema snapshot captured for {config_id}: {len(snapshot.tables)} tables")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture schema snapshot for {config_id}: {e}")
            raise
    
    def _capture_sqlite_schema(self, db_config: DatabaseConfig) -> SchemaSnapshot:
        """Capture SQLite schema snapshot"""
        try:
            database_path = db_config.additional_params['database_path']
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Get schema version from alembic_version table if exists
            schema_version = None
            try:
                cursor.execute("SELECT version_num FROM alembic_version")
                result = cursor.fetchone()
                if result:
                    schema_version = result[0]
            except sqlite3.OperationalError:
                pass  # alembic_version table doesn't exist
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = {}
            for table_name in table_names:
                if table_name == 'alembic_version':
                    continue  # Skip alembic version table
                
                tables[table_name] = self._get_sqlite_table_schema(cursor, table_name)
            
            conn.close()
            
            return SchemaSnapshot(
                database_type=DatabaseType.SQLITE,
                schema_version=schema_version,
                tables=tables,
                captured_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to capture SQLite schema: {e}")
            raise
    
    def _get_sqlite_table_schema(self, cursor, table_name: str) -> TableSchema:
        """Get SQLite table schema information"""
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        columns = []
        primary_key = []
        
        for col_info in columns_info:
            cid, name, data_type, not_null, default_value, pk = col_info
            
            column = {
                'name': name,
                'type': data_type.lower(),
                'nullable': not not_null,
                'default': default_value,
                'primary_key': bool(pk)
            }
            
            if pk:
                primary_key.append(name)
            
            columns.append(column)
        
        # Get index information
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes_info = cursor.fetchall()
        
        indexes = []
        for index_info in indexes_info:
            seq, name, unique, origin, partial = index_info
            
            # Get index columns
            cursor.execute(f"PRAGMA index_info({name})")
            index_columns = [col[2] for col in cursor.fetchall()]
            
            indexes.append({
                'name': name,
                'columns': index_columns,
                'unique': bool(unique)
            })
        
        # Get foreign key information
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_info = cursor.fetchall()
        
        foreign_keys = []
        for fk in fk_info:
            id, seq, table, from_col, to_col, on_update, on_delete, match = fk
            
            foreign_keys.append({
                'column': from_col,
                'referenced_table': table,
                'referenced_column': to_col,
                'on_update': on_update,
                'on_delete': on_delete
            })
        
        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            primary_key=primary_key if primary_key else None
        )
    
    def _capture_postgresql_schema(self, db_config: DatabaseConfig) -> SchemaSnapshot:
        """Capture PostgreSQL schema snapshot"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                password=db_config.password
            )
            cursor = conn.cursor()
            
            # Get schema version
            schema_version = None
            try:
                cursor.execute("SELECT version_num FROM alembic_version")
                result = cursor.fetchone()
                if result:
                    schema_version = result[0]
            except psycopg2.ProgrammingError:
                pass  # alembic_version table doesn't exist
            
            # Get all tables in public schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name != 'alembic_version'
            """)
            
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = {}
            for table_name in table_names:
                tables[table_name] = self._get_postgresql_table_schema(cursor, table_name)
            
            conn.close()
            
            return SchemaSnapshot(
                database_type=DatabaseType.POSTGRESQL,
                schema_version=schema_version,
                tables=tables,
                captured_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to capture PostgreSQL schema: {e}")
            raise
    
    def _get_postgresql_table_schema(self, cursor, table_name: str) -> TableSchema:
        """Get PostgreSQL table schema information"""
        # Get column information
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns_info = cursor.fetchall()
        columns = []
        
        for col_info in columns_info:
            name, data_type, is_nullable, default, char_length, num_precision, num_scale = col_info
            
            # Format data type
            if char_length:
                formatted_type = f"{data_type}({char_length})"
            elif num_precision and num_scale:
                formatted_type = f"{data_type}({num_precision},{num_scale})"
            elif num_precision:
                formatted_type = f"{data_type}({num_precision})"
            else:
                formatted_type = data_type
            
            column = {
                'name': name,
                'type': formatted_type.lower(),
                'nullable': is_nullable == 'YES',
                'default': default,
                'primary_key': False  # Will be updated below
            }
            
            columns.append(column)
        
        # Get primary key information
        cursor.execute("""
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
            AND table_schema = 'public'
            AND constraint_name IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = %s
                AND table_schema = 'public'
                AND constraint_type = 'PRIMARY KEY'
            )
        """, (table_name, table_name))
        
        primary_key_columns = [row[0] for row in cursor.fetchall()]
        
        # Update primary key flags
        for column in columns:
            if column['name'] in primary_key_columns:
                column['primary_key'] = True
        
        # Get index information
        cursor.execute("""
            SELECT 
                i.relname as index_name,
                array_agg(a.attname ORDER BY c.ordinality) as columns,
                ix.indisunique as is_unique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN unnest(ix.indkey) WITH ORDINALITY c(attnum, ordinality) ON true
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = c.attnum
            WHERE t.relname = %s
            AND t.relkind = 'r'
            GROUP BY i.relname, ix.indisunique
        """, (table_name,))
        
        indexes_info = cursor.fetchall()
        indexes = []
        
        for index_info in indexes_info:
            name, columns_array, is_unique = index_info
            
            indexes.append({
                'name': name,
                'columns': columns_array,
                'unique': is_unique
            })
        
        # Get foreign key information
        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc ON kcu.constraint_name = rc.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON rc.unique_constraint_name = ccu.constraint_name
            WHERE kcu.table_name = %s
            AND kcu.table_schema = 'public'
        """, (table_name,))
        
        fk_info = cursor.fetchall()
        foreign_keys = []
        
        for fk in fk_info:
            column, ref_table, ref_column, update_rule, delete_rule = fk
            
            foreign_keys.append({
                'column': column,
                'referenced_table': ref_table,
                'referenced_column': ref_column,
                'on_update': update_rule,
                'on_delete': delete_rule
            })
        
        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            primary_key=primary_key_columns if primary_key_columns else None
        )
    
    def _capture_mysql_schema(self, db_config: DatabaseConfig) -> SchemaSnapshot:
        """Capture MySQL schema snapshot"""
        try:
            import pymysql
            
            conn = pymysql.connect(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                password=db_config.password
            )
            cursor = conn.cursor()
            
            # Get schema version
            schema_version = None
            try:
                cursor.execute("SELECT version_num FROM alembic_version")
                result = cursor.fetchone()
                if result:
                    schema_version = result[0]
            except pymysql.ProgrammingError:
                pass  # alembic_version table doesn't exist
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall() if row[0] != 'alembic_version']
            
            tables = {}
            for table_name in table_names:
                tables[table_name] = self._get_mysql_table_schema(cursor, table_name, db_config.database)
            
            conn.close()
            
            return SchemaSnapshot(
                database_type=DatabaseType.MYSQL,
                schema_version=schema_version,
                tables=tables,
                captured_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to capture MySQL schema: {e}")
            raise
    
    def _get_mysql_table_schema(self, cursor, table_name: str, database_name: str) -> TableSchema:
        """Get MySQL table schema information"""
        # Get column information
        cursor.execute(f"DESCRIBE {table_name}")
        columns_info = cursor.fetchall()
        
        columns = []
        primary_key = []
        
        for col_info in columns_info:
            field, data_type, null, key, default, extra = col_info
            
            column = {
                'name': field,
                'type': data_type.lower(),
                'nullable': null == 'YES',
                'default': default,
                'primary_key': key == 'PRI'
            }
            
            if key == 'PRI':
                primary_key.append(field)
            
            columns.append(column)
        
        # Get index information
        cursor.execute(f"SHOW INDEX FROM {table_name}")
        indexes_info = cursor.fetchall()
        
        # Group indexes by name
        indexes_dict = {}
        for index_info in indexes_info:
            table, non_unique, key_name, seq_in_index, column_name, collation, cardinality, sub_part, packed, null, index_type, comment, index_comment = index_info
            
            if key_name not in indexes_dict:
                indexes_dict[key_name] = {
                    'name': key_name,
                    'columns': [],
                    'unique': non_unique == 0
                }
            
            indexes_dict[key_name]['columns'].append(column_name)
        
        indexes = list(indexes_dict.values())
        
        # Get foreign key information
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME,
                UPDATE_RULE,
                DELETE_RULE
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (database_name, table_name))
        
        fk_info = cursor.fetchall()
        foreign_keys = []
        
        for fk in fk_info:
            column, ref_table, ref_column, update_rule, delete_rule = fk
            
            foreign_keys.append({
                'column': column,
                'referenced_table': ref_table,
                'referenced_column': ref_column,
                'on_update': update_rule,
                'on_delete': delete_rule
            })
        
        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            primary_key=primary_key if primary_key else None
        )
    
    def compare_schemas(self, schema1: SchemaSnapshot, schema2: SchemaSnapshot) -> Dict[str, Any]:
        """Compare two schema snapshots for consistency
        
        Args:
            schema1: First schema snapshot
            schema2: Second schema snapshot
            
        Returns:
            Schema comparison results
        """
        try:
            self.logger.info(f"Comparing schemas: {schema1.database_type.value} vs {schema2.database_type.value}")
            
            comparison = {
                'schemas_match': True,
                'schema1_type': schema1.database_type.value,
                'schema2_type': schema2.database_type.value,
                'schema1_version': schema1.schema_version,
                'schema2_version': schema2.schema_version,
                'version_match': schema1.schema_version == schema2.schema_version,
                'table_differences': [],
                'missing_tables': {
                    'in_schema1': [],
                    'in_schema2': []
                },
                'column_differences': [],
                'index_differences': [],
                'foreign_key_differences': [],
                'comparison_time': datetime.now().isoformat()
            }
            
            # Compare table existence
            tables1 = set(schema1.tables.keys())
            tables2 = set(schema2.tables.keys())
            
            missing_in_schema2 = tables1 - tables2
            missing_in_schema1 = tables2 - tables1
            
            if missing_in_schema1:
                comparison['missing_tables']['in_schema1'] = list(missing_in_schema1)
                comparison['schemas_match'] = False
            
            if missing_in_schema2:
                comparison['missing_tables']['in_schema2'] = list(missing_in_schema2)
                comparison['schemas_match'] = False
            
            # Compare common tables
            common_tables = tables1 & tables2
            
            for table_name in common_tables:
                table1 = schema1.tables[table_name]
                table2 = schema2.tables[table_name]
                
                table_diff = self._compare_table_schemas(table1, table2, schema1.database_type, schema2.database_type)
                
                if not table_diff['tables_match']:
                    comparison['schemas_match'] = False
                    comparison['table_differences'].append(table_diff)
                    
                    # Add specific differences to main comparison
                    if table_diff['column_differences']:
                        comparison['column_differences'].extend(table_diff['column_differences'])
                    
                    if table_diff['index_differences']:
                        comparison['index_differences'].extend(table_diff['index_differences'])
                    
                    if table_diff['foreign_key_differences']:
                        comparison['foreign_key_differences'].extend(table_diff['foreign_key_differences'])
            
            self.logger.info(f"Schema comparison completed: {'Match' if comparison['schemas_match'] else 'Differences found'}")
            return comparison
            
        except Exception as e:
            self.logger.error(f"Schema comparison failed: {e}")
            return {
                'schemas_match': False,
                'error': str(e),
                'comparison_time': datetime.now().isoformat()
            }
    
    def _compare_table_schemas(self, table1: TableSchema, table2: TableSchema, db_type1: DatabaseType, db_type2: DatabaseType) -> Dict[str, Any]:
        """Compare two table schemas"""
        comparison = {
            'table_name': table1.name,
            'tables_match': True,
            'column_differences': [],
            'index_differences': [],
            'foreign_key_differences': []
        }
        
        # Compare columns
        columns1 = {col['name']: col for col in table1.columns}
        columns2 = {col['name']: col for col in table2.columns}
        
        all_columns = set(columns1.keys()) | set(columns2.keys())
        
        for col_name in all_columns:
            if col_name not in columns1:
                comparison['column_differences'].append({
                    'type': 'missing_in_schema1',
                    'table': table1.name,
                    'column': col_name,
                    'schema2_definition': columns2[col_name]
                })
                comparison['tables_match'] = False
                
            elif col_name not in columns2:
                comparison['column_differences'].append({
                    'type': 'missing_in_schema2',
                    'table': table1.name,
                    'column': col_name,
                    'schema1_definition': columns1[col_name]
                })
                comparison['tables_match'] = False
                
            else:
                # Compare column definitions
                col1 = columns1[col_name]
                col2 = columns2[col_name]
                
                # Normalize types for comparison
                normalized_type1 = self._normalize_column_type(col1['type'], db_type1, db_type2)
                normalized_type2 = self._normalize_column_type(col2['type'], db_type2, db_type2)
                
                if normalized_type1 != normalized_type2:
                    comparison['column_differences'].append({
                        'type': 'type_mismatch',
                        'table': table1.name,
                        'column': col_name,
                        'schema1_type': col1['type'],
                        'schema2_type': col2['type'],
                        'normalized_schema1_type': normalized_type1,
                        'normalized_schema2_type': normalized_type2
                    })
                    comparison['tables_match'] = False
                
                # Compare nullable
                if col1['nullable'] != col2['nullable']:
                    comparison['column_differences'].append({
                        'type': 'nullable_mismatch',
                        'table': table1.name,
                        'column': col_name,
                        'schema1_nullable': col1['nullable'],
                        'schema2_nullable': col2['nullable']
                    })
                    comparison['tables_match'] = False
        
        # Compare indexes (simplified - just check if similar indexes exist)
        indexes1_names = {idx['name'] for idx in table1.indexes}
        indexes2_names = {idx['name'] for idx in table2.indexes}
        
        missing_indexes1 = indexes2_names - indexes1_names
        missing_indexes2 = indexes1_names - indexes2_names
        
        if missing_indexes1 or missing_indexes2:
            comparison['index_differences'].append({
                'table': table1.name,
                'missing_in_schema1': list(missing_indexes1),
                'missing_in_schema2': list(missing_indexes2)
            })
            comparison['tables_match'] = False
        
        # Compare foreign keys
        fk1_signatures = {f"{fk['column']}->{fk['referenced_table']}.{fk['referenced_column']}" for fk in table1.foreign_keys}
        fk2_signatures = {f"{fk['column']}->{fk['referenced_table']}.{fk['referenced_column']}" for fk in table2.foreign_keys}
        
        missing_fk1 = fk2_signatures - fk1_signatures
        missing_fk2 = fk1_signatures - fk2_signatures
        
        if missing_fk1 or missing_fk2:
            comparison['foreign_key_differences'].append({
                'table': table1.name,
                'missing_in_schema1': list(missing_fk1),
                'missing_in_schema2': list(missing_fk2)
            })
            comparison['tables_match'] = False
        
        return comparison
    
    def _normalize_column_type(self, column_type: str, source_db_type: DatabaseType, target_db_type: DatabaseType) -> str:
        """Normalize column type for cross-database comparison"""
        if source_db_type == target_db_type:
            return column_type.lower()
        
        # Get mapping key
        mapping_key = f"{source_db_type.value}_to_{target_db_type.value}"
        
        if mapping_key not in self.type_mappings:
            return column_type.lower()  # No mapping available
        
        type_mapping = self.type_mappings[mapping_key]
        
        # Extract base type (remove length/precision specifications)
        base_type = column_type.split('(')[0].lower()
        
        # Look for exact match first
        if base_type in type_mapping:
            return type_mapping[base_type]
        
        # Look for partial matches
        for source_type, target_type in type_mapping.items():
            if base_type.startswith(source_type) or source_type.startswith(base_type):
                return target_type
        
        # No mapping found, return original
        return column_type.lower()
    
    def validate_cross_database_sync(self) -> Dict[str, Any]:
        """Validate schema consistency across different database types
        
        Returns:
            Cross-database validation results
        """
        try:
            self.logger.info("Validating cross-database schema synchronization")
            
            # Capture snapshots for all databases
            snapshots = {}
            for config_id, db_config in self.db_configs.items():
                snapshots[config_id] = self.capture_schema_snapshot(db_config, config_id)
            
            # Perform pairwise comparisons
            comparisons = []
            config_ids = list(snapshots.keys())
            
            for i in range(len(config_ids)):
                for j in range(i + 1, len(config_ids)):
                    config1 = config_ids[i]
                    config2 = config_ids[j]
                    
                    comparison = self.compare_schemas(snapshots[config1], snapshots[config2])
                    comparison['config1_id'] = config1
                    comparison['config2_id'] = config2
                    
                    comparisons.append(comparison)
            
            # Analyze overall consistency
            all_consistent = all(comp['schemas_match'] for comp in comparisons)
            
            results = {
                'overall_consistent': all_consistent,
                'total_databases': len(snapshots),
                'total_comparisons': len(comparisons),
                'consistent_pairs': len([comp for comp in comparisons if comp['schemas_match']]),
                'inconsistent_pairs': len([comp for comp in comparisons if not comp['schemas_match']]),
                'snapshots': {
                    config_id: {
                        'database_type': snapshot.database_type.value,
                        'schema_version': snapshot.schema_version,
                        'table_count': len(snapshot.tables),
                        'captured_at': snapshot.captured_at.isoformat()
                    }
                    for config_id, snapshot in snapshots.items()
                },
                'comparisons': comparisons,
                'validation_time': datetime.now().isoformat()
            }
            
            if all_consistent:
                self.logger.info("Cross-database schema validation passed")
            else:
                self.logger.warning(f"Cross-database schema inconsistencies found: {results['inconsistent_pairs']} pairs")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Cross-database validation failed: {e}")
            return {
                'overall_consistent': False,
                'error': str(e),
                'validation_time': datetime.now().isoformat()
            }
    
    def generate_schema_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate detailed schema comparison report
        
        Args:
            validation_results: Results from validate_cross_database_sync
            
        Returns:
            Formatted schema report as string
        """
        try:
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("SCHEMA SYNCHRONIZATION VALIDATION REPORT")
            report_lines.append("=" * 80)
            report_lines.append("")
            
            # Summary
            report_lines.append("SUMMARY")
            report_lines.append("-" * 40)
            report_lines.append(f"Overall Consistent: {'YES' if validation_results['overall_consistent'] else 'NO'}")
            report_lines.append(f"Total Databases: {validation_results['total_databases']}")
            report_lines.append(f"Total Comparisons: {validation_results['total_comparisons']}")
            report_lines.append(f"Consistent Pairs: {validation_results['consistent_pairs']}")
            report_lines.append(f"Inconsistent Pairs: {validation_results['inconsistent_pairs']}")
            report_lines.append(f"Validation Time: {validation_results['validation_time']}")
            report_lines.append("")
            
            # Database snapshots
            report_lines.append("DATABASE SNAPSHOTS")
            report_lines.append("-" * 40)
            for config_id, snapshot_info in validation_results['snapshots'].items():
                report_lines.append(f"Database: {config_id}")
                report_lines.append(f"  Type: {snapshot_info['database_type']}")
                report_lines.append(f"  Schema Version: {snapshot_info['schema_version'] or 'Unknown'}")
                report_lines.append(f"  Table Count: {snapshot_info['table_count']}")
                report_lines.append(f"  Captured At: {snapshot_info['captured_at']}")
                report_lines.append("")
            
            # Detailed comparisons
            if validation_results['comparisons']:
                report_lines.append("DETAILED COMPARISONS")
                report_lines.append("-" * 40)
                
                for i, comparison in enumerate(validation_results['comparisons'], 1):
                    config1 = comparison['config1_id']
                    config2 = comparison['config2_id']
                    
                    report_lines.append(f"Comparison {i}: {config1} vs {config2}")
                    report_lines.append(f"  Result: {'MATCH' if comparison['schemas_match'] else 'DIFFERENCES FOUND'}")
                    report_lines.append(f"  Schema Types: {comparison['schema1_type']} vs {comparison['schema2_type']}")
                    report_lines.append(f"  Version Match: {'YES' if comparison['version_match'] else 'NO'}")
                    
                    if not comparison['schemas_match']:
                        # Missing tables
                        if comparison['missing_tables']['in_schema1']:
                            report_lines.append(f"  Missing in {config1}: {', '.join(comparison['missing_tables']['in_schema1'])}")
                        
                        if comparison['missing_tables']['in_schema2']:
                            report_lines.append(f"  Missing in {config2}: {', '.join(comparison['missing_tables']['in_schema2'])}")
                        
                        # Column differences
                        if comparison['column_differences']:
                            report_lines.append(f"  Column Differences: {len(comparison['column_differences'])}")
                            for diff in comparison['column_differences'][:5]:  # Show first 5
                                report_lines.append(f"    - {diff['type']}: {diff['table']}.{diff['column']}")
                        
                        # Index differences
                        if comparison['index_differences']:
                            report_lines.append(f"  Index Differences: {len(comparison['index_differences'])}")
                        
                        # Foreign key differences
                        if comparison['foreign_key_differences']:
                            report_lines.append(f"  Foreign Key Differences: {len(comparison['foreign_key_differences'])}")
                    
                    report_lines.append("")
            
            report_lines.append("=" * 80)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            self.logger.error(f"Failed to generate schema report: {e}")
            return f"Error generating schema report: {e}"