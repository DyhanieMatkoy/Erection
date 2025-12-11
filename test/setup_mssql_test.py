"""
Setup script for MSSQL testing

This script helps verify and configure MSSQL for testing:
1. Check if ODBC Driver 17 for SQL Server is installed
2. Test connection to MSSQL server
3. Create test database if needed
4. Verify user permissions

Usage:
    python test/setup_mssql_test.py
"""

import sys
import pyodbc
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_odbc_drivers():
    """Check available ODBC drivers"""
    print("Checking available ODBC drivers...")
    drivers = pyodbc.drivers()
    
    print(f"\nFound {len(drivers)} ODBC drivers:")
    for driver in drivers:
        print(f"  - {driver}")
    
    # Check for SQL Server drivers
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    
    if not sql_drivers:
        print("\n❌ ERROR: No SQL Server ODBC drivers found!")
        print("\nPlease install ODBC Driver 17 for SQL Server:")
        print("  Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
        return False
    
    print(f"\n✓ Found {len(sql_drivers)} SQL Server driver(s)")
    
    # Check for Driver 17 specifically
    driver_17 = [d for d in sql_drivers if '17' in d]
    if driver_17:
        print(f"✓ ODBC Driver 17 for SQL Server is installed: {driver_17[0]}")
        return True
    else:
        print("⚠ Warning: ODBC Driver 17 not found, but other SQL Server drivers are available")
        print(f"  Available: {sql_drivers}")
        return True


def test_connection(host='localhost', port=1433, user='q1', password='q1'):
    """Test connection to MSSQL server"""
    print(f"\nTesting connection to MSSQL server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    
    # Try to find the best driver
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    
    if not sql_drivers:
        print("❌ No SQL Server drivers available")
        return False
    
    # Prefer Driver 17, but fall back to others
    driver = None
    for d in sql_drivers:
        if '17' in d:
            driver = d
            break
    if not driver:
        driver = sql_drivers[0]
    
    print(f"  Using driver: {driver}")
    
    # Build connection string
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    
    try:
        print("\nAttempting to connect...")
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        print("✓ Connection successful!")
        print(f"\nSQL Server version:")
        print(f"  {version.split(chr(10))[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify MSSQL Server is running")
        print("  2. Check that TCP/IP is enabled in SQL Server Configuration Manager")
        print("  3. Verify firewall allows connections on port 1433")
        print("  4. Confirm user credentials are correct")
        print("  5. Check that SQL Server authentication is enabled (not just Windows auth)")
        return False


def check_database(host='localhost', port=1433, user='q1', password='q1', database='construction'):
    """Check if test database exists and user has permissions"""
    print(f"\nChecking database '{database}'...")
    
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    driver = None
    for d in sql_drivers:
        if '17' in d:
            driver = d
            break
    if not driver:
        driver = sql_drivers[0]
    
    # Connect to master database first
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
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT name FROM sys.databases WHERE name = ?",
            (database,)
        )
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Database '{database}' exists")
        else:
            print(f"⚠ Database '{database}' does not exist")
            print(f"\nTo create the database, run this SQL command:")
            print(f"  CREATE DATABASE {database};")
            
            # Try to create it
            try:
                print(f"\nAttempting to create database '{database}'...")
                cursor.execute(f"CREATE DATABASE {database}")
                conn.commit()
                print(f"✓ Database '{database}' created successfully")
            except pyodbc.Error as e:
                print(f"❌ Failed to create database: {e}")
                print("  You may need to create it manually with appropriate permissions")
                cursor.close()
                conn.close()
                return False
        
        cursor.close()
        conn.close()
        
        # Now test connection to the specific database
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
        
        # Test permissions
        print(f"\nTesting permissions on '{database}'...")
        
        # Try to create a test table
        try:
            cursor.execute("""
                IF OBJECT_ID('test_permissions', 'U') IS NOT NULL
                    DROP TABLE test_permissions
            """)
            cursor.execute("""
                CREATE TABLE test_permissions (
                    id INT PRIMARY KEY,
                    test_value VARCHAR(50)
                )
            """)
            cursor.execute("INSERT INTO test_permissions VALUES (1, 'test')")
            cursor.execute("SELECT * FROM test_permissions")
            cursor.fetchall()
            cursor.execute("DROP TABLE test_permissions")
            conn.commit()
            
            print("✓ User has CREATE, INSERT, SELECT, and DROP permissions")
            
        except pyodbc.Error as e:
            print(f"❌ Permission test failed: {e}")
            print("  User may not have sufficient permissions")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Database check failed: {e}")
        return False


def main():
    """Run all setup checks"""
    print("=" * 70)
    print("MSSQL Test Environment Setup")
    print("=" * 70)
    
    # Check ODBC drivers
    if not check_odbc_drivers():
        print("\n" + "=" * 70)
        print("Setup incomplete: ODBC drivers not found")
        print("=" * 70)
        return False
    
    # Test connection
    if not test_connection():
        print("\n" + "=" * 70)
        print("Setup incomplete: Cannot connect to MSSQL server")
        print("=" * 70)
        return False
    
    # Check database
    if not check_database():
        print("\n" + "=" * 70)
        print("Setup incomplete: Database issues")
        print("=" * 70)
        return False
    
    print("\n" + "=" * 70)
    print("✓ MSSQL test environment is ready!")
    print("=" * 70)
    print("\nYou can now run the MSSQL tests:")
    print("  pytest test/test_mssql_backend.py -v")
    print("\nOr run all repository tests with MSSQL:")
    print("  pytest test/test_estimate_repository_sqlalchemy.py -v")
    print("  pytest test/test_reference_repository_sqlalchemy.py -v")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
