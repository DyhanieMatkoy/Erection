"""Estimate service"""
from typing import Optional
from ..data.models.estimate import Estimate
from ..data.repositories.estimate_repository import EstimateRepository
from .print_form_service import PrintFormService


class EstimateService:
    def __init__(self):
        self.repo = EstimateRepository()
        self.print_service = PrintFormService()
    
    def create(self) -> Estimate:
        """Create new estimate"""
        return Estimate()
    
    def load(self, estimate_id: int) -> Optional[Estimate]:
        """Load estimate"""
        return self.repo.find_by_id(estimate_id)
    
    def save(self, estimate: Estimate) -> bool:
        """Save estimate"""
        return self.repo.save(estimate)
    
    def generate_print_form(self, estimate_id: int, variant: Optional[str] = None) -> Optional[tuple]:
        """
        Generate print form for estimate
        
        Args:
            estimate_id: ID of the estimate
            variant: Print variant ('STANDARD' or 'RESOURCE'). If None, uses configured variant.
            
        Returns:
            Tuple of (content bytes, file extension) or None if estimate not found
        """
        return self.print_service.generate_estimate(estimate_id, variant)
