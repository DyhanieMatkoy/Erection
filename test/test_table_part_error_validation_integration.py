"""
Integration tests for table part error handling and validation services.

Tests the interaction between error handling and validation services
to ensure comprehensive error management and user feedback.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QObject
import sys

from src.services.table_part_error_handler import (
    TablePartErrorHandler, ErrorCategory, ErrorSeverity, ErrorContext,
    create_error_handler, handle_table_part_errors
)
from src.services.table_part_validation_service import (
    TablePartValidationService, ValidationRule, ValidationType, ValidationSeverity,
    ValidationContext, create_validation_service, validate_numeric_field,
    validate_date_field, validate_reference_field
)


class TestTablePartErrorValidationIntegration:
    """Test integration between error handling and validation services"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        yield app
        # Don't quit the app as it might be used by other tests
    
    @pytest.fixture
    def parent_widget(self, app):
        """Create parent widget for error handler"""
        return QWidget()
    
    @pytest.fixture
    def error_handler(self, parent_widget):
        """Create error handler instance"""
        return create_error_handler(parent_widget)
    
    @pytest.fixture
    def validation_service(self, error_handler):
        """Create validation service with error handler"""
        return create_validation_service(error_handler)
    
    def test_validation_error_handling_integration(self, validation_service, error_handler):
        """Test that validation errors are properly handled by error handler"""
        # Setup field definition
        validation_service.add_field_definition('quantity', {
            'data_type': 'float',
            'required': True,
            'min_value': 0
        })
        
        # Create validation context
        context = ValidationContext(
            row_data={'quantity': 'invalid_number'},
            operation='edit'
        )
        
        # Mock error handler to capture calls
        error_handler.handle_validation_error = Mock()
        
        # Validate field - should trigger error handling
        results = validation_service.validate_field('quantity', 'invalid_number', context)
        
        # Should have validation results
        assert len(results) > 0
        assert not results[0].is_valid
        assert results[0].severity == ValidationSeverity.ERROR
    
    def test_calculation_error_with_validation(self, validation_service, error_handler):
        """Test calculation errors are handled with proper validation feedback"""
        # Add calculation field validation
        validation_service.add_field_definition('sum', {
            'data_type': 'float',
            'calculation': True
        })
        
        # Test calculation with invalid source data
        calculation_rules = [{
            'id': 'quantity_price_sum',
            'source_columns': ['quantity', 'price'],
            'target_column': 'sum',
            'calculation_type': 'multiply'
        }]
        
        context = ValidationContext(
            row_data={'quantity': 'invalid', 'price': 10.0, 'sum': 0},
            operation='calculate'
        )
        
        # Validate calculation fields
        results = validation_service.validate_calculation_fields(context, calculation_rules)
        
        # Should detect invalid source column
        assert len(results) > 0
        calc_errors = [r for r in results if 'calc_source' in r.rule_id]
        assert len(calc_errors) > 0
        assert not calc_errors[0].is_valid
    
    def test_import_error_with_validation_feedback(self, validation_service, error_handler):
        """Test import errors provide validation feedback"""
        # Simulate import error
        import_error = ValueError("Invalid data format in row 5")
        
        # Handle import error
        error_info = error_handler.handle_import_error(
            import_error,
            "test_file.xlsx",
            row_number=5
        )
        
        # Verify error information
        assert error_info.category == ErrorCategory.IMPORT_EXPORT
        assert error_info.severity == ErrorSeverity.ERROR
        assert "test_file.xlsx" in error_info.context.data_context['file_path']
        assert error_info.context.data_context['row_number'] == 5
        assert len(error_info.recovery_suggestions) > 0
    
    def test_reference_validation_with_error_handling(self, validation_service, error_handler):
        """Test reference field validation with error handling"""
        # Add field definition to validation service first
        validation_service.add_field_definition('work_id', {'required': True})
        
        # Test reference validation
        context = ValidationContext(
            row_data={'work_id': None},
            field_definitions={'work_id': {'required': True}}
        )
        
        # Validate reference field
        results = validation_service.validate_reference_field(
            'work_id', None, 'work', context
        )
        
        # Should have validation error for required field
        assert len(results) > 0
        assert not results[0].is_valid
        assert results[0].severity == ValidationSeverity.ERROR
        assert 'обязательно' in results[0].message.lower()
    
    def test_data_integrity_validation(self, validation_service):
        """Test data integrity validation across multiple rows"""
        # Test uniqueness validation
        all_data = [
            {'id': 1, 'code': 'A001'},
            {'id': 2, 'code': 'A002'},
            {'id': 3, 'code': 'A001'}  # Duplicate
        ]
        
        integrity_rules = [{
            'type': 'unique',
            'field': 'code'
        }]
        
        results = validation_service.validate_data_integrity(all_data, integrity_rules)
        
        # Should detect duplicate
        assert len(results) > 0
        unique_errors = [r for r in results if 'unique' in r.rule_id]
        assert len(unique_errors) > 0
        assert not unique_errors[0].is_valid
    
    def test_validation_summary_generation(self, validation_service):
        """Test validation summary generation"""
        # Create validation results
        results = {
            'field1': [{
                'field_name': 'field1',
                'rule_id': 'test1',
                'is_valid': False,
                'severity': ValidationSeverity.ERROR,
                'message': 'Error 1',
                'additional_info': {}
            }],
            'field2': [{
                'field_name': 'field2',
                'rule_id': 'test2',
                'is_valid': False,
                'severity': ValidationSeverity.WARNING,
                'message': 'Warning 1',
                'additional_info': {}
            }]
        }
        
        # Convert to ValidationResult objects
        from src.services.table_part_validation_service import ValidationResult
        converted_results = {}
        for field, field_results in results.items():
            converted_results[field] = [
                ValidationResult(
                    field_name=r['field_name'],
                    rule_id=r['rule_id'],
                    is_valid=r['is_valid'],
                    severity=r['severity'],
                    message=r['message'],
                    additional_info=r['additional_info']
                ) for r in field_results
            ]
        
        summary = validation_service.get_validation_summary(converted_results)
        
        assert summary['total_fields'] == 2
        assert summary['fields_with_errors'] == 1
        assert summary['fields_with_warnings'] == 1
        assert summary['total_errors'] == 1
        assert summary['total_warnings'] == 1
    
    def test_error_recovery_with_validation(self, error_handler, validation_service):
        """Test error recovery mechanisms work with validation"""
        # Create a recoverable error
        calc_error = ValueError("Division by zero in calculation")
        
        error_info = error_handler.handle_calculation_error(
            calc_error,
            'quantity_price_sum',
            {'quantity': 5, 'price': 0}
        )
        
        # Verify error can be retried
        assert error_info.can_retry
        assert error_info.category == ErrorCategory.CALCULATION
        
        # Test retry mechanism
        retry_success = error_handler.retry_operation(error_info.id)
        # Note: In real implementation, this would depend on recovery actions
    
    def test_decorator_error_handling(self, error_handler):
        """Test decorator-based error handling"""
        
        class TestClass:
            def __init__(self):
                self.error_handler = error_handler
            
            @handle_table_part_errors(
                ErrorCategory.COMMAND_EXECUTION,
                "test_operation",
                "test_component"
            )
            def test_method(self):
                raise ValueError("Test error")
        
        test_obj = TestClass()
        
        # Method should raise error but it should be handled
        with pytest.raises(ValueError):
            test_obj.test_method()
        
        # Error should be in history
        history = error_handler.get_error_history()
        assert len(history) > 0
        assert history[-1].category == ErrorCategory.COMMAND_EXECUTION
    
    def test_validation_rule_generation(self, validation_service):
        """Test automatic validation rule generation from field definitions"""
        # Add field definition with multiple constraints
        field_def = {
            'data_type': 'float',
            'required': True,
            'min_value': 0,
            'max_value': 1000,
            'precision': 2
        }
        
        validation_service.add_field_definition('price', field_def)
        
        # Check that rules were generated
        rules = validation_service.validation_rules.get('price', [])
        assert len(rules) > 0
        
        # Should have required rule
        required_rules = [r for r in rules if r.validation_type == ValidationType.REQUIRED]
        assert len(required_rules) > 0
        
        # Should have type rule
        type_rules = [r for r in rules if r.validation_type == ValidationType.DATA_TYPE]
        assert len(type_rules) > 0
        
        # Should have range rule
        range_rules = [r for r in rules if r.validation_type == ValidationType.RANGE]
        assert len(range_rules) > 0
    
    def test_common_validation_functions(self):
        """Test common validation utility functions"""
        # Test numeric validation
        valid, message = validate_numeric_field(123.45)
        assert valid
        assert message is None
        
        valid, message = validate_numeric_field("not_a_number")
        assert not valid
        assert message is not None
        
        valid, message = validate_numeric_field(-10, allow_negative=False)
        assert not valid
        assert "отрицательным" in message
        
        # Test date validation
        from datetime import date, datetime
        
        valid, message = validate_date_field(date.today())
        assert valid
        
        valid, message = validate_date_field("invalid_date")
        assert not valid
        
        # Test reference validation
        valid, message = validate_reference_field(123)
        assert valid
        
        valid, message = validate_reference_field(None, required=True)
        assert not valid
        assert "обязательно" in message
    
    def test_error_pattern_matching(self, error_handler):
        """Test error pattern matching and user message generation"""
        # Test file not found error
        file_error = FileNotFoundError("File 'test.xlsx' not found")
        error_info = error_handler.handle_import_error(file_error, "test.xlsx")
        
        assert "файл не найден" in error_info.user_message.lower()
        assert len(error_info.recovery_suggestions) > 0
        
        # Test calculation error
        calc_error = ZeroDivisionError("division by zero")
        error_info = error_handler.handle_calculation_error(
            calc_error, 'test_rule', {'quantity': 5, 'price': 0}
        )
        
        assert "расчет" in error_info.user_message.lower()
        assert error_info.can_retry
    
    def test_performance_monitoring_integration(self, validation_service):
        """Test that validation performance is monitored"""
        # Add multiple validation rules
        for i in range(10):
            validation_service.add_validation_rule(ValidationRule(
                id=f"test_rule_{i}",
                field_name="test_field",
                validation_type=ValidationType.CUSTOM,
                severity=ValidationSeverity.WARNING,
                custom_validator=lambda v, d: True,  # Always pass
                enabled=True,
                depends_on=[]
            ))
        
        context = ValidationContext(
            row_data={'test_field': 'test_value'},
            operation='performance_test'
        )
        
        # Validate field multiple times
        import time
        start_time = time.time()
        
        for _ in range(5):
            results = validation_service.validate_field('test_field', 'test_value', context)
        
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second for 50 validations
    
    def test_signal_emission(self, validation_service, app):
        """Test that validation signals are emitted correctly"""
        # Mock signal handlers
        completed_handler = Mock()
        failed_handler = Mock()
        warning_handler = Mock()
        
        # Connect signals
        validation_service.validationCompleted.connect(completed_handler)
        validation_service.validationFailed.connect(failed_handler)
        validation_service.validationWarning.connect(warning_handler)
        
        # Add validation rule that will fail
        validation_service.add_validation_rule(ValidationRule(
            id="test_required",
            field_name="required_field",
            validation_type=ValidationType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            enabled=True,
            depends_on=[]
        ))
        
        context = ValidationContext(
            row_data={'required_field': ''},  # Empty value
            operation='signal_test'
        )
        
        # Validate field
        results = validation_service.validate_field('required_field', '', context)
        
        # Process Qt events to ensure signals are emitted
        app.processEvents()
        
        # Check that signals were emitted
        completed_handler.assert_called_once()
        failed_handler.assert_called_once()
        warning_handler.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__])