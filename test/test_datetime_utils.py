"""Tests for datetime handling utilities

This module tests datetime conversion and query helpers across
different database backends.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import create_engine, Column, Integer, Date, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from src.data.datetime_utils import DateTimeConverter, DateQueryHelper

# Create a test model
TestBase = declarative_base()


class DTTestModel(TestBase):
    """Test model with date and datetime columns"""
    __tablename__ = 'dt_test_model'
    
    id = Column(Integer, primary_key=True)
    test_date = Column(Date)
    test_datetime = Column(DateTime)


class TestDateTimeConverter:
    """Test DateTimeConverter utility methods"""
    
    def test_to_utc_with_naive_datetime(self):
        """Test converting naive datetime to UTC"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.to_utc(naive_dt)
        
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
    
    def test_to_utc_with_aware_datetime(self):
        """Test converting timezone-aware datetime to UTC"""
        # Create datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=est)
        result = DateTimeConverter.to_utc(aware_dt)
        
        assert result.tzinfo == timezone.utc
        # 10:30 EST = 15:30 UTC
        assert result.hour == 15
        assert result.minute == 30
    
    def test_to_utc_with_none(self):
        """Test to_utc with None input"""
        result = DateTimeConverter.to_utc(None)
        assert result is None
    
    def test_to_naive_utc_with_naive_datetime(self):
        """Test converting naive datetime to naive UTC"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.to_naive_utc(naive_dt)
        
        assert result.tzinfo is None
        assert result == naive_dt
    
    def test_to_naive_utc_with_aware_datetime(self):
        """Test converting timezone-aware datetime to naive UTC"""
        est = timezone(timedelta(hours=-5))
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=est)
        result = DateTimeConverter.to_naive_utc(aware_dt)
        
        assert result.tzinfo is None
        assert result.hour == 15  # Converted to UTC
        assert result.minute == 30
    
    def test_from_naive_utc(self):
        """Test converting naive UTC to timezone-aware"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.from_naive_utc(naive_dt)
        
        assert result.tzinfo == timezone.utc
        assert result.hour == 10
        assert result.minute == 30
    
    def test_ensure_naive_with_naive_datetime(self):
        """Test ensure_naive with already naive datetime"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.ensure_naive(naive_dt)
        
        assert result.tzinfo is None
        assert result == naive_dt
    
    def test_ensure_naive_with_aware_datetime(self):
        """Test ensure_naive with timezone-aware datetime"""
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = DateTimeConverter.ensure_naive(aware_dt)
        
        assert result.tzinfo is None
        assert result.hour == 10
    
    def test_ensure_aware_with_naive_datetime(self):
        """Test ensure_aware with naive datetime"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.ensure_aware(naive_dt)
        
        assert result.tzinfo == timezone.utc
        assert result.hour == 10
    
    def test_ensure_aware_with_aware_datetime(self):
        """Test ensure_aware with already aware datetime"""
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = DateTimeConverter.ensure_aware(aware_dt)
        
        assert result.tzinfo == timezone.utc
        assert result == aware_dt
    
    def test_date_to_datetime(self):
        """Test converting date to datetime"""
        test_date = date(2024, 1, 15)
        result = DateTimeConverter.date_to_datetime(test_date)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.tzinfo == timezone.utc
    
    def test_datetime_to_date(self):
        """Test converting datetime to date"""
        test_datetime = datetime(2024, 1, 15, 10, 30, 0)
        result = DateTimeConverter.datetime_to_date(test_datetime)
        
        assert isinstance(result, date)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15


class TestDateQueryHelper:
    """Test DateQueryHelper utility methods with actual database"""
    
    @pytest.fixture
    def session(self):
        """Create a test database session"""
        engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
        TestBase.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add test data
        test_records = [
            DTTestModel(id=1, test_date=date(2024, 1, 15), 
                     test_datetime=datetime(2024, 1, 15, 10, 30, 0)),
            DTTestModel(id=2, test_date=date(2024, 2, 20),
                     test_datetime=datetime(2024, 2, 20, 14, 45, 0)),
            DTTestModel(id=3, test_date=date(2024, 3, 10),
                     test_datetime=datetime(2024, 3, 10, 8, 15, 0)),
            DTTestModel(id=4, test_date=date(2023, 12, 25),
                     test_datetime=datetime(2023, 12, 25, 18, 0, 0)),
        ]
        
        for record in test_records:
            session.add(record)
        session.commit()
        
        yield session
        
        session.close()
        engine.dispose()
    
    def test_date_equals(self, session):
        """Test date equality query"""
        target_date = date(2024, 1, 15)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_equals(DTTestModel.test_date, target_date)
        ).all()
        
        assert len(results) == 1
        assert results[0].id == 1
    
    def test_date_equals_with_datetime(self, session):
        """Test date equality query with datetime input"""
        target_datetime = datetime(2024, 1, 15, 12, 0, 0)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_equals(DTTestModel.test_date, target_datetime)
        ).all()
        
        assert len(results) == 1
        assert results[0].id == 1
    
    def test_date_greater_than(self, session):
        """Test date greater than query"""
        target_date = date(2024, 2, 1)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_greater_than(DTTestModel.test_date, target_date)
        ).all()
        
        assert len(results) == 2
        assert all(r.test_date > target_date for r in results)
    
    def test_date_between(self, session):
        """Test date between query"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 2, 28)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_between(DTTestModel.test_date, start_date, end_date)
        ).all()
        
        assert len(results) == 2
        assert all(start_date <= r.test_date <= end_date for r in results)
    
    def test_date_in_month(self, session):
        """Test date in specific month query"""
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_in_month(DTTestModel.test_date, 2024, 2)
        ).all()
        
        assert len(results) == 1
        assert results[0].test_date.year == 2024
        assert results[0].test_date.month == 2
    
    def test_date_in_year(self, session):
        """Test date in specific year query"""
        results = session.query(DTTestModel).filter(
            DateQueryHelper.date_in_year(DTTestModel.test_date, 2024)
        ).all()
        
        assert len(results) == 3
        assert all(r.test_date.year == 2024 for r in results)
    
    def test_datetime_between(self, session):
        """Test datetime between query"""
        start_dt = datetime(2024, 1, 1, 0, 0, 0)
        end_dt = datetime(2024, 2, 28, 23, 59, 59)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.datetime_between(DTTestModel.test_datetime, start_dt, end_dt)
        ).all()
        
        assert len(results) == 2
    
    def test_datetime_between_with_timezone_aware(self, session):
        """Test datetime between query with timezone-aware datetimes"""
        start_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2024, 2, 28, 23, 59, 59, tzinfo=timezone.utc)
        results = session.query(DTTestModel).filter(
            DateQueryHelper.datetime_between(DTTestModel.test_datetime, start_dt, end_dt)
        ).all()
        
        assert len(results) == 2


class TestDateTimeRoundTrip:
    """Test datetime round-trip storage and retrieval"""
    
    @pytest.fixture
    def session(self):
        """Create a test database session"""
        engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
        TestBase.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
        engine.dispose()
    
    def test_naive_datetime_round_trip(self, session):
        """Test storing and retrieving naive datetime"""
        original_dt = datetime(2024, 1, 15, 10, 30, 45)
        
        # Store
        record = DTTestModel(id=1, test_datetime=original_dt)
        session.add(record)
        session.commit()
        
        # Retrieve
        retrieved = session.query(DTTestModel).filter_by(id=1).first()
        
        assert retrieved.test_datetime.year == original_dt.year
        assert retrieved.test_datetime.month == original_dt.month
        assert retrieved.test_datetime.day == original_dt.day
        assert retrieved.test_datetime.hour == original_dt.hour
        assert retrieved.test_datetime.minute == original_dt.minute
        assert retrieved.test_datetime.second == original_dt.second
    
    def test_aware_datetime_round_trip(self, session):
        """Test storing and retrieving timezone-aware datetime"""
        original_dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        
        # Convert to naive for storage
        naive_dt = DateTimeConverter.to_naive_utc(original_dt)
        
        # Store
        record = DTTestModel(id=1, test_datetime=naive_dt)
        session.add(record)
        session.commit()
        
        # Retrieve and convert back to aware
        retrieved = session.query(DTTestModel).filter_by(id=1).first()
        aware_dt = DateTimeConverter.from_naive_utc(retrieved.test_datetime)
        
        assert aware_dt.year == original_dt.year
        assert aware_dt.month == original_dt.month
        assert aware_dt.day == original_dt.day
        assert aware_dt.hour == original_dt.hour
        assert aware_dt.minute == original_dt.minute
        assert aware_dt.second == original_dt.second
        assert aware_dt.tzinfo == timezone.utc
    
    def test_date_round_trip(self, session):
        """Test storing and retrieving date"""
        original_date = date(2024, 1, 15)
        
        # Store
        record = DTTestModel(id=1, test_date=original_date)
        session.add(record)
        session.commit()
        
        # Retrieve
        retrieved = session.query(DTTestModel).filter_by(id=1).first()
        
        assert retrieved.test_date == original_date
    
    def test_none_datetime_round_trip(self, session):
        """Test storing and retrieving None datetime"""
        # Store
        record = DTTestModel(id=1, test_datetime=None)
        session.add(record)
        session.commit()
        
        # Retrieve
        retrieved = session.query(DTTestModel).filter_by(id=1).first()
        
        assert retrieved.test_datetime is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
