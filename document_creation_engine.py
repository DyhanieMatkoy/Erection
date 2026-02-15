"""Document Creation Engine

This module provides document creation functionality for the sync end-to-end testing system.
It creates realistic test documents (estimates, daily reports, timesheets) with proper data relationships.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add project root to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class DocumentTemplate:
    """Base template for test documents"""
    type: str
    name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EstimateTemplate(DocumentTemplate):
    """Template for estimate documents"""
    def __init__(self):
        super().__init__(
            type="estimate",
            name="Test Estimate",
            description="End-to-end test estimate document",
            required_fields=["number", "date", "customer_id", "object_id", "contractor_id", "responsible_id"],
            optional_fields=["total_sum", "total_labor", "estimate_type", "base_document_id"]
        )


@dataclass
class DailyReportTemplate(DocumentTemplate):
    """Template for daily report documents"""
    def __init__(self):
        super().__init__(
            type="daily_report",
            name="Test Daily Report",
            description="End-to-end test daily report document",
            required_fields=["number", "date", "estimate_id", "foreman_id"],
            optional_fields=["is_posted", "posted_at"]
        )


@dataclass
class TimesheetTemplate(DocumentTemplate):
    """Template for timesheet documents"""
    def __init__(self):
        super().__init__(
            type="timesheet",
            name="Test Timesheet",
            description="End-to-end test timesheet document",
            required_fields=["number", "date", "object_id", "estimate_id", "foreman_id", "month_year"],
            optional_fields=["is_posted", "posted_at", "marked_for_deletion"]
        )


class DocumentDataGenerator:
    """Generates realistic test data for documents"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize document data generator
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
        # Test data pools
        self.customer_names = [
            "ООО 'Строительная компания Альфа'",
            "АО 'Бета Строй'",
            "ИП Иванов И.И.",
            "ООО 'Гамма Девелопмент'",
            "ЗАО 'Дельта Инвест'"
        ]
        
        self.object_names = [
            "Жилой комплекс 'Солнечный'",
            "Торговый центр 'Европа'",
            "Офисное здание 'Бизнес Парк'",
            "Складской комплекс 'Логистик'",
            "Производственный цех №1"
        ]
        
        self.contractor_names = [
            "ООО 'СтройМастер'",
            "АО 'ПрофиСтрой'",
            "ООО 'Надежный Подрядчик'",
            "ИП Петров П.П.",
            "ООО 'Качественное Строительство'"
        ]
        
        self.person_names = [
            "Иванов Иван Иванович",
            "Петров Петр Петрович", 
            "Сидоров Сидор Сидорович",
            "Козлов Козьма Козьмич",
            "Васильев Василий Васильевич"
        ]
        
        self.work_types = [
            {"name": "Земляные работы", "unit": "м3", "price": 150.0, "labor_rate": 0.5},
            {"name": "Бетонные работы", "unit": "м3", "price": 3500.0, "labor_rate": 2.0},
            {"name": "Кирпичная кладка", "unit": "м2", "price": 800.0, "labor_rate": 1.2},
            {"name": "Штукатурные работы", "unit": "м2", "price": 250.0, "labor_rate": 0.8},
            {"name": "Малярные работы", "unit": "м2", "price": 180.0, "labor_rate": 0.6}
        ]
    
    def generate_estimate_data(self, client_id: str) -> Dict[str, Any]:
        """Generate realistic estimate document data
        
        Args:
            client_id: Client identifier for unique data
            
        Returns:
            Estimate document data
        """
        timestamp = datetime.now(timezone.utc)
        
        # Generate unique document number
        doc_number = f"EST-{client_id.upper()}-{timestamp.strftime('%Y%m%d')}-{timestamp.microsecond // 1000:03d}"
        
        estimate_data = {
            "number": doc_number,
            "date": timestamp.date().isoformat(),
            "customer_id": 1,  # Will be resolved to actual ID
            "object_id": 1,    # Will be resolved to actual ID
            "contractor_id": 1, # Will be resolved to actual ID
            "responsible_id": 1, # Will be resolved to actual ID
            "total_sum": 0.0,
            "total_labor": 0.0,
            "estimate_type": "General",
            "created_at": timestamp.isoformat(),
            "modified_at": timestamp.isoformat(),
            
            # Estimate lines
            "lines": []
        }
        
        # Generate estimate lines
        total_sum = 0.0
        total_labor = 0.0
        
        for i, work_type in enumerate(self.work_types[:3], 1):  # Use first 3 work types
            quantity = 10.0 + (i * 5.0)  # Varying quantities
            line_sum = quantity * work_type["price"]
            line_labor = quantity * work_type["labor_rate"]
            
            line_data = {
                "line_number": i,
                "work_id": i,  # Will be resolved to actual work ID
                "quantity": quantity,
                "unit": work_type["unit"],
                "price": work_type["price"],
                "labor_rate": work_type["labor_rate"],
                "sum": line_sum,
                "planned_labor": line_labor,
                "is_group": 0,
                "group_name": None,
                "parent_group_id": None,
                "is_collapsed": 0
            }
            
            estimate_data["lines"].append(line_data)
            total_sum += line_sum
            total_labor += line_labor
        
        estimate_data["total_sum"] = total_sum
        estimate_data["total_labor"] = total_labor
        
        self.logger.debug(f"Generated estimate data for {client_id}: {doc_number}")
        return estimate_data
    
    def generate_daily_report_data(self, client_id: str, estimate_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate realistic daily report document data
        
        Args:
            client_id: Client identifier for unique data
            estimate_id: Optional estimate ID to link to
            
        Returns:
            Daily report document data
        """
        timestamp = datetime.now(timezone.utc)
        
        # Generate unique document number
        doc_number = f"DR-{client_id.upper()}-{timestamp.strftime('%Y%m%d')}-{timestamp.microsecond // 1000:03d}"
        
        daily_report_data = {
            "number": doc_number,
            "date": timestamp.date().isoformat(),
            "estimate_id": estimate_id or 1,  # Will be resolved to actual ID
            "foreman_id": 1,  # Will be resolved to actual ID
            "is_posted": 0,
            "posted_at": None,
            "created_at": timestamp.isoformat(),
            "modified_at": timestamp.isoformat(),
            
            # Daily report lines
            "lines": [],
            "executors": []
        }
        
        # Generate daily report lines
        for i, work_type in enumerate(self.work_types[:2], 1):  # Use first 2 work types
            planned_labor = 8.0 + (i * 2.0)  # Varying planned labor
            actual_labor = planned_labor * (0.9 + (i * 0.05))  # Slight variations
            deviation = ((actual_labor - planned_labor) / planned_labor * 100) if planned_labor > 0 else 0
            
            line_data = {
                "line_number": i,
                "work_id": i,  # Will be resolved to actual work ID
                "planned_labor": planned_labor,
                "actual_labor": actual_labor,
                "labor_deviation_percent": deviation,
                "is_group": 0,
                "group_name": None,
                "parent_group_id": None,
                "is_collapsed": 0
            }
            
            daily_report_data["lines"].append(line_data)
            
            # Add executors for this line
            daily_report_data["executors"].append({
                "report_line_id": i,  # Will be resolved after line creation
                "executor_id": 1  # Will be resolved to actual person ID
            })
        
        self.logger.debug(f"Generated daily report data for {client_id}: {doc_number}")
        return daily_report_data
    
    def generate_timesheet_data(self, client_id: str, estimate_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate realistic timesheet document data
        
        Args:
            client_id: Client identifier for unique data
            estimate_id: Optional estimate ID to link to
            
        Returns:
            Timesheet document data
        """
        timestamp = datetime.now(timezone.utc)
        
        # Generate unique document number
        doc_number = f"TS-{client_id.upper()}-{timestamp.strftime('%Y%m%d')}-{timestamp.microsecond // 1000:03d}"
        
        # Current month/year
        month_year = timestamp.strftime('%m.%Y')
        
        timesheet_data = {
            "number": doc_number,
            "date": timestamp.date().isoformat(),
            "object_id": 1,    # Will be resolved to actual ID
            "estimate_id": estimate_id or 1,  # Will be resolved to actual ID
            "foreman_id": 1,   # Will be resolved to actual ID
            "month_year": month_year,
            "is_posted": 0,
            "posted_at": None,
            "marked_for_deletion": 0,
            "created_at": timestamp.isoformat(),
            "modified_at": timestamp.isoformat(),
            
            # Timesheet lines
            "lines": []
        }
        
        # Generate timesheet lines for 2 employees
        for i in range(1, 3):
            hourly_rate = 200.0 + (i * 50.0)  # Varying hourly rates
            
            # Generate working days (simplified - 8 hours for first 20 days)
            line_data = {
                "line_number": i,
                "employee_id": i,  # Will be resolved to actual person ID
                "hourly_rate": hourly_rate,
                "total_hours": 0.0,
                "total_amount": 0.0
            }
            
            # Add daily hours (first 20 days of month)
            total_hours = 0.0
            for day in range(1, 21):  # Working days
                hours = 8.0 if day <= 20 else 0.0
                line_data[f"day_{day:02d}"] = hours
                total_hours += hours
            
            # Fill remaining days with 0
            for day in range(21, 32):
                line_data[f"day_{day:02d}"] = 0.0
            
            line_data["total_hours"] = total_hours
            line_data["total_amount"] = total_hours * hourly_rate
            
            timesheet_data["lines"].append(line_data)
        
        self.logger.debug(f"Generated timesheet data for {client_id}: {doc_number}")
        return timesheet_data


class DocumentCreationEngine:
    """Engine for creating test documents on desktop clients"""
    
    def __init__(self, desktop_clients: List, logger: logging.Logger):
        """Initialize document creation engine
        
        Args:
            desktop_clients: List of TestDesktopClient instances
            logger: Logger instance
        """
        self.desktop_clients = desktop_clients
        self.logger = logger
        
        # Initialize components
        self.data_generator = DocumentDataGenerator(logger)
        
        # Document templates
        self.templates = {
            'estimate': EstimateTemplate(),
            'daily_report': DailyReportTemplate(),
            'timesheet': TimesheetTemplate()
        }
        
        # Created documents tracking
        self.created_documents: List[Dict[str, Any]] = []
        
        self.logger.info("Document creation engine initialized")
    
    def create_document(self, client, doc_type: str) -> Dict[str, Any]:
        """Create a document on the specified client
        
        Args:
            client: TestDesktopClient instance
            doc_type: Type of document to create
            
        Returns:
            Created document information
        """
        try:
            self.logger.info(f"Creating {doc_type} document on {client.client_id}")
            
            if doc_type not in self.templates:
                raise ValueError(f"Unknown document type: {doc_type}")
            
            # Generate document data
            if doc_type == 'estimate':
                doc_data = self.data_generator.generate_estimate_data(client.client_id)
            elif doc_type == 'daily_report':
                doc_data = self.data_generator.generate_daily_report_data(client.client_id)
            elif doc_type == 'timesheet':
                doc_data = self.data_generator.generate_timesheet_data(client.client_id)
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
            
            # Create document in client database
            self.logger.debug(f"Creating {doc_type} document in database for {client.client_id}")
            created_doc = self._create_document_in_database(client, doc_type, doc_data)
            self.logger.debug(f"Document created in database: {created_doc}")
            
            # Validate created document has required fields
            if 'id' not in created_doc:
                raise ValueError(f"Created document missing 'id' field: {created_doc}")
            
            # Track created document
            document_info = {
                'type': doc_type,
                'client_id': client.client_id,
                'document_id': created_doc['id'],
                'document_number': created_doc['number'],
                'created_at': created_doc['created_at'],
                'data': doc_data
            }
            
            self.created_documents.append(document_info)
            
            self.logger.info(f"Successfully created {doc_type} document {created_doc['number']} on {client.client_id}")
            return document_info
            
        except Exception as e:
            self.logger.error(f"Failed to create {doc_type} document on {client.client_id}: {e}")
            raise
    
    def _create_document_in_database(self, client, doc_type: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create document in client database
        
        Args:
            client: TestDesktopClient instance
            doc_type: Document type
            doc_data: Document data
            
        Returns:
            Created document information with ID
        """
        if not client.db_manager:
            raise Exception("Client database manager not initialized")
        
        try:
            if doc_type == 'estimate':
                return self._create_estimate_in_db(client.db_manager, doc_data)
            elif doc_type == 'daily_report':
                return self._create_daily_report_in_db(client.db_manager, doc_data)
            elif doc_type == 'timesheet':
                return self._create_timesheet_in_db(client.db_manager, doc_data)
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
                
        except Exception as e:
            self.logger.error(f"Database error creating {doc_type}: {e}")
            raise
    
    def _create_estimate_in_db(self, db_manager, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create estimate document in database
        
        Args:
            db_manager: Database manager instance
            doc_data: Estimate document data
            
        Returns:
            Created estimate information
        """
        # Ensure required reference data exists
        self._ensure_reference_data(db_manager)
        
        # Insert estimate header
        estimate_query = """
            INSERT INTO estimates (
                number, date, customer_id, object_id, contractor_id, responsible_id,
                total_sum, total_labor, estimate_type, created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        estimate_params = (
            doc_data['number'],
            doc_data['date'],
            doc_data['customer_id'],
            doc_data['object_id'],
            doc_data['contractor_id'],
            doc_data['responsible_id'],
            doc_data['total_sum'],
            doc_data['total_labor'],
            doc_data['estimate_type'],
            doc_data['created_at'],
            doc_data['modified_at']
        )
        
        estimate_id = db_manager.execute_update(estimate_query, estimate_params)
        
        # Insert estimate lines
        for line in doc_data.get('lines', []):
            line_query = """
                INSERT INTO estimate_lines (
                    estimate_id, line_number, work_id, quantity, unit, price,
                    labor_rate, sum, planned_labor, is_group, group_name,
                    parent_group_id, is_collapsed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            line_params = (
                estimate_id,
                line['line_number'],
                line['work_id'],
                line['quantity'],
                line['unit'],
                line['price'],
                line['labor_rate'],
                line['sum'],
                line['planned_labor'],
                line['is_group'],
                line['group_name'],
                line['parent_group_id'],
                line['is_collapsed']
            )
            
            db_manager.execute_update(line_query, line_params)
        
        return {
            'id': estimate_id,
            'number': doc_data['number'],
            'created_at': doc_data['created_at']
        }
    
    def _create_daily_report_in_db(self, db_manager, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create daily report document in database
        
        Args:
            db_manager: Database manager instance
            doc_data: Daily report document data
            
        Returns:
            Created daily report information
        """
        # Ensure required reference data exists
        self._ensure_reference_data(db_manager)
        
        # Insert daily report header
        report_query = """
            INSERT INTO daily_reports (
                number, date, estimate_id, foreman_id, is_posted, posted_at,
                created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        report_params = (
            doc_data['number'],
            doc_data['date'],
            doc_data['estimate_id'],
            doc_data['foreman_id'],
            doc_data['is_posted'],
            doc_data['posted_at'],
            doc_data['created_at'],
            doc_data['modified_at']
        )
        
        report_id = db_manager.execute_update(report_query, report_params)
        
        # Insert daily report lines
        line_ids = []
        for line in doc_data.get('lines', []):
            line_query = """
                INSERT INTO daily_report_lines (
                    report_id, line_number, work_id, planned_labor, actual_labor,
                    labor_deviation_percent, is_group, group_name, parent_group_id,
                    is_collapsed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            line_params = (
                report_id,
                line['line_number'],
                line['work_id'],
                line['planned_labor'],
                line['actual_labor'],
                line['labor_deviation_percent'],
                line['is_group'],
                line['group_name'],
                line['parent_group_id'],
                line['is_collapsed']
            )
            
            line_id = db_manager.execute_update(line_query, line_params)
            line_ids.append(line_id)
        
        # Insert executors
        for i, executor in enumerate(doc_data.get('executors', [])):
            if i < len(line_ids):
                executor_query = """
                    INSERT INTO daily_report_executors (report_line_id, executor_id)
                    VALUES (?, ?)
                """
                
                executor_params = (line_ids[i], executor['executor_id'])
                db_manager.execute_update(executor_query, executor_params)
        
        return {
            'id': report_id,
            'number': doc_data['number'],
            'created_at': doc_data['created_at']
        }
    
    def _create_timesheet_in_db(self, db_manager, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create timesheet document in database
        
        Args:
            db_manager: Database manager instance
            doc_data: Timesheet document data
            
        Returns:
            Created timesheet information
        """
        # Ensure required reference data exists
        self._ensure_reference_data(db_manager)
        
        # Insert timesheet header
        timesheet_query = """
            INSERT INTO timesheets (
                number, date, object_id, estimate_id, foreman_id, month_year,
                is_posted, posted_at, marked_for_deletion, created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        timesheet_params = (
            doc_data['number'],
            doc_data['date'],
            doc_data['object_id'],
            doc_data['estimate_id'],
            doc_data['foreman_id'],
            doc_data['month_year'],
            doc_data['is_posted'],
            doc_data['posted_at'],
            doc_data['marked_for_deletion'],
            doc_data['created_at'],
            doc_data['modified_at']
        )
        
        timesheet_id = db_manager.execute_update(timesheet_query, timesheet_params)
        
        # Insert timesheet lines
        for line in doc_data.get('lines', []):
            # Build dynamic query for all day columns
            day_columns = [f"day_{i:02d}" for i in range(1, 32)]
            day_placeholders = ", ".join(["?"] * len(day_columns))
            
            line_query = f"""
                INSERT INTO timesheet_lines (
                    timesheet_id, line_number, employee_id, hourly_rate,
                    {", ".join(day_columns)}, total_hours, total_amount
                ) VALUES (?, ?, ?, ?, {day_placeholders}, ?, ?)
            """
            
            # Build parameters
            line_params = [
                timesheet_id,
                line['line_number'],
                line['employee_id'],
                line['hourly_rate']
            ]
            
            # Add day values
            for day_col in day_columns:
                line_params.append(line.get(day_col, 0.0))
            
            # Add totals
            line_params.extend([
                line['total_hours'],
                line['total_amount']
            ])
            
            db_manager.execute_update(line_query, tuple(line_params))
        
        return {
            'id': timesheet_id,
            'number': doc_data['number'],
            'created_at': doc_data['created_at']
        }
    
    def _ensure_reference_data(self, db_manager):
        """Ensure required reference data exists in database
        
        Args:
            db_manager: Database manager instance
        """
        try:
            # Check if reference data exists, create if not
            
            # Ensure at least one counterparty (customer)
            customers = db_manager.execute_query("SELECT COUNT(*) as count FROM counterparties")
            if customers and len(customers) > 0 and customers[0][0] == 0:
                db_manager.execute_update(
                    "INSERT INTO counterparties (name, inn) VALUES (?, ?)",
                    ("Тестовый заказчик", "1234567890")
                )
            
            # Ensure at least one object
            objects = db_manager.execute_query("SELECT COUNT(*) as count FROM objects")
            if objects and len(objects) > 0 and objects[0][0] == 0:
                db_manager.execute_update(
                    "INSERT INTO objects (name, owner_id, address) VALUES (?, ?, ?)",
                    ("Тестовый объект", 1, "Тестовый адрес")
                )
            
            # Ensure at least one organization (contractor)
            organizations = db_manager.execute_query("SELECT COUNT(*) as count FROM organizations")
            if organizations and len(organizations) > 0 and organizations[0][0] == 0:
                db_manager.execute_update(
                    "INSERT INTO organizations (name, inn) VALUES (?, ?)",
                    ("Тестовая организация", "0987654321")
                )
            
            # Ensure at least one person (responsible/foreman)
            persons = db_manager.execute_query("SELECT COUNT(*) as count FROM persons")
            if persons and len(persons) > 0 and persons[0][0] == 0:
                db_manager.execute_update(
                    "INSERT INTO persons (full_name, position) VALUES (?, ?)",
                    ("Тестовый сотрудник", "Прораб")
                )
            
            # Ensure at least one work type
            works = db_manager.execute_query("SELECT COUNT(*) as count FROM works")
            if works and len(works) > 0 and works[0][0] == 0:
                for work_type in self.data_generator.work_types:
                    db_manager.execute_update(
                        "INSERT INTO works (name, unit, price, labor_rate) VALUES (?, ?, ?, ?)",
                        (work_type['name'], work_type['unit'], work_type['price'], work_type['labor_rate'])
                    )
            
        except Exception as e:
            self.logger.warning(f"Error ensuring reference data: {e}")
            # Continue without reference data - tests can still run
    
    def verify_initial_document_distribution(self, clients: List) -> Dict[str, Any]:
        """Verify that documents exist only in their respective client databases
        
        Args:
            clients: List of TestDesktopClient instances
            
        Returns:
            Verification results
        """
        try:
            self.logger.info("Verifying initial document distribution")
            
            verification_results = {
                'success': True,
                'total_documents': len(self.created_documents),
                'verified_distributions': 0,
                'distribution_errors': [],
                'details': []
            }
            
            for doc_info in self.created_documents:
                doc_type = doc_info['type']
                creator_client_id = doc_info['client_id']
                document_number = doc_info['document_number']
                
                # Check each client
                for client in clients:
                    should_exist = (client.client_id == creator_client_id)
                    actually_exists = self._document_exists_in_client(client, doc_type, document_number)
                    
                    if should_exist and actually_exists:
                        verification_results['verified_distributions'] += 1
                        verification_results['details'].append({
                            'document': document_number,
                            'client': client.client_id,
                            'status': 'correctly_present'
                        })
                    elif not should_exist and not actually_exists:
                        verification_results['details'].append({
                            'document': document_number,
                            'client': client.client_id,
                            'status': 'correctly_absent'
                        })
                    else:
                        # Error case
                        error_status = 'unexpectedly_present' if actually_exists else 'unexpectedly_absent'
                        verification_results['distribution_errors'].append({
                            'document': document_number,
                            'client': client.client_id,
                            'status': error_status
                        })
                        verification_results['success'] = False
            
            if verification_results['success']:
                self.logger.info("Initial document distribution verified successfully")
            else:
                self.logger.warning(f"Document distribution errors found: {len(verification_results['distribution_errors'])}")
            
            return verification_results
            
        except Exception as e:
            self.logger.error(f"Failed to verify initial document distribution: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _document_exists_in_client(self, client, doc_type: str, document_number: str) -> bool:
        """Check if document exists in client database
        
        Args:
            client: TestDesktopClient instance
            doc_type: Document type
            document_number: Document number to check
            
        Returns:
            True if document exists
        """
        try:
            if not client.db_manager:
                return False
            
            # Map document types to table names
            table_map = {
                'estimate': 'estimates',
                'daily_report': 'daily_reports',
                'timesheet': 'timesheets'
            }
            
            table_name = table_map.get(doc_type)
            if not table_name:
                return False
            
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE number = ?"
            result = client.db_manager.execute_query(query, (document_number,))
            
            return result[0]['count'] > 0
            
        except Exception as e:
            self.logger.debug(f"Error checking document existence in {client.client_id}: {e}")
            return False
    
    def get_created_documents(self) -> List[Dict[str, Any]]:
        """Get list of all created documents
        
        Returns:
            List of created document information
        """
        return self.created_documents.copy()
    
    def get_document_summary(self) -> Dict[str, Any]:
        """Get summary of created documents
        
        Returns:
            Document creation summary
        """
        summary = {
            'total_documents': len(self.created_documents),
            'by_type': {},
            'by_client': {}
        }
        
        for doc_info in self.created_documents:
            doc_type = doc_info['type']
            client_id = doc_info['client_id']
            
            # Count by type
            if doc_type not in summary['by_type']:
                summary['by_type'][doc_type] = 0
            summary['by_type'][doc_type] += 1
            
            # Count by client
            if client_id not in summary['by_client']:
                summary['by_client'][client_id] = 0
            summary['by_client'][client_id] += 1
        
        return summary