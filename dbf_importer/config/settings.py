"""
Настройки приложения DBF Importer
"""

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR.parent / "construction.db"

# Настройки базы данных
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Настройки DBF
DBF_ENCODING = "cp1251"  # Кодировка для DBF файлов 1С
DBF_DEFAULT_PATH = ""  # Путь к DBF файлам по умолчанию

# Настройки импорта
BATCH_SIZE = 100  # Размер пакета для импорта данных
PROGRESS_UPDATE_INTERVAL = 10  # Интервал обновления прогресса (в записях)

# Настройки UI
WINDOW_TITLE = "DBF Importer"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Сопоставление полей DBF с полями базы данных
DBF_FIELD_MAPPING = {
    "units": {
        "table": "units",
        "dbf_file": "SC46.DBF",
        "fields": {
            "ID": "id",
            "DESCR": "name",
            "CODE": "description",  # Use code as description or ignore
            "ISMARK": "marked_for_deletion"
        }
    },
    "materials": {
        "table": "materials",
        "dbf_file": "SC25.DBF",
        "fields": {
            "ID": "id",
            "DESCR": "description",  # Model uses description
            "CODE": "code",
            "SP27": "price",
            "SP43": "unit_id",
            "ISMARK": "marked_for_deletion"
        }
    },
    "nomenclature": {
        "table": "works",
        "dbf_file": "SC12.DBF",
        "fields": {
            "ID": "id",
            "DESCR": "name",
            "PARENTID": "parent_id",
            "CODE": "code",
            "SP17": "unit_name",  # Temporary field for lookup
            "SP15": "price",
            "SP31": "labor_rate",
            "ISMARK": "marked_for_deletion"
        }
    },
    "composition": {
        "table": "cost_item_materials",  # Target association table
        "dbf_file": "SC20.DBF",
        "fields": {
            "PARENTEXT": "work_id",
            "SP63": "material_id",
            "DESCR": "cost_item_name",  # Special handling needed
            "SP22": "quantity_per_unit",
            "ISMARK": "marked_for_deletion"
        }
    }
}