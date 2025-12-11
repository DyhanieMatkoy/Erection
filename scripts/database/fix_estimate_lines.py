#!/usr/bin/env python3
"""
Script to properly recreate the estimate_lines table without material-related columns.
"""

import sqlite3
import os
from pathlib import Path

def fix_estimate_lines():
    """Properly recreate the estimate_lines table without material-related columns"""
    # Path to the database
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all data from the current table
        cursor.execute("SELECT * FROM estimate_lines")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(estimate_lines)")
        column_info = cursor.fetchall()
        all_columns = [col[1] for col in column_info]
        
        print(f"Current columns: {all_columns}")
        
        # Define the columns we want to keep (excluding material-related columns)
        material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
        keep_columns = [col for col in all_columns if col not in material_columns]
        
        print(f"Columns to keep: {keep_columns}")
        
        # Drop the current table
        cursor.execute("DROP TABLE estimate_lines")
        
        # Create the new table with the correct structure
        create_sql = """
        CREATE TABLE estimate_lines (
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
        )
        """
        
        cursor.execute(create_sql)
        
        # Insert the data back into the new table
        if rows:
            # Build the INSERT statement with only the columns we want to keep
            placeholders = ", ".join(["?"] * len(keep_columns))
            insert_sql = f"INSERT INTO estimate_lines ({', '.join(keep_columns)}) VALUES ({placeholders})"
            
            # Filter the rows to exclude material-related columns
            clean_rows = []
            for row in rows:
                clean_row = [value for i, value in enumerate(row) if all_columns[i] not in material_columns]
                clean_rows.append(clean_row)
            
            cursor.executemany(insert_sql, clean_rows)
            print(f"Inserted {len(clean_rows)} rows back into estimate_lines")
        
        conn.commit()
        print("Successfully recreated estimate_lines table without material-related columns")
        
        # Verify the new table structure
        cursor.execute("PRAGMA table_info(estimate_lines)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"New table columns: {new_columns}")
        
        conn.close()
        return True
                
    except Exception as e:
        print(f"Error fixing estimate_lines: {e}")
        return False

if __name__ == "__main__":
    success = fix_estimate_lines()
    exit(0 if success else 1)