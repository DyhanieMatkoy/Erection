from typing import List, Dict, Any
from sqlalchemy import distinct
from src.controllers.list_form_controller import ListFormController
from src.data.models.sqlalchemy_models import Timesheet, Object, Person
from src.services.timesheet_posting_service import TimesheetPostingService

class TimesheetListFormController(ListFormController):
    """Controller for Timesheet List Form"""
    
    def __init__(self, form_id: str, user_id: int, model_class: Any):
        super().__init__(form_id, user_id, model_class)
        self.posting_service = TimesheetPostingService()
        
        # Ensure deleted timesheets are never shown
        self.filters['marked_for_deletion'] = False
        self.filters['is_deleted'] = False

    def load_data(self):
        """Load data with explicit exclusion of deleted entries"""
        # Ensure deleted entries are always filtered out
        if 'marked_for_deletion' not in self.filters:
            self.filters['marked_for_deletion'] = False
        if 'is_deleted' not in self.filters:
            self.filters['is_deleted'] = False
            
        # Call parent load_data with include_deleted=False explicitly
        try:
            result = self.data_service.get_documents(
                model_class=self.model_class,
                page=self.current_page,
                page_size=self.page_size,
                filters=self.filters,
                sort_by=self.sort_by,
                sort_order=self.sort_order,
                include_deleted=False  # Explicitly exclude deleted
            )
            
            if self.data_callback:
                self.data_callback(result)
                
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Failed to load data: {str(e)}")

    def post_timesheets(self, ids: List[int]):
        """Post selected timesheets"""
        def handler(doc_id):
            success, error = self.posting_service.post_timesheet(doc_id)
            if success:
                return {'success': True}
            return {'success': False, 'error': error}
            
        self.execute_bulk_operation("Проведение табелей", ids, handler)

    def unpost_timesheets(self, ids: List[int]):
        """Unpost selected timesheets"""
        def handler(doc_id):
            success, error = self.posting_service.unpost_timesheet(doc_id)
            if success:
                return {'success': True}
            return {'success': False, 'error': error}
            
        self.execute_bulk_operation("Отмена проведения табелей", ids, handler)

    def get_object_filter_options(self) -> List[Dict[str, Any]]:
        """Get objects used in timesheets for filtering"""
        results = (
            self.session.query(Object.id, Object.name)
            .join(Timesheet, Timesheet.object_id == Object.id)
            .filter(
                Object.marked_for_deletion.is_(False),
                Timesheet.marked_for_deletion.is_(False)  # Only show objects from non-deleted timesheets
            )
            .distinct()
            .order_by(Object.name)
            .all()
        )
        
        return [
            {'id': r.id, 'name': r.name}
            for r in results
        ]

    def get_foreman_filter_options(self) -> List[Dict[str, Any]]:
        """Get foremen used in timesheets for filtering"""
        results = (
            self.session.query(Person.id, Person.full_name)
            .join(Timesheet, Timesheet.foreman_id == Person.id)
            .filter(
                Person.marked_for_deletion.is_(False),
                Timesheet.marked_for_deletion.is_(False)  # Only show foremen from non-deleted timesheets
            )
            .distinct()
            .order_by(Person.full_name)
            .all()
        )
        
        return [
            {'id': r.id, 'name': r.full_name}
            for r in results
        ]
