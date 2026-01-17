"""Cost Item Material repository for managing relationships between work, cost items and materials"""
from typing import List, Optional, Tuple
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import CostItem, Material, CostItemMaterial, Work

logger = logging.getLogger(__name__)


class CostItemMaterialRepository:
    """Repository for managing Work-CostItem-Material relationships"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, association_id: int) -> Optional[CostItemMaterial]:
        """Find association by ID"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(
                        joinedload(CostItemMaterial.work),
                        joinedload(CostItemMaterial.cost_item),
                        joinedload(CostItemMaterial.material)
                    )\
                    .filter(CostItemMaterial.id == association_id)\
                    .first()
        except Exception as e:
            logger.error(f"Failed to find association by ID {association_id}: {e}")
            return None
    
    def find_association(self, work_id: int, cost_item_id: int, material_id: Optional[int] = None) -> Optional[CostItemMaterial]:
        """Find association between work, cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)
                
                if material_id is not None:
                    query = query.filter(CostItemMaterial.material_id == material_id)
                else:
                    query = query.filter(CostItemMaterial.material_id.is_(None))
                
                return query.first()
        except Exception as e:
            logger.error(f"Failed to find association for work {work_id}, cost item {cost_item_id}, material {material_id}: {e}")
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
    
    def get_associations_for_work(self, work_id: int) -> List[CostItemMaterial]:
        """Get all associations for a work"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(
                        joinedload(CostItemMaterial.cost_item),
                        joinedload(CostItemMaterial.material)
                    )\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get associations for work {work_id}: {e}")
            return []
    
    def get_associations_for_cost_item(self, cost_item_id: int) -> List[CostItemMaterial]:
        """Get all associations for a cost item across all works"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(
                        joinedload(CostItemMaterial.work),
                        joinedload(CostItemMaterial.material)
                    )\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get associations for cost item {cost_item_id}: {e}")
            return []
    
    def get_associations_for_material(self, material_id: int) -> List[CostItemMaterial]:
        """Get all associations for a material across all works"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItemMaterial)\
                    .options(
                        joinedload(CostItemMaterial.work),
                        joinedload(CostItemMaterial.cost_item)
                    )\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get associations for material {material_id}: {e}")
            return []
    
    def create_or_update_association(
        self,
        work_id: int,
        cost_item_id: int,
        material_id: Optional[int],
        quantity_per_unit: float
    ) -> Optional[CostItemMaterial]:
        """Create or update association between work, cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                # Check if association already exists
                query = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)
                
                if material_id is not None:
                    query = query.filter(CostItemMaterial.material_id == material_id)
                else:
                    query = query.filter(CostItemMaterial.material_id.is_(None))
                
                association = query.first()
                
                if association:
                    # Update existing association
                    association.quantity_per_unit = quantity_per_unit
                else:
                    # Create new association
                    association = CostItemMaterial(
                        work_id=work_id,
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
    
    def remove_association(self, association_id: int) -> bool:
        """Remove association by ID"""
        try:
            with self.db_manager.session_scope() as session:
                association = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.id == association_id)\
                    .first()
                
                if association:
                    session.delete(association)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to remove association: {e}")
            return False
    
    def remove_association_by_work_cost_item_material(
        self,
        work_id: int,
        cost_item_id: int,
        material_id: Optional[int] = None
    ) -> bool:
        """Remove association by work, cost item and material"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)
                
                if material_id is not None:
                    query = query.filter(CostItemMaterial.material_id == material_id)
                else:
                    query = query.filter(CostItemMaterial.material_id.is_(None))
                
                association = query.first()
                
                if association:
                    session.delete(association)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to remove association: {e}")
            return False
    
    def get_cost_items_for_work(self, work_id: int) -> List[Tuple[CostItem, float]]:
        """Get all cost items for a work"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(CostItem, CostItemMaterial.quantity_per_unit)\
                    .join(CostItemMaterial, CostItem.id == CostItemMaterial.cost_item_id)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.material_id.is_(None))\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
                
                # Detach objects from session
                detached_result = []
                for cost_item, quantity in result:
                    session.expunge(cost_item)
                    detached_result.append((cost_item, quantity))
                
                return detached_result
        except Exception as e:
            logger.error(f"Failed to get cost items for work {work_id}: {e}")
            return []
    
    def get_materials_for_work(self, work_id: int) -> List[Tuple[Material, float, CostItem]]:
        """Get all materials for a work with their quantities and associated cost items"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(
                    Material,
                    CostItemMaterial.quantity_per_unit,
                    CostItem
                )\
                .join(CostItemMaterial, Material.id == CostItemMaterial.material_id)\
                .join(CostItem, CostItemMaterial.cost_item_id == CostItem.id)\
                .filter(CostItemMaterial.work_id == work_id)\
                .filter(CostItemMaterial.material_id.isnot(None))\
                .filter(Material.marked_for_deletion == False)\
                .order_by(Material.code)\
                .all()
                
                # Detach objects from session
                detached_result = []
                for material, quantity, cost_item in result:
                    session.expunge(material)
                    session.expunge(cost_item)
                    detached_result.append((material, quantity, cost_item))
                
                return detached_result
        except Exception as e:
            logger.error(f"Failed to get materials for work {work_id}: {e}")
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
    
    def calculate_total_cost_for_work(self, work_id: int) -> float:
        """Calculate total cost for a work (cost items + materials)"""
        try:
            with self.db_manager.session_scope() as session:
                # Get cost items cost
                cost_items_result = session.query(CostItem.price)\
                    .join(CostItemMaterial, CostItem.id == CostItemMaterial.cost_item_id)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.material_id.is_(None))\
                    .filter(CostItem.marked_for_deletion == False)\
                    .all()
                
                cost_items_total = sum(price[0] for price in cost_items_result)
                
                # Get materials cost
                materials_result = session.query(
                    Material.price,
                    CostItemMaterial.quantity_per_unit
                )\
                .join(CostItemMaterial, Material.id == CostItemMaterial.material_id)\
                .filter(CostItemMaterial.work_id == work_id)\
                .filter(CostItemMaterial.material_id.isnot(None))\
                .filter(Material.marked_for_deletion == False)\
                .all()
                
                materials_total = sum(price * quantity for price, quantity in materials_result)
                
                return cost_items_total + materials_total
        except Exception as e:
            logger.error(f"Failed to calculate total cost for work {work_id}: {e}")
            return 0.0
    
    def find_cost_items_not_in_work(self, work_id: int) -> List[CostItem]:
        """Find cost items that are not associated with a work"""
        try:
            with self.db_manager.session_scope() as session:
                # Get IDs of cost items already in the work
                associated_cost_item_ids = session.query(CostItemMaterial.cost_item_id)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.material_id.is_(None))\
                    .subquery()
                
                # Find cost items not in the associated list (only non-folders)
                return session.query(CostItem)\
                    .filter(~CostItem.id.in_(associated_cost_item_ids))\
                    .filter(CostItem.is_folder == False)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find cost items not in work {work_id}: {e}")
            return []
    
    def find_materials_not_in_work(self, work_id: int) -> List[Material]:
        """Find materials that are not associated with a work"""
        try:
            with self.db_manager.session_scope() as session:
                # Get IDs of materials already in the work
                associated_material_ids = session.query(CostItemMaterial.material_id)\
                    .filter(CostItemMaterial.work_id == work_id)\
                    .filter(CostItemMaterial.material_id.isnot(None))\
                    .subquery()
                
                # Find materials not in the associated list
                return session.query(Material)\
                    .filter(~Material.id.in_(associated_material_ids))\
                    .filter(Material.marked_for_deletion == False)\
                    .order_by(Material.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find materials not in work {work_id}: {e}")
            return []