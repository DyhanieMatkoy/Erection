"""Hierarchy service"""
from typing import List, Optional, Dict, Any
import logging
from ..data.models.estimate import Estimate, EstimateType, HierarchyTree, EstimateLine
from ..data.repositories.estimate_hierarchy_repository import EstimateHierarchyRepository
from ..data.repositories.estimate_repository import EstimateRepository

logger = logging.getLogger(__name__)


class HierarchyService:
    def __init__(self):
        self.hierarchy_repo = EstimateHierarchyRepository()
        self.estimate_repo = EstimateRepository()

    def create_general_estimate(self, estimate: Estimate) -> bool:
        """Create a new general estimate"""
        estimate.estimate_type = EstimateType.GENERAL.value
        estimate.base_document_id = None
        return self.estimate_repo.save(estimate)

    def create_plan_estimate(self, estimate: Estimate, base_id: int) -> bool:
        """Create a new plan estimate based on a general estimate"""
        if not self.hierarchy_repo.validate_hierarchy_integrity(estimate.id, base_id):
            return False
            
        estimate.estimate_type = EstimateType.PLAN.value
        estimate.base_document_id = base_id
        return self.estimate_repo.save(estimate)

    def set_base_document(self, estimate_id: int, base_id: Optional[int]) -> bool:
        """Set or remove base document for an estimate"""
        return self.hierarchy_repo.update_base_document(estimate_id, base_id)

    def copy_works_from_base(self, plan_id: int, selected_work_ids: List[int]) -> bool:
        """
        Copy selected works from base estimate to plan estimate.
        
        Args:
            plan_id: ID of the plan estimate
            selected_work_ids: List of work IDs (not line IDs, but actual work definitions) 
                               OR maybe line IDs from base estimate?
                               Usually user selects rows from base estimate.
        """
        plan_estimate = self.estimate_repo.find_by_id(plan_id)
        if not plan_estimate or not plan_estimate.base_document_id:
            logger.warning(f"Estimate {plan_id} is not a valid plan estimate")
            return False
            
        base_estimate = self.estimate_repo.find_by_id(plan_estimate.base_document_id)
        if not base_estimate:
            logger.warning(f"Base estimate {plan_estimate.base_document_id} not found")
            return False
            
        # Find lines in base estimate that match selected work IDs
        # We assume selected_work_ids are work_ids (from Works table), 
        # but if the base estimate has multiple lines with same work_id, this might be ambiguous.
        # Ideally we should pass base_line_ids.
        # But let's assume work_ids for now as per function signature in plan, 
        # or better, check what's more practical. 
        # Since the UI will show lines from base estimate, passing line IDs is safer.
        # But the Requirement 5.3 says "selected works".
        # Let's assume we pass work_ids for now, as that's what the task description implied.
        
        works_to_copy = []
        for line in base_estimate.lines:
            if line.work_id in selected_work_ids:
                works_to_copy.append(line)
        
        if not works_to_copy:
            logger.warning("No matching works found in base estimate")
            return False
            
        # Add to plan estimate
        current_lines = len(plan_estimate.lines)
        for i, line in enumerate(works_to_copy):
            new_line = EstimateLine(
                estimate_id=plan_id,
                line_number=current_lines + i + 1,
                work_id=line.work_id,
                quantity=line.quantity,
                unit=line.unit,  # This is from EstimateLine, not Work.unit
                price=line.price,
                labor_rate=line.labor_rate,
                sum=line.sum,
                planned_labor=line.planned_labor,
                is_group=line.is_group,
                group_name=line.group_name,
                parent_group_id=0, # Flatten for now
                is_collapsed=False
            )
            plan_estimate.lines.append(new_line)
            
        # Recalculate totals
        plan_estimate.total_sum = sum(l.sum for l in plan_estimate.lines)
        plan_estimate.total_labor = sum(l.planned_labor for l in plan_estimate.lines)
        
        return self.estimate_repo.save(plan_estimate)

    def get_hierarchy_summary(self, base_id: int) -> Dict[str, Any]:
        """Get summary of plan estimates for a general estimate"""
        plan_estimates = self.hierarchy_repo.get_plan_estimates_by_base(base_id)
        
        total_plan_sum = sum(e.total_sum for e in plan_estimates)
        count = len(plan_estimates)
        
        return {
            "base_id": base_id,
            "plan_count": count,
            "total_plan_sum": total_plan_sum,
            "plan_estimates": plan_estimates
        }

    def get_hierarchy_tree(self, root_id: int) -> Optional[HierarchyTree]:
        """Get full hierarchy tree"""
        return self.hierarchy_repo.get_hierarchy_tree(root_id)
