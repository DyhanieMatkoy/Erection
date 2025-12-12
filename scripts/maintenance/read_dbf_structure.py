#!/usr/bin/env python3
"""
Script to read and display the structure of a DBF file
"""
import sys
import os

try:
    from dbfread import DBF
except ImportError:
    print("dbfread package is not installed. Installing...")
    os.system("pip install dbfread")
    from dbfread import DBF

def read_dbf_structure(dbf_path):
    """Read and display the structure of a DBF file"""
    try:
        # Try different encodings
        encodings = ['cp1251', 'cp866', 'utf-8', 'latin1']
        table = None
        
        for encoding in encodings:
            try:
                print(f"Trying encoding: {encoding}")
                table = DBF(dbf_path, load=True, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if table is None:
            table = DBF(dbf_path, load=True, ignore_missing_memofile=True)
        
        print(f"DBF File: {dbf_path}")
        print("=" * 50)
        
        # Display file information
        print(f"Number of records: {len(table)}")
        print(f"Number of fields: {len(table.field_names)}")
        print()
        
        # Display field information
        print("Field Structure:")
        print("-" * 50)
        print(f"{'Field Name':<20} {'Type':<5} {'Length':<8} {'Decimal':<8}")
        print("-" * 50)
        
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
        print("Sample Records (first 5):")
        print("-" * 50)
        
        for i, record in enumerate(table):
            if i >= 5:
                break
            print(f"Record {i+1}:")
            for field_name in table.field_names:
                value = record.get(field_name, "")
                print(f"  {field_name}: {value}")
            print()
            
    except Exception as e:
        print(f"Error reading DBF file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    dbf_path = r"E:\Drive_d\dlds\nsm\SC20.DBF"
    
    if not os.path.exists(dbf_path):
        print(f"Error: DBF file not found at {dbf_path}")
        sys.exit(1)
    
    read_dbf_structure(dbf_path)