
import os
from dbfread import DBF

def inspect_dbfs(directory):
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    print(f"Inspecting DBF files in {directory}")
    for filename in os.listdir(directory):
        if filename.upper().endswith(".DBF"):
            filepath = os.path.join(directory, filename)
            try:
                table = DBF(filepath, encoding='cp1251', load=False) # Use iterator to avoid loading full file
                print(f"\nFile: {filename}")
                print(f"Fields: {table.field_names}")
                
                # Print first record to guess content
                count = 0
                for record in table:
                    print(f"Sample Record: {record}")
                    count += 1
                    if count >= 1:
                        break
            except Exception as e:
                print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    inspect_dbfs(r"F:\traeRepo\Vibe1Co\Erection\8-NSM320-1Cv7")
