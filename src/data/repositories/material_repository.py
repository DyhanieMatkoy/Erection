"""Material repository for Costs & Materials functionality"""
from typing import List, Optional, Dict
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import Material, CostItem, CostItemMaterial, Unit

logger = logging.getLogger(__name__)


class MaterialRepository:
    """Repository for Material entities"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, material_id: int) -> Optional[Material]:
        """Find material by ID"""
        try:
            with self.db_manager.session_scope() as session:
                material = session.query(Material)\
                    .options(joinedload(Material.cost_items))\
                    .filter(Material.id == material_id)\
                    .first()
                if material:
                    session.expunge(material)
                return material
        except Exception as e:
            logger.error(f"Failed to find material by ID {material_id}: {e}")
            return None
    
    def find_by_code(self, code: str) -> Optional[Material]:
        """Find material by code"""
        try:
            with self.db_manager.session_scope() as session:
                material = session.query(Material)\
                    .filter(Material.code == code)\
                    .first()
                return material
        except Exception as e:
            logger.error(f"Failed to find material by code {code}: {e}")
            return None
    
    def find_all(self, include_deleted: bool = False) -> List[Dict]:
        """Find all materials"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Material.id,
                    Material.code,
                    Material.description,
                    Material.price,
                    Material.unit,
                    Material.unit_id,
                    Unit.name.label('unit_name'),
                    Material.marked_for_deletion
                ).outerjoin(Unit, Material.unit_id == Unit.id)
                
                if not include_deleted:
                    query = query.filter(Material.marked_for_deletion == False)
                
                results = []
                for row in query.order_by(Material.code).all():
                    results.append({
                        'id': row.id,
                        'code': row.code,
                        'description': row.description,
                        'price': row.price,
                        'unit': row.unit,
                        'unit_id': row.unit_id,
                        'unit_name': row.unit_name,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find all materials: {e}")
            return []
    
    def search_by_description(self, search_term: str) -> List[Dict]:
        """Search materials by description"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Material.id,
                    Material.code,
                    Material.description,
                    Material.price,
                    Material.unit,
                    Material.unit_id,
                    Unit.name.label('unit_name'),
                    Material.marked_for_deletion
                ).outerjoin(Unit, Material.unit_id == Unit.id)\
                    .filter(Material.description.ilike(f"%{search_term}%"))\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.code)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'code': row.code,
                        'description': row.description,
                        'price': row.price,
                        'unit': row.unit,
                        'unit_id': row.unit_id,
                        'unit_name': row.unit_name,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to search materials by description '{search_term}': {e}")
            return []
    
    def find_by_unit(self, unit: str) -> List[Material]:
        """Find materials by unit"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(Material)\
                    .join(Unit, Material.unit_id == Unit.id)\
                    .filter(Unit.name == unit)\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find materials by unit '{unit}': {e}")
            return []
    
    def find_by_price_range(self, min_price: float, max_price: float) -> List[Material]:
        """Find materials within price range"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(Material)\
                    .filter(Material.price >= min_price)\
                    .filter(Material.price <= max_price)\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.price)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find materials in price range {min_price}-{max_price}: {e}")
            return []
    
    def get_unique_units(self) -> List[str]:
        """Get list of unique units"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(Material.unit)\
                    .filter(Material.unit.isnot(None))\
                    .filter(Material.marked_for_deletion == False)\
                    .distinct()\
                    .all()
                return [row[0] for row in result if row[0]]
        except Exception as e:
            logger.error(f"Failed to get unique units: {e}")
            return []
    
    def save(self, material: Material) -> Optional[Material]:
        """Save material (create or update)"""
        try:
            with self.db_manager.session_scope() as session:
                if material.id is None:
                    # Create new material
                    session.add(material)
                else:
                    # Update existing material
                    existing = session.query(Material).filter(Material.id == material.id).first()
                    if existing:
                        # Update fields
                        existing.code = material.code
                        existing.description = material.description
                        existing.price = material.price
                        # Legacy unit column removed - only use unit_id foreign key
                        existing.unit_id = material.unit_id
                        existing.marked_for_deletion = material.marked_for_deletion
                
                session.flush()
                return material
        except Exception as e:
            logger.error(f"Failed to save material: {e}")
            return None
    
    def delete(self, material_id: int) -> bool:
        """Mark material as deleted (soft delete)"""
        try:
            with self.db_manager.session_scope() as session:
                material = session.query(Material).filter(Material.id == material_id).first()
                if material:
                    material.marked_for_deletion = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete material {material_id}: {e}")
            return False
    
    def get_cost_items(self, material_id: int) -> List[CostItem]:
        """Get all cost items that use this material"""
        try:
            with self.db_manager.session_scope() as session:
                material = session.query(Material)\
                    .options(joinedload(Material.cost_items))\
                    .filter(Material.id == material_id)\
                    .first()
                
                if material:
                    return material.cost_items
                return []
        except Exception as e:
            logger.error(f"Failed to get cost items for material {material_id}: {e}")
            return []
    
    def get_material_consumption(self, material_id: int) -> float:
        """Get total quantity of material used across all cost items"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(CostItemMaterial.quantity_per_unit)\
                    .join(CostItem, CostItemMaterial.cost_item_id == CostItem.id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .all()
                
                return sum(row[0] for row in result)
        except Exception as e:
            logger.error(f"Failed to get material consumption for material {material_id}: {e}")
            return 0.0