#!/usr/bin/env python3

from test_cleanup_manager import TestCleanupManager
from pathlib import Path

# Создаем тестовый файл
test_file = Path('test_cleanup_check.py')
with open(test_file, 'w') as f:
    f.write('print("test file")')

print(f'Created test file: {test_file.exists()}')

# Проверяем, считает ли система очистки его временным
cleanup_manager = TestCleanupManager()
is_temp = cleanup_manager.is_temp_file(test_file)
print(f'Is temp file: {is_temp}')

# Проверяем, найдет ли его система очистки
temp_files = cleanup_manager.find_temp_files()
found_our_file = any(f.name == 'test_cleanup_check.py' for f in temp_files)
print(f'Found in temp files: {found_our_file}')

# Проверяем, найдет ли production_config_test_runner.py
prod_file = Path('production_config_test_runner.py')
if prod_file.exists():
    is_prod_temp = cleanup_manager.is_temp_file(prod_file)
    print(f'production_config_test_runner.py is temp: {is_prod_temp}')
    
    found_prod_file = any(f.name == 'production_config_test_runner.py' for f in temp_files)
    print(f'production_config_test_runner.py found in temp files: {found_prod_file}')
else:
    print('production_config_test_runner.py does not exist')

# Показываем все найденные временные файлы
print(f'\nAll temp files found ({len(temp_files)}):')
for f in temp_files:
    print(f'  - {f}')