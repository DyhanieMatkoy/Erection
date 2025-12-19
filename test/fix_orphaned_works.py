"""Fix orphaned works by setting invalid parent_id to NULL

This script identifies works with parent_id pointing to non-existent parents
and sets their parent_id to NULL, making them root-level works.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work

def fix_orphaned_works(dry_run=True):
    """
    Fix orphaned works by setting their parent_id to NULL
    
    Args:
        dry_run: If True, only report what would be changed without making changes
    """
    db_path = "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    # Initialize database
    db = DatabaseManager()
    db.initialize(db_path)
    session = db.get_session()
    
    try:
        print("=" * 70)
        print("ORPHANED WORKS FIX SCRIPT")
        print("=" * 70)
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will make changes)'}")
        print()
        
        # Find orphaned works
        print("Finding orphaned works...")
        orphaned = session.query(Work).filter(
            Work.parent_id.isnot(None),
            ~Work.parent_id.in_(session.query(Work.id))
        ).all()
        
        print(f"Found {len(orphaned)} orphaned works")
        
        if len(orphaned) == 0:
            print("No orphaned works found. Database is clean!")
            return True
        
        # Show sample
        print("\nSample of orphaned works (first 10):")
        for work in orphaned[:10]:
            print(f"  {work.id}: {work.name[:60]} (parent_id={work.parent_id})")
        
        if len(orphaned) > 10:
            print(f"  ... and {len(orphaned) - 10} more")
        
        # Get unique invalid parent IDs
        invalid_parents = set(work.parent_id for work in orphaned)
        print(f"\nUnique invalid parent IDs: {invalid_parents}")
        
        if dry_run:
            print("\n" + "=" * 70)
            print("DRY RUN - No changes made")
            print("=" * 70)
            print(f"\nWould update {len(orphaned)} works to set parent_id = NULL")
            print("\nTo apply changes, run: python test/fix_orphaned_works.py --apply")
            return True
        
        # Apply fix
        print("\nApplying fix...")
        for work in orphaned:
            work.parent_id = None
        
        session.commit()
        
        print("=" * 70)
        print("FIX APPLIED SUCCESSFULLY")
        print("=" * 70)
        print(f"Updated {len(orphaned)} works to root-level (parent_id = NULL)")
        
        # Verify
        print("\nVerifying...")
        remaining_orphaned = session.query(Work).filter(
            Work.parent_id.isnot(None),
            ~Work.parent_id.in_(session.query(Work.id))
        ).count()
        
        if remaining_orphaned == 0:
            print("✓ All orphaned works fixed!")
        else:
            print(f"⚠ Warning: {remaining_orphaned} orphaned works still remain")
        
        # Show new root count
        root_count = session.query(Work).filter(Work.parent_id.is_(None)).count()
        print(f"✓ Total root-level works: {root_count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    # Check for --apply flag
    apply = "--apply" in sys.argv or "-a" in sys.argv
    
    if not apply:
        print("Running in DRY RUN mode (no changes will be made)")
        print("To apply changes, run: python test/fix_orphaned_works.py --apply")
        print()
    
    success = fix_orphaned_works(dry_run=not apply)
    sys.exit(0 if success else 1)
