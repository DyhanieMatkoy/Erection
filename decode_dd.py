
import os

def decode_dd(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='cp1251') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    decode_dd(r"F:\traeRepo\Vibe1Co\Erection\8-NSM320-1Cv7\1Cv7.DD")
