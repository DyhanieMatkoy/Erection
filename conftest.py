"""
Конфигурация pytest с автоматической очисткой тестовых данных
"""

import pytest
import os
import tempfile
from pathlib import Path
from test_cleanup_manager import TestCleanupManager


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Автоматическая очистка после выполнения всех тестов"""
    yield  # Выполняем тесты
    
    # После завершения тестов выполняем очистку
    cleanup_manager = TestCleanupManager()
    cleanup_manager.cleanup_all()


@pytest.fixture(autouse=True)
def setup_temp_dir():
    """Настройка временной директории для тестов"""
    # Создаем временную директорию для тестов
    temp_dir = Path(tempfile.mkdtemp(prefix="test_", dir="test_databases"))
    
    # Устанавливаем переменную окружения для тестов
    old_temp = os.environ.get('TEST_TEMP_DIR')
    os.environ['TEST_TEMP_DIR'] = str(temp_dir)
    
    yield temp_dir
    
    # Восстанавливаем переменную окружения
    if old_temp is not None:
        os.environ['TEST_TEMP_DIR'] = old_temp
    elif 'TEST_TEMP_DIR' in os.environ:
        del os.environ['TEST_TEMP_DIR']
    
    # Очищаем временную директорию
    try:
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except Exception:
        pass  # Игнорируем ошибки очистки


@pytest.fixture
def temp_config_file():
    """Создает временный файл конфигурации для тестов"""
    import tempfile
    
    # Создаем временный файл в test_databases
    temp_dir = Path("test_databases")
    temp_dir.mkdir(exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(suffix='.ini', dir=temp_dir)
    os.close(fd)
    
    yield Path(temp_path)
    
    # Удаляем временный файл
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


# Настройка Hypothesis для ограничения генерации Unicode символов
try:
    from hypothesis import settings, HealthCheck
    from hypothesis.strategies import text
    import string
    
    # Ограничиваем генерацию текста только ASCII символами для имен файлов
    settings.register_profile("ci", max_examples=50, deadline=None)
    settings.register_profile("dev", max_examples=10, deadline=None)
    settings.load_profile("dev")
    
except ImportError:
    pass  # Hypothesis не установлен