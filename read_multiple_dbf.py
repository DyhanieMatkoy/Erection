#!/usr/bin/env python3
"""
Script to read and display the structure of multiple DBF files and parse 1C dictionary
"""
import sys
import os
import re

try:
    from dbfread import DBF
except ImportError:
    print("dbfread package is not installed. Installing...")
    os.system("pip install dbfread")
    from dbfread import DBF

def read_dbf_structure(dbf_path, encoding='cp1251'):
    """Read and display the structure of a DBF file"""
    try:
        # Open the DBF file
        table = DBF(dbf_path, load=True, encoding=encoding)
        
        print(f"\n{'='*60}")
        print(f"DBF File: {dbf_path}")
        print('='*60)
        
        # Display file information
        print(f"Number of records: {len(table)}")
        print(f"Number of fields: {len(table.field_names)}")
        print()
        
        # Display field information
        print("Field Structure:")
        print("-" * 60)
        print(f"{'Field Name':<20} {'Type':<5} {'Length':<8} {'Decimal':<8} {'Description':<20}")
        print("-" * 60)
        
        # Access fields differently based on dbfread version
        if hasattr(table, 'fields'):
            # Newer version
            for field in table.fields:
                field_name = field.name
                field_type = field.type
                field_length = field.length
                field_decimal = getattr(field, 'decimal', 0)
                print(f"{field_name:<20} {field_type:<5} {field_length:<8} {field_decimal:<8}")
        else:
            # Older version or different structure
            for i, field_name in enumerate(table.field_names):
                print(f"{field_name:<20} {'N':<5} {'10':<8} {'0':<8}")
        
        print()
        
        # Display first few records as sample
        print("Sample Records (first 3):")
        print("-" * 60)
        
        for i, record in enumerate(table):
            if i >= 3:
                break
            print(f"Record {i+1}:")
            for field_name in table.field_names:
                value = record.get(field_name, "")
                # Truncate long values
                if isinstance(value, str) and len(value) > 30:
                    value = value[:30] + "..."
                print(f"  {field_name}: {value}")
            print()
            
        return table
            
    except Exception as e:
        print(f"Error reading DBF file {dbf_path}: {e}")
        return None

def parse_1c_dictionary(dict_path):
    """Parse 1C v7 dictionary file to find T=SCxx statements"""
    try:
        # Try different encodings
        encodings = ['cp1251', 'cp866', 'utf-8', 'latin1', 'charmap']
        content = None
        
        for encoding in encodings:
            try:
                with open(dict_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read dictionary with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Last resort - read with errors='replace'
            with open(dict_path, 'r', encoding='cp1251', errors='replace') as f:
                content = f.read()
            print("Read dictionary with error replacement")
        
        print(f"\n{'='*60}")
        print(f"1C Dictionary File: {dict_path}")
        print('='*60)
        
        # Find all T=SCxx statements
        pattern = r'T=(SC\d+)'
        matches = re.findall(pattern, content)
        
        if matches:
            print(f"Found {len(set(matches))} unique SC tables:")
            for table in sorted(set(matches)):
                print(f"  - {table}")
        else:
            print("No T=SCxx statements found in dictionary")
        
        # Try to extract more detailed information about each table
        table_details = {}
        for table in set(matches):
            # Look for table definitions
            table_pattern = rf'{table}.*?(?=\n\n|\Z)'
            table_match = re.search(table_pattern, content, re.DOTALL)
            if table_match:
                table_details[table] = table_match.group(0)
        
        return table_details
        
    except Exception as e:
        print(f"Error parsing dictionary file {dict_path}: {e}")
        return {}

def analyze_costs_materials_schema(sc12_table, sc25_table, dict_details):
    """Analyze the schema to understand Costs & Materials structure"""
    print(f"\n{'='*60}")
    print("Analysis of Costs & Materials Schema")
    print('='*60)
    
    # Analyze SC12 (likely costs/expenses)
    if sc12_table:
        print("\nSC12 Table Analysis (Costs/Expenses):")
        print("-" * 40)
        print(f"Records: {len(sc12_table)}")
        print(f"Fields: {', '.join(sc12_table.field_names)}")
        
        # Show sample data
        for i, record in enumerate(sc12_table):
            if i >= 2:
                break
            print(f"\nSample record {i+1}:")
            for field_name in sc12_table.field_names:
                value = record.get(field_name, "")
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  {field_name}: {value}")
    
    # Analyze SC25 (likely materials)
    if sc25_table:
        print("\nSC25 Table Analysis (Materials):")
        print("-" * 40)
        print(f"Records: {len(sc25_table)}")
        print(f"Fields: {', '.join(sc25_table.field_names)}")
        
        # Show sample data
        for i, record in enumerate(sc25_table):
            if i >= 2:
                break
            print(f"\nSample record {i+1}:")
            for field_name in sc25_table.field_names:
                value = record.get(field_name, "")
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  {field_name}: {value}")
    
    # Print dictionary details if available
    if dict_details:
        print("\nDictionary Details:")
        print("-" * 40)
        for table, details in dict_details.items():
            if table in ['SC12', 'SC25']:
                print(f"\n{table}:")
                # Show first few lines of details
                lines = details.split('\n')[:10]
                for line in lines:
                    if line.strip():
                        print(f"  {line}")

if __name__ == "__main__":
    # File paths
    sc12_path = r"E:\Drive_d\dlds\nsm\SC12.DBF"
    sc25_path = r"E:\Drive_d\dlds\nsm\NSM\SC25.DBF"
    dict_path = r"E:\Drive_d\dlds\nsm\NSM\1c v7 dictionary.dd"
    
    # Read SC12.DBF
    print("Reading SC12.DBF...")
    sc12_table = read_dbf_structure(sc12_path)
    
    # Read SC25.DBF
    print("\nReading SC25.DBF...")
    sc25_table = read_dbf_structure(sc25_path)
    
    # Parse dictionary file
    print("\nParsing 1C dictionary...")
    dict_details = parse_1c_dictionary(dict_path)
    
    # Analyze the schema
    analyze_costs_materials_schema(sc12_table, sc25_table, dict_details)