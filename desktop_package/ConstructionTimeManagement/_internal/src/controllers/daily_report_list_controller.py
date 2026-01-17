from typing import List, Dict, Any
from sqlalchemy import distinct
from src.controllers.list_form_controller import ListFormController
from src.data.models.sqlalchemy_models import DailyReport, Estimate, Person

class DailyReportListFormController(ListFormController):
    """Controller for Daily Report List Form"""
    
    def get_estimate_filter_options(self) -> List[Dict[str, Any]]:
        """Get estimates used in daily reports for filtering"""
        # query: select distinct e.id, e.number, e.date from estimates e join daily_reports dr ...
        # ORM way:
        results = (
            self.session.query(Estimate.id, Estimate.number, Estimate.date)
            .join(DailyReport, DailyReport.estimate_id == Estimate.id)
            .filter(Estimate.marked_for_deletion == False)
            .distinct()
            .order_by(Estimate.date.desc(), Estimate.number)
            .all()
        )
        
        return [
            {'id': r.id, 'name': f"{r.number} от {r.date}"}
            for r in results
        ]

    def get_foreman_filter_options(self) -> List[Dict[str, Any]]:
        """Get foremen used in daily reports for filtering"""
        results = (
            self.session.query(Person.id, Person.full_name)
            .join(DailyReport, DailyReport.foreman_id == Person.id)
            .filter(Person.marked_for_deletion == False)
            .distinct()
            .order_by(Person.full_name)
            .all()
        )
        
        return [
            {'id': r.id, 'name': r.full_name}
            for r in results
        ]
