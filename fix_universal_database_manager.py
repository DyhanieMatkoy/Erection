#!/usr/bin/env python3
"""Fix Unified Database Manager to include all columns from Legacy Database Manager"""

import re

def fix_unified_database_manager():
    """Fix the Unified Database Manager file"""
    
    # Read the current file
    with open('unified_database_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the corrected estimates table SQL with all columns
    corrected_estimates_sql = '''            # Estimates - ПРАВИЛЬНАЯ СХЕМА из Legacy Database Manager
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
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                estimate_type TEXT DEFAULT 'General',
                base_document_id INTEGER REFERENCES estimates(id)
            )""",'''
    
    # Pattern to match the estimates table definition
    estimates_pattern = r'(# Estimates - ПРАВИЛЬНАЯ СХЕМА из Legacy Database Manager\s*"""CREATE TABLE IF NOT EXISTS estimates \([^"]*\)""",)'
    
    # Replace all occurrences
    content = re.sub(estimates_pattern, corrected_estimates_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also add missing columns to other tables
    
    # Fix persons table to include is_group and hourly_rate
    persons_pattern = r'(# Persons\s*"""CREATE TABLE IF NOT EXISTS persons \([^"]*marked_for_deletion INTEGER DEFAULT 0[^"]*\)""",)'
    corrected_persons_sql = '''            # Persons
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0,
                hourly_rate REAL DEFAULT 0
            )""",'''
    
    content = re.sub(persons_pattern, corrected_persons_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix organizations table to include is_group
    organizations_pattern = r'(# Organizations\s*"""CREATE TABLE IF NOT EXISTS organizations \([^"]*marked_for_deletion INTEGER DEFAULT 0[^"]*\)""",)'
    corrected_organizations_sql = '''            # Organizations
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                default_responsible_id INTEGER REFERENCES persons(id),
                parent_id INTEGER REFERENCES organizations(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",'''
    
    content = re.sub(organizations_pattern, corrected_organizations_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix counterparties table to include is_group
    counterparties_pattern = r'(# Counterparties\s*"""CREATE TABLE IF NOT EXISTS counterparties \([^"]*marked_for_deletion INTEGER DEFAULT 0[^"]*\)""",)'
    corrected_counterparties_sql = '''            # Counterparties
            """CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                contact_person TEXT,
                phone TEXT,
                parent_id INTEGER REFERENCES counterparties(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",'''
    
    content = re.sub(counterparties_pattern, corrected_counterparties_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix objects table to include is_group
    objects_pattern = r'(# Objects\s*"""CREATE TABLE IF NOT EXISTS objects \([^"]*marked_for_deletion INTEGER DEFAULT 0[^"]*\)""",)'
    corrected_objects_sql = '''            # Objects
            """CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES counterparties(id),
                address TEXT,
                parent_id INTEGER REFERENCES objects(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",'''
    
    content = re.sub(objects_pattern, corrected_objects_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix works table to include is_group
    works_pattern = r'(# Works\s*"""CREATE TABLE IF NOT EXISTS works \([^"]*marked_for_deletion INTEGER DEFAULT 0[^"]*\)""",)'
    corrected_works_sql = '''            # Works
            """CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT,
                unit TEXT,
                price REAL,
                labor_rate REAL,
                parent_id INTEGER REFERENCES works(id),
                marked_for_deletion INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )""",'''
    
    content = re.sub(works_pattern, corrected_works_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix daily_reports table to include missing fields
    daily_reports_pattern = r'(# Daily Reports\s*"""CREATE TABLE IF NOT EXISTS daily_reports \([^"]*modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP[^"]*\)""",)'
    corrected_daily_reports_sql = '''            # Daily Reports
            """CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                number TEXT
            )""",'''
    
    content = re.sub(daily_reports_pattern, corrected_daily_reports_sql, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the corrected content back
    with open('unified_database_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Unified Database Manager fixed!")
    print("Added missing columns:")
    print("  - estimates: is_posted, posted_at, marked_for_deletion, estimate_type, base_document_id")
    print("  - persons: is_group, hourly_rate")
    print("  - organizations: is_group")
    print("  - counterparties: is_group")
    print("  - objects: is_group")
    print("  - works: is_group")
    print("  - daily_reports: is_posted, posted_at, marked_for_deletion, number")

if __name__ == "__main__":
    fix_unified_database_manager()