"""
Pagination service for API endpoints
Implements efficient pagination logic with configurable page sizes
"""
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PaginationResult:
    """Pagination result with metadata"""
    items: List[Any]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


@dataclass
class PaginationConfig:
    """Pagination configuration"""
    default_page_size: int = 50
    max_page_size: int = 1000
    min_page_size: int = 1


class PaginationService:
    """Service for handling API pagination"""
    
    def __init__(self, config: Optional[PaginationConfig] = None):
        self.config = config or PaginationConfig()
    
    def validate_pagination_params(self, page: int, page_size: int) -> Tuple[int, int]:
        """Validate and normalize pagination parameters"""
        # Validate page
        if page < 1:
            page = 1
        
        # Validate page_size
        if page_size < self.config.min_page_size:
            page_size = self.config.default_page_size
        elif page_size > self.config.max_page_size:
            page_size = self.config.max_page_size
        
        return page, page_size
    
    def calculate_offset(self, page: int, page_size: int) -> int:
        """Calculate database offset for pagination"""
        return (page - 1) * page_size
    
    def create_pagination_result(
        self, 
        items: List[Any], 
        page: int, 
        page_size: int, 
        total_items: int
    ) -> PaginationResult:
        """Create pagination result with metadata"""
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        
        return PaginationResult(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    def apply_pagination_to_query(
        self, 
        base_query: str, 
        params: List[Any], 
        page: int, 
        page_size: int
    ) -> Tuple[str, List[Any]]:
        """Apply LIMIT and OFFSET to SQL query"""
        page, page_size = self.validate_pagination_params(page, page_size)
        offset = self.calculate_offset(page, page_size)
        
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        paginated_params = params + [page_size, offset]
        
        return paginated_query, paginated_params
    
    def get_count_query(self, base_query: str) -> str:
        """Convert a SELECT query to a COUNT query"""
        # Simple approach: wrap the base query in a COUNT
        # This works for most cases but might need refinement for complex queries
        if "ORDER BY" in base_query.upper():
            # Remove ORDER BY clause for count query as it's not needed
            base_query = base_query.split("ORDER BY")[0].strip()
        
        return f"SELECT COUNT(*) as count FROM ({base_query}) as count_subquery"
    
    def paginate_query_result(
        self,
        db_connection,
        base_query: str,
        params: List[Any],
        page: int,
        page_size: int,
        count_query: Optional[str] = None
    ) -> PaginationResult:
        """Execute paginated query and return result with metadata"""
        cursor = db_connection.cursor()
        
        # Get total count
        if count_query:
            cursor.execute(count_query, params)
        else:
            cursor.execute(self.get_count_query(base_query), params)
        
        total_items = cursor.fetchone()['count']
        
        # Get paginated items
        paginated_query, paginated_params = self.apply_pagination_to_query(
            base_query, params, page, page_size
        )
        cursor.execute(paginated_query, paginated_params)
        items = [dict(row) for row in cursor.fetchall()]
        
        return self.create_pagination_result(items, page, page_size, total_items)
    
    def create_pagination_info_dict(self, result: PaginationResult) -> Dict[str, Any]:
        """Create pagination info dictionary for API response"""
        return {
            "page": result.page,
            "page_size": result.page_size,
            "total_items": result.total_items,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_previous": result.has_previous
        }