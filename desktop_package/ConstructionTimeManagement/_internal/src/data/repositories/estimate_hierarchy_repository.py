"""Estimate hierarchy repository"""
from typing import List, Optional
import logging
from ..database_manager import DatabaseManager
from ..models.estimate import Estimate, HierarchyNode, HierarchyTree, EstimateType
from ..models.sqlalchemy_models import Estimate as EstimateModel
from .estimate_repository import EstimateRepository

logger = logging.getLogger(__name__)


class EstimateHierarchyRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.estimate_repo = EstimateRepository()

    def get_general_estimates(self) -> List[Estimate]:
        """Get all general estimates (base_document_id is NULL)"""
        try:
            with self.db_manager.session_scope() as session:
                models = session.query(EstimateModel)\
                    .filter(EstimateModel.base_document_id.is_(None))\
                    .order_by(EstimateModel.date.desc())\
                    .all()
                
                return [self.estimate_repo._model_to_dataclass(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get general estimates: {e}")
            return []

    def get_plan_estimates_by_base(self, base_id: int) -> List[Estimate]:
        """Get all plan estimates for a given base document"""
        try:
            with self.db_manager.session_scope() as session:
                models = session.query(EstimateModel)\
                    .filter(EstimateModel.base_document_id == base_id)\
                    .order_by(EstimateModel.date.desc())\
                    .all()
                
                return [self.estimate_repo._model_to_dataclass(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get plan estimates for base {base_id}: {e}")
            return []

    def validate_hierarchy_integrity(self, estimate_id: int, base_id: int) -> bool:
        """
        Validate hierarchy integrity rules.
        Returns True if valid, False if rules violated.
        
        Rules:
        1. No circular references
        2. Base document must be a General Estimate
        3. Max depth is 2 (General -> Plan)
        """
        if not base_id:
            return True  # Removing base is always valid
            
        try:
            with self.db_manager.session_scope() as session:
                # Check 1: Self-reference
                if estimate_id == base_id:
                    logger.warning(f"Self-reference detected for estimate {estimate_id}")
                    return False
                
                # Check 2: Base document exists and is General
                base_doc = session.query(EstimateModel).filter(EstimateModel.id == base_id).first()
                if not base_doc:
                    logger.warning(f"Base document {base_id} not found")
                    return False
                    
                if base_doc.estimate_type != EstimateType.GENERAL.value:
                    logger.warning(f"Base document {base_id} is not a General Estimate (type: {base_doc.estimate_type})")
                    return False
                
                # Check 3: Current document doesn't have children (if becoming a plan)
                # If this estimate has children, it cannot become a plan estimate (would make depth > 2)
                if estimate_id > 0:
                    children_count = session.query(EstimateModel)\
                        .filter(EstimateModel.base_document_id == estimate_id)\
                        .count()
                    
                    if children_count > 0:
                        logger.warning(f"Estimate {estimate_id} has {children_count} children, cannot become a plan estimate")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Hierarchy integrity validation failed: {e}")
            return False

    def update_base_document(self, estimate_id: int, base_id: Optional[int]) -> bool:
        """Update base document for an estimate"""
        try:
            # Validate first
            if base_id and not self.validate_hierarchy_integrity(estimate_id, base_id):
                return False
                
            with self.db_manager.session_scope() as session:
                estimate = session.query(EstimateModel).filter(EstimateModel.id == estimate_id).first()
                if not estimate:
                    return False
                
                estimate.base_document_id = base_id
                
                # Auto-update type
                if base_id:
                    estimate.estimate_type = EstimateType.PLAN.value
                else:
                    estimate.estimate_type = EstimateType.GENERAL.value
                    
                return True
        except Exception as e:
            logger.error(f"Failed to update base document for {estimate_id}: {e}")
            return False

    def get_hierarchy_tree(self, root_id: int) -> Optional[HierarchyTree]:
        """Get hierarchy tree for a given root estimate"""
        try:
            with self.db_manager.session_scope() as session:
                root_model = session.query(EstimateModel).filter(EstimateModel.id == root_id).first()
                if not root_model:
                    return None
                
                root_estimate = self.estimate_repo._model_to_dataclass(root_model)
                root_node = HierarchyNode(estimate=root_estimate, depth=0)
                
                # Find children
                children_models = session.query(EstimateModel)\
                    .filter(EstimateModel.base_document_id == root_id)\
                    .all()
                
                total_nodes = 1
                max_depth = 0
                
                for child_model in children_models:
                    child_estimate = self.estimate_repo._model_to_dataclass(child_model)
                    child_node = HierarchyNode(estimate=child_estimate, depth=1)
                    root_node.children.append(child_node)
                    total_nodes += 1
                    max_depth = 1
                    
                return HierarchyTree(root=root_node, total_nodes=total_nodes, max_depth=max_depth)
                
        except Exception as e:
            logger.error(f"Failed to get hierarchy tree for {root_id}: {e}")
            return None
