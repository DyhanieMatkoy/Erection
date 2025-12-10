"""Reference repository with usage checking"""
from typing import List, Tuple
from ..database_manager import DatabaseManager


class ReferenceRepository:
    """Repository for reference data with usage checking"""
    
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
    def find_counterparty_usages(self, counterparty_id: int) -> List[Tuple[str, str]]:
        """Find where counterparty is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        cursor = self.db.cursor()
        
        # Check in estimates (as customer)
        cursor.execute("""
            SELECT id, number, date
            FROM estimates
            WHERE customer_id = ?
        """, (counterparty_id,))
        
        for row in cursor.fetchall():
            usages.append(("Смета (Заказчик)", f"№{row['number']} от {row['date']}"))
        
        # Check in objects (as owner)
        cursor.execute("""
            SELECT id, name
            FROM objects
            WHERE owner_id = ?
        """, (counterparty_id,))
        
        for row in cursor.fetchall():
            usages.append(("Объект (Владелец)", row['name']))
        
        return usages
    
    def find_object_usages(self, object_id: int) -> List[Tuple[str, str]]:
        """Find where object is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        cursor = self.db.cursor()
        
        # Check in estimates
        cursor.execute("""
            SELECT id, number, date
            FROM estimates
            WHERE object_id = ?
        """, (object_id,))
        
        for row in cursor.fetchall():
            usages.append(("Смета", f"№{row['number']} от {row['date']}"))
        
        return usages
    
    def find_work_usages(self, work_id: int) -> List[Tuple[str, str]]:
        """Find where work is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        cursor = self.db.cursor()
        
        # Check in estimate lines
        cursor.execute("""
            SELECT DISTINCT e.id, e.number, e.date
            FROM estimate_lines el
            JOIN estimates e ON el.estimate_id = e.id
            WHERE el.work_id = ?
        """, (work_id,))
        
        for row in cursor.fetchall():
            usages.append(("Смета (строка)", f"№{row['number']} от {row['date']}"))
        
        # Check in daily report lines
        cursor.execute("""
            SELECT DISTINCT dr.id, dr.date
            FROM daily_report_lines drl
            JOIN daily_reports dr ON drl.report_id = dr.id
            WHERE drl.work_id = ?
        """, (work_id,))
        
        for row in cursor.fetchall():
            usages.append(("Ежедневный отчет (строка)", f"от {row['date']}"))
        
        return usages
    
    def find_person_usages(self, person_id: int) -> List[Tuple[str, str]]:
        """Find where person is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        cursor = self.db.cursor()
        
        # Check in estimates (as responsible)
        cursor.execute("""
            SELECT id, number, date
            FROM estimates
            WHERE responsible_id = ?
        """, (person_id,))
        
        for row in cursor.fetchall():
            usages.append(("Смета (Ответственный)", f"№{row['number']} от {row['date']}"))
        
        # Check in daily reports (as foreman)
        cursor.execute("""
            SELECT id, date
            FROM daily_reports
            WHERE foreman_id = ?
        """, (person_id,))
        
        for row in cursor.fetchall():
            usages.append(("Ежедневный отчет (Бригадир)", f"от {row['date']}"))
        
        # Check in daily report executors
        cursor.execute("""
            SELECT DISTINCT dr.id, dr.date
            FROM daily_report_executors dre
            JOIN daily_report_lines drl ON dre.report_line_id = drl.id
            JOIN daily_reports dr ON drl.report_id = dr.id
            WHERE dre.executor_id = ?
        """, (person_id,))
        
        for row in cursor.fetchall():
            usages.append(("Ежедневный отчет (Исполнитель)", f"от {row['date']}"))
        
        # Check in organizations (as default responsible)
        cursor.execute("""
            SELECT id, name
            FROM organizations
            WHERE default_responsible_id = ?
        """, (person_id,))
        
        for row in cursor.fetchall():
            usages.append(("Организация (Ответственный по умолчанию)", row['name']))
        
        return usages
    
    def find_organization_usages(self, organization_id: int) -> List[Tuple[str, str]]:
        """Find where organization is used
        
        Returns list of tuples (document_type, document_info)
        """
        usages = []
        cursor = self.db.cursor()
        
        # Check in estimates (as contractor)
        cursor.execute("""
            SELECT id, number, date
            FROM estimates
            WHERE contractor_id = ?
        """, (organization_id,))
        
        for row in cursor.fetchall():
            usages.append(("Смета (Подрядчик)", f"№{row['number']} от {row['date']}"))
        
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
