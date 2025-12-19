"""
Test Work model properties and validation methods

This test verifies the new properties and methods added to the Work model
for unit reference handling and validation.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models.sqlalchemy_models import Base, Work, Unit


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_unit(db_session):
    """Create a sample unit"""
    unit = Unit(name="м²", description="Square meters")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


class TestWorkModelProperties:
    """Test Work model properties"""
    
    def test_effective_unit_name_with_unit_ref(self, db_session, sample_unit):
        """Test effective_unit_name returns unit_ref.name when unit_id is set"""
        work = Work(name="Test Work", unit_id=sample_unit.id)
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        assert work.effective_unit_name == "м²"
    
    def test_effective_unit_name_with_legacy_unit(self, db_session):
        """Test effective_unit_name returns legacy unit when no unit_id"""
        work = Work(name="Test Work", unit="кг")
        db_session.add(work)
        db_session.commit()
        
        assert work.effective_unit_name == "кг"
    
    def test_effective_unit_name_with_neither(self, db_session):
        """Test effective_unit_name returns None when neither unit_id nor unit"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        
        assert work.effective_unit_name is None
    
    def test_has_unit_reference_true(self, db_session, sample_unit):
        """Test has_unit_reference returns True when unit_id is set"""
        work = Work(name="Test Work", unit_id=sample_unit.id)
        db_session.add(work)
        db_session.commit()
        
        assert work.has_unit_reference is True
    
    def test_has_unit_reference_false(self, db_session):
        """Test has_unit_reference returns False when unit_id is None"""
        work = Work(name="Test Work", unit="кг")
        db_session.add(work)
        db_session.commit()
        
        assert work.has_unit_reference is False
    
    def test_needs_unit_migration_true(self, db_session):
        """Test needs_unit_migration returns True when has legacy unit but no unit_id"""
        work = Work(name="Test Work", unit="кг")
        db_session.add(work)
        db_session.commit()
        
        assert work.needs_unit_migration is True
    
    def test_needs_unit_migration_false_with_unit_id(self, db_session, sample_unit):
        """Test needs_unit_migration returns False when has unit_id"""
        work = Work(name="Test Work", unit_id=sample_unit.id, unit="кг")
        db_session.add(work)
        db_session.commit()
        
        assert work.needs_unit_migration is False
    
    def test_needs_unit_migration_false_no_legacy_unit(self, db_session):
        """Test needs_unit_migration returns False when no legacy unit"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        
        assert work.needs_unit_migration is False
    
    def test_needs_unit_migration_false_empty_legacy_unit(self, db_session):
        """Test needs_unit_migration returns False when legacy unit is empty"""
        work = Work(name="Test Work", unit="")
        db_session.add(work)
        db_session.commit()
        
        assert work.needs_unit_migration is False
    
    def test_validate_unit_reference_valid(self, db_session, sample_unit):
        """Test validate_unit_reference passes with valid unit_id"""
        work = Work(name="Test Work", unit_id=sample_unit.id)
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        # Should not raise exception
        work.validate_unit_reference()
    
    def test_validate_unit_reference_none_unit_id(self, db_session):
        """Test validate_unit_reference passes with None unit_id"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        
        # Should not raise exception
        work.validate_unit_reference()
    
    def test_validate_hierarchy_no_parent(self, db_session):
        """Test validate_hierarchy passes with no parent"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        
        assert work.validate_hierarchy() is True
    
    def test_validate_hierarchy_self_parent(self, db_session):
        """Test validate_hierarchy fails when work is its own parent"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        work.parent_id = work.id
        
        with pytest.raises(ValueError, match="cannot be its own ancestor"):
            work.validate_hierarchy()
    
    def test_repr_with_unit_id(self, db_session, sample_unit):
        """Test __repr__ includes unit_id"""
        work = Work(name="Test Work", unit_id=sample_unit.id)
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        repr_str = repr(work)
        assert "Test Work" in repr_str
        assert f"unit_id={sample_unit.id}" in repr_str
    
    def test_repr_without_unit_id(self, db_session):
        """Test __repr__ shows unit_id=None when not set"""
        work = Work(name="Test Work")
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        repr_str = repr(work)
        assert "Test Work" in repr_str
        assert "unit_id=None" in repr_str


class TestWorkModelIndexes:
    """Test that Work model indexes are properly created"""
    
    def test_work_creation_with_indexes(self, db_session, sample_unit):
        """Test that work can be created and queried efficiently with indexes"""
        # Create a work with all indexed fields
        work = Work(
            name="Test Work",
            unit_id=sample_unit.id,
            parent_id=None
        )
        db_session.add(work)
        db_session.commit()
        db_session.refresh(work)
        
        # Query by indexed fields - should work without errors
        found_by_name = db_session.query(Work).filter(Work.name == "Test Work").first()
        assert found_by_name.id == work.id
        
        found_by_unit_id = db_session.query(Work).filter(Work.unit_id == sample_unit.id).first()
        assert found_by_unit_id.id == work.id
        
        found_by_uuid = db_session.query(Work).filter(Work.uuid == work.uuid).first()
        assert found_by_uuid.id == work.id