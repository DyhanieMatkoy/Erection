"""Diagnostic script to analyze work records in database"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work

db_path = "construction.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    sys.exit(1)

# Initialize database
db = DatabaseManager()
db.initialize(db_path)
session = db.get_session()

print("=" * 70)
print("WORK DATABASE ANALYSIS")
print("=" * 70)

# Total works
total_works = session.query(Work).count()
print(f"\nTotal works in database: {total_works}")

# Root works (parent_id IS NULL)
root_works = session.query(Work).filter(Work.parent_id.is_(None)).count()
print(f"Root-level works (parent_id IS NULL): {root_works}")

# Works with parent
child_works = session.query(Work).filter(Work.parent_id.isnot(None)).count()
print(f"Child works (parent_id IS NOT NULL): {child_works}")

# Marked for deletion
deleted_works = session.query(Work).filter(Work.marked_for_deletion == True).count()
print(f"Marked for deletion: {deleted_works}")

# Active works
active_works = session.query(Work).filter(Work.marked_for_deletion == False).count()
print(f"Active works (not marked for deletion): {active_works}")

# Groups vs items
groups = session.query(Work).filter(Work.is_group == True).count()
items = session.query(Work).filter(Work.is_group == False).count()
print(f"Groups: {groups}")
print(f"Individual items: {items}")

print("\n" + "=" * 70)
print("ROOT-LEVEL WORKS DETAILS")
print("=" * 70)

root_works_list = session.query(Work).filter(Work.parent_id.is_(None)).all()
for work in root_works_list:
    status = []
    if work.is_group:
        status.append("GROUP")
    if work.marked_for_deletion:
        status.append("DELETED")
    status_str = f" [{', '.join(status)}]" if status else ""
    print(f"{work.id}: {work.name}{status_str}")

print("\n" + "=" * 70)
print("CHECKING FOR HIDDEN WORKS")
print("=" * 70)

# Check if there are works with parent_id that don't have a valid parent
orphaned = session.query(Work).filter(
    Work.parent_id.isnot(None),
    ~Work.parent_id.in_(session.query(Work.id))
).count()
print(f"Orphaned works (parent_id points to non-existent parent): {orphaned}")

# Check for works that might have been imported but not visible
print("\nSample of ALL works (first 20):")
all_works_sample = session.query(Work).limit(20).all()
for work in all_works_sample:
    parent_info = f"parent_id={work.parent_id}" if work.parent_id else "ROOT"
    status = []
    if work.is_group:
        status.append("GROUP")
    if work.marked_for_deletion:
        status.append("DELETED")
    status_str = f" [{', '.join(status)}]" if status else ""
    print(f"{work.id}: {work.name} ({parent_info}){status_str}")

session.close()

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
