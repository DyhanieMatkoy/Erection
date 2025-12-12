"""
Test Task 1: Verify backend database schema and models

This test verifies:
- cost_item_materials table has work_id column
- SQLAlchemy models have proper relationships
- Indexes exist for performance
- UNIQUE constraint exists
- CASCADE DELETE on foreign keys
"""
import sqlite3
from src.data.models.sqlalchemy_models import Work, CostItemMaterial, CostItem, Material, Unit
from sqlalchemy import inspect


def test_cost_item_materials_schema():
    """Verify cost_item_materials table structure"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    # Get table columns
    cursor.execute('PRAGMA table_info(cost_item_materials)')
    columns = {row[1]: row for row in cursor.fetchall()}
    
    # Verify work_id column exists and is NOT NULL
    assert 'work_id' in columns, "work_id column missing"
    assert columns['work_id'][3] == 1, "work_id should be NOT NULL"
    
    # Verify cost_item_id column exists and is NOT NULL
    assert 'cost_item_id' in columns, "cost_item_id column missing"
    assert columns['cost_item_id'][3] == 1, "cost_item_id should be NOT NULL"
    
    # Verify material_id column exists and is nullable
    assert 'material_id' in columns, "material_id column missing"
    assert columns['material_id'][3] == 0, "material_id should be nullable"
    
    # Verify quantity_per_unit column exists
    assert 'quantity_per_unit' in columns, "quantity_per_unit column missing"
    
    print("✓ cost_item_materials table has correct columns")
    
    # Verify indexes
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='cost_item_materials'")
    indexes = [row[0] for row in cursor.fetchall() if row[0]]
    
    assert any('work_id' in idx for idx in indexes), "Missing index on work_id"
    assert any('cost_item_id' in idx for idx in indexes), "Missing index on cost_item_id"
    assert any('material_id' in idx for idx in indexes), "Missing index on material_id"
    
    print("✓ Indexes exist for work_id, cost_item_id, material_id")
    
    # Verify UNIQUE constraint
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cost_item_materials'")
    table_def = cursor.fetchone()[0]
    
    assert 'uq_work_cost_item_material' in table_def, "Missing UNIQUE constraint"
    assert 'UNIQUE (work_id, cost_item_id, material_id)' in table_def, "UNIQUE constraint incorrect"
    
    print("✓ UNIQUE constraint on (work_id, cost_item_id, material_id) exists")
    
    # Verify CASCADE DELETE on foreign keys
    cursor.execute('PRAGMA foreign_key_list(cost_item_materials)')
    foreign_keys = cursor.fetchall()
    
    fk_dict = {}
    for fk in foreign_keys:
        fk_dict[fk[3]] = fk  # key by 'from' column
    
    assert 'work_id' in fk_dict, "Missing FK for work_id"
    assert fk_dict['work_id'][6] == 'CASCADE', "work_id FK should have CASCADE DELETE"
    
    assert 'cost_item_id' in fk_dict, "Missing FK for cost_item_id"
    assert fk_dict['cost_item_id'][6] == 'CASCADE', "cost_item_id FK should have CASCADE DELETE"
    
    assert 'material_id' in fk_dict, "Missing FK for material_id"
    assert fk_dict['material_id'][6] == 'CASCADE', "material_id FK should have CASCADE DELETE"
    
    print("✓ CASCADE DELETE on all foreign keys")
    
    conn.close()


def test_work_model_relationships():
    """Verify Work model has proper relationships"""
    
    # Check that Work model has cost_item_materials relationship
    assert hasattr(Work, 'cost_item_materials'), "Work model missing cost_item_materials relationship"
    
    # Check relationship properties
    work_mapper = inspect(Work)
    relationships = {rel.key: rel for rel in work_mapper.relationships}
    
    assert 'cost_item_materials' in relationships, "cost_item_materials relationship not found"
    
    # Verify cascade delete
    rel = relationships['cost_item_materials']
    assert 'delete-orphan' in rel.cascade, "cost_item_materials should have delete-orphan cascade"
    assert 'delete' in rel.cascade, "cost_item_materials should have delete cascade"
    
    print("✓ Work model has proper cost_item_materials relationship with cascade")
    
    # Check unit_id relationship
    assert hasattr(Work, 'unit_ref'), "Work model missing unit_ref relationship"
    assert 'unit_ref' in relationships, "unit_ref relationship not found"
    
    print("✓ Work model has unit_ref relationship")


def test_cost_item_material_model_relationships():
    """Verify CostItemMaterial model has proper relationships"""
    
    # Check that CostItemMaterial model has relationships
    assert hasattr(CostItemMaterial, 'work'), "CostItemMaterial model missing work relationship"
    assert hasattr(CostItemMaterial, 'cost_item'), "CostItemMaterial model missing cost_item relationship"
    assert hasattr(CostItemMaterial, 'material'), "CostItemMaterial model missing material relationship"
    
    print("✓ CostItemMaterial model has all required relationships")
    
    # Verify table args for unique constraint
    assert hasattr(CostItemMaterial, '__table_args__'), "CostItemMaterial missing __table_args__"
    
    # Check for unique constraint in table args
    table_args = CostItemMaterial.__table_args__
    has_unique = False
    has_indexes = False
    
    for arg in table_args:
        if hasattr(arg, 'name') and arg.name == 'uq_work_cost_item_material':
            has_unique = True
        if hasattr(arg, 'name') and 'idx_cost_item_material' in arg.name:
            has_indexes = True
    
    assert has_unique, "CostItemMaterial missing unique constraint in __table_args__"
    assert has_indexes, "CostItemMaterial missing indexes in __table_args__"
    
    print("✓ CostItemMaterial model has unique constraint and indexes defined")


def test_works_table_unit_id():
    """Verify works table has unit_id column"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    cursor.execute('PRAGMA table_info(works)')
    columns = {row[1]: row for row in cursor.fetchall()}
    
    assert 'unit_id' in columns, "works table missing unit_id column"
    assert columns['unit_id'][3] == 0, "unit_id should be nullable"
    
    print("✓ works table has unit_id column")
    
    conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Task 1: Backend Database Schema and Models Verification")
    print("=" * 60)
    
    try:
        test_cost_item_materials_schema()
        print()
        test_work_model_relationships()
        print()
        test_cost_item_material_model_relationships()
        print()
        test_works_table_unit_id()
        print()
        print("=" * 60)
        print("✓ ALL TESTS PASSED - Task 1 Complete")
        print("=" * 60)
        print()
        print("Summary:")
        print("- ✓ cost_item_materials table has work_id column (NOT NULL)")
        print("- ✓ Indexes exist on work_id, cost_item_id, material_id")
        print("- ✓ UNIQUE constraint on (work_id, cost_item_id, material_id)")
        print("- ✓ CASCADE DELETE on all foreign keys")
        print("- ✓ Work model has proper relationships")
        print("- ✓ CostItemMaterial model has proper relationships")
        print("- ✓ works table has unit_id column")
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("✗ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        raise
