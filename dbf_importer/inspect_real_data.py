
import os
import sys
from dbfread import DBF

# Path to DBF files
DBF_DIR = r"F:\traeRepo\Vibe1Co\Erection\8-NSM320-1Cv7"
SC12_PATH = os.path.join(DBF_DIR, "SC12.DBF") # Works
SC46_PATH = os.path.join(DBF_DIR, "SC46.DBF") # Units

def inspect_data():
    print(f"Inspecting SC12.DBF (Works) for CODE='1.01-00002'...")
    
    found_work = None
    try:
        table = DBF(SC12_PATH, encoding='cp1251')
        for record in table:
            # Check for the specific code
            # Note: Field names in DBF might be case sensitive or padded
            code = record.get('CODE', '').strip()
            if code == '1.01-00002':
                found_work = record
                print("\nFOUND WORK RECORD:")
                print("-" * 50)
                for k, v in record.items():
                    print(f"{k}: {repr(v)}")
                
                # Specifically check SP17 (Unit Name Ref)
                unit_ref = record.get('SP17')
                print(f"\nUnit Ref (SP17): {repr(unit_ref)}")
                if isinstance(unit_ref, str):
                    print(f"Hex: {unit_ref.encode('cp1251', errors='replace').hex()}")
                break
                
        if not found_work:
            print("Work with code '1.01-00002' NOT FOUND in SC12.DBF")
            
    except Exception as e:
        print(f"Error reading SC12.DBF: {e}")

    print("\n" + "="*50 + "\n")
    
    print("Inspecting SC46.DBF (Units)...")
    try:
        table = DBF(SC46_PATH, encoding='cp1251')
        print("First 20 units:")
        count = 0
        for record in table:
            print(f"ID: {record.get('ID')}, DESCR: {repr(record.get('DESCR'))}")
            count += 1
            if count >= 20:
                break
                
        # If we found the work, let's try to find the matching unit
        if found_work:
            target_unit = found_work.get('SP17', '').strip()
            print(f"\nSearching for unit matching: '{target_unit}'")
            
            table = DBF(SC46_PATH, encoding='cp1251')
            found_unit = False
            for record in table:
                unit_name = record.get('DESCR', '').strip()
                if unit_name == target_unit:
                    print(f"MATCH FOUND: ID={record.get('ID')}, DESCR={repr(record.get('DESCR'))}")
                    found_unit = True
            
            if not found_unit:
                print(f"NO EXACT MATCH FOUND for '{target_unit}' in SC46.DBF")

    except Exception as e:
        print(f"Error reading SC46.DBF: {e}")

if __name__ == "__main__":
    inspect_data()
