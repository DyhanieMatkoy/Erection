"""Cost Item repository for Costs & Materials functionality"""
from typing import List, Optional, Dict
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import CostItem, CostItemMaterial, Material, Unit

logger = logging.getLogger(__name__)


class CostItemRepository:
    """Repository for CostItem entities"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, cost_item_id: int) -> Optional[CostItem]:
        """Find cost item by ID"""
        try:
            with self.db_manager.session_scope() as session:
                cost_item = session.query(CostItem)\
                    .options(joinedload(CostItem.materials))\
                    .filter(CostItem.id == cost_item_id)\
                    .first()
                if cost_item:
                    # Expunge the object from the session so it can be used after the session is closed
                    session.expunge(cost_item)
                return cost_item
        except Exception as e:
            logger.error(f"Failed to find cost item by ID {cost_item_id}: {e}")
            return None
    
    def find_by_code(self, code: str) -> Optional[CostItem]:
        """Find cost item by code"""
        try:
            with self.db_manager.session_scope() as session:
                cost_item = session.query(CostItem)\
                    .filter(CostItem.code == code)\
                    .first()
                return cost_item
        except Exception as e:
            logger.error(f"Failed to find cost item by code {code}: {e}")
            return None
    
    def find_all(self, include_deleted: bool = False) -> List[Dict]:
        """Find all cost items"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    CostItem.id,
                    CostItem.code,
                    CostItem.description,
                    CostItem.is_folder,
                    CostItem.parent_id,
                    CostItem.price,
                    CostItem.unit,
                    CostItem.unit_id,
                    Unit.name.label('unit_name'),
                    CostItem.labor_coefficient,
                    CostItem.marked_for_deletion
                ).outerjoin(Unit, CostItem.unit_id == Unit.id)
                
                if not include_deleted:
                    query = query.filter(CostItem.marked_for_deletion == False)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'code': row.code,
                        'description': row.description,
                        'is_folder': row.is_folder,
                        'parent_id': row.parent_id,
                        'price': row.price,
                        'unit': row.unit,
                        'unit_id': row.unit_id,
                        'unit_name': row.unit_name,
                        'labor_coefficient': row.labor_coefficient,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find all cost items: {e}")
            return []
    
    def find_root_items(self) -> List[CostItem]:
        """Find root cost items (items without parent)"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItem)\
                    .filter(CostItem.parent_id.is_(None))\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find root cost items: {e}")
            return []
    
    def find_by_parent(self, parent_id: int) -> List[CostItem]:
        """Find cost items by parent ID"""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(CostItem)\
                    .filter(CostItem.parent_id == parent_id)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to find cost items by parent {parent_id}: {e}")
            return []
    
    def find_folders(self) -> List[Dict]:
        """Find all folder cost items"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    CostItem.id,
                    CostItem.code,
                    CostItem.description,
                    CostItem.is_folder,
                    CostItem.parent_id,
                    CostItem.price,
                    CostItem.unit,
                    CostItem.unit_id,
                    Unit.name.label('unit_name'),
                    CostItem.labor_coefficient,
                    CostItem.marked_for_deletion
                ).outerjoin(Unit, CostItem.unit_id == Unit.id)\
                    .filter(CostItem.is_folder == True)\
                    .filter(CostItem.marked_for_deletion == False)\
                    .order_by(CostItem.code)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'code': row.code,
                        'description': row.description,
                        'is_folder': row.is_folder,
                        'parent_id': row.parent_id,
                        'price': row.price,
                        'unit': row.unit,
                        'unit_id': row.unit_id,
                        'unit_name': row.unit_name,
                        'labor_coefficient': row.labor_coefficient,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find cost item folders: {e}")
            return []
    
    def find_non_folders(self) -> List[CostItem]:
            """Find all non-folder cost items"""
            try:
                with self.db_manager.session_scope() as session:
                    return session.query(CostItem)\
                        .filter(CostItem.is_folder == False)\
                        .filter(CostItem.marked_for_deletion == False)\
                        .order_by(CostItem.code)\
                        .all()
            except Exception as e:
                logger.error(f"Failed to find non-folder cost items: {e}")
                return []
    
    def save(self, cost_item: CostItem) -> Optional[CostItem]:
        """Save cost item (create or update)"""
        try:
            with self.db_manager.session_scope() as session:
                if cost_item.id is None:
                    # Create new cost item
                    session.add(cost_item)
                else:
                    # Update existing cost item
                    existing = session.query(CostItem).filter(CostItem.id == cost_item.id).first()
                    if existing:
                        # Update fields
                        existing.parent_id = cost_item.parent_id
                        existing.code = cost_item.code
                        existing.description = cost_item.description
                        existing.is_folder = cost_item.is_folder
                        existing.price = cost_item.price
                        # Legacy unit column removed - only use unit_id foreign key
                        existing.unit_id = cost_item.unit_id
                        existing.labor_coefficient = cost_item.labor_coefficient
                        existing.marked_for_deletion = cost_item.marked_for_deletion
                
                session.flush()
                return cost_item
        except Exception as e:
            logger.error(f"Failed to save cost item: {e}")
            return None
    
    def delete(self, cost_item_id: int) -> bool:
        """Mark cost item as deleted (soft delete)"""
        try:
            with self.db_manager.session_scope() as session:
                cost_item = session.query(CostItem).filter(CostItem.id == cost_item_id).first()
                if cost_item:
                    cost_item.marked_for_deletion = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete cost item {cost_item_id}: {e}")
            return False
    
    def add_material(self, cost_item_id: int, material_id: int, quantity_per_unit: float) -> bool:
        """Add material to cost item"""
        try:
            with self.db_manager.session_scope() as session:
                # Check if association already exists
                existing = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .filter(CostItemMaterial.material_id == material_id)\
                    .first()
                
                if existing:
                    # Update quantity
                    existing.quantity_per_unit = quantity_per_unit
                else:
                    # Create new association
                    association = CostItemMaterial(
                        cost_item_id=cost_item_id,
                        material_id=material_id,
                        quantity_per_unit=quantity_per_unit
                    )
                    session.add(association)
                
                return True
        except Exception as e:
            logger.error(f"Failed to add material {material_id} to cost item {cost_item_id}: {e}")
            return False
    
    def remove_material(self, cost_item_id: int, material_id: int) -> bool:
        """Remove material from cost item"""
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
            logger.error(f"Failed to remove material {material_id} from cost item {cost_item_id}: {e}")
            return False
    
    def get_materials(self, cost_item_id: int) -> List[Material]:
        """Get all materials for a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                cost_item = session.query(CostItem)\
                    .options(joinedload(CostItem.materials))\
                    .filter(CostItem.id == cost_item_id)\
                    .first()
                
                if cost_item:
                    return cost_item.materials
                return []
        except Exception as e:
            logger.error(f"Failed to get materials for cost item {cost_item_id}: {e}")
            return []
    
    def find_materials(self, cost_item_id: int) -> List[Dict]:
        """Find materials associated with a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    CostItemMaterial.material_id,
                    CostItemMaterial.quantity_per_unit,
                    Material.code,
                    Material.description
                ).join(Material, CostItemMaterial.material_id == Material.id)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)
                
                results = []
                for row in query.all():
                    results.append({
                        'material_id': row.material_id,
                        'quantity_per_unit': row.quantity_per_unit,
                        'code': row.code,
                        'description': row.description
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find materials for cost item {cost_item_id}: {e}")
            return []
    
    def save_materials(self, cost_item_id: int, materials: List[Dict]) -> bool:
        """Save materials associated with a cost item"""
        try:
            with self.db_manager.session_scope() as session:
                # Get existing associations
                existing = session.query(CostItemMaterial)\
                    .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                    .all()
                
                # Create a set of existing material IDs
                existing_material_ids = {assoc.material_id for assoc in existing}
                
                # Create a set of new material IDs
                new_material_ids = {material['material_id'] for material in materials}
                
                # Remove associations that are no longer needed
                for assoc in existing:
                    if assoc.material_id not in new_material_ids:
                        session.delete(assoc)
                
                # Add or update associations
                for material in materials:
                    material_id = material['material_id']
                    quantity = material['quantity_per_unit']
                    
                    # Check if association already exists
                    existing_assoc = session.query(CostItemMaterial)\
                        .filter(CostItemMaterial.cost_item_id == cost_item_id)\
                        .filter(CostItemMaterial.material_id == material_id)\
                        .first()
                    
                    if existing_assoc:
                        # Update quantity
                        existing_assoc.quantity_per_unit = quantity
                    else:
                        # Create new association
                        new_assoc = CostItemMaterial(
                            cost_item_id=cost_item_id,
                            material_id=material_id,
                            quantity_per_unit=quantity
                        )
                        session.add(new_assoc)
                
                return True
        except Exception as e:
            logger.error(f"Failed to save materials for cost item {cost_item_id}: {e}")
            return False