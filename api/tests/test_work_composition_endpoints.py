"""
Test work composition API endpoints

Tests for Requirements: 2.3, 3.4, 4.5, 5.3, 6.3, 7.2
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.dependencies.database import get_db
from src.data.models.sqlalchemy_models import Base, Work, CostItem, Material, Unit, CostItemMaterial


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_work_composition.db"
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


def get_error_message(response_data):
    """Extract error message from response, handling both FastAPI and custom formats"""
    return response_data.get("detail", "") or response_data.get("error", {}).get("message", "")


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_data(db_session):
    """Create test data"""
    # Create unit
    unit = Unit(id=1, name="м²", description="Square meter")
    db_session.add(unit)
    
    # Create work
    work = Work(
        id=1,
        code="W001",
        name="Test Work",
        unit_id=1,
        price=100.0,
        labor_rate=2.0,
        is_group=False
    )
    db_session.add(work)
    
    # Create cost items
    cost_item1 = CostItem(
        id=1,
        code="C001",
        description="Labor",
        price=50.0,
        unit_id=1,
        labor_coefficient=1.5,
        is_folder=False
    )
    cost_item2 = CostItem(
        id=2,
        code="C002",
        description="Equipment",
        price=30.0,
        unit_id=1,
        labor_coefficient=0.5,
        is_folder=False
    )
    db_session.add_all([cost_item1, cost_item2])
    
    # Create materials
    material1 = Material(
        id=1,
        code="M001",
        description="Cement",
        price=5000.0,
        unit_id=1
    )
    material2 = Material(
        id=2,
        code="M002",
        description="Sand",
        price=800.0,
        unit_id=1
    )
    db_session.add_all([material1, material2])
    
    db_session.commit()
    
    return {
        "work_id": 1,
        "cost_item1_id": 1,
        "cost_item2_id": 2,
        "material1_id": 1,
        "material2_id": 2
    }


class TestGetWorkComposition:
    """Test GET /api/works/{id}/composition endpoint"""
    
    def test_get_empty_composition(self, test_data):
        """Test getting composition for work with no associations"""
        response = client.get(f"/api/works/{test_data['work_id']}/composition")
        assert response.status_code == 200
        data = response.json()
        assert data["work_id"] == test_data["work_id"]
        assert data["work_name"] == "Test Work"
        assert len(data["cost_items"]) == 0
        assert len(data["materials"]) == 0
        assert data["total_cost"] == 0.0
    
    def test_get_composition_with_cost_items(self, test_data):
        """Test getting composition with cost items"""
        # Add cost item
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        
        response = client.get(f"/api/works/{test_data['work_id']}/composition")
        assert response.status_code == 200
        data = response.json()
        assert len(data["cost_items"]) == 1
        assert data["cost_items"][0]["cost_item_id"] == test_data["cost_item1_id"]
        assert data["total_cost_items_price"] == 50.0
    
    def test_get_composition_not_found(self, test_data):
        """Test getting composition for non-existent work"""
        response = client.get("/api/works/99999/composition")
        assert response.status_code == 404


class TestAddCostItemToWork:
    """Test POST /api/works/{id}/cost-items endpoint - Requirement 2.3"""
    
    def test_add_cost_item_success(self, test_data):
        """Test successfully adding cost item to work"""
        response = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["work_id"] == test_data["work_id"]
        assert data["cost_item_id"] == test_data["cost_item1_id"]
        assert data["material_id"] is None
    
    def test_add_duplicate_cost_item(self, test_data):
        """Test adding duplicate cost item fails"""
        # Add first time
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        # Try to add again
        response = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert response.status_code == 400
        assert "already added" in get_error_message(response.json()).lower()
    
    def test_add_cost_item_work_not_found(self, test_data):
        """Test adding cost item to non-existent work"""
        response = client.post(
            "/api/works/99999/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert response.status_code == 404
    
    def test_add_cost_item_not_found(self, test_data):
        """Test adding non-existent cost item"""
        response = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": 99999}
        )
        assert response.status_code == 404


class TestRemoveCostItemFromWork:
    """Test DELETE /api/works/{id}/cost-items/{cost_item_id} endpoint - Requirement 3.4"""
    
    def test_remove_cost_item_success(self, test_data):
        """Test successfully removing cost item without materials"""
        # Add cost item
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        
        # Remove it
        response = client.delete(
            f"/api/works/{test_data['work_id']}/cost-items/{test_data['cost_item1_id']}"
        )
        assert response.status_code == 204
        
        # Verify it's gone
        comp_response = client.get(f"/api/works/{test_data['work_id']}/composition")
        assert len(comp_response.json()["cost_items"]) == 0
    
    def test_remove_cost_item_with_materials_fails(self, test_data):
        """Test removing cost item with materials fails"""
        # Add cost item
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        # Add material to cost item
        resp2 = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert resp2.status_code == 201
        
        # Try to remove cost item
        response = client.delete(
            f"/api/works/{test_data['work_id']}/cost-items/{test_data['cost_item1_id']}"
        )
        assert response.status_code == 400
        assert "materials" in get_error_message(response.json()).lower()


class TestAddMaterialToWork:
    """Test POST /api/works/{id}/materials endpoint - Requirement 4.5"""
    
    def test_add_material_success(self, test_data):
        """Test successfully adding material to work"""
        # First add cost item
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        
        # Add material
        response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["work_id"] == test_data["work_id"]
        assert data["cost_item_id"] == test_data["cost_item1_id"]
        assert data["material_id"] == test_data["material1_id"]
        assert data["quantity_per_unit"] == 0.5
    
    def test_add_material_without_cost_item_fails(self, test_data):
        """Test adding material without cost item fails"""
        response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert response.status_code == 400
        assert "cost item must be added" in get_error_message(response.json()).lower()
    
    def test_add_material_zero_quantity_fails(self, test_data):
        """Test adding material with zero quantity fails"""
        # Add cost item
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        # Try to add material with zero quantity
        response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.0
            }
        )
        assert response.status_code == 400
        assert "greater than zero" in get_error_message(response.json()).lower()
    
    def test_add_duplicate_material_fails(self, test_data):
        """Test adding duplicate material fails"""
        # Add cost item
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        # Add material first time
        resp2 = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert resp2.status_code == 201
        
        # Try to add again
        response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.8
            }
        )
        assert response.status_code == 400
        assert "already added" in get_error_message(response.json()).lower()


class TestUpdateMaterialAssociation:
    """Test PUT /api/works/{id}/materials/{id} endpoint - Requirements 5.3, 6.3"""
    
    def test_update_material_quantity(self, test_data):
        """Test updating material quantity - Requirement 5.3"""
        # Setup: Add cost item and material
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        
        add_response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        association_id = add_response.json()["id"]
        
        # Update quantity
        response = client.put(
            f"/api/works/{test_data['work_id']}/materials/{association_id}",
            json={"quantity_per_unit": 1.5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity_per_unit"] == 1.5
        assert data["cost_item_id"] == test_data["cost_item1_id"]  # Should not change
    
    def test_update_material_cost_item(self, test_data):
        """Test changing material's cost item - Requirement 6.3"""
        # Setup: Add two cost items and material
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item2_id"]}
        )
        
        add_response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        association_id = add_response.json()["id"]
        
        # Change cost item
        response = client.put(
            f"/api/works/{test_data['work_id']}/materials/{association_id}",
            json={"cost_item_id": test_data["cost_item2_id"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cost_item_id"] == test_data["cost_item2_id"]
        assert data["quantity_per_unit"] == 0.5  # Should not change
    
    def test_update_material_invalid_quantity(self, test_data):
        """Test updating with invalid quantity fails"""
        # Setup
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        add_response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert add_response.status_code == 201
        association_id = add_response.json()["id"]
        
        # Try to update with zero quantity - Pydantic validation returns 422
        response = client.put(
            f"/api/works/{test_data['work_id']}/materials/{association_id}",
            json={"quantity_per_unit": 0.0}
        )
        assert response.status_code in [400, 422]  # Accept both validation error codes
    
    def test_update_material_to_unadded_cost_item_fails(self, test_data):
        """Test changing to cost item not added to work fails"""
        # Setup: Add only one cost item
        resp1 = client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        assert resp1.status_code == 201
        
        add_response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        assert add_response.status_code == 201
        association_id = add_response.json()["id"]
        
        # Try to change to cost item not added to work
        response = client.put(
            f"/api/works/{test_data['work_id']}/materials/{association_id}",
            json={"cost_item_id": test_data["cost_item2_id"]}
        )
        assert response.status_code == 400
        assert "must be added to work" in get_error_message(response.json()).lower()


class TestRemoveMaterialFromWork:
    """Test DELETE /api/works/{id}/materials/{id} endpoint - Requirement 7.2"""
    
    def test_remove_material_success(self, test_data):
        """Test successfully removing material"""
        # Setup
        client.post(
            f"/api/works/{test_data['work_id']}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        
        add_response = client.post(
            f"/api/works/{test_data['work_id']}/materials",
            json={
                "work_id": test_data["work_id"],
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        association_id = add_response.json()["id"]
        
        # Remove material
        response = client.delete(
            f"/api/works/{test_data['work_id']}/materials/{association_id}"
        )
        assert response.status_code == 204
        
        # Verify it's gone
        comp_response = client.get(f"/api/works/{test_data['work_id']}/composition")
        assert len(comp_response.json()["materials"]) == 0
    
    def test_remove_material_not_found(self, test_data):
        """Test removing non-existent material"""
        response = client.delete(
            f"/api/works/{test_data['work_id']}/materials/99999"
        )
        assert response.status_code == 404


class TestWorkCompositionIntegration:
    """Integration tests for complete work composition workflows"""
    
    def test_complete_workflow(self, test_data):
        """Test complete workflow: add cost items, add materials, update, remove"""
        work_id = test_data["work_id"]
        
        # 1. Add cost items
        client.post(
            f"/api/works/{work_id}/cost-items",
            json={"cost_item_id": test_data["cost_item1_id"]}
        )
        client.post(
            f"/api/works/{work_id}/cost-items",
            json={"cost_item_id": test_data["cost_item2_id"]}
        )
        
        # 2. Add materials
        mat1_response = client.post(
            f"/api/works/{work_id}/materials",
            json={
                "work_id": work_id,
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material1_id"],
                "quantity_per_unit": 0.5
            }
        )
        mat1_id = mat1_response.json()["id"]
        
        mat2_response = client.post(
            f"/api/works/{work_id}/materials",
            json={
                "work_id": work_id,
                "cost_item_id": test_data["cost_item1_id"],
                "material_id": test_data["material2_id"],
                "quantity_per_unit": 1.0
            }
        )
        mat2_id = mat2_response.json()["id"]
        
        # 3. Get composition
        comp = client.get(f"/api/works/{work_id}/composition").json()
        assert len(comp["cost_items"]) == 2
        assert len(comp["materials"]) == 2
        
        # 4. Update material quantity
        client.put(
            f"/api/works/{work_id}/materials/{mat1_id}",
            json={"quantity_per_unit": 0.75}
        )
        
        # 5. Move material to different cost item
        client.put(
            f"/api/works/{work_id}/materials/{mat2_id}",
            json={"cost_item_id": test_data["cost_item2_id"]}
        )
        
        # 6. Remove one material
        client.delete(f"/api/works/{work_id}/materials/{mat1_id}")
        
        # 7. Verify final state
        final_comp = client.get(f"/api/works/{work_id}/composition").json()
        assert len(final_comp["materials"]) == 1
        assert final_comp["materials"][0]["cost_item_id"] == test_data["cost_item2_id"]
        assert final_comp["materials"][0]["quantity_per_unit"] == 1.0



class TestCostItemsPagination:
    """Test GET /api/cost-items with pagination and filtering - Requirements 14.1, 14.2"""
    
    def test_cost_items_pagination_basic(self, db_session):
        """Test basic pagination for cost items"""
        # Create multiple cost items
        for i in range(15):
            cost_item = CostItem(
                code=f"C{i:03d}",
                description=f"Cost Item {i}",
                price=100.0 + i,
                is_folder=False
            )
            db_session.add(cost_item)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/cost-items?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["total"] == 15
        assert data["pagination"]["total_pages"] == 2
    
    def test_cost_items_pagination_second_page(self, db_session):
        """Test second page of cost items"""
        # Create multiple cost items
        for i in range(15):
            cost_item = CostItem(
                code=f"C{i:03d}",
                description=f"Cost Item {i}",
                price=100.0 + i,
                is_folder=False
            )
            db_session.add(cost_item)
        db_session.commit()
        
        # Test second page
        response = client.get("/api/cost-items?page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5  # Remaining items
        assert data["pagination"]["page"] == 2
    
    def test_cost_items_search_by_code(self, db_session):
        """Test searching cost items by code - Requirement 14.2"""
        # Create cost items with different codes
        cost_items = [
            CostItem(code="LAB001", description="Labor", price=50.0, is_folder=False),
            CostItem(code="EQP001", description="Equipment", price=30.0, is_folder=False),
            CostItem(code="LAB002", description="Skilled Labor", price=75.0, is_folder=False),
        ]
        for item in cost_items:
            db_session.add(item)
        db_session.commit()
        
        # Search by code
        response = client.get("/api/cost-items?search=LAB")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert "LAB" in item["code"]
    
    def test_cost_items_search_by_description(self, db_session):
        """Test searching cost items by description - Requirement 14.2"""
        # Create cost items
        cost_items = [
            CostItem(code="C001", description="Labor costs", price=50.0, is_folder=False),
            CostItem(code="C002", description="Equipment rental", price=30.0, is_folder=False),
            CostItem(code="C003", description="Labor overhead", price=75.0, is_folder=False),
        ]
        for item in cost_items:
            db_session.add(item)
        db_session.commit()
        
        # Search by description
        response = client.get("/api/cost-items?search=Labor")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert "Labor" in item["description"] or "labor" in item["description"]
    
    def test_cost_items_filter_by_parent(self, db_session):
        """Test filtering cost items by parent_id - Requirement 14.2"""
        # Create parent and child cost items
        parent = CostItem(id=100, code="P001", description="Parent", price=0.0, is_folder=True)
        child1 = CostItem(code="C001", description="Child 1", price=50.0, parent_id=100, is_folder=False)
        child2 = CostItem(code="C002", description="Child 2", price=30.0, parent_id=100, is_folder=False)
        orphan = CostItem(code="C003", description="Orphan", price=20.0, is_folder=False)
        
        db_session.add_all([parent, child1, child2, orphan])
        db_session.commit()
        
        # Filter by parent
        response = client.get("/api/cost-items?parent_id=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert item["parent_id"] == 100
    
    def test_cost_items_filter_by_is_folder(self, db_session):
        """Test filtering cost items by is_folder - Requirement 14.2"""
        # Create folders and items
        folder1 = CostItem(code="F001", description="Folder 1", price=0.0, is_folder=True)
        folder2 = CostItem(code="F002", description="Folder 2", price=0.0, is_folder=True)
        item1 = CostItem(code="I001", description="Item 1", price=50.0, is_folder=False)
        item2 = CostItem(code="I002", description="Item 2", price=30.0, is_folder=False)
        
        db_session.add_all([folder1, folder2, item1, item2])
        db_session.commit()
        
        # Filter folders only
        response = client.get("/api/cost-items?is_folder=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert item["is_folder"] is True
        
        # Filter items only
        response = client.get("/api/cost-items?is_folder=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert item["is_folder"] is False
    
    def test_cost_items_combined_filters(self, db_session):
        """Test combining multiple filters"""
        # Create test data
        parent = CostItem(id=100, code="P001", description="Parent", price=0.0, is_folder=True)
        child1 = CostItem(code="LAB001", description="Labor", price=50.0, parent_id=100, is_folder=False)
        child2 = CostItem(code="EQP001", description="Equipment", price=30.0, parent_id=100, is_folder=False)
        
        db_session.add_all([parent, child1, child2])
        db_session.commit()
        
        # Search + filter by parent
        response = client.get("/api/cost-items?search=LAB&parent_id=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["code"] == "LAB001"


class TestMaterialsPagination:
    """Test GET /api/materials with pagination and filtering - Requirements 14.3, 14.4"""
    
    def test_materials_pagination_basic(self, db_session):
        """Test basic pagination for materials"""
        # Create unit
        unit = Unit(id=1, name="т", description="Ton")
        db_session.add(unit)
        db_session.commit()
        
        # Create multiple materials
        for i in range(15):
            material = Material(
                code=f"M{i:03d}",
                description=f"Material {i}",
                price=1000.0 + i,
                unit_id=1
            )
            db_session.add(material)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/materials?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["total"] == 15
        assert data["pagination"]["total_pages"] == 2
    
    def test_materials_pagination_second_page(self, db_session):
        """Test second page of materials"""
        # Create unit
        unit = Unit(id=1, name="т", description="Ton")
        db_session.add(unit)
        db_session.commit()
        
        # Create multiple materials
        for i in range(15):
            material = Material(
                code=f"M{i:03d}",
                description=f"Material {i}",
                price=1000.0 + i,
                unit_id=1
            )
            db_session.add(material)
        db_session.commit()
        
        # Test second page
        response = client.get("/api/materials?page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5  # Remaining items
        assert data["pagination"]["page"] == 2
    
    def test_materials_search_by_code(self, db_session):
        """Test searching materials by code - Requirement 14.4"""
        # Create materials with different codes
        materials = [
            Material(code="CEM001", description="Cement M400", price=5000.0),
            Material(code="SND001", description="Sand", price=800.0),
            Material(code="CEM002", description="Cement M500", price=6000.0),
        ]
        for material in materials:
            db_session.add(material)
        db_session.commit()
        
        # Search by code
        response = client.get("/api/materials?search=CEM")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert "CEM" in item["code"]
    
    def test_materials_search_by_description(self, db_session):
        """Test searching materials by description - Requirement 14.4"""
        # Create materials
        materials = [
            Material(code="M001", description="Cement M400", price=5000.0),
            Material(code="M002", description="Sand river", price=800.0),
            Material(code="M003", description="Cement M500", price=6000.0),
        ]
        for material in materials:
            db_session.add(material)
        db_session.commit()
        
        # Search by description
        response = client.get("/api/materials?search=Cement")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert "Cement" in item["description"]
    
    def test_materials_filter_by_unit(self, db_session):
        """Test filtering materials by unit_id - Requirement 14.4"""
        # Create units
        unit1 = Unit(id=1, name="т", description="Ton")
        unit2 = Unit(id=2, name="м³", description="Cubic meter")
        db_session.add_all([unit1, unit2])
        db_session.commit()
        
        # Create materials with different units
        materials = [
            Material(code="M001", description="Cement", price=5000.0, unit_id=1),
            Material(code="M002", description="Sand", price=800.0, unit_id=2),
            Material(code="M003", description="Gravel", price=1200.0, unit_id=2),
        ]
        for material in materials:
            db_session.add(material)
        db_session.commit()
        
        # Filter by unit
        response = client.get("/api/materials?unit_id=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert item["unit_id"] == 2
    
    def test_materials_combined_filters(self, db_session):
        """Test combining multiple filters"""
        # Create unit
        unit = Unit(id=1, name="т", description="Ton")
        db_session.add(unit)
        db_session.commit()
        
        # Create materials
        materials = [
            Material(code="CEM001", description="Cement M400", price=5000.0, unit_id=1),
            Material(code="CEM002", description="Cement M500", price=6000.0, unit_id=1),
            Material(code="SND001", description="Sand", price=800.0, unit_id=1),
        ]
        for material in materials:
            db_session.add(material)
        db_session.commit()
        
        # Search + filter by unit
        response = client.get("/api/materials?search=Cement&unit_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        for item in data["data"]:
            assert "Cement" in item["description"]
            assert item["unit_id"] == 1
    
    def test_materials_pagination_with_search(self, db_session):
        """Test pagination works correctly with search"""
        # Create many materials with similar names
        for i in range(25):
            material = Material(
                code=f"CEM{i:03d}",
                description=f"Cement Type {i}",
                price=5000.0 + i
            )
            db_session.add(material)
        db_session.commit()
        
        # Search with pagination
        response = client.get("/api/materials?search=Cement&page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["total_pages"] == 3


class TestPaginationEdgeCases:
    """Test edge cases for pagination"""
    
    def test_empty_results(self, db_session):
        """Test pagination with no results"""
        response = client.get("/api/cost-items?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["total_pages"] == 0
    
    def test_invalid_page_number(self, db_session):
        """Test with page number beyond available pages"""
        # Create one item
        cost_item = CostItem(code="C001", description="Test", price=100.0, is_folder=False)
        db_session.add(cost_item)
        db_session.commit()
        
        # Request page 10 when only 1 page exists
        response = client.get("/api/cost-items?page=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0  # No items on this page
        assert data["pagination"]["total"] == 1
    
    def test_large_limit(self, db_session):
        """Test with limit at maximum"""
        # Create items
        for i in range(100):
            cost_item = CostItem(
                code=f"C{i:03d}",
                description=f"Item {i}",
                price=100.0,
                is_folder=False
            )
            db_session.add(cost_item)
        db_session.commit()
        
        # Request with max limit
        response = client.get("/api/cost-items?page=1&limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 100
        assert data["pagination"]["limit"] == 1000
