from typing import List, Dict, Any, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DataService:
    """
    Service for fetching, filtering, sorting, and paginating document data.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_documents(
        self,
        model_class: Type,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = 'asc',
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        Get documents with filtering, sorting, and pagination.
        
        Args:
            model_class: SQLAlchemy model class
            page: Page number (1-based)
            page_size: Number of records per page
            sort_by: Column name to sort by
            sort_order: 'asc' or 'desc'
            filters: Dictionary of field: value or field: {op: value}
            date_range: Dictionary with 'start' and 'end' keys (optional)
            include_deleted: Whether to include marked for deletion records
            
        Returns:
            Dict with 'items', 'total', 'page', 'pages'
        """
        query = self.db.query(model_class)
        
        # Apply Soft Delete Filter (exclude deleted by default)
        if not include_deleted and hasattr(model_class, 'marked_for_deletion'):
            query = query.filter(model_class.marked_for_deletion == False)
        
        # Apply Date Range Filter (Task 4.4)
        if date_range:
            date_field = getattr(model_class, 'date', None)
            if date_field:
                if date_range.get('start'):
                    query = query.filter(date_field >= date_range['start'])
                if date_range.get('end'):
                    query = query.filter(date_field <= date_range['end'])
        
        # Apply Filters (Task 4.3 - Real-time filtering)
        if filters:
            for field, value in filters.items():
                if not hasattr(model_class, field):
                    continue
                
                column = getattr(model_class, field)
                
                # Handle None values (NULL in SQL) - use IS NULL instead of = NULL
                if value is None:
                    query = query.filter(column.is_(None))
                # Simple exact match or LIKE for strings
                elif isinstance(value, str):
                    query = query.filter(column.ilike(f"%{value}%"))
                else:
                    query = query.filter(column == value)
        
        # Get total count before pagination (Task 4.1)
        total_count = query.count()
        
        # Apply Sorting
        if sort_by and hasattr(model_class, sort_by):
            column = getattr(model_class, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        
        # Apply Pagination (Task 4.1, 4.2)
        if page < 1: page = 1
        offset = (page - 1) * page_size
        
        # Optimization for large datasets: limit/offset
        query = query.limit(page_size).offset(offset)
        
        items = query.all()
        
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'size': page_size,
            'pages': total_pages
        }

    def export_documents(
        self,
        model_class: Type,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, Any]] = None,
        format: str = 'csv'
    ) -> Any:
        """
        Export documents based on current filters (Task 4.6).
        Returns data ready for file generation (simplified).
        """
        # Reuse get_documents logic but without pagination limit
        # Or re-build query to avoid overhead of creating full response dict
        
        # Simplified: fetch all with filters
        result = self.get_documents(
            model_class, 
            page=1, 
            page_size=100000, # Large limit for export
            filters=filters, 
            date_range=date_range
        )
        
        # In a real implementation, we would stream this or use pandas
        return result['items']

    def delete_documents(self, model_class: Type, ids: List[Any], soft: bool = True) -> int:
        """
        Delete documents by ID.
        If soft=True, sets marked_for_deletion=True.
        """
        if not ids:
            return 0
            
        try:
            query = self.db.query(model_class).filter(model_class.id.in_(ids))
            if soft and hasattr(model_class, 'marked_for_deletion'):
                # Soft delete
                count = query.update({model_class.marked_for_deletion: True}, synchronize_session=False)
            else:
                # Hard delete
                count = query.delete(synchronize_session=False)
            
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting documents: {e}")
            raise e

