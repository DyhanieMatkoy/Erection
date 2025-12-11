
import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dbf_importer.core.importer import DBFImporter
from dbf_importer.core.database import DatabaseManager

from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)

def reproduce_issue():
    # 1. Setup
    importer = DBFImporter()
    
    # Mock DBFReader to return controlled data
    importer.dbf_reader = MagicMock()
    
    # Mock data for Units (SC46) with DUPLICATES and WHITESPACE
    units_data = [
        {"ID": "1", "DESCR": "m2", "CODE": "001", "ISMARK": False},
        {"ID": "2", "DESCR": "m2", "CODE": "002", "ISMARK": False},  # Duplicate name
        {"ID": "3", "DESCR": "kg ", "CODE": "003", "ISMARK": False}   # Trailing space
    ]
    
    # Mock data for Works (SC12)
    # Work 1: Refers to "m2" (should pick one of them)
    # Work 2: Refers to "kg" (should match "kg ")
    works_data = [
        {
            "ID": "100", 
            "DESCR": "Test Work 1", 
            "CODE": "1.01-00002", 
            "SP17": "m2", 
            "SP15": 100.0,
            "SP31": 10.0,
            "ISMARK": False
        },
        {
            "ID": "101", 
            "DESCR": "Test Work 2", 
            "CODE": "1.01-00003", 
            "SP17": "kg",  # No space here
            "SP15": 100.0,
            "SP31": 10.0,
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
    
    # Mock transform_data to behave like the real one (partial logic or delegate)
    # Since we can't easily import the real transform_data without real DBFReader instance usage logic which depends on settings
    # We will instantiate a real DBFReader just for transform_data
    from dbf_importer.core.dbf_reader import DBFReader
    real_reader = DBFReader()
    importer.dbf_reader.transform_data.side_effect = real_reader.transform_data

    # 2. Run Import
    print("Running import...")
    # We pass a dummy directory
    importer.import_all_entities("dummy_dir", clear_existing=True)
    
    # 3. Verify
    session = importer.db_manager.get_session()
    try:
        # Check Unit
        unit = session.execute(
            text("SELECT id, name FROM units WHERE name = 'm2'")
        ).fetchone()
        
        if not unit:
            print("FAILURE: Unit 'm2' not found in database")
            return
            
        print(f"Unit 'm2' found with ID: {unit[0]}")
        
        # Check Work 1
        work = session.execute(
            text("SELECT id, name, unit_id FROM works WHERE code = '1.01-00002'")
        ).fetchone()
        
        if not work:
            print("FAILURE: Work '1.01-00002' not found in database")
            return
            
        print(f"Work 1 found: ID={work[0]}, UnitID={work[2]}")
        
        if work[2]:
            print(f"SUCCESS: Work 1 is correctly linked to Unit ID {work[2]}")
        else:
            print(f"FAILURE: Work 1 UnitID is None. Expected link to 'm2'")
            
        # Check Work 2
        work2 = session.execute(
            text("SELECT id, name, unit_id FROM works WHERE code = '1.01-00003'")
        ).fetchone()
        
        if work2:
             print(f"Work 2 found: ID={work2[0]}, UnitID={work2[2]}")
             if work2[2]:
                 print(f"SUCCESS: Work 2 is correctly linked to Unit ID {work2[2]}")
             else:
                 print(f"FAILURE: Work 2 UnitID is None. Expected link to 'kg' (ignoring whitespace)")

        # Check for duplicates in units
        units_count = session.execute(text("SELECT count(*) FROM units")).scalar()
        print(f"Total units in DB: {units_count}")
        
        m2_count = session.execute(text("SELECT count(*) FROM units WHERE name LIKE 'm2%'")).scalar()
        print(f"Units starting with 'm2': {m2_count}")
        
        if m2_count > 1:
            print("WARNING: Duplicates found for 'm2'")

            
    finally:
        session.close()

if __name__ == "__main__":
    reproduce_issue()
