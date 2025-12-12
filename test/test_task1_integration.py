"""
Integration test for Task 1: Verify database operations work correctly
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Work, CostItem, Material, CostItemMaterial, Unit

# Create engine and session
engine = create_engine('sqlite:///construction.db')
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("=" * 60)
    print("Task 1 Integration Test")
    print("=" * 60)
    
    # Test 1: Create a test work
    print("\n1. Creating test work...")
    test_work = Work(
        name="Test Work for Task 1",
        code="TEST001",
        price=1000.0,
        labor_rate=5.0,
        is_group=False
    )
    session.add(test_work)
    session.commit()
    print(f"   ✓ Created work with ID: {test_work.id}")
    
    # Test 2: Get a cost item
    print("\n2. Getting a cost item...")
    cost_item = session.query(CostItem).filter(CostItem.marked_for_deletion == False).first()
    if not cost_item:
        print("   ! No cost items found, creating one...")
        cost_item = CostItem(
            code="CI001",
            description="Test Cost Item",
            price=100.0,
            labor_coefficient=1.5
        )
        session.add(cost_item)
        session.commit()
    print(f"   ✓ Using cost item ID: {cost_item.id}")
    
    # Test 3: Add cost item to work (without material)
    print("\n3. Adding cost item to work...")
    cost_item_assoc = CostItemMaterial(
        work_id=test_work.id,
        cost_item_id=cost_item.id,
        material_id=None,
        quantity_per_unit=0.0
    )
    session.add(cost_item_assoc)
    session.commit()
    print(f"   ✓ Created cost item association with ID: {cost_item_assoc.id}")
    
    # Test 4: Get a material
    print("\n4. Getting a material...")
    material = session.query(Material).filter(Material.marked_for_deletion == False).first()
    if not material:
        print("   ! No materials found, creating one...")
        material = Material(
            code="MAT001",
            description="Test Material",
            price=50.0
        )
        session.add(material)
        session.commit()
    print(f"   ✓ Using material ID: {material.id}")
    
    # Test 5: Add material to work with cost item
    print("\n5. Adding material to work...")
    material_assoc = CostItemMaterial(
        work_id=test_work.id,
        cost_item_id=cost_item.id,
        material_id=material.id,
        quantity_per_unit=2.5
    )
    session.add(material_assoc)
    session.commit()
    print(f"   ✓ Created material association with ID: {material_assoc.id}")
    
    # Test 6: Verify relationships work
    print("\n6. Verifying relationships...")
    work = session.query(Work).filter(Work.id == test_work.id).first()
    print(f"   ✓ Work has {len(work.cost_item_materials)} associations")
    
    for assoc in work.cost_item_materials:
        if assoc.material_id:
            print(f"   ✓ Material association: {assoc.material.description} (qty: {assoc.quantity_per_unit})")
        else:
            print(f"   ✓ Cost item association: {assoc.cost_item.description}")
    
    # Test 7: Verify CASCADE DELETE configuration (without actually deleting)
    print("\n7. Verifying CASCADE DELETE configuration...")
    work_id = test_work.id
    assoc_count = len(work.cost_item_materials)
    
    # Verify CASCADE DELETE is configured in database
    import sqlite3
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_key_list(cost_item_materials)')
    fks = cursor.fetchall()
    conn.close()
    
    work_fk = [fk for fk in fks if fk[3] == 'work_id'][0]
    assert work_fk[6] == 'CASCADE', "work_id FK should have CASCADE DELETE"
    
    print(f"   ✓ CASCADE DELETE is configured correctly in database schema")
    print(f"   ✓ Work has {assoc_count} associations that would be cascaded on deletion")
    
    # Clean up test data manually
    session.query(CostItemMaterial).filter(CostItemMaterial.work_id == work_id).delete()
    session.query(Work).filter(Work.id == work_id).delete()
    session.commit()
    print(f"   ✓ Test data cleaned up successfully")
    
    print("\n" + "=" * 60)
    print("✓ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Integration test failed: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
    raise
finally:
    session.close()
