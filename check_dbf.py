#!/usr/bin/env python
"""
Simple script to check DBF file structure
"""
from dbfread import DBF

def check_dbf():
    # Check SC12.DBF (works/nomenclature)
    print('=== SC12.DBF (Works) ===')
    try:
        table = DBF('8-NSM320-1Cv7/SC12.DBF', encoding='cp1251', load=True)
        if table:
            record = table[0]
            print('Fields:', list(record.keys()))
            for key, value in record.items():
                if key in ['ID', 'DESCR', 'SP17']:
                    print(f'{key}: {value} (type: {type(value)})')
    except Exception as e:
        print(f'Error: {e}')

    print('\n=== SC46.DBF (Units) ===')
    try:
        table = DBF('8-NSM320-1Cv7/SC46.DBF', encoding='cp1251', load=True)
        if table:
            record = table[0]
            print('Fields:', list(record.keys()))
            for key, value in record.items():
                if key in ['ID', 'DESCR']:
                    print(f'{key}: {value} (type: {type(value)})')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_dbf()