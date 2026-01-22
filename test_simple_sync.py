#!/usr/bin/env python3
"""
Simplified Multi-Database Synchronization Test

This script tests the core synchronization functionality without document creation.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_multi_database_sync import MultiDatabaseSyncTester

def main():
    """Run simplified synchronization test"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("🚀 Starting Simplified Multi-Database Synchronization Test")
    print("=" * 60)
    
    try:
        # Initialize tester
        config = {
            'server_url': 'http://localhost:8000',
            'server_port': 8000,
            'test_duration': 60,  # 1 minute
            'cleanup_on_exit': True
        }
        
        tester = MultiDatabaseSyncTester(config)
        
        # Test only the core synchronization without document creation
        print("\n📋 Testing SQLite-only scenario (simplified)")
        
        # Setup environment
        success = tester.env_manager.setup_multi_database_environment('sqlite_only')
        if not success:
            print("❌ Failed to setup test environment")
            return False
        
        print("✅ Test environment setup completed")
        
        # Test basic synchronization
        print("\n🔄 Testing basic synchronization...")
        
        sync_results = {}
        for client in tester.env_manager.desktop_clients:
            try:
                result = client.trigger_sync()
                sync_results[client.client_id] = result
                status = "✅" if result.get('status') == 'success' else "❌"
                print(f"{status} {client.client_id}: {result.get('status', 'unknown')}")
            except Exception as e:
                sync_results[client.client_id] = {'status': 'error', 'error': str(e)}
                print(f"❌ {client.client_id}: Error - {e}")
        
        # Check results
        successful_syncs = sum(1 for r in sync_results.values() if r.get('status') == 'success')
        total_clients = len(sync_results)
        
        print(f"\n📊 Synchronization Results: {successful_syncs}/{total_clients} successful")
        
        if successful_syncs == total_clients:
            print("🎉 All synchronization tests PASSED!")
            return True
        else:
            print("⚠️ Some synchronization tests FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            if 'tester' in locals():
                tester.env_manager.cleanup_multi_database_environment()
                print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)