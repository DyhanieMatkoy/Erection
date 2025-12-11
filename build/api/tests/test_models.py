"""
Unit tests for Pydantic models
Tests validation, serialization, and deserialization
"""
import pytest
from pydantic import ValidationError
from datetime import date, datetime
from api.models.auth import LoginRequest, LoginResponse, UserInfo, TokenData
from api.models.references import (
    CounterpartyBase, CounterpartyCreate, Counterparty,
    ObjectBase, ObjectCreate, Object,
    WorkBase, WorkCreate, Work,
    PersonBase, PersonCreate, Person,
    OrganizationBase, OrganizationCreate, Organization
)
from api.models.documents import (
    EstimateBase, EstimateCreate, Estimate,
    EstimateLineBase, EstimateLineCreate, EstimateLine,
    DailyReportBase, DailyReportCreate, DailyReport,
    DailyReportLineBase, DailyReportLineCreate, DailyReportLine,
    TimesheetBase, TimesheetCreate, Timesheet,
    TimesheetLineBase, TimesheetLineCreate, TimesheetLine
)


class TestAuthModels:
    """Test suite for authentication models"""
    
    def test_login_request_valid(self):
        """Test LoginRequest with valid data"""
        data = {"username": "admin", "password": "password123"}
        model = LoginRequest(**data)
        
        assert model.username == "admin"
        assert model.password == "password123"
    
    def test_login_request_missing_username(self):
        """Test LoginRequest with missing username"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(password="password123")
        
        assert "username" in str(exc_info.value)
    
    def test_login_request_missing_password(self):
        """Test LoginRequest with missing password"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="admin")
        
        assert "password" in str(exc_info.value)
    
    def test_login_request_empty_username(self):
        """Test LoginRequest with empty username - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="", password="password123")
        
        assert "username" in str(exc_info.value)
    
    def test_login_request_empty_password(self):
        """Test LoginRequest with empty password - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="admin", password="")
        
        assert "password" in str(exc_info.value)
    
    def test_login_request_username_too_long(self):
        """Test LoginRequest with username exceeding max_length"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="a" * 101, password="password123")
        
        assert "username" in str(exc_info.value)
    
    def test_user_info_valid(self):
        """Test UserInfo with valid data"""
        data = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "is_active": True
        }
        model = UserInfo(**data)
        
        assert model.id == 1
        assert model.username == "admin"
        assert model.role == "admin"
        assert model.is_active is True
    
    def test_user_info_missing_required_fields(self):
        """Test UserInfo with missing required fields"""
        with pytest.raises(ValidationError):
            UserInfo(id=1, username="user")
    
    def test_login_response_valid(self):
        """Test LoginResponse with valid data"""
        user_data = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "is_active": True
        }
        data = {
            "access_token": "token123",
            "token_type": "bearer",
            "expires_in": 28800,
            "user": user_data
        }
        model = LoginResponse(**data)
        
        assert model.access_token == "token123"
        assert model.token_type == "bearer"
        assert model.expires_in == 28800
        assert model.user.username == "admin"
    
    def test_login_response_default_token_type(self):
        """Test LoginResponse with default token_type"""
        user_data = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "is_active": True
        }
        data = {
            "access_token": "token123",
            "expires_in": 28800,
            "user": user_data
        }
        model = LoginResponse(**data)
        
        assert model.token_type == "bearer"
    
    def test_token_data_valid(self):
        """Test TokenData with valid data"""
        now = datetime.now()
        data = {
            "sub": 1,
            "username": "admin",
            "role": "admin",
            "exp": now,
            "iat": now
        }
        model = TokenData(**data)
        
        assert model.sub == 1
        assert model.username == "admin"
        assert model.role == "admin"


class TestReferenceModels:
    """Test suite for reference models"""
    
    # Counterparty Tests
    
    def test_counterparty_base_valid(self):
        """Test CounterpartyBase with valid data"""
        data = {"name": "Test Counterparty"}
        model = CounterpartyBase(**data)
        
        assert model.name == "Test Counterparty"
        assert model.is_deleted is False
    
    def test_counterparty_base_missing_name(self):
        """Test CounterpartyBase with missing name"""
        with pytest.raises(ValidationError):
            CounterpartyBase()
    
    def test_counterparty_base_empty_name(self):
        """Test CounterpartyBase with empty name - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            CounterpartyBase(name="")
        
        assert "name" in str(exc_info.value)
    
    def test_counterparty_base_name_too_long(self):
        """Test CounterpartyBase with name exceeding max_length"""
        with pytest.raises(ValidationError) as exc_info:
            CounterpartyBase(name="a" * 501)
        
        assert "name" in str(exc_info.value)
    
    def test_counterparty_create_with_parent(self):
        """Test CounterpartyCreate with parent_id"""
        data = {
            "name": "Sub Counterparty",
            "parent_id": 1
        }
        model = CounterpartyCreate(**data)
        
        assert model.parent_id == 1
    
    def test_counterparty_full_model(self):
        """Test full Counterparty model"""
        data = {
            "id": 1,
            "name": "Test Counterparty",
            "parent_id": None,
            "is_deleted": False
        }
        model = Counterparty(**data)
        
        assert model.id == 1
        assert model.is_deleted is False
    
    # Object Tests
    
    def test_object_base_valid(self):
        """Test ObjectBase with valid data"""
        data = {"name": "Construction Site A"}
        model = ObjectBase(**data)
        
        assert model.name == "Construction Site A"
    
    def test_object_base_missing_name(self):
        """Test ObjectBase with missing name"""
        with pytest.raises(ValidationError):
            ObjectBase()
    
    def test_object_base_empty_name(self):
        """Test ObjectBase with empty name - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            ObjectBase(name="")
        
        assert "name" in str(exc_info.value)
    
    def test_object_with_address(self):
        """Test Object with address"""
        data = {
            "id": 1,
            "name": "Site A",
            "address": "123 Main St",
            "is_deleted": False
        }
        model = Object(**data)
        
        assert model.address == "123 Main St"
    
    def test_object_with_owner(self):
        """Test Object with owner_id"""
        data = {
            "id": 1,
            "name": "Site A",
            "owner_id": 5,
            "is_deleted": False
        }
        model = Object(**data)
        
        assert model.owner_id == 5
    
    # Work Tests
    
    def test_work_base_valid(self):
        """Test WorkBase with valid data"""
        data = {"name": "Concrete Work", "unit": "m3"}
        model = WorkBase(**data)
        
        assert model.name == "Concrete Work"
        assert model.unit == "m3"
    
    def test_work_base_missing_name(self):
        """Test WorkBase with missing name"""
        with pytest.raises(ValidationError):
            WorkBase()
    
    def test_work_with_parent(self):
        """Test Work with parent_id (hierarchical)"""
        data = {
            "id": 2,
            "name": "Sub Work",
            "unit": "m2",
            "parent_id": 1,
            "is_deleted": False
        }
        model = Work(**data)
        
        assert model.parent_id == 1
    
    # Person Tests
    
    def test_person_base_valid(self):
        """Test PersonBase with valid data"""
        data = {"full_name": "John Doe"}
        model = PersonBase(**data)
        
        assert model.full_name == "John Doe"
    
    def test_person_base_missing_name(self):
        """Test PersonBase with missing full_name"""
        with pytest.raises(ValidationError):
            PersonBase()
    
    def test_person_base_empty_name(self):
        """Test PersonBase with empty full_name - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            PersonBase(full_name="")
        
        assert "full_name" in str(exc_info.value)
    
    def test_person_with_position(self):
        """Test Person with position"""
        data = {
            "id": 1,
            "full_name": "John Doe",
            "position": "Foreman",
            "is_deleted": False
        }
        model = Person(**data)
        
        assert model.position == "Foreman"
    
    # Organization Tests
    
    def test_organization_base_valid(self):
        """Test OrganizationBase with valid data"""
        data = {"name": "ABC Construction"}
        model = OrganizationBase(**data)
        
        assert model.name == "ABC Construction"
    
    def test_organization_base_missing_name(self):
        """Test OrganizationBase with missing name"""
        with pytest.raises(ValidationError):
            OrganizationBase()


class TestDocumentModels:
    """Test suite for document models"""
    
    # Estimate Tests
    
    def test_estimate_base_valid(self):
        """Test EstimateBase with valid data"""
        data = {
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1
        }
        model = EstimateBase(**data)
        
        assert model.number == "EST-001"
        assert model.date == date(2025, 11, 21)
        assert model.customer_id == 1
    
    def test_estimate_base_missing_required(self):
        """Test EstimateBase with missing required fields"""
        with pytest.raises(ValidationError):
            EstimateBase(number="EST-001")
    
    def test_estimate_base_empty_number(self):
        """Test EstimateBase with empty number - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateBase(number="", date=date(2025, 11, 21))
        
        assert "number" in str(exc_info.value)
    
    def test_estimate_base_number_too_long(self):
        """Test EstimateBase with number exceeding max_length"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateBase(number="a" * 101, date=date(2025, 11, 21))
        
        assert "number" in str(exc_info.value)
    
    def test_estimate_create_with_lines(self):
        """Test EstimateCreate with lines"""
        line_data = {
            "line_number": 1,
            "work_id": 1,
            "quantity": 10.0,
            "price": 1000.0,
            "labor_rate": 5.0
        }
        data = {
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1,
            "lines": [line_data]
        }
        model = EstimateCreate(**data)
        
        assert len(model.lines) == 1
        assert model.lines[0].quantity == 10.0
    
    def test_estimate_full_model(self):
        """Test full Estimate model"""
        data = {
            "id": 1,
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1,
            "contractor_id": 2,
            "responsible_id": 3,
            "total_sum": 10000.0,
            "total_labor": 50.0,
            "is_posted": False,
            "posted_at": None,
            "marked_for_deletion": False,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = Estimate(**data)
        
        assert model.id == 1
        assert model.total_sum == 10000.0
        assert model.is_posted is False
    
    # Estimate Line Tests
    
    def test_estimate_line_base_valid(self):
        """Test EstimateLineBase with valid data"""
        data = {
            "line_number": 1,
            "work_id": 1,
            "quantity": 10.0,
            "price": 1000.0,
            "labor_rate": 5.0
        }
        model = EstimateLineBase(**data)
        
        assert model.line_number == 1
        assert model.work_id == 1
        assert model.quantity == 10.0
        assert model.price == 1000.0
        assert model.labor_rate == 5.0
    
    def test_estimate_line_missing_line_number(self):
        """Test EstimateLineBase with missing line_number"""
        with pytest.raises(ValidationError):
            EstimateLineBase(work_id=1, quantity=10.0)
    
    def test_estimate_line_invalid_line_number(self):
        """Test EstimateLineBase with line_number < 1 - should fail ge validation"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=0, work_id=1)
        
        assert "line_number" in str(exc_info.value)
    
    def test_estimate_line_negative_quantity(self):
        """Test EstimateLine with negative quantity - should fail ge validation"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=1, quantity=-10.0)
        
        assert "quantity" in str(exc_info.value)
    
    def test_estimate_line_negative_price(self):
        """Test EstimateLine with negative price - should fail ge validation"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=1, price=-1000.0)
        
        assert "price" in str(exc_info.value)
    
    def test_estimate_line_with_parent(self):
        """Test EstimateLine with parent_group_id (groups)"""
        data = {
            "id": 2,
            "estimate_id": 1,
            "line_number": 2,
            "work_id": 1,
            "parent_group_id": 1,
            "quantity": 10.0,
            "price": 1000.0,
            "labor_rate": 5.0,
            "sum": 10000.0,
            "is_group": False
        }
        model = EstimateLine(**data)
        
        assert model.parent_group_id == 1
        assert model.sum == 10000.0
    
    def test_estimate_line_as_group(self):
        """Test EstimateLine as a group"""
        data = {
            "line_number": 1,
            "is_group": True,
            "group_name": "Foundation Works"
        }
        model = EstimateLineBase(**data)
        
        assert model.is_group is True
        assert model.group_name == "Foundation Works"
    
    # Daily Report Tests
    
    def test_daily_report_base_valid(self):
        """Test DailyReportBase with valid data"""
        data = {
            "date": date(2025, 11, 21),
            "estimate_id": 1,
            "foreman_id": 1
        }
        model = DailyReportBase(**data)
        
        assert model.date == date(2025, 11, 21)
        assert model.estimate_id == 1
        assert model.foreman_id == 1
    
    def test_daily_report_base_missing_date(self):
        """Test DailyReportBase with missing date"""
        with pytest.raises(ValidationError):
            DailyReportBase(estimate_id=1, foreman_id=1)
    
    def test_daily_report_create_with_lines(self):
        """Test DailyReportCreate with lines"""
        line_data = {
            "line_number": 1,
            "work_id": 1,
            "actual_labor": 8.0,
            "executor_ids": [1, 2]
        }
        data = {
            "date": date(2025, 11, 21),
            "estimate_id": 1,
            "foreman_id": 1,
            "lines": [line_data]
        }
        model = DailyReportCreate(**data)
        
        assert len(model.lines) == 1
        assert model.lines[0].actual_labor == 8.0
        assert len(model.lines[0].executor_ids) == 2
    
    def test_daily_report_full_model(self):
        """Test full DailyReport model"""
        data = {
            "id": 1,
            "date": date(2025, 11, 21),
            "estimate_id": 1,
            "foreman_id": 1,
            "is_posted": False,
            "posted_at": None,
            "marked_for_deletion": False,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = DailyReport(**data)
        
        assert model.id == 1
        assert model.is_posted is False
    
    # Daily Report Line Tests
    
    def test_daily_report_line_base_valid(self):
        """Test DailyReportLineBase with valid data"""
        data = {
            "line_number": 1,
            "work_id": 1,
            "actual_labor": 8.0,
            "executor_ids": [1, 2, 3]
        }
        model = DailyReportLineBase(**data)
        
        assert model.line_number == 1
        assert model.work_id == 1
        assert model.actual_labor == 8.0
        assert len(model.executor_ids) == 3
    
    def test_daily_report_line_missing_line_number(self):
        """Test DailyReportLineBase with missing line_number"""
        with pytest.raises(ValidationError):
            DailyReportLineBase(work_id=1, actual_labor=8.0)
    
    def test_daily_report_line_negative_labor(self):
        """Test DailyReportLineBase with negative labor - should fail ge validation"""
        with pytest.raises(ValidationError) as exc_info:
            DailyReportLineBase(line_number=1, actual_labor=-8.0)
        
        assert "actual_labor" in str(exc_info.value)
    
    def test_daily_report_line_empty_executors(self):
        """Test DailyReportLine with empty executors"""
        data = {
            "line_number": 1,
            "work_id": 1,
            "actual_labor": 8.0,
            "executor_ids": []
        }
        model = DailyReportLineBase(**data)
        
        assert len(model.executor_ids) == 0
    
    def test_daily_report_line_full_model(self):
        """Test full DailyReportLine model"""
        data = {
            "id": 1,
            "report_id": 1,
            "line_number": 1,
            "work_id": 1,
            "actual_labor": 8.0,
            "planned_labor": 10.0,
            "deviation_percent": -20.0,
            "executor_ids": [1, 2]
        }
        model = DailyReportLine(**data)
        
        assert model.deviation_percent == -20.0
        assert model.planned_labor == 10.0
    
    # Timesheet Tests
    
    def test_timesheet_base_valid(self):
        """Test TimesheetBase with valid data"""
        data = {
            "number": "TS-001",
            "date": date(2025, 11, 21),
            "month_year": "2025-11"
        }
        model = TimesheetBase(**data)
        
        assert model.number == "TS-001"
        assert model.date == date(2025, 11, 21)
        assert model.month_year == "2025-11"
    
    def test_timesheet_base_missing_required(self):
        """Test TimesheetBase with missing required fields"""
        with pytest.raises(ValidationError):
            TimesheetBase(number="TS-001")
    
    def test_timesheet_base_empty_number(self):
        """Test TimesheetBase with empty number - should fail min_length validation"""
        with pytest.raises(ValidationError) as exc_info:
            TimesheetBase(number="", date=date(2025, 11, 21), month_year="2025-11")
        
        assert "number" in str(exc_info.value)
    
    def test_timesheet_create_with_lines(self):
        """Test TimesheetCreate with lines"""
        line_data = {
            "line_number": 1,
            "employee_id": 1,
            "hourly_rate": 150.0,
            "days": {1: 8.0, 2: 7.5}
        }
        data = {
            "number": "TS-001",
            "date": date(2025, 11, 21),
            "month_year": "2025-11",
            "lines": [line_data]
        }
        model = TimesheetCreate(**data)
        
        assert len(model.lines) == 1
        assert model.lines[0].hourly_rate == 150.0
        assert len(model.lines[0].days) == 2
    
    # Timesheet Line Tests
    
    def test_timesheet_line_base_valid(self):
        """Test TimesheetLineBase with valid data"""
        data = {
            "line_number": 1,
            "employee_id": 1,
            "hourly_rate": 150.0,
            "days": {1: 8.0, 2: 7.5, 3: 8.0}
        }
        model = TimesheetLineBase(**data)
        
        assert model.line_number == 1
        assert model.employee_id == 1
        assert model.hourly_rate == 150.0
        assert len(model.days) == 3
    
    def test_timesheet_line_missing_employee(self):
        """Test TimesheetLineBase with missing employee_id"""
        with pytest.raises(ValidationError):
            TimesheetLineBase(line_number=1, hourly_rate=150.0)
    
    def test_timesheet_line_negative_rate(self):
        """Test TimesheetLineBase with negative hourly_rate - should fail ge validation"""
        with pytest.raises(ValidationError) as exc_info:
            TimesheetLineBase(line_number=1, employee_id=1, hourly_rate=-150.0)
        
        assert "hourly_rate" in str(exc_info.value)
    
    def test_timesheet_line_empty_days(self):
        """Test TimesheetLineBase with empty days dict"""
        data = {
            "line_number": 1,
            "employee_id": 1,
            "hourly_rate": 150.0,
            "days": {}
        }
        model = TimesheetLineBase(**data)
        
        assert len(model.days) == 0


class TestModelSerialization:
    """Test model serialization and deserialization"""
    
    def test_estimate_to_dict(self):
        """Test Estimate model serialization to dict"""
        data = {
            "id": 1,
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1,
            "total_sum": 10000.0,
            "total_labor": 50.0,
            "is_posted": False,
            "marked_for_deletion": False,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = Estimate(**data)
        result = model.model_dump()
        
        assert result["id"] == 1
        assert result["number"] == "EST-001"
        assert result["total_sum"] == 10000.0
    
    def test_estimate_to_json(self):
        """Test Estimate model serialization to JSON"""
        data = {
            "id": 1,
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1,
            "total_sum": 10000.0,
            "total_labor": 50.0,
            "is_posted": False,
            "marked_for_deletion": False,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = Estimate(**data)
        json_str = model.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "EST-001" in json_str
        assert "10000" in json_str
    
    def test_model_from_dict(self):
        """Test model creation from dict"""
        data = {
            "name": "Test Counterparty"
        }
        model = CounterpartyBase.model_validate(data)
        
        assert model.name == "Test Counterparty"
    
    def test_daily_report_to_dict(self):
        """Test DailyReport model serialization to dict"""
        data = {
            "id": 1,
            "date": date(2025, 11, 21),
            "estimate_id": 1,
            "foreman_id": 1,
            "is_posted": False,
            "marked_for_deletion": False,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = DailyReport(**data)
        result = model.model_dump()
        
        assert result["id"] == 1
        assert result["estimate_id"] == 1
        assert result["is_posted"] is False
    
    def test_nested_model_serialization(self):
        """Test serialization of models with nested models"""
        user_data = {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "is_active": True
        }
        data = {
            "access_token": "token123",
            "expires_in": 28800,
            "user": user_data
        }
        model = LoginResponse(**data)
        result = model.model_dump()
        
        assert result["user"]["username"] == "admin"
        assert result["user"]["id"] == 1


class TestModelValidation:
    """Test model validation rules"""
    
    def test_estimate_date_validation(self):
        """Test that date field accepts date objects"""
        data = {
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "customer_id": 1,
            "object_id": 1
        }
        model = EstimateBase(**data)
        assert isinstance(model.date, date)
    
    def test_estimate_numeric_validation(self):
        """Test numeric field validation"""
        data = {
            "line_number": 1,
            "work_id": 1,
            "quantity": 10.5,
            "price": 1000.99,
            "labor_rate": 5.25
        }
        model = EstimateLineBase(**data)
        
        assert model.quantity == 10.5
        assert model.price == 1000.99
        assert model.labor_rate == 5.25
    
    def test_model_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        data = {
            "name": "Test",
            "extra_field": "should be ignored"
        }
        model = CounterpartyBase(**data)
        
        assert model.name == "Test"
        assert not hasattr(model, "extra_field")
    
    def test_model_type_coercion(self):
        """Test that types are coerced when possible"""
        data = {
            "line_number": "1",
            "work_id": "1",  # String instead of int
            "quantity": "10.5",  # String instead of float
            "price": "1000",
            "labor_rate": "5"
        }
        model = EstimateLineBase(**data)
        
        assert model.line_number == 1
        assert model.work_id == 1
        assert model.quantity == 10.5
        assert model.price == 1000.0
        assert model.labor_rate == 5.0
    
    def test_invalid_type_coercion(self):
        """Test that invalid types raise ValidationError"""
        with pytest.raises(ValidationError):
            EstimateLineBase(line_number="not_a_number", work_id=1)
    
    def test_date_string_coercion(self):
        """Test that date strings are coerced to date objects"""
        data = {
            "number": "EST-001",
            "date": "2025-11-21",  # String instead of date
        }
        model = EstimateBase(**data)
        
        assert isinstance(model.date, date)
        assert model.date == date(2025, 11, 21)
    
    def test_invalid_date_format(self):
        """Test that invalid date format raises ValidationError"""
        with pytest.raises(ValidationError):
            EstimateBase(number="EST-001", date="invalid-date")


class TestModelDefaults:
    """Test model default values"""
    
    def test_counterparty_defaults(self):
        """Test Counterparty default values"""
        data = {
            "name": "Test"
        }
        model = CounterpartyBase(**data)
        
        assert model.is_deleted is False  # Default
        assert model.parent_id is None  # Default
    
    def test_estimate_defaults(self):
        """Test Estimate default values"""
        data = {
            "id": 1,
            "number": "EST-001",
            "date": date(2025, 11, 21),
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        model = Estimate(**data)
        
        assert model.is_posted is False  # Default
        assert model.marked_for_deletion is False  # Default
        assert model.posted_at is None  # Default
        assert model.total_sum == 0  # Default
        assert model.total_labor == 0  # Default
    
    def test_estimate_line_defaults(self):
        """Test EstimateLine default values"""
        data = {
            "line_number": 1
        }
        model = EstimateLineBase(**data)
        
        assert model.quantity == 0  # Default
        assert model.price == 0  # Default
        assert model.labor_rate == 0  # Default
        assert model.sum == 0  # Default
        assert model.planned_labor == 0  # Default
        assert model.is_group is False  # Default
        assert model.is_collapsed is False  # Default
    
    def test_daily_report_line_defaults(self):
        """Test DailyReportLine default values"""
        data = {
            "line_number": 1
        }
        model = DailyReportLineBase(**data)
        
        assert model.planned_labor == 0  # Default
        assert model.actual_labor == 0  # Default
        assert model.deviation_percent == 0  # Default
        assert model.executor_ids == []  # Default
        assert model.is_group is False  # Default
    
    def test_timesheet_line_defaults(self):
        """Test TimesheetLine default values"""
        data = {
            "line_number": 1,
            "employee_id": 1
        }
        model = TimesheetLineBase(**data)
        
        assert model.hourly_rate == 0  # Default
        assert model.days == {}  # Default


class TestModelConstraints:
    """Test model field constraints"""
    
    def test_line_number_must_be_positive(self):
        """Test that line_number must be >= 1"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=0)
        
        assert "line_number" in str(exc_info.value)
    
    def test_quantity_must_be_non_negative(self):
        """Test that quantity must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=1, quantity=-5.0)
        
        assert "quantity" in str(exc_info.value)
    
    def test_price_must_be_non_negative(self):
        """Test that price must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=1, price=-100.0)
        
        assert "price" in str(exc_info.value)
    
    def test_labor_rate_must_be_non_negative(self):
        """Test that labor_rate must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            EstimateLineBase(line_number=1, labor_rate=-5.0)
        
        assert "labor_rate" in str(exc_info.value)
    
    def test_actual_labor_must_be_non_negative(self):
        """Test that actual_labor must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            DailyReportLineBase(line_number=1, actual_labor=-8.0)
        
        assert "actual_labor" in str(exc_info.value)
    
    def test_planned_labor_must_be_non_negative(self):
        """Test that planned_labor must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            DailyReportLineBase(line_number=1, planned_labor=-10.0)
        
        assert "planned_labor" in str(exc_info.value)
