"""Estimate view model"""
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional
from ..data.models.estimate import Estimate
from ..services.estimate_service import EstimateService
from ..services.calculator_service import CalculatorService


class EstimateViewModel(QObject):
    modified = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = EstimateService()
        self.estimate: Optional[Estimate] = None
    
    def load(self, estimate_id: int):
        """Load estimate"""
        self.estimate = self.service.load(estimate_id)
    
    def create_new(self):
        """Create new estimate"""
        self.estimate = self.service.create()
    
    def save(self) -> bool:
        """Save estimate"""
        if not self.estimate:
            return False
        return self.service.save(self.estimate)
    
    def recalculate(self):
        """Recalculate estimate totals"""
        if not self.estimate:
            return
        
        total_sum = 0.0
        total_labor = 0.0
        
        for line in self.estimate.lines:
            line.sum = CalculatorService.calculate_sum(line.quantity, line.price)
            line.planned_labor = CalculatorService.calculate_labor(line.quantity, line.labor_rate)
            total_sum += line.sum
            total_labor += line.planned_labor
        
        self.estimate.total_sum = total_sum
        self.estimate.total_labor = total_labor
        
        self.modified.emit()
