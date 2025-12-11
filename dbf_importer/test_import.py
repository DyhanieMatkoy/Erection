#!/usr/bin/env python
"""
Тестовый скрипт для импорта данных из DBF
"""

import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.importer import DBFImporter

def test_import():
    """Тестирует импорт данных"""
    # Создаем импортер с callback для прогресса
    def progress_callback(message, progress):
        print(f'{progress}% - {message}')
    
    importer = DBFImporter(progress_callback=progress_callback)
    
    # Импортируем только 5 записей для теста
    result = importer.import_entity(
        'F:/traeRepo/Vibe1Co/Erection/8-NSM320-1Cv7', 
        'nomenclature', 
        clear_existing=False, 
        limit=5
    )
    
    print(f'Результат импорта: {result}')

if __name__ == "__main__":
    test_import()