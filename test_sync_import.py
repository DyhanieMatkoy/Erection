#!/usr/bin/env python3
"""Test sync module import"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing sync module import...")
    from api.endpoints import sync
    print(f"✓ Sync module imported successfully")
    print(f"✓ Router created: {sync.router}")
    print(f"✓ Routes: {[route.path for route in sync.router.routes]}")
    
    print("\nTesting dependencies...")
    from src.data.sync_manager import get_sync_manager
    print("✓ sync_manager imported")
    
    from src.data.packet_manager import PacketManager
    print("✓ packet_manager imported")
    
    from src.data.conflict_resolver import ConflictResolver
    print("✓ conflict_resolver imported")
    
    print("\nTesting FastAPI app creation...")
    from api.main import app
    print("✓ FastAPI app created")
    
    # Check if sync router is included
    sync_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and '/sync/' in route.path:
            sync_routes.append(route.path)
    
    print(f"✓ Sync routes in app: {sync_routes}")
    
    if not sync_routes:
        print("❌ No sync routes found in app!")
        # Check all routes
        all_routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                all_routes.append(route.path)
        print(f"All routes: {all_routes}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()