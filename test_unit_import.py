#!/usr/bin/env python
"""
Test script to verify unit import fix
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.importer import DBFImporter

def test_unit_import():
    """Test unit import with mapping"""
    print("Testing unit import fix...")
    
    # Create importer
    importer = DBFImporter()
    
    # Test path
    dbf_dir = r"F:\traeRepo\Vibe1Co\Erection\8-NSM320-1Cv7"
    
    # Import only units first to create mapping
    print("Step 1: Importing units...")
    result = importer.import_entity(dbf_dir, "units", clear_existing=True, limit=5)
    print(f"Units import result: {result}")
    
    # Check mapping was created
    print(f"Unit mapping created: {len(importer._unit_id_mapping)} entries")
    if importer._unit_id_mapping:
        print("Sample unit mappings:")
        for i, (dbf_id, db_id) in enumerate(list(importer._unit_id_mapping.items())[:3]):
            print(f"  DBF ID: {dbf_id} -> DB ID: {db_id}")
    
    # Import works with unit mapping
    print("\nStep 2: Importing works with unit mapping...")
    result = importer.import_entity(dbf_dir, "nomenclature", clear_existing=False, limit=5)
    print(f"Works import result: {result}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_unit_import()