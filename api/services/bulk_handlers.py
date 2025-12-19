from typing import List, Dict, Any
from api.services.bulk_operation_service import BulkOperationHandler, BulkOperationResult, bulk_operation_service
import sqlite3
import sys
import os

class BulkDeleteHandler(BulkOperationHandler):
    """Handler for bulk delete (mark for deletion) operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        
    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        db = context.get('db')
        if not db:
            return BulkOperationResult(
                success=False,
                message="Database connection not provided in context",
                processed=0,
                errors=["Database connection missing"]
            )
            
        cursor = db.cursor()
        processed = 0
        errors = []
        
        # Validate table name to prevent SQL injection
        allowed_tables = ['counterparties', 'objects', 'works', 'persons', 'organizations', 'units', 'estimates', 'timesheets', 'daily_reports']
        if self.table_name not in allowed_tables:
             return BulkOperationResult(
                success=False,
                message=f"Invalid table name: {self.table_name}",
                processed=0,
                errors=["Security violation: Invalid table name"]
            )
            
        for item_id in ids:
            try:
                # We use parameterized query for ID, but table name is interpolated (validated above)
                query = f"UPDATE {self.table_name} SET marked_for_deletion = 1 WHERE id = ?"
                cursor.execute(query, (item_id,))
                
                if cursor.rowcount > 0:
                    processed += 1
                else:
                    errors.append(f"ID {item_id}: Item not found or update failed")
                    
            except Exception as e:
                errors.append(f"ID {item_id}: {str(e)}")
        
        try:
            db.commit()
        except Exception as e:
            return BulkOperationResult(
                success=False,
                message="Transaction commit failed",
                processed=0,
                errors=[str(e)]
            )
            
        return BulkOperationResult(
            success=True,
            message=f"Marked {processed} of {len(ids)} items for deletion",
            processed=processed,
            errors=errors
        )

class BulkPermanentDeleteHandler(BulkOperationHandler):
    """Handler for permanent delete operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name

    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        db = context.get('db')
        if not db:
             return BulkOperationResult(
                success=False,
                message="Database connection missing",
                processed=0,
                errors=["Database connection missing"]
            )

        cursor = db.cursor()
        processed = 0
        errors = []
        
        allowed_tables = ['counterparties', 'objects', 'works', 'persons', 'organizations', 'units', 'estimates', 'timesheets', 'daily_reports']
        if self.table_name not in allowed_tables:
             return BulkOperationResult(
                success=False,
                message=f"Invalid table name: {self.table_name}",
                processed=0,
                errors=["Security violation: Invalid table name"]
            )

        if ids:
            for item_id in ids:
                try:
                    query = f"DELETE FROM {self.table_name} WHERE id = ?"
                    cursor.execute(query, (item_id,))
                    if cursor.rowcount > 0:
                        processed += 1
                    else:
                        errors.append(f"ID {item_id}: Not found")
                except Exception as e:
                    errors.append(f"ID {item_id}: {str(e)}")
        
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {processed} items",
            processed=processed,
            errors=errors
        )

class BulkDocumentDeleteHandler(BulkDeleteHandler):
    """Handler for bulk delete of documents (checks is_posted)"""
    
    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        db = context.get('db')
        if not db:
            return BulkOperationResult(success=False, message="No DB", processed=0, errors=["No DB"])
            
        cursor = db.cursor()
        processed = 0
        errors = []
        
        if self.table_name not in ['estimates', 'timesheets', 'daily_reports']:
             return BulkOperationResult(success=False, message="Invalid table", processed=0, errors=["Invalid table"])

        for item_id in ids:
            try:
                # Check is_posted
                cursor.execute(f"SELECT is_posted, number FROM {self.table_name} WHERE id = ?", (item_id,))
                row = cursor.fetchone()
                if not row:
                    errors.append(f"ID {item_id}: Not found")
                    continue
                
                # Check column name/index for is_posted. Assuming it exists.
                # In sqlite3 row is dict-like if configured, or tuple.
                # If dict factory is used (common in this project), row['is_posted'].
                # If tuple, we need index.
                # Let's assume dict access if row is not tuple, or handle both.
                is_posted = False
                number = "Unknown"
                
                if isinstance(row, dict) or hasattr(row, 'keys'):
                    is_posted = row['is_posted']
                    number = row.get('number', str(item_id))
                elif isinstance(row, sqlite3.Row):
                    is_posted = row['is_posted']
                    number = row['number']
                else:
                    # Fallback for tuple
                    # SELECT id, number, is_posted -> 0, 1, 2
                    number = row[1]
                    is_posted = row[2]

                if is_posted:
                    errors.append(f"Document {number} is posted, cannot delete")
                    continue

                # Delete (Mark)
                cursor.execute(f"UPDATE {self.table_name} SET marked_for_deletion = 1, modified_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
                processed += 1
                
            except Exception as e:
                errors.append(f"ID {item_id}: {str(e)}")
        
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Marked {processed} of {len(ids)} documents for deletion",
            processed=processed,
            errors=errors
        )

class BulkPostHandler(BulkOperationHandler):
    """Handler for bulk posting documents"""
    
    def __init__(self, doc_type: str):
        self.doc_type = doc_type # 'estimate', 'daily_report', 'timesheet'

    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        # We need DocumentPostingService.
        # It is in src/services/document_posting_service.py
        # Import lazily to avoid circular deps or path issues
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from src.services.document_posting_service import DocumentPostingService
        except ImportError:
            return BulkOperationResult(success=False, message="Posting service not found", processed=0, errors=["Service missing"])

        posting_service = DocumentPostingService()
        processed = 0
        errors = []
        
        for item_id in ids:
            try:
                success = False
                error = ""
                if self.doc_type == 'estimate':
                    success, error = posting_service.post_estimate(item_id)
                elif self.doc_type == 'daily_report':
                    success, error = posting_service.post_daily_report(item_id)
                elif self.doc_type == 'timesheet':
                    success, error = posting_service.post_timesheet(item_id)
                else:
                    error = f"Unknown document type: {self.doc_type}"
                
                if success:
                    processed += 1
                else:
                    errors.append(f"ID {item_id}: {error}")
            except Exception as e:
                errors.append(f"ID {item_id}: {str(e)}")
        
        return BulkOperationResult(
            success=True,
            message=f"Posted {processed} of {len(ids)} documents",
            processed=processed,
            errors=errors
        )

class BulkUnpostHandler(BulkOperationHandler):
    """Handler for bulk unposting documents"""
    
    def __init__(self, doc_type: str):
        self.doc_type = doc_type

    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from src.services.document_posting_service import DocumentPostingService
        except ImportError:
            return BulkOperationResult(success=False, message="Posting service not found", processed=0, errors=["Service missing"])

        posting_service = DocumentPostingService()
        processed = 0
        errors = []
        
        for item_id in ids:
            try:
                success = False
                error = ""
                if self.doc_type == 'estimate':
                    success, error = posting_service.unpost_estimate(item_id)
                elif self.doc_type == 'daily_report':
                    success, error = posting_service.unpost_daily_report(item_id)
                elif self.doc_type == 'timesheet':
                    success, error = posting_service.unpost_timesheet(item_id)
                else:
                    error = f"Unknown document type: {self.doc_type}"
                
                if success:
                    processed += 1
                else:
                    errors.append(f"ID {item_id}: {error}")
            except Exception as e:
                errors.append(f"ID {item_id}: {str(e)}")
        
        return BulkOperationResult(
            success=True,
            message=f"Unposted {processed} of {len(ids)} documents",
            processed=processed,
            errors=errors
        )

def register_default_handlers():
    """Register default bulk operation handlers"""
    # Delete (Mark for deletion) handlers
    bulk_operation_service.register_handler('counterparties:delete', BulkDeleteHandler('counterparties'))
    bulk_operation_service.register_handler('objects:delete', BulkDeleteHandler('objects'))
    bulk_operation_service.register_handler('works:delete', BulkDeleteHandler('works'))
    bulk_operation_service.register_handler('persons:delete', BulkDeleteHandler('persons'))
    bulk_operation_service.register_handler('organizations:delete', BulkDeleteHandler('organizations'))
    
    # Document Delete handlers
    bulk_operation_service.register_handler('estimates:delete', BulkDocumentDeleteHandler('estimates'))
    bulk_operation_service.register_handler('daily_reports:delete', BulkDocumentDeleteHandler('daily_reports'))
    bulk_operation_service.register_handler('timesheets:delete', BulkDocumentDeleteHandler('timesheets'))

    # Permanent delete handlers
    bulk_operation_service.register_handler('counterparties:permanent_delete', BulkPermanentDeleteHandler('counterparties'))
    bulk_operation_service.register_handler('objects:permanent_delete', BulkPermanentDeleteHandler('objects'))
    bulk_operation_service.register_handler('works:permanent_delete', BulkPermanentDeleteHandler('works'))
    bulk_operation_service.register_handler('persons:permanent_delete', BulkPermanentDeleteHandler('persons'))
    bulk_operation_service.register_handler('organizations:permanent_delete', BulkPermanentDeleteHandler('organizations'))
    
    # Post/Unpost handlers
    bulk_operation_service.register_handler('estimates:post', BulkPostHandler('estimate'))
    bulk_operation_service.register_handler('daily_reports:post', BulkPostHandler('daily_report'))
    bulk_operation_service.register_handler('timesheets:post', BulkPostHandler('timesheet'))
    
    bulk_operation_service.register_handler('estimates:unpost', BulkUnpostHandler('estimate'))
    bulk_operation_service.register_handler('daily_reports:unpost', BulkUnpostHandler('daily_report'))
    bulk_operation_service.register_handler('timesheets:unpost', BulkUnpostHandler('timesheet'))
