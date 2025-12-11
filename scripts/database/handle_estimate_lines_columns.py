#!/usr/bin/env python3
"""
Script to handle material-related columns in estimate_lines table that may interfere with migration.
This script will recreate the estimate_lines table without the material_id column.
"""

import sqlite3
import os
from pathlib import Path

def handle_estimate_lines_columns():
    """Handle material-related columns in estimate_lines table"""
    # Path to the database
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if material_id column exists in estimate_lines
        cursor.execute("PRAGMA table_info(estimate_lines)")
        columns = [row[1] for row in cursor.fetchall()]
        
        material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
        columns_found = [col for col in material_columns if col in columns]
        
        if not columns_found:
            print("No material-related columns found in estimate_lines table")
            conn.close()
            return True
        
        print(f"Found material-related columns in estimate_lines: {columns_found}")
        
        # Get the current table structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='estimate_lines'")
        create_sql = cursor.fetchone()[0]
        print(f"Current CREATE SQL: {create_sql}")
        
        # Create a new table without material-related columns
        # First, get all data from the current table
        cursor.execute("SELECT * FROM estimate_lines")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(estimate_lines)")
        column_info = cursor.fetchall()
        all_columns = [col[1] for col in column_info]
        
        # Filter out material-related columns
        clean_columns = [col for col in all_columns if col not in material_columns]
        
        # Drop the current table
        cursor.execute("DROP TABLE estimate_lines")
        
        # Create the new table without material-related columns
        # We need to reconstruct the CREATE statement without the material columns
        new_create_sql = create_sql
        for col in material_columns:
            # Remove column definitions
            new_create_sql = new_create_sql.replace(f",\n        {col}", "")
            # Handle case where it's the last column before closing parenthesis
            new_create_sql = new_create_sql.replace(f",\n        {col}\n    ", "\n    ")
        
        # Execute the new CREATE statement
        cursor.execute(new_create_sql)
        
        # Insert the data back into the new table
        if rows:
            # Build the INSERT statement with only the clean columns
            placeholders = ", ".join(["?"] * len(clean_columns))
            insert_sql = f"INSERT INTO estimate_lines ({', '.join(clean_columns)}) VALUES ({placeholders})"
            
            # Filter the rows to exclude material-related columns
            clean_rows = []
            for row in rows:
                clean_row = [value for i, value in enumerate(row) if all_columns[i] not in material_columns]
                clean_rows.append(clean_row)
            
            cursor.executemany(insert_sql, clean_rows)
        
        conn.commit()
        print("Successfully recreated estimate_lines table without material-related columns")
        
        conn.close()
        return True
                
    except Exception as e:
        print(f"Error handling estimate_lines columns: {e}")
        return False

if __name__ == "__main__":
    success = handle_estimate_lines_columns()
    exit(0 if success else 1)