"""
Create MSSQL database for testing

This script creates the 'construction' database on MSSQL server.
"""

import sys
import pyodbc
from pathlib import Path


def create_database(host='localhost', port=1433, user='q1', password='q1', database='construction'):
    """Create the test database"""
    print(f"Creating database '{database}' on {host}:{port}...")
    
    # Find SQL Server driver
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    
    if not sql_drivers:
        print("❌ No SQL Server drivers found")
        return False
    
    driver = None
    for d in sql_drivers:
        if '17' in d:
            driver = d
            break
    if not driver:
        driver = sql_drivers[0]
    
    print(f"Using driver: {driver}")
    
    # Connect to master database
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE=master;"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    
    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        conn.autocommit = True  # Required for CREATE DATABASE
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT name FROM sys.databases WHERE name = ?",
            (database,)
        )
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Database '{database}' already exists")
        else:
            # Create database
            print(f"Creating database '{database}'...")
            cursor.execute(f"CREATE DATABASE [{database}]")
            print(f"✓ Database '{database}' created successfully")
        
        cursor.close()
        conn.close()
        
        # Verify we can connect to the new database
        print(f"\nVerifying connection to '{database}'...")
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )
        
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"✓ Connected to database: {db_name}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database setup complete!")
        print(f"\nYou can now run tests with MSSQL backend:")
        print(f"  pytest test/test_mssql_backend.py -v")
        
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
