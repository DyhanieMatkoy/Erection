#!/usr/bin/env python3
"""
Скрипт для скачивания файлов из папки src репозитория GitHub
"""

import os
import sys
import json
import requests
from pathlib import Path
from urllib.parse import urljoin

# Настройки репозитория
REPO_OWNER = "DyhanieMatkoy"
REPO_NAME = "Erection"
BRANCH = "main"
SOURCE_PATH = "src"

def download_file(url, target_path):
    """Скачивает файл по URL в указанный путь"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Создаем папки если не существуют
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return False

def get_directory_contents(repo_owner, repo_name, path, branch="main"):
    """Получает содержимое папки через GitHub API"""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    params = {"ref": branch}
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при получении списка файлов: {e}")
        return None

def download_directory_recursive(repo_owner, repo_name, source_path, target_dir, branch="main", level=0):
    """Рекурсивно скачивает все файлы из папки"""
    indent = "  " * level
    print(f"{indent}Обрабатываем папку: {source_path}")
    
    contents = get_directory_contents(repo_owner, repo_name, source_path, branch)
    if not contents:
        return 0, 0
    
    total_files = 0
    downloaded_files = 0
    
    for item in contents:
        item_name = item["name"]
        item_type = item["type"]
        
        if item_type == "file":
            total_files += 1
            download_url = item["download_url"]
            target_path = Path(target_dir) / Path(source_path).relative_to(Path(SOURCE_PATH)) / item_name
            
            print(f"{indent}[{total_files}] Скачиваем файл: {item_name}")
            
            if download_file(download_url, target_path):
                downloaded_files += 1
                print(f"{indent}  ✓ Успешно скачан")
            
        elif item_type == "dir":
            print(f"{indent}Найдена подпапка: {item_name}")
            sub_path = f"{source_path}/{item_name}"
            sub_total, sub_downloaded = download_directory_recursive(
                repo_owner, repo_name, sub_path, target_dir, branch, level + 1
            )
            total_files += sub_total
            downloaded_files += sub_downloaded
    
    return total_files, downloaded_files

def main():
    print("=" * 50)
    print("Скачивание файлов src с GitHub")
    print("=" * 50)
    
    # Определяем целевую папку
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.path.join(os.getcwd(), "src")
    
    target_path = Path(target_dir)
    
    print(f"Репозиторий: https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"Исходная папка: {SOURCE_PATH}")
    print(f"Целевая папка: {target_path.absolute()}")
    print(f"Ветка: {BRANCH}")
    print()
    
    # Создаем целевую папку
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Проверяем доступность GitHub API
    try:
        response = requests.get("https://api.github.com/rate_limit")
        rate_limit = response.json()
        remaining = rate_limit["rate"]["remaining"]
        print(f"GitHub API запросов осталось: {remaining}")
        
        if remaining < 10:
            print("⚠️  Предупреждение: Мало оставшихся запросов к GitHub API")
        print()
    except:
        print("⚠️  Не удалось проверить лимиты GitHub API")
        print()
    
    # Скачиваем файлы
    print("Начинаем скачивание...")
    total_files, downloaded_files = download_directory_recursive(
        REPO_OWNER, REPO_NAME, SOURCE_PATH, target_dir, BRANCH
    )
    
    print()
    print("=" * 50)
    print("ЗАВЕРШЕНО!")
    print("=" * 50)
    print(f"Всего файлов найдено: {total_files}")
    print(f"Успешно скачано: {downloaded_files}")
    print(f"Файлы сохранены в: {target_path.absolute()}")
    
    if downloaded_files < total_files:
        print(f"⚠️  Не удалось скачать {total_files - downloaded_files} файлов")
    
    # Показываем структуру скачанных файлов
    print("\nСтруктура скачанных файлов:")
    for root, dirs, files in os.walk(target_path):
        level = root.replace(str(target_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nСкачивание прервано пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)