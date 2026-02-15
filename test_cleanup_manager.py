"""
Test Cleanup Manager

Автоматическая система очистки тестовых данных, включая:
- Папки с Unicode символами, созданные тестами
- Временные базы данных
- Тестовые файлы конфигурации
- Кэш файлы pytest и hypothesis
"""

import os
import shutil
import re
import logging
from pathlib import Path
from typing import List, Set
import unicodedata


class TestCleanupManager:
    """Менеджер очистки тестовых данных"""
    
    def __init__(self, project_root: str = "."):
        """Инициализация менеджера очистки
        
        Args:
            project_root: Корневая директория проекта
        """
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        
        # Папки, которые нужно сохранить (белый список)
        self.protected_dirs = {
            '.git', '.kiro', '.vscode', '.trae', 'alembic', 'api', 'archives',
            'config', 'dbf_importer', 'deploy-to-prod', 'desktop_package',
            'dist', 'docs', 'examples', 'fonts', 'migration_backups',
            'migration_results', 'migrations', 'node_modules', 'password_fix_deployment',
            'PrnForms', 'run', 'scripts', 'src', 'test', 'web-client',
            'test_configs', 'test_databases', 'test_logs', 'test_migrations',
            'test_reports', 'validation_results', 'api_test_results', '.pytest_cache'
        }
        
        # Расширения файлов для очистки
        self.cleanup_extensions = {'.db', '.tmp', '.temp', '.cache', '.log'}
        
        # Паттерны для временных файлов
        self.temp_patterns = [
            r'^tmp[a-zA-Z0-9_]+$',  # tmpXXXXXX файлы
            r'^test_[a-zA-Z0-9_]+\.db$',  # test_*.db файлы
            r'^.*\.tmp$',  # *.tmp файлы
        ]
    
    def _setup_logger(self) -> logging.Logger:
        """Настройка логгера"""
        logger = logging.getLogger('TestCleanupManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def is_unicode_test_dir(self, dir_name: str) -> bool:
        """Проверяет, является ли директория тестовой с Unicode символами
        
        Args:
            dir_name: Имя директории
            
        Returns:
            True если это тестовая директория с Unicode символами
        """
        # Проверяем, содержит ли имя не-ASCII символы
        try:
            dir_name.encode('ascii')
            # Если кодирование прошло успешно, проверяем другие критерии
            # Папки типа "0", "1", "L", "A" и т.д. (короткие имена)
            if len(dir_name) <= 3:
                # Цифровые папки
                if dir_name.isdigit():
                    return True
                # Одиночные буквы
                if len(dir_name) == 1 and dir_name.isalpha():
                    return True
                # Короткие случайные имена
                if len(dir_name) <= 2 and dir_name.isalnum():
                    return True
            return False
        except UnicodeEncodeError:
            # Содержит не-ASCII символы
            return True
    
    def is_temp_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл временным
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл временный
        """
        file_name = file_path.name
        
        # Проверяем расширение
        if file_path.suffix in self.cleanup_extensions:
            return True
        
        # Проверяем паттерны
        for pattern in self.temp_patterns:
            if re.match(pattern, file_name):
                return True
        
        return False
    
    def find_unicode_test_dirs(self) -> List[Path]:
        """Находит все тестовые директории с Unicode символами
        
        Returns:
            Список путей к тестовым директориям
        """
        unicode_dirs = []
        
        try:
            for item in self.project_root.iterdir():
                if item.is_dir() and item.name not in self.protected_dirs:
                    if self.is_unicode_test_dir(item.name):
                        unicode_dirs.append(item)
                        self.logger.info(f"Найдена тестовая директория: {item.name}")
        
        except Exception as e:
            self.logger.error(f"Ошибка при поиске Unicode директорий: {e}")
        
        return unicode_dirs
    
    def find_temp_files(self) -> List[Path]:
        """Находит все временные файлы в проекте
        
        Returns:
            Список путей к временным файлам
        """
        temp_files = []
        
        try:
            for item in self.project_root.rglob('*'):
                if item.is_file() and self.is_temp_file(item):
                    # Проверяем, что файл не в защищенных директориях
                    if not any(protected in item.parts for protected in self.protected_dirs):
                        temp_files.append(item)
                        self.logger.info(f"Найден временный файл: {item}")
        
        except Exception as e:
            self.logger.error(f"Ошибка при поиске временных файлов: {e}")
        
        return temp_files
    
    def cleanup_pytest_cache(self) -> bool:
        """Очищает кэш pytest
        
        Returns:
            True если очистка прошла успешно
        """
        try:
            cache_dirs = [
                self.project_root / '.pytest_cache',
                self.project_root / '__pycache__',
                self.project_root / '.hypothesis'
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    self.logger.info(f"Удален кэш: {cache_dir}")
            
            # Удаляем __pycache__ во всех поддиректориях
            for pycache in self.project_root.rglob('__pycache__'):
                if pycache.is_dir():
                    shutil.rmtree(pycache)
                    self.logger.info(f"Удален __pycache__: {pycache}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка при очистке кэша pytest: {e}")
            return False
    
    def remove_unicode_dirs(self, dirs: List[Path]) -> int:
        """Удаляет Unicode тестовые директории
        
        Args:
            dirs: Список директорий для удаления
            
        Returns:
            Количество успешно удаленных директорий
        """
        removed_count = 0
        
        for dir_path in dirs:
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    self.logger.info(f"Удалена директория: {dir_path.name}")
                    removed_count += 1
                else:
                    self.logger.warning(f"Директория не существует: {dir_path}")
            
            except Exception as e:
                self.logger.error(f"Ошибка при удалении {dir_path}: {e}")
        
        return removed_count
    
    def remove_temp_files(self, files: List[Path]) -> int:
        """Удаляет временные файлы
        
        Args:
            files: Список файлов для удаления
            
        Returns:
            Количество успешно удаленных файлов
        """
        removed_count = 0
        
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.logger.info(f"Удален файл: {file_path}")
                    removed_count += 1
                else:
                    self.logger.warning(f"Файл не существует: {file_path}")
            
            except Exception as e:
                self.logger.error(f"Ошибка при удалении {file_path}: {e}")
        
        return removed_count
    
    def cleanup_all(self, dry_run: bool = False) -> dict:
        """Выполняет полную очистку тестовых данных
        
        Args:
            dry_run: Если True, только показывает что будет удалено
            
        Returns:
            Словарь с результатами очистки
        """
        self.logger.info("Начинаем очистку тестовых данных...")
        
        results = {
            'unicode_dirs_found': 0,
            'unicode_dirs_removed': 0,
            'temp_files_found': 0,
            'temp_files_removed': 0,
            'cache_cleaned': False
        }
        
        # Находим Unicode директории
        unicode_dirs = self.find_unicode_test_dirs()
        results['unicode_dirs_found'] = len(unicode_dirs)
        
        # Находим временные файлы
        temp_files = self.find_temp_files()
        results['temp_files_found'] = len(temp_files)
        
        if dry_run:
            self.logger.info("=== РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА ===")
            self.logger.info(f"Будет удалено {len(unicode_dirs)} Unicode директорий:")
            for dir_path in unicode_dirs:
                self.logger.info(f"  - {dir_path.name}")
            
            self.logger.info(f"Будет удалено {len(temp_files)} временных файлов:")
            for file_path in temp_files:
                self.logger.info(f"  - {file_path}")
            
            return results
        
        # Удаляем Unicode директории
        if unicode_dirs:
            results['unicode_dirs_removed'] = self.remove_unicode_dirs(unicode_dirs)
        
        # Удаляем временные файлы
        if temp_files:
            results['temp_files_removed'] = self.remove_temp_files(temp_files)
        
        # Очищаем кэш
        results['cache_cleaned'] = self.cleanup_pytest_cache()
        
        self.logger.info("Очистка завершена!")
        self.logger.info(f"Удалено директорий: {results['unicode_dirs_removed']}/{results['unicode_dirs_found']}")
        self.logger.info(f"Удалено файлов: {results['temp_files_removed']}/{results['temp_files_found']}")
        self.logger.info(f"Кэш очищен: {results['cache_cleaned']}")
        
        return results
    
    def setup_auto_cleanup(self) -> bool:
        """Настраивает автоматическую очистку после тестов
        
        Returns:
            True если настройка прошла успешно
        """
        try:
            # Создаем conftest.py для автоматической очистки
            conftest_content = '''"""
Конфигурация pytest с автоматической очисткой тестовых данных
"""

import pytest
from test_cleanup_manager import TestCleanupManager


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Автоматическая очистка после выполнения всех тестов"""
    yield  # Выполняем тесты
    
    # После завершения тестов выполняем очистку
    cleanup_manager = TestCleanupManager()
    cleanup_manager.cleanup_all()


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Очистка временных файлов после каждого теста"""
    yield  # Выполняем тест
    
    # Очищаем только временные файлы, созданные во время теста
    cleanup_manager = TestCleanupManager()
    temp_files = cleanup_manager.find_temp_files()
    if temp_files:
        cleanup_manager.remove_temp_files(temp_files)
'''
            
            conftest_path = self.project_root / 'conftest.py'
            
            # Проверяем, существует ли уже conftest.py
            if conftest_path.exists():
                # Читаем существующий файл
                with open(conftest_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Если уже содержит нашу очистку, не перезаписываем
                if 'cleanup_after_tests' in existing_content:
                    self.logger.info("Автоматическая очистка уже настроена в conftest.py")
                    return True
                
                # Добавляем к существующему содержимому
                with open(conftest_path, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + conftest_content)
                self.logger.info("Добавлена автоматическая очистка в существующий conftest.py")
            else:
                # Создаем новый файл
                with open(conftest_path, 'w', encoding='utf-8') as f:
                    f.write(conftest_content)
                self.logger.info("Создан conftest.py с автоматической очисткой")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка при настройке автоматической очистки: {e}")
            return False


def main():
    """Основная функция для запуска очистки"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Менеджер очистки тестовых данных')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Показать что будет удалено без фактического удаления')
    parser.add_argument('--setup-auto', action='store_true',
                       help='Настроить автоматическую очистку после тестов')
    
    args = parser.parse_args()
    
    cleanup_manager = TestCleanupManager()
    
    if args.setup_auto:
        cleanup_manager.setup_auto_cleanup()
    
    # Выполняем очистку
    results = cleanup_manager.cleanup_all(dry_run=args.dry_run)
    
    return results


if __name__ == "__main__":
    main()