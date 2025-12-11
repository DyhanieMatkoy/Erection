"""
Точка входа в приложение DBF Importer
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from config.settings import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dbf_importer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_application():
    """Настраивает приложение"""
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setApplicationVersion("1.0.0")
    
    # Установка высокой DPI для лучшего отображения на высоких разрешениях
    # В PyQt6 эти атрибуты могут быть недоступны или изменены
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # Если атрибуты недоступны, просто игнорируем
        pass
    
    return app


def main():
    """Главная функция"""
    try:
        # Создание приложения
        app = setup_application()
        
        # Создание и отображение главного окна
        main_window = MainWindow()
        main_window.setWindowTitle(WINDOW_TITLE)
        main_window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        main_window.show()
        
        logger.info("Приложение DBF Importer запущено")
        
        # Запуск цикла событий
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()