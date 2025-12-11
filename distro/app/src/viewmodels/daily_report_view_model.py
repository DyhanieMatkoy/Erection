"""Daily report view model"""
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional
from ..data.models.daily_report import DailyReport
from ..services.daily_report_service import DailyReportService
from ..services.calculator_service import CalculatorService


class DailyReportViewModel(QObject):
    modified = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = DailyReportService()
        self.report: Optional[DailyReport] = None
    
    def load(self, report_id: int):
        """Load daily report"""
        self.report = self.service.load(report_id)
    
    def create_new(self):
        """Create new daily report"""
        self.report = self.service.create()
    
    def save(self) -> bool:
        """Save daily report"""
        if not self.report:
            return False
        return self.service.save(self.report)
    
    def recalculate_deviations(self):
        """Recalculate deviation percentages"""
        if not self.report:
            return
        
        for line in self.report.lines:
            if line.planned_labor > 0:
                line.deviation_percent = CalculatorService.calculate_deviation(
                    line.planned_labor, 
                    line.actual_labor
                )
            else:
                line.deviation_percent = 0.0
        
        self.modified.emit()
