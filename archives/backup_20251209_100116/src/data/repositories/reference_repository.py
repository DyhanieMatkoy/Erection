"""Reference repository with usage checking"""
from typing import List, Tuple
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import (
    Counterparty, Object, Work, Person, Organization,
    Estimate, DailyReport, DailyReportLine, DailyReportExecutor
)


class ReferenceRepository:
    """Repository for reference data with usage checking"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_counterparty_usages(self, counterparty_id: int) -> List[Tuple[str, str]]:
        """Find where counterparty is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        
        with self.db_manager.session_scope() as session:
            # Check in estimates (as customer)
            estimates = session.query(Estimate).filter(
                Estimate.customer_id == counterparty_id
            ).all()
            
            for estimate in estimates:
                usages.append(("Смета (Заказчик)", f"№{estimate.number} от {estimate.date}"))
            
            # Check in objects (as owner)
            objects = session.query(Object).filter(
                Object.owner_id == counterparty_id
            ).all()
            
            for obj in objects:
                usages.append(("Объект (Владелец)", obj.name))
        
        return usages
    
    def find_object_usages(self, object_id: int) -> List[Tuple[str, str]]:
        """Find where object is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        
        with self.db_manager.session_scope() as session:
            # Check in estimates
            estimates = session.query(Estimate).filter(
                Estimate.object_id == object_id
            ).all()
            
            for estimate in estimates:
                usages.append(("Смета", f"№{estimate.number} от {estimate.date}"))
        
        return usages
    
    def find_work_usages(self, work_id: int) -> List[Tuple[str, str]]:
        """Find where work is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        
        with self.db_manager.session_scope() as session:
            # Check in estimate lines - use join to get estimate info
            estimates = session.query(Estimate).join(
                Estimate.lines
            ).filter(
                Estimate.lines.any(work_id=work_id)
            ).distinct().all()
            
            for estimate in estimates:
                usages.append(("Смета (строка)", f"№{estimate.number} от {estimate.date}"))
            
            # Check in daily report lines - use join to get report info
            daily_reports = session.query(DailyReport).join(
                DailyReport.lines
            ).filter(
                DailyReport.lines.any(work_id=work_id)
            ).distinct().all()
            
            for report in daily_reports:
                usages.append(("Ежедневный отчет (строка)", f"от {report.date}"))
        
        return usages
    
    def find_person_usages(self, person_id: int) -> List[Tuple[str, str]]:
        """Find where person is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        
        with self.db_manager.session_scope() as session:
            # Check in estimates (as responsible)
            estimates = session.query(Estimate).filter(
                Estimate.responsible_id == person_id
            ).all()
            
            for estimate in estimates:
                usages.append(("Смета (Ответственный)", f"№{estimate.number} от {estimate.date}"))
            
            # Check in daily reports (as foreman)
            daily_reports = session.query(DailyReport).filter(
                DailyReport.foreman_id == person_id
            ).all()
            
            for report in daily_reports:
                usages.append(("Ежедневный отчет (Бригадир)", f"от {report.date}"))
            
            # Check in daily report executors - use joins
            daily_reports_executor = session.query(DailyReport).join(
                DailyReport.lines
            ).join(
                DailyReportLine.executors
            ).filter(
                DailyReportExecutor.executor_id == person_id
            ).distinct().all()
            
            for report in daily_reports_executor:
                usages.append(("Ежедневный отчет (Исполнитель)", f"от {report.date}"))
            
            # Check in organizations (as default responsible)
            organizations = session.query(Organization).filter(
                Organization.default_responsible_id == person_id
            ).all()
            
            for org in organizations:
                usages.append(("Организация (Ответственный по умолчанию)", org.name))
        
        return usages
    
    def find_organization_usages(self, organization_id: int) -> List[Tuple[str, str]]:
        """Find where organization is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        
        with self.db_manager.session_scope() as session:
            # Check in estimates (as contractor)
            estimates = session.query(Estimate).filter(
                Estimate.contractor_id == organization_id
            ).all()
            
            for estimate in estimates:
                usages.append(("Смета (Подрядчик)", f"№{estimate.number} от {estimate.date}"))
        
        return usages
    
    def can_delete_counterparty(self, counterparty_id: int) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if counterparty can be deleted
        
        Returns (can_delete, usages)
        """
        usages = self.find_counterparty_usages(counterparty_id)
        return len(usages) == 0, usages
    
    def can_delete_object(self, object_id: int) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if object can be deleted
        
        Returns (can_delete, usages)
        """
        usages = self.find_object_usages(object_id)
        return len(usages) == 0, usages
    
    def can_delete_work(self, work_id: int) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if work can be deleted
        
        Returns (can_delete, usages)
        """
        usages = self.find_work_usages(work_id)
        return len(usages) == 0, usages
    
    def can_delete_person(self, person_id: int) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if person can be deleted
        
        Returns (can_delete, usages)
        """
        usages = self.find_person_usages(person_id)
        return len(usages) == 0, usages
    
    def can_delete_organization(self, organization_id: int) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if organization can be deleted
        
        Returns (can_delete, usages)
        """
        usages = self.find_organization_usages(organization_id)
        return len(usages) == 0, usages
