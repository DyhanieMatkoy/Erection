"""
Модуль для работы с базой данных
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления подключением к базе данных"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Создает и возвращает сессию базы данных"""
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Выполняет SQL-запрос и возвращает результат
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Список словарей с результатами запроса
        """
        session = None
        try:
            session = self.get_session()
            result = session.execute(text(query), params or {})
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
                
        except SQLAlchemyError as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise
        finally:
            if session:
                session.close()
    
    def insert_records(self, table_name: str, records: List[Dict[str, Any]]) -> bool:
        """
        Вставляет записи в указанную таблицу
        
        Args:
            table_name: Имя таблицы
            records: Список записей для вставки
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        session = None
        try:
            session = self.get_session()
            for record in records:
                # Формирование SQL-запроса для вставки
                columns = ", ".join(record.keys())
                placeholders = ", ".join([f":{key}" for key in record.keys()])
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
                session.execute(text(query), record)
            
            session.commit()
            logger.info(f"Вставлено {len(records)} записей в таблицу {table_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при вставке записей в таблицу {table_name}: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def update_or_insert_records(self, table_name: str, records: List[Dict[str, Any]], 
                                id_field: str = "id") -> bool:
        """
        Обновляет или вставляет записи в указанную таблицу
        
        Args:
            table_name: Имя таблицы
            records: Список записей для вставки/обновления
            id_field: Имя поля ID
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        session = None
        try:
            session = self.get_session()
            for record in records:
                # Special handling for cost_item_materials table with unique constraint
                if table_name == "cost_item_materials":
                    # Check for existing record by unique constraint (work_id, cost_item_id, material_id)
                    work_id = record.get("work_id")
                    cost_item_id = record.get("cost_item_id")
                    material_id = record.get("material_id")
                    
                    if work_id and cost_item_id:
                        # Build check query based on available fields
                        if material_id:
                            check_query = """
                                SELECT id FROM cost_item_materials 
                                WHERE work_id = :work_id AND cost_item_id = :cost_item_id AND material_id = :material_id
                            """
                            check_params = {"work_id": work_id, "cost_item_id": cost_item_id, "material_id": material_id}
                        else:
                            check_query = """
                                SELECT id FROM cost_item_materials 
                                WHERE work_id = :work_id AND cost_item_id = :cost_item_id AND material_id IS NULL
                            """
                            check_params = {"work_id": work_id, "cost_item_id": cost_item_id}
                        
                        result = session.execute(text(check_query), check_params)
                        existing_row = result.fetchone()
                        
                        if existing_row:
                            # Update existing record
                            existing_id = existing_row[0]
                            set_clause = ", ".join([f"{key} = :{key}" for key in record.keys() if key != "id"])
                            update_query = f"UPDATE {table_name} SET {set_clause} WHERE id = :existing_id"
                            update_params = record.copy()
                            update_params["existing_id"] = existing_id
                            session.execute(text(update_query), update_params)
                            continue
                        else:
                            # Insert new record
                            columns = ", ".join(record.keys())
                            placeholders = ", ".join([f":{key}" for key in record.keys()])
                            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                            session.execute(text(insert_query), record)
                            continue
                
                # Default handling for other tables
                if id_field in record and record[id_field] is not None:
                    # Проверяем, существует ли запись с таким ID
                    check_query = f"SELECT COUNT(*) FROM {table_name} WHERE {id_field} = :id"
                    result = session.execute(text(check_query), {"id": record[id_field]})
                    count = result.scalar()
                    exists = count > 0
                    
                    if exists:
                        # Обновление существующей записи
                        set_clause = ", ".join([f"{key} = :{key}" for key in record.keys() if key != id_field])
                        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {id_field} = :id"
                        session.execute(text(update_query), record)
                    else:
                        # Вставка новой записи
                        columns = ", ".join(record.keys())
                        placeholders = ", ".join([f":{key}" for key in record.keys()])
                        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        session.execute(text(insert_query), record)
                else:
                    # Вставка новой записи без ID
                    columns = ", ".join(record.keys())
                    placeholders = ", ".join([f":{key}" for key in record.keys()])
                    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    session.execute(text(insert_query), record)
            
            session.commit()
            logger.info(f"Обработано {len(records)} записей для таблицы {table_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обработке записей для таблицы {table_name}: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def delete_records_by_ids(self, table_name: str, ids: List[Any], 
                              id_field: str = "id") -> bool:
        """
        Удаляет записи из таблицы по списку ID
        
        Args:
            table_name: Имя таблицы
            ids: Список ID для удаления
            id_field: Имя поля ID
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        session = None
        try:
            session = self.get_session()
            if not ids:
                return True
            
            # Формирование запроса на удаление
            placeholders = ", ".join([f":id_{i}" for i in range(len(ids))])
            params = {f"id_{i}": id for i, id in enumerate(ids)}
            delete_query = f"DELETE FROM {table_name} WHERE {id_field} IN ({placeholders})"
            
            session.execute(text(delete_query), params)
            session.commit()
            
            logger.info(f"Удалено {len(ids)} записей из таблицы {table_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записей из таблицы {table_name}: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получает информацию о столбцах таблицы
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Список словарей с информацией о столбцах
        """
        session = None
        try:
            # Для SQLite
            session = self.get_session()
            query = f"PRAGMA table_info({table_name})"
            result = session.execute(text(query))
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении информации о таблице {table_name}: {e}")
            return []
        finally:
            if session:
                session.close()
    
    def table_exists(self, table_name: str) -> bool:
        """
        Проверяет существование таблицы
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            True если таблица существует, False в противном случае
        """
        session = None
        try:
            # Для SQLite
            session = self.get_session()
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
            result = session.execute(text(query), {"table_name": table_name})
            rows = result.fetchall()
            return len(rows) > 0
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при проверке существования таблицы {table_name}: {e}")
            return False
        finally:
            if session:
                session.close()