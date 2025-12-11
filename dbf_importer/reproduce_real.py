
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

def reproduce_real_issue():
    # 1. Setup
    importer = DBFImporter()
    
    # Mock DBFReader to return controlled data based on REAL findings
    importer.dbf_reader = MagicMock()
    
    # Real data snippet from SC46.DBF (Units)
    # Notice multiple 'm2' entries and one ' м2' (leading space)
    units_data = [
        {"ID": "3HB", "DESCR": "м2", "CODE": "001", "ISMARK": False},
        {"ID": "3HC", "DESCR": "м2", "CODE": "002", "ISMARK": False},
        {"ID": "3ZJ", "DESCR": " м2", "CODE": "003", "ISMARK": False}, # Leading space!
        {"ID": "3GD", "DESCR": "шт", "CODE": "004", "ISMARK": False}
    ]
    
    # Real data snippet from SC12.DBF (Works)
    # Work 1.01-00002 has SP17 = ' м2' (leading space)
    works_data = [
        {
            "ID": "4VA", 
            "DESCR": "Составление сметной документации на объекты, пл. до 200 м2.", 
            "CODE": "1.01-00002", 
            "SP17": " м2",  # Note the leading space!
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
    
    # Use real transform_data
    from dbf_importer.core.dbf_reader import DBFReader
    real_reader = DBFReader()
    importer.dbf_reader.transform_data.side_effect = real_reader.transform_data

    # 2. Run Import
    print("Running import with REAL data snippet...")
    importer.import_all_entities("dummy_dir", clear_existing=True)
    
    # 3. Verify
    session = importer.db_manager.get_session()
    try:
        # Check Work
        work = session.execute(
            text("SELECT id, name, unit_id FROM works WHERE code = '1.01-00002'")
        ).fetchone()
        
        if not work:
            print("FAILURE: Work '1.01-00002' not found in database")
            return
            
        print(f"Work found: ID={work[0]}, UnitID={work[2]}")
        
        # Check Unit
        if work[2]:
             unit = session.execute(
                 text("SELECT id, name FROM units WHERE id = :id"),
                 {"id": work[2]}
             ).fetchone()
             print(f"Linked Unit: ID={unit[0]}, Name='{unit[1]}'")
             
             # The canonical name should be "м2" (stripped)
             if unit[1] == "м2":
                 print("SUCCESS: Linked to correct canonical unit name 'м2'")
             else:
                 print(f"FAILURE: Linked to unit '{unit[1]}', expected 'м2'")
        else:
            print("FAILURE: Work UnitID is None. Expected link to 'м2'")
            
    finally:
        session.close()

if __name__ == "__main__":
    reproduce_real_issue()
