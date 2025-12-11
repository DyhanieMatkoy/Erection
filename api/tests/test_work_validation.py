"""
Tests for work validation logic

This test suite verifies all validation requirements from task 4:
- Work name validation (not empty, not whitespace-only)
- Group work validation (cannot have price or labor_rate)
- Quantity validation (must be > 0, must be numeric)
- Duplicate cost item prevention
- Duplicate material prevention
- Cost item deletion check (prevent if has materials)
- Circular reference prevention for parent_id
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.dependencies.database import get_db
from src.data.models.sqlalchemy_models import Base, Work, CostItem, Material, CostItemMaterial, Unit


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


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
    unit = Unit(name="м²")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


@pytest.fixture
def sample_work(db_session, sample_unit):
    """Create a sample work"""
    work = Work(name="Test Work", unit_id=sample_unit.id, price=100.0, labor_rate=2.0)
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)
    return work


@pytest.fixture
def sample_cost_item(db_session, sample_unit):
    """Create a sample cost item"""
    cost_item = CostItem(
        code="CI001",
        description="Test Cost Item",
        unit_id=sample_unit.id,
        price=50.0,
        labor_coefficient=1.5
    )
    db_session.add(cost_item)
    db_session.commit()
    db_session.refresh(cost_item)
    return cost_item


@pytest.fixture
def sample_material(db_session, sample_unit):
    """Create a sample material"""
    material = Material(
        code="M001",
        description="Test Material",
        unit_id=sample_unit.id,
        price=25.0
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


class TestWorkNameValidation:
    """Test work name validation (Requirements 1.2, 11.1)"""
    
    def test_empty_name_rejected(self, db_session, sample_unit):
        """Test that empty work name is rejected"""
        from api.validation import validate_work_name
        
        with pytest.raises(HTTPException) as exc_info:
            validate_work_name("")
        
        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()
    
    def test_whitespace_only_name_rejected(self, db_session, sample_unit):
        """Test that whitespace-only work name is rejected"""
        from api.validation import validate_work_name
        
        with pytest.raises(HTTPException) as exc_info:
            validate_work_name("   ")
        
        assert exc_info.value.status_code == 400
        assert "whitespace" in exc_info.value.detail.lower()
    
    def test_none_name_rejected(self, db_session, sample_unit):
        """Test that None work name is rejected"""
        from api.validation import validate_work_name
        
        with pytest.raises(HTTPException) as exc_info:
            validate_work_name(None)
        
        assert exc_info.value.status_code == 400
    
    def test_valid_name_accepted(self, db_session, sample_unit):
        """Test that valid work name is accepted"""
        from api.validation import validate_work_name
        
        # Should not raise exception
        validate_work_name("Valid Work Name")


class TestGroupWorkValidation:
    """Test group work validation (Requirements 1.3, 11.2)"""
    
    def test_group_with_price_rejected(self, db_session):
        """Test that group work with price is rejected"""
        from api.validation import validate_group_work_constraints
        
        with pytest.raises(HTTPException) as exc_info:
            validate_group_work_constraints(is_group=True, price=100.0, labor_rate=0.0)
        
        assert exc_info.value.status_code == 400
        assert "price" in exc_info.value.detail.lower()
    
    def test_group_with_labor_rate_rejected(self, db_session):
        """Test that group work with labor_rate is rejected"""
        from api.validation import validate_group_work_constraints
        
        with pytest.raises(HTTPException) as exc_info:
            validate_group_work_constraints(is_group=True, price=0.0, labor_rate=2.0)
        
        assert exc_info.value.status_code == 400
        assert "labor" in exc_info.value.detail.lower()
    
    def test_group_with_both_rejected(self, db_session):
        """Test that group work with both price and labor_rate is rejected"""
        from api.validation import validate_group_work_constraints
        
        with pytest.raises(HTTPException) as exc_info:
            validate_group_work_constraints(is_group=True, price=100.0, labor_rate=2.0)
        
        assert exc_info.value.status_code == 400
    
    def test_group_with_zero_values_accepted(self, db_session):
        """Test that group work with zero price and labor_rate is accepted"""
        from api.validation import validate_group_work_constraints
        
        # Should not raise exception
        validate_group_work_constraints(is_group=True, price=0.0, labor_rate=0.0)
    
    def test_non_group_with_values_accepted(self, db_session):
        """Test that non-group work with price and labor_rate is accepted"""
        from api.validation import validate_group_work_constraints
        
        # Should not raise exception
        validate_group_work_constraints(is_group=False, price=100.0, labor_rate=2.0)


class TestQuantityValidation:
    """Test quantity validation (Requirements 4.4, 5.2, 11.3)"""
    
    def test_zero_quantity_rejected(self):
        """Test that zero quantity is rejected"""
        from api.validation import validate_quantity
        
        with pytest.raises(HTTPException) as exc_info:
            validate_quantity(0.0)
        
        assert exc_info.value.status_code == 400
        assert "greater than zero" in exc_info.value.detail.lower()
    
    def test_negative_quantity_rejected(self):
        """Test that negative quantity is rejected"""
        from api.validation import validate_quantity
        
        with pytest.raises(HTTPException) as exc_info:
            validate_quantity(-5.0)
        
        assert exc_info.value.status_code == 400
        assert "greater than zero" in exc_info.value.detail.lower()
    
    def test_none_quantity_rejected(self):
        """Test that None quantity is rejected"""
        from api.validation import validate_quantity
        
        with pytest.raises(HTTPException) as exc_info:
            validate_quantity(None)
        
        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()
    
    def test_positive_quantity_accepted(self):
        """Test that positive quantity is accepted"""
        from api.validation import validate_quantity
        
        # Should not raise exception
        validate_quantity(5.0)
        validate_quantity(0.001)
        validate_quantity(1000.0)


class TestDuplicateCostItemPrevention:
    """Test duplicate cost item prevention (Requirement 2.5)"""
    
    def test_duplicate_cost_item_rejected(self, db_session, sample_work, sample_cost_item):
        """Test that duplicate cost item is rejected"""
        from api.validation import check_duplicate_cost_item
        
        # Add cost item first time
        assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=None
        )
        db_session.add(assoc)
        db_session.commit()
        
        # Try to add again
        with pytest.raises(HTTPException) as exc_info:
            check_duplicate_cost_item(db_session, sample_work.id, sample_cost_item.id)
        
        assert exc_info.value.status_code == 400
        assert "already added" in exc_info.value.detail.lower()
    
    def test_non_duplicate_cost_item_accepted(self, db_session, sample_work, sample_cost_item):
        """Test that non-duplicate cost item is accepted"""
        from api.validation import check_duplicate_cost_item
        
        # Should not raise exception
        check_duplicate_cost_item(db_session, sample_work.id, sample_cost_item.id)


class TestDuplicateMaterialPrevention:
    """Test duplicate material prevention (Requirement 4.4)"""
    
    def test_duplicate_material_rejected(self, db_session, sample_work, sample_cost_item, sample_material):
        """Test that duplicate material is rejected"""
        from api.validation import check_duplicate_material
        
        # Add cost item first
        cost_item_assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=None
        )
        db_session.add(cost_item_assoc)
        db_session.commit()
        
        # Add material first time
        material_assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=sample_material.id,
            quantity_per_unit=5.0
        )
        db_session.add(material_assoc)
        db_session.commit()
        
        # Try to add again
        with pytest.raises(HTTPException) as exc_info:
            check_duplicate_material(db_session, sample_work.id, sample_cost_item.id, sample_material.id)
        
        assert exc_info.value.status_code == 400
        assert "already added" in exc_info.value.detail.lower()
    
    def test_non_duplicate_material_accepted(self, db_session, sample_work, sample_cost_item, sample_material):
        """Test that non-duplicate material is accepted"""
        from api.validation import check_duplicate_material
        
        # Should not raise exception
        check_duplicate_material(db_session, sample_work.id, sample_cost_item.id, sample_material.id)


class TestCostItemDeletionCheck:
    """Test cost item deletion check (Requirements 3.1, 3.2)"""
    
    def test_cost_item_with_materials_cannot_be_deleted(self, db_session, sample_work, sample_cost_item, sample_material):
        """Test that cost item with materials cannot be deleted"""
        from api.validation import check_cost_item_has_materials
        
        # Add cost item
        cost_item_assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=None
        )
        db_session.add(cost_item_assoc)
        db_session.commit()
        
        # Add material to cost item
        material_assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=sample_material.id,
            quantity_per_unit=5.0
        )
        db_session.add(material_assoc)
        db_session.commit()
        
        # Try to delete cost item
        with pytest.raises(HTTPException) as exc_info:
            check_cost_item_has_materials(db_session, sample_work.id, sample_cost_item.id)
        
        assert exc_info.value.status_code == 400
        assert "materials" in exc_info.value.detail.lower()
        assert "delete materials first" in exc_info.value.detail.lower()
    
    def test_cost_item_without_materials_can_be_deleted(self, db_session, sample_work, sample_cost_item):
        """Test that cost item without materials can be deleted"""
        from api.validation import check_cost_item_has_materials
        
        # Add cost item
        cost_item_assoc = CostItemMaterial(
            work_id=sample_work.id,
            cost_item_id=sample_cost_item.id,
            material_id=None
        )
        db_session.add(cost_item_assoc)
        db_session.commit()
        
        # Should not raise exception
        check_cost_item_has_materials(db_session, sample_work.id, sample_cost_item.id)


class TestCircularReferenceValidation:
    """Test circular reference prevention (Requirements 1.4, 15.3)"""
    
    def test_work_cannot_be_its_own_parent(self, db_session, sample_work):
        """Test that a work cannot be its own parent"""
        from api.validation import validate_parent_circular_reference
        
        with pytest.raises(HTTPException) as exc_info:
            validate_parent_circular_reference(db_session, sample_work.id, sample_work.id)
        
        assert exc_info.value.status_code == 400
        assert "own parent" in exc_info.value.detail.lower()
    
    def test_circular_reference_two_levels(self, db_session, sample_unit):
        """Test that circular reference is prevented (A -> B -> A)"""
        from api.validation import validate_parent_circular_reference
        
        # Create work A
        work_a = Work(name="Work A", unit_id=sample_unit.id)
        db_session.add(work_a)
        db_session.commit()
        db_session.refresh(work_a)
        
        # Create work B with A as parent
        work_b = Work(name="Work B", unit_id=sample_unit.id, parent_id=work_a.id)
        db_session.add(work_b)
        db_session.commit()
        db_session.refresh(work_b)
        
        # Try to set B as parent of A (would create circular reference)
        with pytest.raises(HTTPException) as exc_info:
            validate_parent_circular_reference(db_session, work_a.id, work_b.id)
        
        assert exc_info.value.status_code == 400
        assert "circular" in exc_info.value.detail.lower()
    
    def test_circular_reference_three_levels(self, db_session, sample_unit):
        """Test that circular reference is prevented (A -> B -> C -> A)"""
        from api.validation import validate_parent_circular_reference
        
        # Create work A
        work_a = Work(name="Work A", unit_id=sample_unit.id)
        db_session.add(work_a)
        db_session.commit()
        db_session.refresh(work_a)
        
        # Create work B with A as parent
        work_b = Work(name="Work B", unit_id=sample_unit.id, parent_id=work_a.id)
        db_session.add(work_b)
        db_session.commit()
        db_session.refresh(work_b)
        
        # Create work C with B as parent
        work_c = Work(name="Work C", unit_id=sample_unit.id, parent_id=work_b.id)
        db_session.add(work_c)
        db_session.commit()
        db_session.refresh(work_c)
        
        # Try to set C as parent of A (would create circular reference)
        with pytest.raises(HTTPException) as exc_info:
            validate_parent_circular_reference(db_session, work_a.id, work_c.id)
        
        assert exc_info.value.status_code == 400
        assert "circular" in exc_info.value.detail.lower()
    
    def test_valid_parent_accepted(self, db_session, sample_unit):
        """Test that valid parent is accepted"""
        from api.validation import validate_parent_circular_reference
        
        # Create work A
        work_a = Work(name="Work A", unit_id=sample_unit.id)
        db_session.add(work_a)
        db_session.commit()
        db_session.refresh(work_a)
        
        # Create work B
        work_b = Work(name="Work B", unit_id=sample_unit.id)
        db_session.add(work_b)
        db_session.commit()
        db_session.refresh(work_b)
        
        # Should not raise exception - A can be parent of B
        validate_parent_circular_reference(db_session, work_b.id, work_a.id)
    
    def test_none_parent_accepted(self, db_session, sample_work):
        """Test that None parent is accepted"""
        from api.validation import validate_parent_circular_reference
        
        # Should not raise exception
        validate_parent_circular_reference(db_session, sample_work.id, None)
    
    def test_new_work_with_any_parent_accepted(self, db_session, sample_work):
        """Test that new work (work_id=None) can have any parent"""
        from api.validation import validate_parent_circular_reference
        
        # Should not raise exception
        validate_parent_circular_reference(db_session, None, sample_work.id)


class TestReferentialIntegrityValidation:
    """Test referential integrity validation (Requirements 13.1, 13.2, 13.3)"""
    
    def test_invalid_work_id_rejected(self, db_session):
        """Test that invalid work ID is rejected"""
        from api.validation import validate_work_exists
        
        with pytest.raises(HTTPException) as exc_info:
            validate_work_exists(db_session, 99999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_invalid_cost_item_id_rejected(self, db_session):
        """Test that invalid cost item ID is rejected"""
        from api.validation import validate_cost_item_exists
        
        with pytest.raises(HTTPException) as exc_info:
            validate_cost_item_exists(db_session, 99999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_invalid_material_id_rejected(self, db_session):
        """Test that invalid material ID is rejected"""
        from api.validation import validate_material_exists
        
        with pytest.raises(HTTPException) as exc_info:
            validate_material_exists(db_session, 99999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_valid_work_id_accepted(self, db_session, sample_work):
        """Test that valid work ID is accepted"""
        from api.validation import validate_work_exists
        
        work = validate_work_exists(db_session, sample_work.id)
        assert work.id == sample_work.id
    
    def test_valid_cost_item_id_accepted(self, db_session, sample_cost_item):
        """Test that valid cost item ID is accepted"""
        from api.validation import validate_cost_item_exists
        
        cost_item = validate_cost_item_exists(db_session, sample_cost_item.id)
        assert cost_item.id == sample_cost_item.id
    
    def test_valid_material_id_accepted(self, db_session, sample_material):
        """Test that valid material ID is accepted"""
        from api.validation import validate_material_exists
        
        material = validate_material_exists(db_session, sample_material.id)
        assert material.id == sample_material.id
