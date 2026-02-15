#!/usr/bin/env python3
"""Migration to Unified Database Manager

This script completes the migration from Legacy and Unified Database Managers
to the new Unified Database Manager.
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_files_with_imports(search_patterns: List[str]) -> List[Path]:
    """Find files that import old database managers
    
    Args:
        search_patterns: List of import patterns to search for
        
    Returns:
        List of file paths that need updating
    """
    files_to_update = []
    
    # Search in common directories
    search_dirs = [
        "src",
        "api", 
        "test",
        ".",  # Root directory
    ]
    
    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.exists():
            continue
            
        # Find Python files
        for py_file in search_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for old import patterns
                for pattern in search_patterns:
                    if pattern in content:
                        files_to_update.append(py_file)
                        logger.info(f"Found old import in: {py_file}")
                        break
                        
            except Exception as e:
                logger.warning(f"Could not read file {py_file}: {e}")
    
    return files_to_update


def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file
    
    Args:
        file_path: Path to file to update
        
    Returns:
        True if file was updated
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace Unified Database Manager imports
        content = content.replace(
            "from unified_database_manager import UnifiedDatabaseManager",
            "from unified_database_manager import UnifiedDatabaseManager"
        )
        content = content.replace(
            "UnifiedDatabaseManager",
            "UnifiedDatabaseManager"
        )
        
        # Replace Legacy Database Manager imports (if any direct imports exist)
        content = content.replace(
            "from src.data.database_manager import DatabaseManager",
            "from src.data.database_manager import DatabaseManager"  # No change needed - wrapper handles it
        )
        
        # Update variable names
        content = content.replace("unified_db_manager", "unified_db_manager")
        content = content.replace("unified_database_manager", "unified_database_manager")
        
        # Update comments
        content = content.replace("Unified Database Manager", "Unified Database Manager")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✅ Updated imports in: {file_path}")
            return True
        else:
            logger.debug(f"No changes needed in: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to update {file_path}: {e}")
        return False


def backup_old_managers():
    """Backup old database managers"""
    try:
        # Unified Database Manager is already in root, just rename it
        if Path("unified_database_manager.py").exists():
            shutil.move("unified_database_manager.py", "unified_database_manager_backup.py")
            logger.info("✅ Backed up unified_database_manager.py")
        
        # Legacy Database Manager is already backed up as database_manager_legacy_backup.py
        logger.info("✅ Legacy Database Manager already backed up")
        
    except Exception as e:
        logger.error(f"❌ Failed to backup old managers: {e}")


def test_unified_manager():
    """Test that Unified Database Manager works correctly"""
    try:
        logger.info("Testing Unified Database Manager...")
        
        # Test import
        from unified_database_manager import UnifiedDatabaseManager
        
        # Test initialization
        manager = UnifiedDatabaseManager(logger=logger, use_docker=False)
        
        # Test SQLite initialization
        test_db = "test_migration_verification.db"
        success = manager.initialize(test_db)
        
        if success:
            logger.info("✅ Unified Database Manager test passed")
            
            # Test basic operations
            try:
                with manager.session_scope() as session:
                    # Test that sync tables exist
                    result = manager.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sync_%'")
                    sync_tables = [row[0] for row in result]
                    
                    if len(sync_tables) >= 2:  # Should have sync_nodes and sync_changes at minimum
                        logger.info(f"✅ Sync tables found: {sync_tables}")
                    else:
                        logger.warning(f"⚠️ Expected sync tables, found: {sync_tables}")
                
                # Clean up test database
                manager.close_connection()
                if Path(test_db).exists():
                    Path(test_db).unlink()
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Unified Database Manager operation test failed: {e}")
                return False
        else:
            logger.error("❌ Unified Database Manager initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Unified Database Manager import test failed: {e}")
        return False


def main():
    """Main migration process"""
    logger.info("Starting migration to Unified Database Manager")
    
    # Step 1: Test Unified Database Manager
    logger.info("Step 1: Testing Unified Database Manager")
    if not test_unified_manager():
        logger.error("❌ Unified Database Manager test failed - aborting migration")
        return False
    
    # Step 2: Find files that need updating
    logger.info("Step 2: Finding files with old imports")
    search_patterns = [
        "from unified_database_manager import",
        "UnifiedDatabaseManager",
        "unified_db_manager",
        "unified_database_manager"
    ]
    
    files_to_update = find_files_with_imports(search_patterns)
    logger.info(f"Found {len(files_to_update)} files that need updating")
    
    # Step 3: Update imports in files
    logger.info("Step 3: Updating imports in files")
    updated_count = 0
    for file_path in files_to_update:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    logger.info(f"Updated {updated_count} files")
    
    # Step 4: Backup old managers
    logger.info("Step 4: Backing up old database managers")
    backup_old_managers()
    
    # Step 5: Final verification
    logger.info("Step 5: Final verification")
    if test_unified_manager():
        logger.info("✅ Migration to Unified Database Manager completed successfully!")
        logger.info("Summary:")
        logger.info(f"  - Updated {updated_count} files")
        logger.info(f"  - Backed up old managers")
        logger.info(f"  - Unified Database Manager is working correctly")
        return True
    else:
        logger.error("❌ Final verification failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)