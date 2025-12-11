"""Tests for ReferenceRepository SQLAlchemy migration

This test suite verifies that the ReferenceRepository works correctly
with SQLAlchemy sessions and maintains the same behavior as the original
implementation.
"""

import pytest
import os
from datetime import date
from src.data.database_manager import DatabaseManager
from src.data.repositories.reference_repository import ReferenceRepository
from src.data.models.sqlalchemy_models import (
    Counterparty, Object, Work, Person, Organization,
    Estimate, EstimateLine, DailyReport, DailyReportLine, DailyReportExecutor
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    db_path = "test_reference_repo.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass  # File might be locked, will be overwritten
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize(db_path)
    
    yield db_manager
    
    # Cleanup - dispose engine and close connections
    if db_manager._engine:
        db_manager._engine.dispose()
    if db_manager._connection:
        db_manager._connection.close()
    
    # Try to remove the test database
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass  # File might still be locked on Windows


@pytest.fixture
def sample_data(test_db):
    """Create sample data for testing"""
    with test_db.session_scope() as session:
        # Create counterparty
        counterparty = Counterparty(
            id=1,
            name="Test Customer",
            inn="1234567890"
        )
        session.add(counterparty)
        
        # Create object
        obj = Object(
            id=1,
            name="Test Object",
            owner_id=1,
            address="Test Address"
        )
        session.add(obj)
        
        # Create work
        work = Work(
            id=1,
            name="Test Work",
            code="W001",
            unit="м2",
            price=100.0
        )
        session.add(work)
        
        # Create person
        person = Person(
            id=1,
            full_name="Test Person",
            position="Foreman"
        )
        session.add(person)
        
        # Create organization
        organization = Organization(
            id=1,
            name="Test Organization",
            inn="9876543210",
            default_responsible_id=1
        )
        session.add(organization)
        
        # Create estimate
        estimate = Estimate(
            id=1,
            number="EST-001",
            date=date(2024, 1, 1),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1
        )
        session.add(estimate)
        
        # Create estimate line
        estimate_line = EstimateLine(
            id=1,
            estimate_id=1,
            line_number=1,
            work_id=1,
            quantity=10.0
        )
        session.add(estimate_line)
        
        # Create daily report
        daily_report = DailyReport(
            id=1,
            number="DR-001",
            date=date(2024, 1, 2),
            estimate_id=1,
            foreman_id=1
        )
        session.add(daily_report)
        
        # Create daily report line
        daily_report_line = DailyReportLine(
            id=1,
            report_id=1,
            line_number=1,
            work_id=1,
            planned_labor=8.0,
            actual_labor=7.5
        )
        session.add(daily_report_line)
        
        # Create daily report executor
        executor = DailyReportExecutor(
            report_line_id=1,
            executor_id=1
        )
        session.add(executor)
        
        session.commit()


def test_find_counterparty_usages(test_db, sample_data):
    """Test finding counterparty usages"""
    repo = ReferenceRepository()
    
    usages = repo.find_counterparty_usages(1)
    
    # Should find usage in estimate (as customer) and object (as owner)
    assert len(usages) == 2
    
    usage_types = [usage[0] for usage in usages]
    assert "Смета (Заказчик)" in usage_types
    assert "Объект (Владелец)" in usage_types


def test_find_counterparty_no_usages(test_db, sample_data):
    """Test finding counterparty with no usages"""
    repo = ReferenceRepository()
    
    # Create a counterparty with no usages
    with test_db.session_scope() as session:
        counterparty = Counterparty(
            id=2,
            name="Unused Customer"
        )
        session.add(counterparty)
        session.commit()
    
    usages = repo.find_counterparty_usages(2)
    assert len(usages) == 0


def test_find_object_usages(test_db, sample_data):
    """Test finding object usages"""
    repo = ReferenceRepository()
    
    usages = repo.find_object_usages(1)
    
    # Should find usage in estimate
    assert len(usages) == 1
    assert usages[0][0] == "Смета"
    assert "EST-001" in usages[0][1]


def test_find_work_usages(test_db, sample_data):
    """Test finding work usages"""
    repo = ReferenceRepository()
    
    usages = repo.find_work_usages(1)
    
    # Should find usage in estimate line and daily report line
    assert len(usages) == 2
    
    usage_types = [usage[0] for usage in usages]
    assert "Смета (строка)" in usage_types
    assert "Ежедневный отчет (строка)" in usage_types


def test_find_person_usages(test_db, sample_data):
    """Test finding person usages"""
    repo = ReferenceRepository()
    
    usages = repo.find_person_usages(1)
    
    # Should find usage in:
    # - estimate (as responsible)
    # - daily report (as foreman)
    # - daily report executor
    # - organization (as default responsible)
    assert len(usages) == 4
    
    usage_types = [usage[0] for usage in usages]
    assert "Смета (Ответственный)" in usage_types
    assert "Ежедневный отчет (Бригадир)" in usage_types
    assert "Ежедневный отчет (Исполнитель)" in usage_types
    assert "Организация (Ответственный по умолчанию)" in usage_types


def test_find_organization_usages(test_db, sample_data):
    """Test finding organization usages"""
    repo = ReferenceRepository()
    
    usages = repo.find_organization_usages(1)
    
    # Should find usage in estimate (as contractor)
    assert len(usages) == 1
    assert usages[0][0] == "Смета (Подрядчик)"
    assert "EST-001" in usages[0][1]


def test_can_delete_counterparty_with_usages(test_db, sample_data):
    """Test checking if counterparty can be deleted when it has usages"""
    repo = ReferenceRepository()
    
    can_delete, usages = repo.can_delete_counterparty(1)
    
    assert can_delete is False
    assert len(usages) > 0


def test_can_delete_counterparty_without_usages(test_db, sample_data):
    """Test checking if counterparty can be deleted when it has no usages"""
    repo = ReferenceRepository()
    
    # Create a counterparty with no usages
    with test_db.session_scope() as session:
        counterparty = Counterparty(
            id=2,
            name="Unused Customer"
        )
        session.add(counterparty)
        session.commit()
    
    can_delete, usages = repo.can_delete_counterparty(2)
    
    assert can_delete is True
    assert len(usages) == 0


def test_can_delete_object(test_db, sample_data):
    """Test checking if object can be deleted"""
    repo = ReferenceRepository()
    
    # Object with usages
    can_delete, usages = repo.can_delete_object(1)
    assert can_delete is False
    assert len(usages) > 0


def test_can_delete_work(test_db, sample_data):
    """Test checking if work can be deleted"""
    repo = ReferenceRepository()
    
    # Work with usages
    can_delete, usages = repo.can_delete_work(1)
    assert can_delete is False
    assert len(usages) > 0


def test_can_delete_person(test_db, sample_data):
    """Test checking if person can be deleted"""
    repo = ReferenceRepository()
    
    # Person with usages
    can_delete, usages = repo.can_delete_person(1)
    assert can_delete is False
    assert len(usages) > 0


def test_can_delete_organization(test_db, sample_data):
    """Test checking if organization can be deleted"""
    repo = ReferenceRepository()
    
    # Organization with usages
    can_delete, usages = repo.can_delete_organization(1)
    assert can_delete is False
    assert len(usages) > 0


def test_query_performance_with_joins(test_db, sample_data):
    """Test that queries with joins work correctly"""
    repo = ReferenceRepository()
    
    # Create multiple estimates with the same work
    with test_db.session_scope() as session:
        for i in range(2, 6):
            estimate = Estimate(
                id=i,
                number=f"EST-{i:03d}",
                date=date(2024, 1, i),
                customer_id=1,
                object_id=1
            )
            session.add(estimate)
            
            estimate_line = EstimateLine(
                estimate_id=i,
                line_number=1,
                work_id=1,
                quantity=10.0
            )
            session.add(estimate_line)
        
        session.commit()
    
    # Find work usages - should return distinct estimates
    usages = repo.find_work_usages(1)
    
    # Count estimate usages
    estimate_usages = [u for u in usages if u[0] == "Смета (строка)"]
    assert len(estimate_usages) == 5  # Original + 4 new ones


def test_multiple_daily_report_executors(test_db, sample_data):
    """Test finding person usages when they are executor in multiple reports"""
    repo = ReferenceRepository()
    
    # Create additional daily reports with the same executor
    with test_db.session_scope() as session:
        for i in range(2, 4):
            daily_report = DailyReport(
                id=i,
                number=f"DR-{i:03d}",
                date=date(2024, 1, i + 1),
                estimate_id=1,
                foreman_id=1
            )
            session.add(daily_report)
            
            daily_report_line = DailyReportLine(
                id=i,
                report_id=i,
                line_number=1,
                work_id=1,
                planned_labor=8.0
            )
            session.add(daily_report_line)
            
            executor = DailyReportExecutor(
                report_line_id=i,
                executor_id=1
            )
            session.add(executor)
        
        session.commit()
    
    usages = repo.find_person_usages(1)
    
    # Count executor usages - should be distinct reports
    executor_usages = [u for u in usages if u[0] == "Ежедневный отчет (Исполнитель)"]
    assert len(executor_usages) == 3  # Original + 2 new ones


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
