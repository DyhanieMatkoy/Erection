"""Cost Item Material repository for managing relationships between cost items and materials"""
from typing import List, Optional, Tuple
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import CostItem, Material, CostItemMaterial

logger = logging.getLogger(__name__)


class CostItemMaterialRepository:
    """Repository for managing CostItem-Material relationships"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_association(self, cost_item_id: int, material_id: int) -> Optional[CostItemMaterial]:
        """Find association between cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .first()
        except Exception as e:
            logger.error(f"Failed to find association between cost item {cost_item_id} and material {material_id}: {e}")
            return None
    
    def get_all_associations(self) -> List[CostItemMaterial]:
        """Get all cost item-material associations"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(
                        joinedload(CostItemMaterial.cost_item),
                        joinedload(CostItemMaterial.material)
                    )\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get all associations: {e}")
            return []
    
    def get_associations_for_cost_item(self, cost_item_id: int) -> List[CostItemMaterial]:
        """Get all material associations for a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(joinedload(CostItemMaterial.material))\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get associations for cost item {cost_item_id}: {e}")
            return []
    
    def get_associations_for_material(self, material_id: int) -> List[CostItemMaterial]:
        """Get all cost item associations for a material"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(joinedload(CostItemMaterial.cost_item))\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get associations for material {material_id}: {e}")
            return []
    
    def create_or_update_association(
        self, 
        cost_item_id: int, 
        material_id: int, 
        quantity_per_unit: float
    ) -> Optional[CostItemMaterial]:
        """Create or update association between cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                # Check if association already exists
                association = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .first()
                
                if association:
                    # Update existing association
                    association.quantity_per_unit = quantity_per_unit
                else:
                    # Create new association
                    association = CostItemMaterial(
                        cost_item_id=cost_item_id,
                        material_id=material_id,
                        quantity_per_unit=quantity_per_unit
                    )
                    session.add(association)
                
                session.flush()
                return association
        except Exception as e:
            logger.error(f"Failed to create/update association: {e}")
            return None
    
    def remove_association(self, cost_item_id: int, material_id: int) -> bool:
        """Remove association between cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                association = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .first()
                
                if association:
                    session.delete(association)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to remove association: {e}")
            return False
    
    def get_materials_for_cost_item(self, cost_item_id: int) -> List[Tuple[Material, float]]:
        """Get all materials for a cost item with their quantities"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(Material, CostItemMaterial.quantity_per_unit)\
                    .join(CostItemMaterial, Material.id == CostItemMaterial.material_id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.code)\
                    .all()
                
                return [(material, quantity) for material, quantity in result]
        except Exception as e:
            logger.error(f"Failed to get materials for cost item {cost_item_id}: {e}")
            return []
    
    def get_cost_items_for_material(self, material_id: int) -> List[Tuple[CostItem, float]]:
        """Get all cost items for a material with their quantities"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(CostItem, CostItemMaterial.quantity_per_unit)\
                    .join(CostItemMaterial, CostItem.id == CostItemMaterial.cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
                
                return [(cost_item, quantity) for cost_item, quantity in result]
        except Exception as e:
            logger.error(f"Failed to get cost items for material {material_id}: {e}")
            return []
    
    def calculate_material_cost_for_cost_item(self, cost_item_id: int) -> float:
        """Calculate total material cost for a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(
                    Material.price,
                    CostItemMaterial.quantity_per_unit
                )\
                .join(CostItemMaterial, Material.id == CostItemMaterial.material_id)\
                .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                .filter(Material.marked_for_deletion == False)\
                .all()
                
                return sum(price * quantity for price, quantity in result)
        except Exception as e:
            logger.error(f"Failed to calculate material cost for cost item {cost_item_id}: {e}")
            return 0.0
    
    def find_materials_not_in_cost_item(self, cost_item_id: int) -> List[Material]:
        """Find materials that are not associated with a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                # Get IDs of materials already associated with the cost item
                associated_material_ids = session.query(CostItemMaterial.material_id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .subquery()
                
                # Find materials not in the associated list
                return session.query(Material)\
                    .filter(~Material.id.in_(associated_material_ids))\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find materials not in cost item {cost_item_id}: {e}")
            return []
    
    def find_cost_items_not_using_material(self, material_id: int) -> List[CostItem]:
        """Find cost items that are not using a specific material"""
        try:
            with self.db_manager.session_scope() as session:
                # Get IDs of cost items already using the material
                using_cost_item_ids = session.query(CostItemMaterial.cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .subquery()
                
                # Find cost items not in the using list (only non-folders)
                return session.query(CostItem)\
                    .filter(~CostItem.id.in_(using_cost_item_ids))\
                    .filter(CostItem.is_folder == False)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find cost items not using material {material_id}: {e}")
            return []