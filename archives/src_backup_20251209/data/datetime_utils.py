"""Datetime handling utilities for multi-backend database support

This module provides utilities for consistent datetime handling across
SQLite, PostgreSQL, and Microsoft SQL Server backends.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from datetime import datetime, date, timezone
from typing import Optional, Union
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Query


class DateTimeConverter:
    """Utilities for converting datetime objects between timezone-aware and naive formats"""
    
    @staticmethod
    def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Convert datetime to UTC timezone-aware datetime
        
        Args:
            dt: Datetime object (timezone-aware or naive)
            
        Returns:
            UTC timezone-aware datetime, or None if input is None
            
        Note:
            Naive datetimes are assumed to be in UTC
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            # Naive datetime - assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Already timezone-aware - convert to UTC
            return dt.astimezone(timezone.utc)
    
    @staticmethod
    def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Convert datetime to naive UTC datetime (for database storage)
        
        Args:
            dt: Datetime object (timezone-aware or naive)
            
        Returns:
            Naive UTC datetime, or None if input is None
            
        Note:
            This is useful for databases that don't support timezone-aware datetimes
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            # Already naive - assume it's UTC
            return dt
        else:
            # Convert to UTC and remove timezone info
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    @staticmethod
    def from_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Convert naive UTC datetime to timezone-aware datetime
        
        Args:
            dt: Naive datetime (assumed to be UTC)
            
        Returns:
            UTC timezone-aware datetime, or None if input is None
        """
        if dt is None:
            return None
        
        if dt.tzinfo is not None:
            # Already timezone-aware
            return dt
        else:
            # Add UTC timezone info
            return dt.replace(tzinfo=timezone.utc)
    
    @staticmethod
    def ensure_naive(dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is naive (remove timezone info)
        
        Args:
            dt: Datetime object (timezone-aware or naive)
            
        Returns:
            Naive datetime, or None if input is None
            
        Note:
            If datetime is timezone-aware, it's converted to UTC first
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            return dt
        else:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    @staticmethod
    def ensure_aware(dt: Optional[datetime], tz: timezone = timezone.utc) -> Optional[datetime]:
        """Ensure datetime is timezone-aware
        
        Args:
            dt: Datetime object (timezone-aware or naive)
            tz: Timezone to use for naive datetimes (default: UTC)
            
        Returns:
            Timezone-aware datetime, or None if input is None
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        else:
            return dt
    
    @staticmethod
    def date_to_datetime(d: Optional[date]) -> Optional[datetime]:
        """Convert date to datetime at midnight UTC
        
        Args:
            d: Date object
            
        Returns:
            Datetime at midnight UTC, or None if input is None
        """
        if d is None:
            return None
        
        return datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    @staticmethod
    def datetime_to_date(dt: Optional[datetime]) -> Optional[date]:
        """Convert datetime to date
        
        Args:
            dt: Datetime object
            
        Returns:
            Date object, or None if input is None
        """
        if dt is None:
            return None
        
        return dt.date()


class DateQueryHelper:
    """Helper methods for date comparison queries across different backends"""
    
    @staticmethod
    def date_equals(column, target_date: Union[date, datetime]) -> any:
        """Create a query condition for date equality
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            target_date: Date or datetime to compare against
            
        Returns:
            SQLAlchemy query condition
            
        Example:
            query.filter(DateQueryHelper.date_equals(Estimate.date, date(2024, 1, 1)))
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        return func.date(column) == target_date
    
    @staticmethod
    def date_greater_than(column, target_date: Union[date, datetime]) -> any:
        """Create a query condition for date greater than
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            target_date: Date or datetime to compare against
            
        Returns:
            SQLAlchemy query condition
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        return func.date(column) > target_date
    
    @staticmethod
    def date_greater_or_equal(column, target_date: Union[date, datetime]) -> any:
        """Create a query condition for date greater than or equal
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            target_date: Date or datetime to compare against
            
        Returns:
            SQLAlchemy query condition
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        return func.date(column) >= target_date
    
    @staticmethod
    def date_less_than(column, target_date: Union[date, datetime]) -> any:
        """Create a query condition for date less than
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            target_date: Date or datetime to compare against
            
        Returns:
            SQLAlchemy query condition
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        return func.date(column) < target_date
    
    @staticmethod
    def date_less_or_equal(column, target_date: Union[date, datetime]) -> any:
        """Create a query condition for date less than or equal
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            target_date: Date or datetime to compare against
            
        Returns:
            SQLAlchemy query condition
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        return func.date(column) <= target_date
    
    @staticmethod
    def date_between(column, start_date: Union[date, datetime], 
                     end_date: Union[date, datetime]) -> any:
        """Create a query condition for date between two dates (inclusive)
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            SQLAlchemy query condition
        """
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        return and_(
            func.date(column) >= start_date,
            func.date(column) <= end_date
        )
    
    @staticmethod
    def date_in_month(column, year: int, month: int) -> any:
        """Create a query condition for dates in a specific month
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            SQLAlchemy query condition
        """
        # Calculate first and last day of month
        from calendar import monthrange
        
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        
        return DateQueryHelper.date_between(column, first_day, last_day)
    
    @staticmethod
    def date_in_year(column, year: int) -> any:
        """Create a query condition for dates in a specific year
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            year: Year (e.g., 2024)
            
        Returns:
            SQLAlchemy query condition
        """
        first_day = date(year, 1, 1)
        last_day = date(year, 12, 31)
        
        return DateQueryHelper.date_between(column, first_day, last_day)
    
    @staticmethod
    def datetime_between(column, start_dt: datetime, end_dt: datetime) -> any:
        """Create a query condition for datetime between two datetimes (inclusive)
        
        Args:
            column: SQLAlchemy column (DateTime type)
            start_dt: Start datetime (inclusive)
            end_dt: End datetime (inclusive)
            
        Returns:
            SQLAlchemy query condition
            
        Note:
            Handles both timezone-aware and naive datetimes consistently
        """
        # Ensure both datetimes are naive for consistent comparison
        start_naive = DateTimeConverter.ensure_naive(start_dt)
        end_naive = DateTimeConverter.ensure_naive(end_dt)
        
        return and_(
            column >= start_naive,
            column <= end_naive
        )
    
    @staticmethod
    def extract_year(column) -> any:
        """Extract year from date/datetime column
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            
        Returns:
            SQLAlchemy expression for year extraction
        """
        return func.extract('year', column)
    
    @staticmethod
    def extract_month(column) -> any:
        """Extract month from date/datetime column
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            
        Returns:
            SQLAlchemy expression for month extraction
        """
        return func.extract('month', column)
    
    @staticmethod
    def extract_day(column) -> any:
        """Extract day from date/datetime column
        
        Args:
            column: SQLAlchemy column (Date or DateTime type)
            
        Returns:
            SQLAlchemy expression for day extraction
        """
        return func.extract('day', column)
