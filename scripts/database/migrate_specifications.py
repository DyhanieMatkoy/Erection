import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from data.models.sqlalchemy_models import Work, CostItemMaterial, WorkSpecification, CostItem, Material, Unit
from data.database_manager import DatabaseManager

def migrate_specifications():
    print("Starting migration of specifications...")
    
    # Initialize database connection
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        print("Failed to initialize database connection")
        return

    # Create session
    Session = sessionmaker(bind=db_manager.get_engine())
    session = Session()

    try:
        # Get valid work IDs and Unit IDs to avoid FK errors
        valid_work_ids = set(session.execute(select(Work.id)).scalars().all())
        valid_unit_ids = set(session.execute(select(Unit.id)).scalars().all())
        print(f"Loaded {len(valid_work_ids)} works and {len(valid_unit_ids)} units")

        # Get all cost_item_materials
        query = select(CostItemMaterial)
        cost_item_materials = session.execute(query).scalars().all()
        
        print(f"Found {len(cost_item_materials)} existing cost item materials")
        
        migrated_count = 0
        skipped_count = 0
        
        for cim in cost_item_materials:
            if cim.work_id not in valid_work_ids:
                print(f"Skipping CIM {cim.id}: Work ID {cim.work_id} not found")
                skipped_count += 1
                continue

            component_type = 'Labor'
            component_name = ''
            unit_id = None
            consumption_rate = cim.quantity_per_unit
            unit_price = 0
            
            if cim.material_id:
                component_type = 'Material'
                material = session.get(Material, cim.material_id)
                if material:
                    component_name = material.description or material.code
                    unit_id = material.unit_id
                    unit_price = material.price
            else:
                cost_item = session.get(CostItem, cim.cost_item_id)
                if cost_item:
                    component_name = cost_item.description or cost_item.code
                    unit_id = cost_item.unit_id
                    unit_price = cost_item.price
                    # Try to infer type from cost item description if possible
                    # For now default to Labor as per plan
                    component_type = 'Labor' 
            
            if not component_name:
                # print(f"Skipping CIM {cim.id}: could not determine component name")
                skipped_count += 1
                continue
            
            # Verify unit_id exists
            if unit_id is not None and unit_id not in valid_unit_ids:
                print(f"Warning: Unit ID {unit_id} not found for CIM {cim.id}, setting to None")
                unit_id = None
                
            # Create WorkSpecification
            spec = WorkSpecification(
                work_id=cim.work_id,
                component_type=component_type,
                component_name=component_name,
                unit_id=unit_id,
                consumption_rate=consumption_rate,
                unit_price=unit_price
            )
            session.add(spec)
            migrated_count += 1
            
        session.commit()
        print(f"Successfully migrated {migrated_count} specifications. Skipped {skipped_count}.")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_specifications()
