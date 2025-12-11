
import sys
import os
import logging
from unittest.mock import MagicMock
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dbf_importer.core.importer import DBFImporter

# Configure logging
logging.basicConfig(level=logging.INFO)

def debug_full_import():
    """
    Debugs the full import process by checking mapping population and usage.
    Simulates the structure of import_all_entities calling import_entity.
    """
    # 1. Setup
    importer = DBFImporter()
    
    # Mock DBFReader
    importer.dbf_reader = MagicMock()
    
    # Use real transform_data
    from dbf_importer.core.dbf_reader import DBFReader
    real_reader = DBFReader()
    importer.dbf_reader.transform_data.side_effect = real_reader.transform_data
    
    # Real data snippet
    units_data = [
        {"ID": "3HB", "DESCR": "м2", "CODE": "001", "ISMARK": False},
        {"ID": "3ZJ", "DESCR": " м2", "CODE": "003", "ISMARK": False}, # Leading space
    ]
    
    works_data = [
        {
            "ID": "4VA", 
            "DESCR": "Work 1", 
            "CODE": "1.01-00002", 
            "SP17": " м2",  # Leading space
            "SP15": 19.32,
            "SP31": 0.4,
            "ISMARK": False
        }
    ]
    
    # Mock read_dbf_directory
    def side_effect(directory, entity_type):
        if entity_type == "units":
            return units_data
        elif entity_type == "nomenclature":
            return works_data
        return []

    importer.dbf_reader.read_dbf_directory.side_effect = side_effect
    
    print("\n--- Starting Debug Process ---")
    
    # Step 1: Simulate import_all_entities logic
    print("\n1. Calling _create_unit_mapping...")
    importer._create_unit_mapping("dummy_dir")
    
    # Check mapping
    print(f"Mapping size: {len(importer._unit_id_mapping)}")
    print(f"Mapping 'м2': {importer._unit_id_mapping.get('м2')}")
    print(f"Mapping ' м2': {importer._unit_id_mapping.get(' м2')}")
    
    if 'м2' not in importer._unit_id_mapping:
        print("CRITICAL: 'м2' not found in mapping after creation!")
    
    # Step 2: Simulate import_entity for nomenclature
    print("\n2. Calling import_entity('nomenclature')...")
    # We clear existing to ensure clean state
    importer.import_entity("dummy_dir", "nomenclature", clear_existing=True)
    
    # Step 3: Verify DB
    session = importer.db_manager.get_session()
    try:
        work = session.execute(
            text("SELECT id, name, unit_id FROM works WHERE code = '1.01-00002'")
        ).fetchone()
        
        if work:
            print(f"\nWork found: ID={work[0]}, UnitID={work[2]}")
            if work[2]:
                print("SUCCESS: UnitID is present.")
            else:
                print("FAILURE: UnitID is None!")
        else:
            print("FAILURE: Work not found.")
            
    finally:
        session.close()

if __name__ == "__main__":
    debug_full_import()
