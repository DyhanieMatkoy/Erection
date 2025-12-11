
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dbf_importer.core.importer import DBFImporter

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_full_import():
    importer = DBFImporter()
    dbf_dir = r"F:\traeRepo\Vibe1Co\Erection\8-NSM320-1Cv7"
    
    print(f"Starting import from {dbf_dir}")
    results = importer.import_all_entities(dbf_dir, clear_existing=True, limit=100) # Limit for testing
    
    print("Import results:", results)

if __name__ == "__main__":
    test_full_import()
