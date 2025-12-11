#!/usr/bin/env python3
"""
Script to migrate costs and materials data from DBF files to the Erection database
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dbfread import DBF
except ImportError:
    print("dbfread package is not installed. Installing...")
    os.system("pip install dbfread")
    from dbfread import DBF

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import CostItem, Material, CostItemMaterial
from sqlalchemy.orm import Session


def migrate_cost_items(db_manager, sc12_path):
    """Migrate cost items from SC12.DBF"""
    print("Migrating cost items from SC12.DBF...")
    
    try:
        # Read DBF file
        table = DBF(sc12_path, load=True, encoding='cp1251')
        
        with db_manager.session_scope() as session:
            # Create a mapping of DBF IDs to new database IDs
            id_mapping = {}
            
            for record in table:
                # Extract data from DBF record
                dbf_id = record.get('ID', '').strip()
                parent_id = record.get('PARENTID', '').strip()
                code = record.get('CODE', '').strip()
                description = record.get('DESCR', '').strip()
                is_folder = record.get('ISFOLDER', 0) == 1
                price = float(record.get('SP15', 0) or 0)
                unit = record.get('SP17', '').strip()
                labor_coefficient = float(record.get('SP31', 0) or 0)
                
                # Create CostItem object
                cost_item = CostItem(
                    parent_id=id_mapping.get(parent_id) if parent_id else None,
                    code=code,
                    description=description,
                    is_folder=is_folder,
                    price=price,
                    unit=unit,
                    labor_coefficient=labor_coefficient
                )
                
                session.add(cost_item)
                session.flush()  # Get the new ID
                
                # Store mapping for parent references
                id_mapping[dbf_id] = cost_item.id
            
            print(f"Migrated {len(table)} cost items")
            
    except Exception as e:
        print(f"Error migrating cost items: {e}")
        raise


def migrate_materials(db_manager, sc25_path):
    """Migrate materials from SC25.DBF"""
    print("Migrating materials from SC25.DBF...")
    
    try:
        # Read DBF file
        table = DBF(sc25_path, load=True, encoding='cp1251')
        
        with db_manager.session_scope() as session:
            for record in table:
                # Extract data from DBF record
                code = record.get('CODE', '').strip()
                description = record.get('DESCR', '').strip()
                price = float(record.get('SP27', 0) or 0)
                unit = record.get('SP43', '').strip()
                
                # Create Material object
                material = Material(
                    code=code,
                    description=description,
                    price=price,
                    unit=unit
                )
                
                session.add(material)
            
            print(f"Migrated {len(table)} materials")
            
    except Exception as e:
        print(f"Error migrating materials: {e}")
        raise


def main():
    """Main migration function"""
    # File paths
    sc12_path = r"E:\Drive_d\dlds\nsm\SC12.DBF"
    sc25_path = r"E:\Drive_d\dlds\nsm\NSM\SC25.DBF"
    
    # Verify files exist
    if not os.path.exists(sc12_path):
        print(f"Error: SC12.DBF not found at {sc12_path}")
        sys.exit(1)
    
    if not os.path.exists(sc25_path):
        print(f"Error: SC25.DBF not found at {sc25_path}")
        sys.exit(1)
    
    # Initialize database
    print("Initializing database...")
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
    try:
        # Migrate cost items
        migrate_cost_items(db_manager, sc12_path)
        
        # Migrate materials
        migrate_materials(db_manager, sc25_path)
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()