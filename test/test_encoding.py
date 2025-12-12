#!/usr/bin/env python
"""
Тестирование различных методов кодирования для DBF файлов
"""

import os
from dbfread import DBF

def test_encoding_methods():
    """Тестирует различные методы кодирования"""
    file_path = "F:/traeRepo/Vibe1Co/Erection/8-NSM320-1Cv7/SC12.DBF"
    
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        return
    
    print("Тестирование различных методов кодирования:")
    print("=" * 50)
    
    # Метод 1: Текущий подход (encode latin1, decode cp866)
    print("\n1. Текущий подход (encode latin1, decode cp866):")
    try:
        table = DBF(file_path, encoding='cp866', load=True)
        for i, record in enumerate(table):
            if i >= 3:  # Показываем только первые 3 записи
                break
            name = record.get('DESCR', '')
            if isinstance(name, str):
                decoded_name = name.encode('latin1').decode('cp866')
                print(f"  Оригинал: {repr(name)}")
                print(f"  Декодировано: {decoded_name}")
            print()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # Метод 2: Прямое декодирование cp866
    print("\n2. Прямое декодирование cp866:")
    try:
        table = DBF(file_path, encoding='cp866', load=True)
        for i, record in enumerate(table):
            if i >= 3:  # Показываем только первые 3 записи
                break
            name = record.get('DESCR', '')
            if isinstance(name, str):
                print(f"  Значение: {repr(name)}")
                print(f"  Как есть: {name}")
            print()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # Метод 3: Использование不同的编码
    print("\n3. Тест с кодировкой 'cp1251':")
    try:
        table = DBF(file_path, encoding='cp1251', load=True)
        for i, record in enumerate(table):
            if i >= 3:  # Показываем только первые 3 записи
                break
            name = record.get('DESCR', '')
            print(f"  Значение: {repr(name)}")
            print(f"  Как есть: {name}")
            print()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # Метод 4: Без указания кодировки
    print("\n4. Без указания кодировки:")
    try:
        table = DBF(file_path, load=True)
        for i, record in enumerate(table):
            if i >= 3:  # Показываем только первые 3 записи
                break
            name = record.get('DESCR', '')
            print(f"  Значение: {repr(name)}")
            print(f"  Как есть: {name}")
            print()
    except Exception as e:
        print(f"  Ошибка: {e}")

if __name__ == "__main__":
    test_encoding_methods()