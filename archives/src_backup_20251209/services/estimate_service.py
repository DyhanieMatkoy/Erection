"""Estimate service"""
from typing import Optional
from ..data.models.estimate import Estimate
from ..data.repositories.estimate_repository import EstimateRepository
from .estimate_print_form import EstimatePrintForm


class EstimateService:
    def __init__(self):
        self.repo = EstimateRepository()
        self.print_form = EstimatePrintForm()
    
    def create(self) -> Estimate:
        """Create new estimate"""
        return Estimate()
    
    def load(self, estimate_id: int) -> Optional[Estimate]:
        """Load estimate"""
        return self.repo.find_by_id(estimate_id)
    
    def save(self, estimate: Estimate) -> bool:
        """Save estimate"""
        return self.repo.save(estimate)
    
    def generate_print_form(self, estimate_id: int) -> Optional[bytes]:
        """
        Generate print form for estimate
        
        Args:
            estimate_id: ID of the estimate
            
        Returns:
            PDF content as bytes or None if estimate not found
        """
        return self.print_form.generate(estimate_id)
