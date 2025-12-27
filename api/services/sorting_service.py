"""
Sorting service for API endpoints
Implements column sorting with validation and SQL generation
"""
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class SortDirection(Enum):
    """Sort direction enumeration"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortConfig:
    """Sort configuration for a column"""
    column: str
    direction: SortDirection
    data_type: str  # 'string', 'number', 'date', 'boolean'
    table_alias: Optional[str] = None


@dataclass
class SortableColumn:
    """Definition of a sortable column"""
    name: str
    data_type: str
    table_alias: Optional[str] = None
    sql_expression: Optional[str] = None  # Custom SQL expression for complex sorting


class SortingService:
    """Service for handling column sorting in API endpoints"""
    
    def __init__(self):
        # Define sortable columns for each table/endpoint
        self.sortable_columns = {
            'estimates': {
                'id': SortableColumn('id', 'number', 'e'),
                'number': SortableColumn('number', 'string', 'e'),
                'date': SortableColumn('date', 'date', 'e'),
                'customer_name': SortableColumn('name', 'string', 'c'),
                'object_name': SortableColumn('name', 'string', 'o'),
                'contractor_name': SortableColumn('name', 'string', 'org'),
                'responsible_name': SortableColumn('full_name', 'string', 'p'),
                'total_sum': SortableColumn('total_sum', 'number', 'e'),
                'total_labor': SortableColumn('total_labor', 'number', 'e'),
                'estimate_type': SortableColumn('estimate_type', 'string', 'e'),
                'created_at': SortableColumn('created_at', 'date', 'e'),
                'modified_at': SortableColumn('modified_at', 'date', 'e')
            },
            'daily_reports': {
                'id': SortableColumn('id', 'number', 'dr'),
                'date': SortableColumn('date', 'date', 'dr'),
                'estimate_number': SortableColumn('number', 'string', 'e'),
                'foreman_name': SortableColumn('full_name', 'string', 'p'),
                'created_at': SortableColumn('created_at', 'date', 'dr'),
                'modified_at': SortableColumn('modified_at', 'date', 'dr')
            },
            'timesheets': {
                'id': SortableColumn('id', 'number', 't'),
                'number': SortableColumn('number', 'string', 't'),
                'date': SortableColumn('date', 'date', 't'),
                'object_name': SortableColumn('name', 'string', 'o'),
                'estimate_number': SortableColumn('number', 'string', 'e'),
                'foreman_name': SortableColumn('full_name', 'string', 'p'),
                'month_year': SortableColumn('month_year', 'string', 't'),
                'created_at': SortableColumn('created_at', 'date', 't'),
                'modified_at': SortableColumn('modified_at', 'date', 't')
            }
        }
    
    def validate_sort_params(
        self, 
        table_name: str, 
        sort_by: str, 
        sort_order: str
    ) -> Tuple[bool, Optional[SortConfig], Optional[str]]:
        """Validate sort parameters and return sort config"""
        # Check if table is supported
        if table_name not in self.sortable_columns:
            return False, None, f"Sorting not supported for table: {table_name}"
        
        # Check if column is sortable
        if sort_by not in self.sortable_columns[table_name]:
            available_columns = list(self.sortable_columns[table_name].keys())
            return False, None, f"Column '{sort_by}' is not sortable. Available columns: {available_columns}"
        
        # Validate sort direction
        try:
            direction = SortDirection(sort_order.lower())
        except ValueError:
            return False, None, f"Invalid sort direction: {sort_order}. Use 'asc' or 'desc'"
        
        # Create sort config
        sortable_col = self.sortable_columns[table_name][sort_by]
        sort_config = SortConfig(
            column=sortable_col.name,
            direction=direction,
            data_type=sortable_col.data_type,
            table_alias=sortable_col.table_alias
        )
        
        return True, sort_config, None
    
    def get_sortable_columns(self, table_name: str) -> List[str]:
        """Get list of sortable columns for a table"""
        if table_name not in self.sortable_columns:
            return []
        return list(self.sortable_columns[table_name].keys())
    
    def build_order_by_clause(self, sort_config: SortConfig) -> str:
        """Build ORDER BY clause from sort configuration"""
        if sort_config.table_alias:
            column_ref = f"{sort_config.table_alias}.{sort_config.column}"
        else:
            column_ref = sort_config.column
        
        direction = sort_config.direction.value.upper()
        
        # Handle different data types for proper sorting
        if sort_config.data_type == 'number':
            # Ensure numeric sorting
            return f"CAST({column_ref} AS REAL) {direction}"
        elif sort_config.data_type == 'date':
            # Ensure date sorting
            return f"datetime({column_ref}) {direction}"
        else:
            # String sorting (default)
            return f"{column_ref} COLLATE NOCASE {direction}"
    
    def apply_sorting_to_query(
        self, 
        base_query: str, 
        table_name: str, 
        sort_by: str, 
        sort_order: str
    ) -> Tuple[str, Optional[str]]:
        """Apply sorting to SQL query"""
        is_valid, sort_config, error = self.validate_sort_params(table_name, sort_by, sort_order)
        
        if not is_valid:
            return base_query, error
        
        # Remove existing ORDER BY clause if present
        query_upper = base_query.upper()
        if "ORDER BY" in query_upper:
            base_query = base_query[:query_upper.rfind("ORDER BY")].strip()
        
        # Add new ORDER BY clause
        order_by_clause = self.build_order_by_clause(sort_config)
        sorted_query = f"{base_query} ORDER BY {order_by_clause}"
        
        return sorted_query, None
    
    def get_default_sort(self, table_name: str) -> Tuple[str, str]:
        """Get default sort column and direction for a table"""
        defaults = {
            'estimates': ('date', 'desc'),
            'daily_reports': ('date', 'desc'),
            'timesheets': ('date', 'desc')
        }
        return defaults.get(table_name, ('id', 'desc'))
    
    def create_multi_column_sort(
        self, 
        table_name: str, 
        sort_configs: List[Tuple[str, str]]
    ) -> Tuple[str, Optional[str]]:
        """Create ORDER BY clause for multiple columns"""
        if not sort_configs:
            return "", None
        
        order_clauses = []
        for sort_by, sort_order in sort_configs:
            is_valid, sort_config, error = self.validate_sort_params(table_name, sort_by, sort_order)
            if not is_valid:
                return "", error
            
            order_clauses.append(self.build_order_by_clause(sort_config))
        
        return f"ORDER BY {', '.join(order_clauses)}", None
    
    def add_sortable_column(
        self, 
        table_name: str, 
        column_key: str, 
        sortable_column: SortableColumn
    ):
        """Add a new sortable column configuration"""
        if table_name not in self.sortable_columns:
            self.sortable_columns[table_name] = {}
        
        self.sortable_columns[table_name][column_key] = sortable_column
    
    def remove_sortable_column(self, table_name: str, column_key: str):
        """Remove a sortable column configuration"""
        if table_name in self.sortable_columns and column_key in self.sortable_columns[table_name]:
            del self.sortable_columns[table_name][column_key]