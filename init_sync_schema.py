#!/usr/bin/env python3
"""Initialize synchronization schema in database"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.database_manager import DatabaseManager
from src.data.models.sync_models import SyncNode, SyncChange, ObjectVersionHistory
from src.data.sqlalchemy_base import Base

def init_sync_schema():
    """Initialize synchronization schema"""
    try:
        print("Initializing synchronization schema...")
        
        # Get database manager
        db_manager = DatabaseManager()
        db_manager.initialize()  # Initialize the database manager
        engine = db_manager.get_engine()
        
        # Create sync tables
        print("Creating sync tables...")
        SyncNode.__table__.create(engine, checkfirst=True)
        print("✓ sync_nodes table created")
        
        SyncChange.__table__.create(engine, checkfirst=True)
        print("✓ sync_changes table created")
        
        ObjectVersionHistory.__table__.create(engine, checkfirst=True)
        print("✓ object_version_history table created")
        
        print("✓ Synchronization schema initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing sync schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_sync_schema()
    sys.exit(0 if success else 1)