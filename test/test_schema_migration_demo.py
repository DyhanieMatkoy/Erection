"""Demo script for schema management and migration

This script demonstrates:
1. Creating a new database with schema
2. Verifying schema integrity
3. Checking migration status
"""

import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from src.data.schema_manager import SchemaManager
from src.data.models import sqlalchemy_models  # noqa: F401


def demo_schema_management():
    """Demonstrate schema management functionality"""
    
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        print("=" * 60)
        print("Schema Management Demo")
        print("=" * 60)
        
        # Create engine
        connection_string = f"sqlite:///{db_path}"
        engine = create_engine(connection_string, poolclass=NullPool)
        
        # Create schema manager
        schema_manager = SchemaManager(engine)
        
        # Check if database is empty
        print(f"\n1. Database is empty: {schema_manager.is_database_empty()}")
        
        # Initialize schema
        print("\n2. Initializing schema...")
        schema_manager.initialize_schema(use_alembic=True)
        print("   Schema initialized successfully!")
        
        # Verify schema
        print("\n3. Verifying schema...")
        verification = schema_manager.verify_schema()
        print(f"   Valid: {verification['valid']}")
        print(f"   Current revision: {verification['current_revision']}")
        print(f"   Head revision: {verification['head_revision']}")
        print(f"   Needs migration: {verification['needs_migration']}")
        print(f"   Missing tables: {verification['missing_tables']}")
        print(f"   Extra tables: {verification['extra_tables']}")
        
        # Get migration history
        print("\n4. Migration history:")
        history = schema_manager.get_migration_history()
        for rev in history:
            current_marker = " (current)" if rev['is_current'] else ""
            print(f"   - {rev['revision']}: {rev['message']}{current_marker}")
        
        # Test idempotence
        print("\n5. Testing idempotence (running initialization again)...")
        schema_manager.initialize_schema(use_alembic=True)
        print("   No errors - idempotence confirmed!")
        
        # Final verification
        print("\n6. Final verification...")
        final_verification = schema_manager.verify_schema()
        print(f"   Valid: {final_verification['valid']}")
        print(f"   Schema is up to date: {not final_verification['needs_migration']}")
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
        engine.dispose()
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    demo_schema_management()
