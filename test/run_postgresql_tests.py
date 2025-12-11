"""
Run all repository tests with PostgreSQL backend

This script temporarily configures the system to use PostgreSQL and runs
all repository tests to verify compatibility.
"""

import sys
import os
import shutil
from pathlib import Path
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def backup_env_ini():
    """Backup current env.ini"""
    if Path('env.ini').exists():
        shutil.copy('env.ini', 'env.ini.backup_postgresql')
        print("✓ Backed up env.ini to env.ini.backup_postgresql")
        return True
    return False


def restore_env_ini():
    """Restore original env.ini"""
    if Path('env.ini.backup_postgresql').exists():
        shutil.copy('env.ini.backup_postgresql', 'env.ini')
        os.unlink('env.ini.backup_postgresql')
        print("✓ Restored original env.ini")
        return True
    return False


def configure_postgresql():
    """Configure env.ini to use PostgreSQL"""
    config_content = """[Auth]
login = admin
password = admin

[PrintForms]
format = EXCEL
templates_path = PrnForms

[Database]
type = postgresql
sqlite_path = construction.db
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = q1
postgres_password = q1
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
"""
    
    with open('env.ini', 'w') as f:
        f.write(config_content)
    
    print("✓ Configured env.ini for PostgreSQL")


def run_tests():
    """Run repository tests"""
    print("\n" + "=" * 70)
    print("Running Repository Tests with PostgreSQL Backend")
    print("=" * 70 + "\n")
    
    test_files = [
        'test/test_postgresql_backend.py',
        'test/test_estimate_repository_sqlalchemy.py',
    ]
    
    results = {}
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"⚠ Skipping {test_file} (not found)")
            continue
        
        print(f"\nRunning {test_file}...")
        print("-" * 70)
        
        result = subprocess.run(
            ['pytest', test_file, '-v', '--tb=short'],
            capture_output=False
        )
        
        results[test_file] = result.returncode == 0
        
        if result.returncode == 0:
            print(f"✓ {test_file} PASSED")
        else:
            print(f"✗ {test_file} FAILED")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {test_file}")
    
    print(f"\nTotal: {passed}/{total} test files passed")
    
    return all(results.values())


def main():
    """Main execution"""
    print("=" * 70)
    print("PostgreSQL Repository Test Runner")
    print("=" * 70)
    
    # Backup current config
    backup_env_ini()
    
    try:
        # Configure for PostgreSQL
        configure_postgresql()
        
        # Run tests
        success = run_tests()
        
        return success
        
    finally:
        # Always restore original config
        restore_env_ini()
        print("\n" + "=" * 70)
        print("Configuration restored")
        print("=" * 70)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
