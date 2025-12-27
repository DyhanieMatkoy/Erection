"""
Date filter service for API endpoints
Implements intelligent date filtering with default range calculation
"""
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class DateRange:
    """Date range configuration"""
    start_date: Optional[date]
    end_date: Optional[date]
    is_default: bool = False


@dataclass
class DateFilterConfig:
    """Date filter configuration for a table"""
    table_name: str
    date_column: str
    table_alias: Optional[str] = None
    default_range_days: int = 365  # Default to 1 year if no documents exist


class DateFilterService:
    """Service for handling intelligent date filtering"""
    
    def __init__(self):
        # Configure date filter settings for each table
        self.filter_configs = {
            'estimates': DateFilterConfig('estimates', 'date', 'e'),
            'daily_reports': DateFilterConfig('daily_reports', 'date', 'dr'),
            'timesheets': DateFilterConfig('timesheets', 'date', 't')
        }
    
    def get_default_date_range(self, db_connection, table_name: str) -> DateRange:
        """Calculate intelligent default date range based on last document"""
        if table_name not in self.filter_configs:
            # Fallback to last 365 days
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            return DateRange(start_date, end_date, is_default=True)
        
        config = self.filter_configs[table_name]
        cursor = db_connection.cursor()
        
        try:
            # Get the most recent document date
            if config.table_alias:
                query = f"""
                    SELECT MAX({config.table_alias}.{config.date_column}) as max_date
                    FROM {config.table_name} {config.table_alias}
                    WHERE {config.table_alias}.marked_for_deletion = 0
                """
            else:
                query = f"""
                    SELECT MAX({config.date_column}) as max_date
                    FROM {config.table_name}
                    WHERE marked_for_deletion = 0
                """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result['max_date']:
                # Parse the date (handle both string and date formats)
                if isinstance(result['max_date'], str):
                    max_date = datetime.fromisoformat(result['max_date']).date()
                else:
                    max_date = result['max_date']
                
                # Set start date to beginning of the day of the last document
                start_date = max_date
                # Set end date to infinity (None means no upper limit)
                end_date = None
                
                return DateRange(start_date, end_date, is_default=True)
            else:
                # No documents exist, use default range
                end_date = date.today()
                start_date = end_date - timedelta(days=config.default_range_days)
                return DateRange(start_date, end_date, is_default=True)
                
        except Exception as e:
            print(f"Error calculating default date range for {table_name}: {e}")
            # Fallback to default range
            end_date = date.today()
            start_date = end_date - timedelta(days=config.default_range_days)
            return DateRange(start_date, end_date, is_default=True)
    
    def validate_date_range(
        self, 
        start_date: Optional[date], 
        end_date: Optional[date]
    ) -> Tuple[bool, Optional[str]]:
        """Validate date range parameters"""
        if start_date and end_date:
            if start_date > end_date:
                return False, "Start date cannot be after end date"
        
        # Check for reasonable date limits (not too far in the past or future)
        min_date = date(1900, 1, 1)
        max_date = date(2100, 12, 31)
        
        if start_date and start_date < min_date:
            return False, f"Start date cannot be before {min_date}"
        
        if end_date and end_date > max_date:
            return False, f"End date cannot be after {max_date}"
        
        return True, None
    
    def apply_date_filter_to_query(
        self,
        base_query: str,
        table_name: str,
        start_date: Optional[date],
        end_date: Optional[date],
        where_clauses: list,
        params: list
    ) -> Tuple[str, list, list, Optional[str]]:
        """Apply date filter to SQL query"""
        if table_name not in self.filter_configs:
            return base_query, where_clauses, params, f"Date filtering not supported for table: {table_name}"
        
        # Validate date range
        is_valid, error = self.validate_date_range(start_date, end_date)
        if not is_valid:
            return base_query, where_clauses, params, error
        
        config = self.filter_configs[table_name]
        
        # Build date column reference
        if config.table_alias:
            date_column_ref = f"{config.table_alias}.{config.date_column}"
        else:
            date_column_ref = config.date_column
        
        # Add date filter clauses
        if start_date:
            where_clauses.append(f"{date_column_ref} >= ?")
            params.append(start_date.isoformat())
        
        if end_date:
            where_clauses.append(f"{date_column_ref} <= ?")
            params.append(end_date.isoformat())
        
        return base_query, where_clauses, params, None
    
    def get_date_range_summary(self, date_range: DateRange) -> str:
        """Get human-readable summary of date range"""
        if not date_range.start_date and not date_range.end_date:
            return "All dates"
        
        if date_range.start_date and not date_range.end_date:
            return f"From {date_range.start_date.strftime('%Y-%m-%d')} onwards"
        
        if not date_range.start_date and date_range.end_date:
            return f"Up to {date_range.end_date.strftime('%Y-%m-%d')}"
        
        if date_range.start_date and date_range.end_date:
            if date_range.start_date == date_range.end_date:
                return f"On {date_range.start_date.strftime('%Y-%m-%d')}"
            else:
                return f"From {date_range.start_date.strftime('%Y-%m-%d')} to {date_range.end_date.strftime('%Y-%m-%d')}"
        
        return "Invalid date range"
    
    def create_date_filter_info(
        self, 
        applied_range: DateRange, 
        default_range: DateRange
    ) -> Dict[str, Any]:
        """Create date filter information for API response"""
        return {
            "applied_range": {
                "start_date": applied_range.start_date.isoformat() if applied_range.start_date else None,
                "end_date": applied_range.end_date.isoformat() if applied_range.end_date else None,
                "is_default": applied_range.is_default,
                "summary": self.get_date_range_summary(applied_range)
            },
            "default_range": {
                "start_date": default_range.start_date.isoformat() if default_range.start_date else None,
                "end_date": default_range.end_date.isoformat() if default_range.end_date else None,
                "is_default": default_range.is_default,
                "summary": self.get_date_range_summary(default_range)
            }
        }
    
    def parse_date_param(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date parameter from string"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            try:
                # Try alternative formats
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
    
    def add_filter_config(self, table_name: str, config: DateFilterConfig):
        """Add date filter configuration for a table"""
        self.filter_configs[table_name] = config
    
    def get_filter_config(self, table_name: str) -> Optional[DateFilterConfig]:
        """Get date filter configuration for a table"""
        return self.filter_configs.get(table_name)