"""
Setup script for PostgreSQL testing

This script helps verify and configure PostgreSQL for testing:
1. Check if psycopg2 is installed
2. Test connection to PostgreSQL server
3. Create test database if needed
4. Verify user permissions

Usage:
    python test/setup_postgresql_test.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_psycopg2():
    """Check if psycopg2 is installed"""
    print("Checking psycopg2 installation...")
    
    try:
        import psycopg2
        print(f"✓ psycopg2 is installed (version {psycopg2.__version__})")
        return True
    except ImportError:
        print("❌ ERROR: psycopg2 is not installed!")
        print("\nPlease install psycopg2:")
        print("  pip install psycopg2-binary")
        return False


def test_connection(host='localhost', port=5432, user='q1', password='q1', database='postgres'):
    """Test connection to PostgreSQL server"""
    print(f"\nTesting connection to PostgreSQL server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Database: {database}")
    
    try:
        import psycopg2
        
        print("\nAttempting to connect...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        print("✓ Connection successful!")
        print(f"\nPostgreSQL version:")
        print(f"  {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify PostgreSQL Server is running")
        print("  2. Check that PostgreSQL is listening on the specified port")
        print("  3. Verify firewall allows connections on port 5432")
        print("  4. Confirm user credentials are correct")
        print("  5. Check pg_hba.conf allows connections from localhost")
        print("  6. Ensure the user has login privileges")
        return False


def check_database(host='localhost', port=5432, user='q1', password='q1', database='construction'):
    """Check if test database exists and user has permissions"""
    print(f"\nChecking database '{database}'...")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to postgres database first
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres',
            connect_timeout=10
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database,)
        )
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Database '{database}' exists")
        else:
            print(f"⚠ Database '{database}' does not exist")
            print(f"\nAttempting to create database '{database}'...")
            
            try:
                cursor.execute(f'CREATE DATABASE "{database}"')
                print(f"✓ Database '{database}' created successfully")
            except Exception as e:
                print(f"❌ Failed to create database: {e}")
                print("  You may need to create it manually with appropriate permissions")
                print(f"\n  SQL command: CREATE DATABASE {database};")
                cursor.close()
                conn.close()
                return False
        
        cursor.close()
        conn.close()
        
        # Now test connection to the specific database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Test permissions
        print(f"\nTesting permissions on '{database}'...")
        
        # Try to create a test table
        try:
            cursor.execute("DROP TABLE IF EXISTS test_permissions")
            cursor.execute("""
                CREATE TABLE test_permissions (
                    id SERIAL PRIMARY KEY,
                    test_value VARCHAR(50)
                )
            """)
            cursor.execute("INSERT INTO test_permissions (test_value) VALUES ('test')")
            cursor.execute("SELECT * FROM test_permissions")
            cursor.fetchall()
            cursor.execute("DROP TABLE test_permissions")
            conn.commit()
            
            print("✓ User has CREATE, INSERT, SELECT, and DROP permissions")
            
        except Exception as e:
            print(f"❌ Permission test failed: {e}")
            print("  User may not have sufficient permissions")
            conn.rollback()
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False


def main():
    """Run all setup checks"""
    print("=" * 70)
    print("PostgreSQL Test Environment Setup")
    print("=" * 70)
    
    # Check psycopg2
    if not check_psycopg2():
        print("\n" + "=" * 70)
        print("Setup incomplete: psycopg2 not installed")
        print("=" * 70)
        return False
    
    # Test connection
    if not test_connection():
        print("\n" + "=" * 70)
        print("Setup incomplete: Cannot connect to PostgreSQL server")
        print("=" * 70)
        return False
    
    # Check database
    if not check_database():
        print("\n" + "=" * 70)
        print("Setup incomplete: Database issues")
        print("=" * 70)
        return False
    
    print("\n" + "=" * 70)
    print("✓ PostgreSQL test environment is ready!")
    print("=" * 70)
    print("\nYou can now run the PostgreSQL tests:")
    print("  pytest test/test_postgresql_backend.py -v")
    print("\nOr run all repository tests with PostgreSQL:")
    print("  pytest test/test_estimate_repository_sqlalchemy.py -v")
    print("  pytest test/test_reference_repository_sqlalchemy.py -v")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
