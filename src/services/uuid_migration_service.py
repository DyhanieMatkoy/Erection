"""
UUID Migration Service

This service handles the migration of works table from integer IDs to UUIDs,
including generation of UUIDs for existing records and updating all foreign
key relationships.
"""

import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy import text, inspect, MetaData, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..data.database_manager import DatabaseManager
from ..data.models.sqlalchemy_models import Work, Base


class UUIDMigrationService:
    """Service for managing UUID migration of works table"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
    def generate_uuid_for_work(self, work_id: int) -> str:
        """Generate a UUID for a specific work record"""
        # Use deterministic UUID generation based on work ID for consistency
        # This ensures the same work always gets the same UUID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        work_uuid = uuid.uuid5(namespace, f"work_{work_id}")
        return str(work_uuid)
    
    def validate_uuid_format(self, uuid_string: str) -> bool:
        """Validate that a string is a properly formatted UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def check_uuid_uniqueness(self, session: Session, uuid_string: str, exclude_work_id: Optional[int] = None) -> bool:
        """Check if a UUID is unique in the works table"""
        query = session.query(Work).filter(Work.uuid == uuid_string)
        if exclude_work_id:
            query = query.filter(Work.id != exclude_work_id)
        
        return query.count() == 0
    
    def assign_uuids_to_existing_works(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Assign UUIDs to all existing works that don't have them"""
        session = self.db_manager.get_session()
        results = {
            'total_processed': 0,
            'uuids_assigned': 0,
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Find works without UUIDs
            works_without_uuid = session.query(Work).filter(
                (Work.uuid == None) | (Work.uuid == '')
            ).all()
            
            results['total_processed'] = len(works_without_uuid)
            self.logger.info(f"Found {len(works_without_uuid)} works without UUIDs")
            
            # Process in batches
            for i in range(0, len(works_without_uuid), batch_size):
                batch = works_without_uuid[i:i + batch_size]
                
                for work in batch:
                    try:
                        # Generate UUID
                        new_uuid = self.generate_uuid_for_work(work.id)
                        
                        # Check uniqueness
                        if not self.check_uuid_uniqueness(session, new_uuid, work.id):
                            # If collision, use random UUID
                            new_uuid = str(uuid.uuid4())
                            self.logger.warning(f"UUID collision for work {work.id}, using random UUID")
                        
                        # Assign UUID
                        work.uuid = new_uuid
                        results['uuids_assigned'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error assigning UUID to work {work.id}: {str(e)}"
                        self.logger.error(error_msg)
                        results['errors'].append(error_msg)
                
                # Commit batch
                try:
                    session.commit()
                    self.logger.info(f"Committed batch {i//batch_size + 1}, processed {min(i + batch_size, len(works_without_uuid))} works")
                except Exception as e:
                    session.rollback()
                    error_msg = f"Error committing batch {i//batch_size + 1}: {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
        except Exception as e:
            session.rollback()
            error_msg = f"Critical error during UUID assignment: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            session.close()
        
        return results
    
    def get_foreign_key_tables(self) -> List[Dict[str, Any]]:
        """Get all tables that have foreign keys to the works table"""
        metadata = MetaData()
        metadata.reflect(bind=self.db_manager.get_engine())
        
        fk_tables = []
        
        for table_name, table in metadata.tables.items():
            for column in table.columns:
                for fk in column.foreign_keys:
                    if fk.column.table.name == 'works':
                        fk_tables.append({
                            'table_name': table_name,
                            'column_name': column.name,
                            'constraint_name': fk.constraint.name if fk.constraint else None,
                            'is_nullable': column.nullable
                        })
        
        return fk_tables
    
    def add_uuid_columns_to_fk_tables(self) -> Dict[str, Any]:
        """Add UUID columns to all tables that reference works"""
        session = self.db_manager.get_session()
        results = {
            'tables_updated': [],
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            fk_tables = self.get_foreign_key_tables()
            
            for fk_info in fk_tables:
                table_name = fk_info['table_name']
                column_name = fk_info['column_name']
                
                # Skip if this is the works table itself (self-reference)
                if table_name == 'works':
                    continue
                
                try:
                    # Add UUID column for the foreign key
                    uuid_column_name = column_name.replace('_id', '_uuid')
                    
                    # Check if column already exists
                    inspector = inspect(self.db_manager.get_engine())
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    
                    if uuid_column_name not in columns:
                        # Add the UUID column
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {uuid_column_name} VARCHAR(36)"
                        session.execute(text(alter_sql))
                        
                        # Add index for performance
                        index_sql = f"CREATE INDEX idx_{table_name}_{uuid_column_name} ON {table_name}({uuid_column_name})"
                        try:
                            session.execute(text(index_sql))
                        except Exception as e:
                            # Index creation might fail if it already exists, that's OK
                            self.logger.warning(f"Could not create index for {table_name}.{uuid_column_name}: {e}")
                        
                        results['tables_updated'].append(f"{table_name}.{uuid_column_name}")
                        self.logger.info(f"Added UUID column {uuid_column_name} to table {table_name}")
                    
                except Exception as e:
                    error_msg = f"Error adding UUID column to {table_name}: {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            error_msg = f"Critical error adding UUID columns: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            session.close()
        
        return results
    
    def update_foreign_key_uuids(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Update all foreign key UUID columns with corresponding work UUIDs"""
        session = self.db_manager.get_session()
        results = {
            'tables_processed': [],
            'total_records_updated': 0,
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            fk_tables = self.get_foreign_key_tables()
            
            for fk_info in fk_tables:
                table_name = fk_info['table_name']
                column_name = fk_info['column_name']
                
                # Skip self-references for now
                if table_name == 'works':
                    continue
                
                try:
                    uuid_column_name = column_name.replace('_id', '_uuid')
                    
                    # Update UUID values based on work IDs
                    update_sql = f"""
                    UPDATE {table_name} 
                    SET {uuid_column_name} = works.uuid 
                    FROM works 
                    WHERE {table_name}.{column_name} = works.id 
                    AND {table_name}.{column_name} IS NOT NULL
                    """
                    
                    result = session.execute(text(update_sql))
                    updated_count = result.rowcount
                    
                    results['tables_processed'].append({
                        'table': table_name,
                        'column': uuid_column_name,
                        'records_updated': updated_count
                    })
                    results['total_records_updated'] += updated_count
                    
                    self.logger.info(f"Updated {updated_count} records in {table_name}.{uuid_column_name}")
                    
                except Exception as e:
                    error_msg = f"Error updating UUIDs in {table_name}: {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            error_msg = f"Critical error updating foreign key UUIDs: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            session.close()
        
        return results
    
    def validate_uuid_migration(self) -> Dict[str, Any]:
        """Validate that UUID migration was successful"""
        session = self.db_manager.get_session()
        validation_results = {
            'works_without_uuid': 0,
            'duplicate_uuids': 0,
            'orphaned_fk_uuids': [],
            'missing_fk_uuids': [],
            'validation_passed': False,
            'errors': []
        }
        
        try:
            # Check for works without UUIDs
            works_without_uuid = session.query(Work).filter(
                (Work.uuid == None) | (Work.uuid == '')
            ).count()
            validation_results['works_without_uuid'] = works_without_uuid
            
            # Check for duplicate UUIDs
            duplicate_uuids = session.execute(text("""
                SELECT uuid, COUNT(*) as count 
                FROM works 
                WHERE uuid IS NOT NULL AND uuid != ''
                GROUP BY uuid 
                HAVING COUNT(*) > 1
            """)).fetchall()
            validation_results['duplicate_uuids'] = len(duplicate_uuids)
            
            # Check foreign key UUID consistency
            fk_tables = self.get_foreign_key_tables()
            
            for fk_info in fk_tables:
                table_name = fk_info['table_name']
                column_name = fk_info['column_name']
                
                if table_name == 'works':
                    continue
                
                uuid_column_name = column_name.replace('_id', '_uuid')
                
                # Check for orphaned UUID references
                orphaned_sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE {uuid_column_name} IS NOT NULL 
                AND {uuid_column_name} NOT IN (SELECT uuid FROM works WHERE uuid IS NOT NULL)
                """
                
                try:
                    orphaned_count = session.execute(text(orphaned_sql)).scalar()
                    if orphaned_count > 0:
                        validation_results['orphaned_fk_uuids'].append({
                            'table': table_name,
                            'column': uuid_column_name,
                            'count': orphaned_count
                        })
                except Exception as e:
                    validation_results['errors'].append(f"Error checking orphaned UUIDs in {table_name}: {e}")
                
                # Check for missing UUID values where work_id exists
                missing_sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE {column_name} IS NOT NULL 
                AND ({uuid_column_name} IS NULL OR {uuid_column_name} = '')
                """
                
                try:
                    missing_count = session.execute(text(missing_sql)).scalar()
                    if missing_count > 0:
                        validation_results['missing_fk_uuids'].append({
                            'table': table_name,
                            'column': uuid_column_name,
                            'count': missing_count
                        })
                except Exception as e:
                    validation_results['errors'].append(f"Error checking missing UUIDs in {table_name}: {e}")
            
            # Determine if validation passed
            validation_results['validation_passed'] = (
                validation_results['works_without_uuid'] == 0 and
                validation_results['duplicate_uuids'] == 0 and
                len(validation_results['orphaned_fk_uuids']) == 0 and
                len(validation_results['missing_fk_uuids']) == 0 and
                len(validation_results['errors']) == 0
            )
            
        except Exception as e:
            validation_results['errors'].append(f"Critical validation error: {str(e)}")
        
        finally:
            session.close()
        
        return validation_results
    
    def perform_full_uuid_migration(self) -> Dict[str, Any]:
        """Perform complete UUID migration process"""
        migration_results = {
            'start_time': datetime.now(),
            'end_time': None,
            'phases_completed': [],
            'overall_success': False,
            'uuid_assignment': None,
            'column_addition': None,
            'fk_update': None,
            'validation': None,
            'errors': []
        }
        
        try:
            self.logger.info("Starting full UUID migration process")
            
            # Phase 1: Assign UUIDs to works
            self.logger.info("Phase 1: Assigning UUIDs to works")
            uuid_results = self.assign_uuids_to_existing_works()
            migration_results['uuid_assignment'] = uuid_results
            migration_results['phases_completed'].append('uuid_assignment')
            
            if uuid_results['errors']:
                migration_results['errors'].extend(uuid_results['errors'])
            
            # Phase 2: Add UUID columns to FK tables
            self.logger.info("Phase 2: Adding UUID columns to foreign key tables")
            column_results = self.add_uuid_columns_to_fk_tables()
            migration_results['column_addition'] = column_results
            migration_results['phases_completed'].append('column_addition')
            
            if column_results['errors']:
                migration_results['errors'].extend(column_results['errors'])
            
            # Phase 3: Update foreign key UUIDs
            self.logger.info("Phase 3: Updating foreign key UUID values")
            fk_results = self.update_foreign_key_uuids()
            migration_results['fk_update'] = fk_results
            migration_results['phases_completed'].append('fk_update')
            
            if fk_results['errors']:
                migration_results['errors'].extend(fk_results['errors'])
            
            # Phase 4: Validate migration
            self.logger.info("Phase 4: Validating UUID migration")
            validation_results = self.validate_uuid_migration()
            migration_results['validation'] = validation_results
            migration_results['phases_completed'].append('validation')
            
            if validation_results['errors']:
                migration_results['errors'].extend(validation_results['errors'])
            
            # Determine overall success
            migration_results['overall_success'] = (
                len(migration_results['errors']) == 0 and
                validation_results['validation_passed']
            )
            
            if migration_results['overall_success']:
                self.logger.info("UUID migration completed successfully")
            else:
                self.logger.error("UUID migration completed with errors")
            
        except Exception as e:
            error_msg = f"Critical error during UUID migration: {str(e)}"
            self.logger.error(error_msg)
            migration_results['errors'].append(error_msg)
        
        finally:
            migration_results['end_time'] = datetime.now()
        
        return migration_results