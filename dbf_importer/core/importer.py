"""
Основной модуль импорта данных из DBF файлов
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
from sqlalchemy import text

from .dbf_reader import DBFReader
from .database import DatabaseManager
from config.settings import DBF_FIELD_MAPPING, BATCH_SIZE

logger = logging.getLogger(__name__)


class DBFImporter:
    """Класс для импорта данных из DBF файлов в базу данных"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.dbf_reader = DBFReader()
        self.db_manager = DatabaseManager()
        self.progress_callback = progress_callback
    
    def import_entity(self, dbf_path: str, entity_type: str, 
                     clear_existing: bool = False, limit: int = None) -> bool:
        """
        Импортирует данные для указанного типа сущности
        
        Args:
            dbf_path: Путь к DBF файлу или директории с DBF файлами
            entity_type: Тип сущности (nomenclature->works, works, materials, cost_items)
            clear_existing: Флаг очистки существующих данных перед импортом
            limit: Ограничение на количество импортируемых записей (None - все записи)
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            if entity_type not in DBF_FIELD_MAPPING:
                raise ValueError(f"Неизвестный тип сущности: {entity_type}")
            
            if entity_type == "composition":
                return self._import_composition(dbf_path, clear_existing, limit)

            table_name = DBF_FIELD_MAPPING[entity_type]["table"]
            
            # Проверка существования таблицы
            if not self.db_manager.table_exists(table_name):
                logger.error(f"Таблица {table_name} не существует в базе данных")
                return False
            
            # Очистка существующих данных, если требуется
            if clear_existing:
                logger.info(f"Очистка таблицы {table_name}")
                session = self.db_manager.get_session()
                try:
                    session.execute(text(f"DELETE FROM {table_name}"))
                    session.commit()
                except Exception as e:
                    logger.error(f"Ошибка при очистке таблицы {table_name}: {e}")
                    session.rollback()
                    return False
                finally:
                    session.close()
            
            # Чтение данных из DBF файла
            logger.info(f"Чтение данных из DBF для типа {entity_type}")
            if Path(dbf_path).is_file():
                raw_data = self.dbf_reader.read_dbf_file(dbf_path)
            else:
                raw_data = self.dbf_reader.read_dbf_directory(dbf_path, entity_type)
            
            if not raw_data:
                logger.warning(f"Нет данных для импорта в файле {dbf_path}")
                return True
            
            # Применение ограничения на количество записей
            if limit is not None and limit > 0:
                raw_data = raw_data[:limit]
                logger.info(f"Ограничение импорта до {limit} записей")
            
            # Преобразование данных
            logger.info(f"Преобразование данных для типа {entity_type}")
            data = self.dbf_reader.transform_data(raw_data, entity_type)
            
            # Handle duplicate unit names to avoid UNIQUE constraint violation
            if entity_type == "units":
                name_counts = {}
                for record in data:
                    name = record.get("name")
                    if name:
                        if name in name_counts:
                            name_counts[name] += 1
                            record["name"] = f"{name} ({name_counts[name]})"
                        else:
                            name_counts[name] = 1
                logger.info(f"Обработано имен единиц измерения: {len(data)}")
            
            # Resolve units for Works
            if entity_type == "nomenclature":
                self._resolve_work_units(data)
            
            # Импорт данных пакетами
            logger.info(f"Импорт данных в таблицу {table_name}")
            return self._import_data_in_batches(data, table_name, entity_type)
            
        except Exception as e:
            logger.error(f"Ошибка при импорте данных для типа {entity_type}: {e}")
            return False
    
    def _import_composition(self, dbf_path: str, clear_existing: bool = False, limit: int = None) -> bool:
        """
        Special handling for composition import (SC20)
        """
        entity_type = "composition"
        table_name = DBF_FIELD_MAPPING[entity_type]["table"]
        
        try:
            # 1. Clear existing
            if clear_existing:
                logger.info(f"Очистка таблицы {table_name}")
                session = self.db_manager.get_session()
                try:
                    session.execute(text(f"DELETE FROM {table_name}"))
                    session.commit()
                except Exception as e:
                    logger.error(f"Ошибка при очистке таблицы {table_name}: {e}")
                    session.rollback()
                    return False
                finally:
                    session.close()

            # 2. Read DBF
            logger.info(f"Чтение данных из DBF для типа {entity_type}")
            if Path(dbf_path).is_file():
                raw_data = self.dbf_reader.read_dbf_file(dbf_path)
            else:
                raw_data = self.dbf_reader.read_dbf_directory(dbf_path, entity_type)
            
            if not raw_data:
                logger.warning(f"Нет данных для импорта в файле {dbf_path}")
                return True
            
            if limit is not None and limit > 0:
                raw_data = raw_data[:limit]
            
            # 3. Transform data
            logger.info(f"Преобразование данных для типа {entity_type}")
            data = self.dbf_reader.transform_data(raw_data, entity_type)
            
            # 4. Handle Cost Items (SC20 DESCR -> cost_items table)
            # Get unique cost item names
            unique_names = set()
            for record in data:
                name = record.get("cost_item_name")
                if name:
                    unique_names.add(name)
            
            # Get existing cost items map
            db_session = self.db_manager.get_session()
            cost_item_map = {} # name -> id
            try:
                rows = db_session.execute(text("SELECT id, description FROM cost_items")).fetchall()
                for row in rows:
                    if row[1]:
                        cost_item_map[row[1]] = row[0]
                
                # Insert new cost items
                new_items_count = 0
                for name in unique_names:
                    if name not in cost_item_map:
                        # Insert
                        result = db_session.execute(
                            text("INSERT INTO cost_items (description, code, is_folder, marked_for_deletion, price, labor_coefficient) VALUES (:desc, :code, 0, 0, 0, 0)"), 
                            {"desc": name, "code": name[:50]} # Use name as code for now
                        )
                        # Get ID (SQLite specific for now, but SQLAlchemy usually handles return)
                        # For cross-db support, usually we need to select back or use returning.
                        # Since we use execute, we can use cursor.lastrowid for SQLite.
                        new_id = result.lastrowid
                        cost_item_map[name] = new_id
                        new_items_count += 1
                
                db_session.commit()
                logger.info(f"Создано {new_items_count} новых элементов затрат")
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении справочника затрат: {e}")
                db_session.rollback()
                return False
            finally:
                db_session.close()
                
            # 5. Prepare final data for cost_item_materials
            final_data = []
            for record in data:
                name = record.get("cost_item_name")
                cost_item_id = cost_item_map.get(name)
                
                if not cost_item_id:
                    continue # Should not happen
                
                new_record = {
                    "work_id": record.get("work_id"),
                    "material_id": record.get("material_id"),
                    "cost_item_id": cost_item_id,
                    "quantity_per_unit": record.get("quantity_per_unit", 0.0)
                }
                
                # Validate IDs
                if not new_record["work_id"]:
                    continue
                
                final_data.append(new_record)
                
            # 6. Batch Import
            logger.info(f"Импорт данных в таблицу {table_name}")
            return self._import_data_in_batches(final_data, table_name, entity_type)
            
        except Exception as e:
            logger.error(f"Ошибка при импорте композиции: {e}")
            return False

    def _resolve_work_units(self, data: List[Dict[str, Any]]):
        """Resolves unit_name to unit_id for Works"""
        try:
            session = self.db_manager.get_session()
            units = session.execute(text("SELECT id, name FROM units")).fetchall()
            # Create map: lowercase name -> id
            unit_map = {row[1].strip().lower(): row[0] for row in units if row[1]}
            session.close()
            
            for record in data:
                unit_name = record.pop("unit_name", None) # Remove temporary field
                if unit_name:
                    record["unit"] = unit_name # Keep legacy string
                    # Lookup ID
                    unit_id = unit_map.get(str(unit_name).strip().lower())
                    if unit_id:
                        record["unit_id"] = unit_id
        except Exception as e:
            logger.error(f"Error resolving units: {e}")

    def import_all_entities(self, dbf_directory: str, 
                           clear_existing: bool = False, limit: int = None) -> Dict[str, bool]:
        """
        Импортирует данные всех типов сущностей из указанной директории
        
        Args:
            dbf_directory: Директория с DBF файлами
            clear_existing: Флаг очистки существующих данных перед импортом
            limit: Ограничение на количество импортируемых записей для каждой сущности
            
        Returns:
            Словарь с результатами импорта для каждого типа сущности
        """
        results = {}
        
        # Определение порядка импорта (сначала справочники, потом документы)
        import_order = ["units", "materials", "nomenclature", "composition"]
        
        for entity_type in import_order:
            if entity_type not in DBF_FIELD_MAPPING:
                logger.warning(f"Тип сущности {entity_type} не найден в настройках, пропуск")
                continue

            logger.info(f"Начало импорта сущности: {entity_type}")
            
            # Вызов callback для обновления прогресса
            if self.progress_callback:
                self.progress_callback(f"Импорт {entity_type}...", 0)
            
            # Импорт сущности
            success = self.import_entity(dbf_directory, entity_type, clear_existing, limit)
            results[entity_type] = success
            
            if success:
                logger.info(f"Успешно импортирована сущность: {entity_type}")
            else:
                logger.error(f"Ошибка при импорте сущности: {entity_type}")
        
        return results
    
    def _import_data_in_batches(self, data: List[Dict[str, Any]], 
                                table_name: str, entity_type: str) -> bool:
        """
        Импортирует данные пакетами
        
        Args:
            data: Данные для импорта
            table_name: Имя таблицы
            entity_type: Тип сущности
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            total_records = len(data)
            processed_records = 0
            
            # Разделение данных на пакеты
            for i in range(0, total_records, BATCH_SIZE):
                batch = data[i:i + BATCH_SIZE]
                
                # Импорт пакета
                success = self.db_manager.update_or_insert_records(table_name, batch)
                
                if not success:
                    logger.warning(f"Ошибка при импорте пакета {i//BATCH_SIZE + 1}. Пробуем импортировать записи по одной.")
                    # Если пакет не удалось импортировать, пробуем по одной записи
                    for record in batch:
                        try:
                            single_success = self.db_manager.update_or_insert_records(table_name, [record])
                            if not single_success:
                                logger.error(f"Не удалось импортировать запись: {record}")
                        except Exception as e:
                            logger.error(f"Ошибка при импорте записи: {e}. Данные: {record}")
                
                processed_records += len(batch)
                
                # Обновление прогресса
                progress = int((processed_records / total_records) * 100)
                logger.info(f"Обработано {processed_records} из {total_records} записей ({progress}%)")
                
                if self.progress_callback:
                    self.progress_callback(
                        f"Импорт {entity_type}: {processed_records}/{total_records}", 
                        progress
                    )
            
            logger.info(f"Успешно импортировано {total_records} записей в таблицу {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при пакетном импорте данных: {e}")
            return False
    
    def validate_dbf_structure(self, dbf_path: str, entity_type: str) -> Dict[str, Any]:
        """
        Проверяет структуру DBF файла на соответствие ожидаемой
        
        Args:
            dbf_path: Путь к DBF файлу
            entity_type: Тип сущности
            
        Returns:
            Словарь с результатами валидации
        """
        try:
            if entity_type not in DBF_FIELD_MAPPING:
                raise ValueError(f"Неизвестный тип сущности: {entity_type}")
            
            # Чтение данных из DBF файла
            if Path(dbf_path).is_dir():
                # Если передан путь к директории, получаем имя файла из настроек
                dbf_file = DBF_FIELD_MAPPING[entity_type].get("dbf_file")
                if not dbf_file:
                    raise ValueError(f"Для сущности {entity_type} не указан файл DBF в настройках")
                file_path = str(Path(dbf_path) / dbf_file)
            else:
                file_path = dbf_path

            raw_data = self.dbf_reader.read_dbf_file(file_path)
            
            if not raw_data:
                return {"valid": False, "message": "DBF файл пуст или не существует"}
            
            # Проверка наличия обязательных полей
            expected_fields = set(DBF_FIELD_MAPPING[entity_type]["fields"].keys())
            actual_fields = set(raw_data[0].keys())
            
            missing_fields = expected_fields - actual_fields
            extra_fields = actual_fields - expected_fields
            
            result = {
                "valid": len(missing_fields) == 0,
                "record_count": len(raw_data),
                "missing_fields": list(missing_fields),
                "extra_fields": list(extra_fields)
            }
            
            if not result["valid"]:
                result["message"] = f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            else:
                result["message"] = "Структура DBF файла корректна"
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при валидации DBF файла: {e}")
            return {"valid": False, "message": str(e)}