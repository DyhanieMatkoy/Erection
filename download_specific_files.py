#!/usr/bin/env python3
"""
Скрипт для скачивания конкретных файлов из репозитория GitHub
"""

import os
import sys
import requests
from pathlib import Path

# Настройки репозитория
REPO_OWNER = "DyhanieMatkoy"
REPO_NAME = "Erection"
BRANCH = "main"

def download_file(repo_owner, repo_name, file_path, target_path, branch="main"):
    """Скачивает конкретный файл из репозитория"""
    # URL для скачивания файла
    download_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"
    
    try:
        print(f"Скачиваем: {file_path}")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Создаем папки если не существуют
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл
        with open(target_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ Сохранен как: {target_path}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"  ✗ Файл не найден: {file_path}")
        else:
            print(f"  ✗ HTTP ошибка {e.response.status_code}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return False

def main():
    print("=" * 60)
    print("Скачивание конкретных файлов с GitHub")
    print("=" * 60)
    
    # Определяем целевую папку
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.getcwd()
    
    target_path = Path(target_dir)
    
    print(f"Репозиторий: https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"Целевая папка: {target_path.absolute()}")
    print(f"Ветка: {BRANCH}")
    print()
    
    # Список файлов для скачивания (можно редактировать)
    files_to_download = [
        # Основные файлы приложения
        "src/main.py",
        "src/config.py",
        "src/database.py",
        
        # Модели данных
        "src/models/__init__.py",
        "src/models/base.py",
        "src/models/work.py",
        "src/models/material.py",
        
        # Сервисы
        "src/services/__init__.py",
        "src/services/work_service.py",
        "src/services/material_service.py",
        
        # Представления (views)
        "src/views/__init__.py",
        "src/views/main_window.py",
        "src/views/work_form.py",
        
        # Утилиты
        "src/utils/__init__.py",
        "src/utils/helpers.py",
        "src/utils/validators.py",
    ]
    
    print("Файлы для скачивания:")
    for file_path in files_to_download:
        print(f"  - {file_path}")
    print()
    
    # Создаем целевую папку
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Скачиваем файлы
    downloaded_count = 0
    total_count = len(files_to_download)
    
    for i, file_path in enumerate(files_to_download, 1):
        print(f"[{i}/{total_count}] ", end="")
        
        # Определяем путь для сохранения
        relative_path = Path(file_path)
        save_path = target_path / relative_path
        
        if download_file(REPO_OWNER, REPO_NAME, file_path, save_path, BRANCH):
            downloaded_count += 1
    
    print()
    print("=" * 60)
    print("ЗАВЕРШЕНО!")
    print("=" * 60)
    print(f"Всего файлов: {total_count}")
    print(f"Успешно скачано: {downloaded_count}")
    print(f"Не удалось скачать: {total_count - downloaded_count}")
    print(f"Файлы сохранены в: {target_path.absolute()}")
    
    if downloaded_count < total_count:
        print("\n⚠️  Некоторые файлы не были найдены в репозитории.")
        print("Возможные причины:")
        print("- Файл не существует в указанной ветке")
        print("- Изменилась структура репозитория")
        print("- Файл был переименован или перемещен")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nСкачивание прервано пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)