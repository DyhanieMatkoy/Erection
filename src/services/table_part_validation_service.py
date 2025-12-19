"""
Input validation service for table parts.

This module provides comprehensive validation for table part fields,
including calculation fields, reference fields, and data integrity checks.

Requirements: 13.2 - Add input validation
"""

import re
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from PyQt6.QtCore import QObject, pyqtSignal

from .table_part_error_handler import TablePartErrorHandler, ErrorCategory


class ValidationType(Enum):
    """Types of validation rules"""
    REQUIRED = "required"
    DATA_TYPE = "data_type"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"
    REFERENCE = "reference"
    CALCULATION = "calculation"
    UNIQUE = "unique"
    DEPENDENCY = "dependency"


class ValidationSeverity(Enum):
    """Severity levels for validation results"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    """Configuration for a validation rule"""
    id: str
    field_name: str
    validation_type: ValidationType
    severity: ValidationSeverity = ValidationSeverity.ERROR
    message: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    custom_validator: Optional[Callable[[Any, Dict[str, Any]], bool]] = None
    enabled: bool = True
    depends_on: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    field_name: str
    rule_id: str
    is_valid: bool
    severity: ValidationSeverity
    message: str
    suggested_value: Optional[Any] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationContext:
    """Context for validation operations"""
    row_data: Dict[str, Any]
    all_data: List[Dict[str, Any]] = field(default_factory=list)
    field_definitions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_row_index: Optional[int] = None
    operation: str = "edit"


class TablePartValidationService(QObject):
    """
    Comprehensive validation service for table parts.
    
    Provides:
    - Field-level validation (required, type, format, range)
    - Reference field validation
    - Calculation field validation
    - Cross-field dependencies
    - Data integrity checks
    - User-friendly validation feedback
    """
    
    # Signals
    validationCompleted = pyqtSignal(str, list)  # field_name, results
    validationFailed = pyqtSignal(str, ValidationResult)  # field_name, result
    validationWarning = pyqtSignal(str, ValidationResult)  # field_name, result
    
    def __init__(self, error_handler: Optional[TablePartErrorHandler] = None):
        super().__init__()
        self.error_handler = error_handler
        self.validation_rules: Dict[str, List[ValidationRule]] = {}
        self.field_definitions: Dict[str, Dict[str, Any]] = {}
        
        # Setup standard validation rules
        self._setup_standard_rules()
    
    def add_field_definition(self, field_name: str, definition: Dict[str, Any]):
        """
        Add field definition for validation.
        
        Args:
            field_name: Name of the field
            definition: Field definition with type, constraints, etc.
        """
        self.field_definitions[field_name] = definition
        
        # Auto-generate validation rules from definition
        self._generate_rules_from_definition(field_name, definition)
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a validation rule for a field"""
        if rule.field_name not in self.validation_rules:
            self.validation_rules[rule.field_name] = []
        
        self.validation_rules[rule.field_name].append(rule)
    
    def remove_validation_rule(self, field_name: str, rule_id: str):
        """Remove a validation rule"""
        if field_name in self.validation_rules:
            self.validation_rules[field_name] = [
                rule for rule in self.validation_rules[field_name]
                if rule.id != rule_id
            ]
    
    def validate_field(
        self,
        field_name: str,
        value: Any,
        context: ValidationContext
    ) -> List[ValidationResult]:
        """
        Validate a single field value.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
            context: Validation context with row data and metadata
            
        Returns:
            List of validation results
        """
        results = []
        
        # Get validation rules for the field
        rules = self.validation_rules.get(field_name, [])
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check dependencies
            if rule.depends_on and not self._check_dependencies(rule.depends_on, context):
                continue
            
            try:
                result = self._execute_validation_rule(rule, value, context)
                if result:
                    results.append(result)
                    
                    # Emit signals based on severity
                    if result.severity == ValidationSeverity.ERROR:
                        self.validationFailed.emit(field_name, result)
                    elif result.severity == ValidationSeverity.WARNING:
                        self.validationWarning.emit(field_name, result)
                        
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_validation_error(
                        e, field_name, value, rule.id
                    )
                
                # Create error result
                error_result = ValidationResult(
                    field_name=field_name,
                    rule_id=rule.id,
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Ошибка валидации: {str(e)}"
                )
                results.append(error_result)
        
        # Emit completion signal
        self.validationCompleted.emit(field_name, results)
        
        return results
    
    def validate_row(self, context: ValidationContext) -> Dict[str, List[ValidationResult]]:
        """
        Validate all fields in a row.
        
        Args:
            context: Validation context with complete row data
            
        Returns:
            Dictionary mapping field names to validation results
        """
        all_results = {}
        
        for field_name, value in context.row_data.items():
            results = self.validate_field(field_name, value, context)
            if results:
                all_results[field_name] = results
        
        return all_results
    
    def validate_calculation_fields(
        self,
        context: ValidationContext,
        calculation_rules: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate calculation field values and dependencies.
        
        Args:
            context: Validation context
            calculation_rules: List of calculation rule definitions
            
        Returns:
            List of validation results for calculation fields
        """
        results = []
        
        for rule in calculation_rules:
            source_columns = rule.get('source_columns', [])
            target_column = rule.get('target_column')
            
            if not target_column:
                continue
            
            # Validate source columns have valid numeric values
            for source_col in source_columns:
                value = context.row_data.get(source_col)
                
                if value is not None and value != '':
                    try:
                        # Try to convert to Decimal for validation
                        Decimal(str(value))
                    except (InvalidOperation, ValueError):
                        result = ValidationResult(
                            field_name=source_col,
                            rule_id=f"calc_source_{rule.get('id', 'unknown')}",
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"Поле '{source_col}' должно содержать числовое значение для расчета"
                        )
                        results.append(result)
            
            # Validate target column is not manually edited if auto-calculated
            if rule.get('auto_calculate', True):
                target_value = context.row_data.get(target_column)
                if target_value is not None:
                    # Check if value matches expected calculation
                    expected_value = self._calculate_expected_value(rule, context.row_data)
                    if expected_value is not None and abs(float(target_value) - float(expected_value)) > 0.01:
                        result = ValidationResult(
                            field_name=target_column,
                            rule_id=f"calc_target_{rule.get('id', 'unknown')}",
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"Значение поля '{target_column}' не соответствует расчету",
                            suggested_value=expected_value
                        )
                        results.append(result)
        
        return results
    
    def validate_reference_field(
        self,
        field_name: str,
        reference_id: Any,
        reference_type: str,
        context: ValidationContext
    ) -> List[ValidationResult]:
        """
        Validate reference field value.
        
        Args:
            field_name: Name of the reference field
            reference_id: ID of the referenced object
            reference_type: Type of reference (e.g., 'work', 'material')
            context: Validation context
            
        Returns:
            List of validation results
        """
        results = []
        
        if reference_id is None or reference_id == '':
            # Check if field is required
            field_def = self.field_definitions.get(field_name, {})
            if field_def.get('required', False):
                result = ValidationResult(
                    field_name=field_name,
                    rule_id=f"ref_required_{field_name}",
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Поле '{field_name}' обязательно для заполнения"
                )
                results.append(result)
            return results
        
        # Validate reference exists and is accessible
        try:
            # This would typically involve checking with a reference service
            # For now, we'll do basic validation
            
            if not isinstance(reference_id, (int, str)) or str(reference_id).strip() == '':
                result = ValidationResult(
                    field_name=field_name,
                    rule_id=f"ref_format_{field_name}",
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Некорректный формат ссылки в поле '{field_name}'"
                )
                results.append(result)
            
            # Additional reference-specific validation could be added here
            # e.g., checking if the referenced object exists, is active, etc.
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_validation_error(
                    e, field_name, reference_id, f"reference_{reference_type}"
                )
            
            result = ValidationResult(
                field_name=field_name,
                rule_id=f"ref_error_{field_name}",
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Ошибка проверки ссылки в поле '{field_name}'"
            )
            results.append(result)
        
        return results
    
    def validate_data_integrity(
        self,
        all_data: List[Dict[str, Any]],
        integrity_rules: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate data integrity across all rows.
        
        Args:
            all_data: All table data
            integrity_rules: List of integrity rule definitions
            
        Returns:
            List of validation results for integrity violations
        """
        results = []
        
        for rule in integrity_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'unique':
                results.extend(self._validate_uniqueness(all_data, rule))
            elif rule_type == 'sum_constraint':
                results.extend(self._validate_sum_constraint(all_data, rule))
            elif rule_type == 'dependency':
                results.extend(self._validate_dependencies(all_data, rule))
        
        return results
    
    def get_validation_summary(self, results: Dict[str, List[ValidationResult]]) -> Dict[str, int]:
        """
        Get summary of validation results.
        
        Args:
            results: Validation results by field
            
        Returns:
            Summary with counts by severity
        """
        summary = {
            'total_fields': len(results),
            'fields_with_errors': 0,
            'fields_with_warnings': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'total_info': 0
        }
        
        for field_results in results.values():
            has_error = False
            has_warning = False
            
            for result in field_results:
                if result.severity == ValidationSeverity.ERROR:
                    summary['total_errors'] += 1
                    has_error = True
                elif result.severity == ValidationSeverity.WARNING:
                    summary['total_warnings'] += 1
                    has_warning = True
                elif result.severity == ValidationSeverity.INFO:
                    summary['total_info'] += 1
            
            if has_error:
                summary['fields_with_errors'] += 1
            elif has_warning:
                summary['fields_with_warnings'] += 1
        
        return summary
    
    def _setup_standard_rules(self):
        """Setup standard validation rules for common field types"""
        
        # Standard numeric field validation
        self.add_validation_rule(ValidationRule(
            id="numeric_format",
            field_name="*",  # Applies to all numeric fields
            validation_type=ValidationType.DATA_TYPE,
            message="Поле должно содержать числовое значение",
            parameters={"data_type": "numeric"}
        ))
        
        # Standard date field validation
        self.add_validation_rule(ValidationRule(
            id="date_format",
            field_name="*",  # Applies to all date fields
            validation_type=ValidationType.DATA_TYPE,
            message="Поле должно содержать корректную дату",
            parameters={"data_type": "date"}
        ))
    
    def _generate_rules_from_definition(self, field_name: str, definition: Dict[str, Any]):
        """Generate validation rules from field definition"""
        
        # Required field rule
        if definition.get('required', False):
            self.add_validation_rule(ValidationRule(
                id=f"required_{field_name}",
                field_name=field_name,
                validation_type=ValidationType.REQUIRED,
                message=f"Поле '{field_name}' обязательно для заполнения"
            ))
        
        # Data type rule
        data_type = definition.get('data_type')
        if data_type:
            self.add_validation_rule(ValidationRule(
                id=f"type_{field_name}",
                field_name=field_name,
                validation_type=ValidationType.DATA_TYPE,
                message=f"Поле '{field_name}' должно быть типа {data_type}",
                parameters={"data_type": data_type}
            ))
        
        # Range validation for numeric fields
        if data_type in ['int', 'float', 'decimal']:
            min_value = definition.get('min_value')
            max_value = definition.get('max_value')
            
            if min_value is not None or max_value is not None:
                self.add_validation_rule(ValidationRule(
                    id=f"range_{field_name}",
                    field_name=field_name,
                    validation_type=ValidationType.RANGE,
                    message=f"Значение поля '{field_name}' вне допустимого диапазона",
                    parameters={"min_value": min_value, "max_value": max_value}
                ))
        
        # Length validation for string fields
        if data_type == 'str':
            max_length = definition.get('max_length')
            if max_length:
                self.add_validation_rule(ValidationRule(
                    id=f"length_{field_name}",
                    field_name=field_name,
                    validation_type=ValidationType.LENGTH,
                    message=f"Длина поля '{field_name}' не должна превышать {max_length} символов",
                    parameters={"max_length": max_length}
                ))
        
        # Pattern validation
        pattern = definition.get('pattern')
        if pattern:
            self.add_validation_rule(ValidationRule(
                id=f"pattern_{field_name}",
                field_name=field_name,
                validation_type=ValidationType.PATTERN,
                message=f"Поле '{field_name}' не соответствует требуемому формату",
                parameters={"pattern": pattern}
            ))
    
    def _execute_validation_rule(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Execute a single validation rule"""
        
        if rule.validation_type == ValidationType.REQUIRED:
            return self._validate_required(rule, value, context)
        elif rule.validation_type == ValidationType.DATA_TYPE:
            return self._validate_data_type(rule, value, context)
        elif rule.validation_type == ValidationType.RANGE:
            return self._validate_range(rule, value, context)
        elif rule.validation_type == ValidationType.LENGTH:
            return self._validate_length(rule, value, context)
        elif rule.validation_type == ValidationType.PATTERN:
            return self._validate_pattern(rule, value, context)
        elif rule.validation_type == ValidationType.CUSTOM:
            return self._validate_custom(rule, value, context)
        
        return None
    
    def _validate_required(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Validate required field"""
        if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=rule.message or f"Поле '{rule.field_name}' обязательно для заполнения"
            )
        return None
    
    def _validate_data_type(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Validate data type"""
        if value is None or value == '':
            return None  # Empty values are handled by required validation
        
        data_type = rule.parameters.get('data_type')
        
        try:
            if data_type == 'int':
                int(value)
            elif data_type == 'float':
                float(value)
            elif data_type == 'decimal':
                Decimal(str(value))
            elif data_type == 'date':
                if isinstance(value, str):
                    datetime.strptime(value, '%Y-%m-%d')
                elif not isinstance(value, (date, datetime)):
                    raise ValueError("Invalid date type")
            elif data_type == 'bool':
                if not isinstance(value, bool) and str(value).lower() not in ['true', 'false', '1', '0']:
                    raise ValueError("Invalid boolean value")
            
        except (ValueError, InvalidOperation, TypeError):
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=rule.message or f"Поле '{rule.field_name}' должно быть типа {data_type}"
            )
        
        return None
    
    def _validate_range(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Validate numeric range"""
        if value is None or value == '':
            return None
        
        try:
            numeric_value = float(value)
            min_value = rule.parameters.get('min_value')
            max_value = rule.parameters.get('max_value')
            
            if min_value is not None and numeric_value < min_value:
                return ValidationResult(
                    field_name=rule.field_name,
                    rule_id=rule.id,
                    is_valid=False,
                    severity=rule.severity,
                    message=f"Значение поля '{rule.field_name}' должно быть не менее {min_value}"
                )
            
            if max_value is not None and numeric_value > max_value:
                return ValidationResult(
                    field_name=rule.field_name,
                    rule_id=rule.id,
                    is_valid=False,
                    severity=rule.severity,
                    message=f"Значение поля '{rule.field_name}' должно быть не более {max_value}"
                )
                
        except (ValueError, TypeError):
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=f"Поле '{rule.field_name}' должно содержать числовое значение"
            )
        
        return None
    
    def _validate_length(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Validate string length"""
        if value is None:
            return None
        
        str_value = str(value)
        max_length = rule.parameters.get('max_length')
        min_length = rule.parameters.get('min_length', 0)
        
        if len(str_value) < min_length:
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=f"Длина поля '{rule.field_name}' должна быть не менее {min_length} символов"
            )
        
        if max_length and len(str_value) > max_length:
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=f"Длина поля '{rule.field_name}' не должна превышать {max_length} символов"
            )
        
        return None
    
    def _validate_pattern(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Validate against regex pattern"""
        if value is None or value == '':
            return None
        
        pattern = rule.parameters.get('pattern')
        if not pattern:
            return None
        
        str_value = str(value)
        if not re.match(pattern, str_value):
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=rule.severity,
                message=rule.message or f"Поле '{rule.field_name}' не соответствует требуемому формату"
            )
        
        return None
    
    def _validate_custom(
        self,
        rule: ValidationRule,
        value: Any,
        context: ValidationContext
    ) -> Optional[ValidationResult]:
        """Execute custom validation function"""
        if not rule.custom_validator:
            return None
        
        try:
            is_valid = rule.custom_validator(value, context.row_data)
            if not is_valid:
                return ValidationResult(
                    field_name=rule.field_name,
                    rule_id=rule.id,
                    is_valid=False,
                    severity=rule.severity,
                    message=rule.message or f"Поле '{rule.field_name}' не прошло проверку"
                )
        except Exception as e:
            return ValidationResult(
                field_name=rule.field_name,
                rule_id=rule.id,
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Ошибка при выполнении проверки: {str(e)}"
            )
        
        return None
    
    def _check_dependencies(self, depends_on: List[str], context: ValidationContext) -> bool:
        """Check if dependency fields have valid values"""
        for dep_field in depends_on:
            value = context.row_data.get(dep_field)
            if value is None or value == '':
                return False
        return True
    
    def _calculate_expected_value(self, rule: Dict[str, Any], row_data: Dict[str, Any]) -> Optional[float]:
        """Calculate expected value for validation"""
        calculation_type = rule.get('calculation_type', 'multiply')
        source_columns = rule.get('source_columns', [])
        
        if calculation_type == 'multiply' and len(source_columns) >= 2:
            try:
                result = 1.0
                for col in source_columns:
                    value = row_data.get(col)
                    if value is None or value == '':
                        return None
                    result *= float(value)
                return result
            except (ValueError, TypeError):
                return None
        
        return None
    
    def _validate_uniqueness(
        self,
        all_data: List[Dict[str, Any]],
        rule: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate field uniqueness across all rows"""
        results = []
        field_name = rule.get('field')
        
        if not field_name:
            return results
        
        seen_values = {}
        for i, row in enumerate(all_data):
            value = row.get(field_name)
            if value is not None and value != '':
                if value in seen_values:
                    result = ValidationResult(
                        field_name=field_name,
                        rule_id=f"unique_{field_name}",
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Значение '{value}' в поле '{field_name}' должно быть уникальным",
                        additional_info={"duplicate_rows": [seen_values[value], i]}
                    )
                    results.append(result)
                else:
                    seen_values[value] = i
        
        return results
    
    def _validate_sum_constraint(
        self,
        all_data: List[Dict[str, Any]],
        rule: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate sum constraints across all rows"""
        results = []
        field_name = rule.get('field')
        max_sum = rule.get('max_sum')
        min_sum = rule.get('min_sum')
        
        if not field_name:
            return results
        
        try:
            total = sum(float(row.get(field_name, 0) or 0) for row in all_data)
            
            if max_sum is not None and total > max_sum:
                result = ValidationResult(
                    field_name=field_name,
                    rule_id=f"sum_max_{field_name}",
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Общая сумма по полю '{field_name}' ({total}) превышает максимум ({max_sum})",
                    additional_info={"current_sum": total, "max_sum": max_sum}
                )
                results.append(result)
            
            if min_sum is not None and total < min_sum:
                result = ValidationResult(
                    field_name=field_name,
                    rule_id=f"sum_min_{field_name}",
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Общая сумма по полю '{field_name}' ({total}) меньше минимума ({min_sum})",
                    additional_info={"current_sum": total, "min_sum": min_sum}
                )
                results.append(result)
                
        except (ValueError, TypeError) as e:
            result = ValidationResult(
                field_name=field_name,
                rule_id=f"sum_error_{field_name}",
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Ошибка при расчете суммы по полю '{field_name}': {str(e)}"
            )
            results.append(result)
        
        return results
    
    def _validate_dependencies(
        self,
        all_data: List[Dict[str, Any]],
        rule: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate field dependencies across rows"""
        results = []
        # Implementation would depend on specific dependency rules
        # This is a placeholder for complex dependency validation
        return results


def create_validation_service(error_handler: Optional[TablePartErrorHandler] = None) -> TablePartValidationService:
    """Factory function to create validation service"""
    return TablePartValidationService(error_handler)


# Common validation functions
def validate_numeric_field(value: Any, allow_negative: bool = True, precision: int = 2) -> Tuple[bool, Optional[str]]:
    """Validate numeric field value"""
    if value is None or value == '':
        return True, None
    
    try:
        numeric_value = Decimal(str(value))
        
        if not allow_negative and numeric_value < 0:
            return False, "Значение не может быть отрицательным"
        
        # Check precision
        if numeric_value.as_tuple().exponent < -precision:
            return False, f"Слишком много знаков после запятой (максимум {precision})"
        
        return True, None
        
    except (InvalidOperation, ValueError):
        return False, "Значение должно быть числом"


def validate_date_field(value: Any, allow_future: bool = True, allow_past: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate date field value"""
    if value is None or value == '':
        return True, None
    
    try:
        if isinstance(value, str):
            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime):
            parsed_date = value.date()
        elif isinstance(value, date):
            parsed_date = value
        else:
            return False, "Неверный формат даты"
        
        today = date.today()
        
        if not allow_future and parsed_date > today:
            return False, "Дата не может быть в будущем"
        
        if not allow_past and parsed_date < today:
            return False, "Дата не может быть в прошлом"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Неверный формат даты"


def validate_reference_field(value: Any, required: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate reference field value"""
    if value is None or value == '':
        if required:
            return False, "Поле обязательно для заполнения"
        return True, None
    
    # Basic validation - in real implementation would check if reference exists
    if not isinstance(value, (int, str)) or str(value).strip() == '':
        return False, "Некорректное значение ссылки"
    
    return True, None