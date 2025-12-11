"""
Модуль для чтения DBF файлов
"""

import os
import logging
import zlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dbfread import DBF

from config.settings import DBF_ENCODING, DBF_FIELD_MAPPING

logger = logging.getLogger(__name__)


class DBFReader:
    """Класс для чтения DBF файлов"""
    
    def __init__(self, encoding: str = DBF_ENCODING):
        self.encoding = encoding
    
    def read_dbf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Читает DBF файл и возвращает список записей
        
        Args:
            file_path: Путь к DBF файлу
            
        Returns:
            Список словарей с данными из DBF файла
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"DBF файл не найден: {file_path}")
            
            table = DBF(file_path, encoding=self.encoding, load=True)
            records = []
            
            for record in table:
                # Преобразуем запись в словарь с корректной кодировкой
                decoded_record = {}
                for key, value in record.items():
                    if isinstance(value, str):
                        try:
                            # Декодируем строку в правильную кодировке
                            # Для 1С DBF файлов обычно используется cp1251
                            decoded_record[key] = value
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # Если не удалось декодировать, оставляем как есть
                            decoded_record[key] = value
                    else:
                        decoded_record[key] = value
                
                records.append(decoded_record)
            
            logger.info(f"Прочитано {len(records)} записей из файла {file_path}")
            return records
            
        except Exception as e:
            logger.error(f"Ошибка при чтении DBF файла {file_path}: {e}")
            raise
    
    def read_dbf_directory(self, directory_path: str, entity_type: str) -> List[Dict[str, Any]]:
        """
        Читает все DBF файлы для указанного типа сущности из директории
        
        Args:
            directory_path: Путь к директории с DBF файлами
            entity_type: Тип сущности (nomenclature->works, works, materials, cost_items)
            
        Returns:
            Список словарей с данными из DBF файлов
        """
        try:
            if entity_type not in DBF_FIELD_MAPPING:
                raise ValueError(f"Неизвестный тип сущности: {entity_type}")
            
            # Имя файла DBF для типа сущности
            entity_config = DBF_FIELD_MAPPING[entity_type]
            dbf_filename = entity_config.get("dbf_file", f"{entity_type}.dbf")
            file_path = os.path.join(directory_path, dbf_filename)
            
            return self.read_dbf_file(file_path)
            
        except Exception as e:
            logger.error(f"Ошибка при чтении DBF файлов для типа {entity_type}: {e}")
            raise
    
    def transform_data(self, data: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """
        Преобразует данные из DBF в формат базы данных
        
        Args:
            data: Данные из DBF файла
            entity_type: Тип сущности
            
        Returns:
            Преобразованные данные
        """
        try:
            if entity_type not in DBF_FIELD_MAPPING:
                raise ValueError(f"Неизвестный тип сущности: {entity_type}")
            
            mapping = DBF_FIELD_MAPPING[entity_type]["fields"]
            transformed_data = []
            
            for record in data:
                transformed_record = {}
                
                # Преобразование полей согласно маппингу
                for dbf_field, db_field in mapping.items():
                    if dbf_field in record:
                        value = record[dbf_field]
                        
                        # Обработка специальных значений
                        if value is None:
                            value = "" if db_field == "name" else None
                        
                        # Преобразование ID в integer
                        if db_field == "id" or db_field.endswith("_id"):
                            if isinstance(value, str):
                                # Преобразуем строковый ID в число
                                try:
                                    # Убираем пробелы и преобразуем в hex, затем в int
                                    clean_value = value.strip()
                                    if clean_value:
                                        transformed_record[db_field] = int(clean_value, 16)
                                    else:
                                        transformed_record[db_field] = None
                                except (ValueError, TypeError):
                                    # Если не удалось преобразовать, используем детерминированный хеш (CRC32)
                                    # hash() в Python рандомизирован, что ломает ссылки между запусками
                                    transformed_record[db_field] = zlib.crc32(clean_value.encode(self.encoding, errors='ignore')) & 0x7FFFFFFF
                            else:
                                transformed_record[db_field] = value
                        # Преобразование логических значений
                        elif db_field == "marked_for_deletion" and isinstance(value, bool):
                            transformed_record[db_field] = value
                        elif db_field == "marked_for_deletion" and isinstance(value, str):
                            transformed_record[db_field] = value.lower() in ["true", "1", "t", "y", "yes"]
                        else:
                            transformed_record[db_field] = value
                
                transformed_data.append(transformed_record)
            
            logger.info(f"Преобразовано {len(transformed_data)} записей для типа {entity_type}")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Ошибка при преобразовании данных для типа {entity_type}: {e}")
            raise
    
    def get_dbf_files_list(self, directory_path: str) -> List[str]:
        """
        Возвращает список DBF файлов в директории
        
        Args:
            directory_path: Путь к директории
            
        Returns:
            Список путей к DBF файлам
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Директория не найдена: {directory_path}")
            
            dbf_files = []
            for file in os.listdir(directory_path):
                if file.lower().endswith(".dbf"):
                    dbf_files.append(os.path.join(directory_path, file))
            
            return dbf_files
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка DBF файлов: {e}")
            raise