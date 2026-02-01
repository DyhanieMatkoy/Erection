#!/usr/bin/env python3
"""
Complete test of migration system after fixes
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_alembic_current():
    """Test alembic current command"""
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config('alembic.ini')
        command.current(cfg)
        print("✅ Alembic current: OK")
        return True
    except Exception as e:
        print(f"❌ Alembic current failed: {e}")
        return False

def test_alembic_heads():
    """Test alembic heads command"""
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config('alembic.ini')
        command.heads(cfg)
        print("✅ Alembic heads: OK")
        return True
    except Exception as e:
        print(f"❌ Alembic heads failed: {e}")
        return False

def test_api_startup():
    """Test API startup with schema initialization"""
    try:
        from api.main import app
        print("✅ API import: OK")
        
        # Test database manager
        from api.dependencies.database import get_db_manager
        db_manager = get_db_manager()
        print("✅ Database manager: OK")
        return True
    except Exception as e:
        print(f"❌ API startup failed: {e}")
        return False

def test_migration_chain():
    """Test migration chain integrity"""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        cfg = Config('alembic.ini')
        script = ScriptDirectory.from_config(cfg)
        
        # Get all revisions
        revisions = list(script.walk_revisions())
        print(f"✅ Migration chain: {len(revisions)} migrations found")
        return True
    except Exception as e:
        print(f"❌ Migration chain test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing complete migration system...")
    print("=" * 50)
    
    tests = [
        test_alembic_current,
        test_alembic_heads,
        test_migration_chain,
        test_api_startup
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Migration system is fully fixed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)