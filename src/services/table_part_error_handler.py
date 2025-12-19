"""
Comprehensive error handling service for table parts.

This module provides centralized error handling, recovery mechanisms,
and user-friendly error reporting for table part operations.

Requirements: 13.1 - Implement comprehensive error handling
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors that can occur in table parts"""
    COMMAND_EXECUTION = "command_execution"
    CALCULATION = "calculation"
    IMPORT_EXPORT = "import_export"
    VALIDATION = "validation"
    REFERENCE_SELECTION = "reference_selection"
    DATA_ACCESS = "data_access"
    UI_INTERACTION = "ui_interaction"
    NETWORK = "network"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    component: str
    user_action: Optional[str] = None
    data_context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorInfo:
    """Detailed error information"""
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: Optional[str] = None
    context: Optional[ErrorContext] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    can_retry: bool = False
    retry_count: int = 0
    max_retries: int = 3
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryAction:
    """Recovery action that can be taken for an error"""
    id: str
    name: str
    description: str
    action: Callable[[], bool]
    automatic: bool = False
    priority: int = 0


class TablePartErrorHandler(QObject):
    """
    Comprehensive error handler for table part operations.
    
    Provides:
    - Centralized error handling and logging
    - User-friendly error messages
    - Recovery mechanisms and suggestions
    - Error categorization and severity assessment
    - Retry logic for transient errors
    """
    
    # Signals
    errorOccurred = pyqtSignal(ErrorInfo)
    errorRecovered = pyqtSignal(str, str)  # error_id, recovery_method
    criticalErrorOccurred = pyqtSignal(ErrorInfo)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.error_history: List[ErrorInfo] = []
        self.recovery_actions: Dict[str, List[RecoveryAction]] = {}
        self.error_patterns: Dict[str, ErrorInfo] = {}
        self.max_history_size = 100
        self.auto_recovery_enabled = True
        
        # Setup standard error patterns and recovery actions
        self._setup_standard_error_patterns()
        self._setup_standard_recovery_actions()
    
    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory,
        operation: str,
        component: str,
        user_action: Optional[str] = None,
        data_context: Optional[Dict[str, Any]] = None,
        show_to_user: bool = True
    ) -> ErrorInfo:
        """
        Handle an error with comprehensive processing.
        
        Args:
            exception: The exception that occurred
            category: Category of the error
            operation: Operation being performed when error occurred
            component: Component where error occurred
            user_action: User action that triggered the error
            data_context: Additional context data
            show_to_user: Whether to show error message to user
            
        Returns:
            ErrorInfo object with processed error details
        """
        # Create error context
        context = ErrorContext(
            operation=operation,
            component=component,
            user_action=user_action,
            data_context=data_context or {},
            stack_trace=traceback.format_exc()
        )
        
        # Determine error severity
        severity = self._determine_severity(exception, category)
        
        # Generate error ID
        error_id = self._generate_error_id(exception, category, operation)
        
        # Create user-friendly message
        user_message = self._create_user_message(exception, category, operation)
        
        # Get recovery suggestions
        recovery_suggestions = self._get_recovery_suggestions(exception, category)
        
        # Create error info
        error_info = ErrorInfo(
            id=error_id,
            category=category,
            severity=severity,
            message=str(exception),
            user_message=user_message,
            technical_details=traceback.format_exc(),
            context=context,
            recovery_suggestions=recovery_suggestions,
            can_retry=self._can_retry(exception, category)
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Add to history
        self._add_to_history(error_info)
        
        # Emit signals
        self.errorOccurred.emit(error_info)
        if severity == ErrorSeverity.CRITICAL:
            self.criticalErrorOccurred.emit(error_info)
        
        # Attempt automatic recovery if enabled
        if self.auto_recovery_enabled and error_info.can_retry:
            recovery_attempted = self._attempt_automatic_recovery(error_info)
            if recovery_attempted:
                return error_info
        
        # Show to user if requested
        if show_to_user:
            self._show_error_to_user(error_info)
        
        return error_info
    
    def handle_command_error(
        self,
        exception: Exception,
        command_id: str,
        context: Dict[str, Any],
        show_to_user: bool = True
    ) -> ErrorInfo:
        """Handle command execution errors"""
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.COMMAND_EXECUTION,
            operation=f"execute_command_{command_id}",
            component="command_manager",
            user_action=f"Execute command: {command_id}",
            data_context=context,
            show_to_user=show_to_user
        )
    
    def handle_calculation_error(
        self,
        exception: Exception,
        rule_id: str,
        row_data: Dict[str, Any],
        show_to_user: bool = True
    ) -> ErrorInfo:
        """Handle calculation errors"""
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.CALCULATION,
            operation=f"calculate_{rule_id}",
            component="calculation_engine",
            user_action="Field calculation",
            data_context={"rule_id": rule_id, "row_data": row_data},
            show_to_user=show_to_user
        )
    
    def handle_import_error(
        self,
        exception: Exception,
        file_path: str,
        row_number: Optional[int] = None,
        show_to_user: bool = True
    ) -> ErrorInfo:
        """Handle import/export errors"""
        context = {"file_path": file_path}
        if row_number is not None:
            context["row_number"] = row_number
        
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.IMPORT_EXPORT,
            operation="import_data",
            component="import_service",
            user_action=f"Import from {file_path}",
            data_context=context,
            show_to_user=show_to_user
        )
    
    def handle_validation_error(
        self,
        exception: Exception,
        field_name: str,
        field_value: Any,
        validation_rule: str,
        show_to_user: bool = True
    ) -> ErrorInfo:
        """Handle validation errors"""
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.VALIDATION,
            operation=f"validate_{field_name}",
            component="validation_service",
            user_action=f"Input validation for {field_name}",
            data_context={
                "field_name": field_name,
                "field_value": field_value,
                "validation_rule": validation_rule
            },
            show_to_user=show_to_user
        )
    
    def retry_operation(self, error_id: str) -> bool:
        """
        Retry a failed operation.
        
        Args:
            error_id: ID of the error to retry
            
        Returns:
            True if retry was successful, False otherwise
        """
        error_info = self._find_error_by_id(error_id)
        if not error_info or not error_info.can_retry:
            return False
        
        if error_info.retry_count >= error_info.max_retries:
            logger.warning(f"Maximum retries exceeded for error {error_id}")
            return False
        
        error_info.retry_count += 1
        
        # Attempt recovery actions
        recovery_actions = self.recovery_actions.get(error_info.category.value, [])
        for action in recovery_actions:
            try:
                if action.action():
                    logger.info(f"Recovery successful for error {error_id} using {action.name}")
                    self.errorRecovered.emit(error_id, action.name)
                    return True
            except Exception as e:
                logger.warning(f"Recovery action {action.name} failed: {e}")
        
        return False
    
    def get_error_history(self, category: Optional[ErrorCategory] = None) -> List[ErrorInfo]:
        """Get error history, optionally filtered by category"""
        if category:
            return [error for error in self.error_history if error.category == category]
        return self.error_history.copy()
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
    
    def add_recovery_action(self, category: ErrorCategory, action: RecoveryAction):
        """Add a recovery action for a specific error category"""
        if category.value not in self.recovery_actions:
            self.recovery_actions[category.value] = []
        self.recovery_actions[category.value].append(action)
    
    def enable_auto_recovery(self, enabled: bool):
        """Enable or disable automatic recovery attempts"""
        self.auto_recovery_enabled = enabled
    
    def _setup_standard_error_patterns(self):
        """Setup standard error patterns for common issues"""
        # Command execution patterns
        self.error_patterns["method_not_found"] = ErrorInfo(
            id="method_not_found",
            category=ErrorCategory.COMMAND_EXECUTION,
            severity=ErrorSeverity.ERROR,
            message="Method not found",
            user_message="Команда недоступна в текущем контексте",
            recovery_suggestions=[
                "Проверьте, что форма поддерживает данную операцию",
                "Обновите форму и попробуйте снова"
            ]
        )
        
        # Calculation patterns
        self.error_patterns["division_by_zero"] = ErrorInfo(
            id="division_by_zero",
            category=ErrorCategory.CALCULATION,
            severity=ErrorSeverity.WARNING,
            message="Division by zero",
            user_message="Деление на ноль в расчете",
            recovery_suggestions=[
                "Проверьте значения в полях расчета",
                "Убедитесь, что делитель не равен нулю"
            ],
            can_retry=True
        )
        
        # Import/Export patterns
        self.error_patterns["file_not_found"] = ErrorInfo(
            id="file_not_found",
            category=ErrorCategory.IMPORT_EXPORT,
            severity=ErrorSeverity.ERROR,
            message="File not found",
            user_message="Файл не найден",
            recovery_suggestions=[
                "Проверьте путь к файлу",
                "Убедитесь, что файл существует и доступен для чтения"
            ]
        )
        
        # Validation patterns
        self.error_patterns["invalid_format"] = ErrorInfo(
            id="invalid_format",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            message="Invalid format",
            user_message="Неверный формат данных",
            recovery_suggestions=[
                "Проверьте формат введенных данных",
                "Используйте правильный формат для данного поля"
            ],
            can_retry=True
        )
    
    def _setup_standard_recovery_actions(self):
        """Setup standard recovery actions"""
        # Command execution recovery
        self.add_recovery_action(
            ErrorCategory.COMMAND_EXECUTION,
            RecoveryAction(
                id="refresh_form",
                name="Обновить форму",
                description="Обновить состояние формы и команд",
                action=lambda: True,  # Placeholder - would be implemented by caller
                automatic=False,
                priority=1
            )
        )
        
        # Calculation recovery
        self.add_recovery_action(
            ErrorCategory.CALCULATION,
            RecoveryAction(
                id="reset_calculation",
                name="Сбросить расчет",
                description="Сбросить значения расчетных полей",
                action=lambda: True,  # Placeholder
                automatic=True,
                priority=2
            )
        )
        
        # Import/Export recovery
        self.add_recovery_action(
            ErrorCategory.IMPORT_EXPORT,
            RecoveryAction(
                id="retry_file_operation",
                name="Повторить операцию с файлом",
                description="Повторить чтение/запись файла",
                action=lambda: True,  # Placeholder
                automatic=True,
                priority=1
            )
        )
    
    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on exception type and category"""
        # Critical errors
        if isinstance(exception, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        # Category-specific severity
        if category == ErrorCategory.DATA_ACCESS:
            return ErrorSeverity.ERROR
        elif category == ErrorCategory.VALIDATION:
            return ErrorSeverity.WARNING
        elif category == ErrorCategory.CALCULATION:
            return ErrorSeverity.WARNING
        elif category == ErrorCategory.COMMAND_EXECUTION:
            return ErrorSeverity.ERROR
        elif category == ErrorCategory.IMPORT_EXPORT:
            return ErrorSeverity.ERROR
        
        # Default based on exception type
        if isinstance(exception, (ValueError, TypeError)):
            return ErrorSeverity.WARNING
        elif isinstance(exception, (IOError, OSError, FileNotFoundError)):
            return ErrorSeverity.ERROR
        elif isinstance(exception, PermissionError):
            return ErrorSeverity.ERROR
        else:
            return ErrorSeverity.ERROR
    
    def _generate_error_id(self, exception: Exception, category: ErrorCategory, operation: str) -> str:
        """Generate unique error ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exception_name = exception.__class__.__name__
        return f"{category.value}_{operation}_{exception_name}_{timestamp}"
    
    def _create_user_message(self, exception: Exception, category: ErrorCategory, operation: str) -> str:
        """Create user-friendly error message"""
        # Check for known patterns
        exception_name = exception.__class__.__name__.lower()
        message_lower = str(exception).lower()
        
        # File-related errors
        if "file" in message_lower and "not found" in message_lower:
            return "Файл не найден. Проверьте путь к файлу и попробуйте снова."
        elif "permission" in message_lower or isinstance(exception, PermissionError):
            return "Недостаточно прав доступа. Проверьте права на файл или папку."
        elif "memory" in exception_name:
            return "Недостаточно памяти для выполнения операции."
        
        # Calculation errors
        if category == ErrorCategory.CALCULATION:
            if "division" in message_lower and "zero" in message_lower:
                return "Ошибка в расчете: деление на ноль. Проверьте значения в полях."
            elif "invalid" in message_lower and "operation" in message_lower:
                return "Ошибка в расчете: недопустимая операция. Проверьте типы данных."
            else:
                return "Ошибка при выполнении расчета. Проверьте введенные значения."
        
        # Command errors
        elif category == ErrorCategory.COMMAND_EXECUTION:
            if "not found" in message_lower or "attribute" in message_lower:
                return "Команда недоступна в текущем контексте."
            else:
                return "Ошибка при выполнении команды. Попробуйте еще раз."
        
        # Import/Export errors
        elif category == ErrorCategory.IMPORT_EXPORT:
            if "format" in message_lower or "decode" in message_lower:
                return "Неподдерживаемый формат файла или ошибка кодировки."
            elif "corrupt" in message_lower or "invalid" in message_lower:
                return "Файл поврежден или содержит некорректные данные."
            else:
                return "Ошибка при работе с файлом. Проверьте файл и попробуйте снова."
        
        # Validation errors
        elif category == ErrorCategory.VALIDATION:
            return "Введенные данные не соответствуют требованиям. Проверьте формат и значения."
        
        # Generic message
        return f"Произошла ошибка при выполнении операции: {operation}. Обратитесь к администратору."
    
    def _get_recovery_suggestions(self, exception: Exception, category: ErrorCategory) -> List[str]:
        """Get recovery suggestions based on error type"""
        suggestions = []
        
        # Generic suggestions based on exception type
        if isinstance(exception, FileNotFoundError):
            suggestions.extend([
                "Проверьте путь к файлу",
                "Убедитесь, что файл существует"
            ])
        elif isinstance(exception, PermissionError):
            suggestions.extend([
                "Проверьте права доступа к файлу",
                "Запустите приложение от имени администратора"
            ])
        elif isinstance(exception, (ValueError, TypeError)):
            suggestions.extend([
                "Проверьте формат введенных данных",
                "Убедитесь в корректности значений"
            ])
        
        # Category-specific suggestions
        if category == ErrorCategory.CALCULATION:
            suggestions.extend([
                "Проверьте числовые значения в полях",
                "Убедитесь, что все обязательные поля заполнены"
            ])
        elif category == ErrorCategory.IMPORT_EXPORT:
            suggestions.extend([
                "Проверьте формат файла",
                "Убедитесь, что файл не поврежден"
            ])
        elif category == ErrorCategory.COMMAND_EXECUTION:
            suggestions.extend([
                "Обновите форму и попробуйте снова",
                "Проверьте, что операция доступна в текущем контексте"
            ])
        
        return suggestions
    
    def _can_retry(self, exception: Exception, category: ErrorCategory) -> bool:
        """Determine if operation can be retried"""
        # Never retry critical system errors
        if isinstance(exception, (MemoryError, SystemError)):
            return False
        
        # Retry transient errors
        if isinstance(exception, (IOError, OSError)) and "temporarily unavailable" in str(exception).lower():
            return True
        
        # Category-specific retry logic
        if category in [ErrorCategory.CALCULATION, ErrorCategory.VALIDATION]:
            return True
        elif category == ErrorCategory.IMPORT_EXPORT:
            return not isinstance(exception, (FileNotFoundError, PermissionError))
        elif category == ErrorCategory.COMMAND_EXECUTION:
            return "not found" not in str(exception).lower()
        
        return False
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        log_message = f"[{error_info.category.value}] {error_info.message}"
        
        if error_info.context:
            log_message += f" | Operation: {error_info.context.operation}"
            log_message += f" | Component: {error_info.context.component}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif error_info.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _add_to_history(self, error_info: ErrorInfo):
        """Add error to history with size limit"""
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def _find_error_by_id(self, error_id: str) -> Optional[ErrorInfo]:
        """Find error in history by ID"""
        for error in self.error_history:
            if error.id == error_id:
                return error
        return None
    
    def _attempt_automatic_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt automatic recovery for the error"""
        recovery_actions = self.recovery_actions.get(error_info.category.value, [])
        automatic_actions = [action for action in recovery_actions if action.automatic]
        
        # Sort by priority
        automatic_actions.sort(key=lambda x: x.priority)
        
        for action in automatic_actions:
            try:
                if action.action():
                    logger.info(f"Automatic recovery successful: {action.name}")
                    self.errorRecovered.emit(error_info.id, action.name)
                    return True
            except Exception as e:
                logger.warning(f"Automatic recovery failed for {action.name}: {e}")
        
        return False
    
    def _show_error_to_user(self, error_info: ErrorInfo):
        """Show error message to user via message box"""
        if not self.parent_widget:
            return
        
        # Determine message box icon based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            icon = QMessageBox.Icon.Critical
            title = "Критическая ошибка"
        elif error_info.severity == ErrorSeverity.ERROR:
            icon = QMessageBox.Icon.Critical
            title = "Ошибка"
        elif error_info.severity == ErrorSeverity.WARNING:
            icon = QMessageBox.Icon.Warning
            title = "Предупреждение"
        else:
            icon = QMessageBox.Icon.Information
            title = "Информация"
        
        # Create message text
        message_text = error_info.user_message
        
        if error_info.recovery_suggestions:
            message_text += "\n\nРекомендации:"
            for suggestion in error_info.recovery_suggestions[:3]:  # Limit to 3 suggestions
                message_text += f"\n• {suggestion}"
        
        # Show message box
        msg_box = QMessageBox(icon, title, message_text, QMessageBox.StandardButton.Ok, self.parent_widget)
        
        # Add retry button for retryable errors
        if error_info.can_retry and error_info.retry_count < error_info.max_retries:
            retry_button = msg_box.addButton("Повторить", QMessageBox.ButtonRole.ActionRole)
            msg_box.exec()
            
            if msg_box.clickedButton() == retry_button:
                self.retry_operation(error_info.id)
        else:
            msg_box.exec()


def create_error_handler(parent_widget: Optional[QWidget] = None) -> TablePartErrorHandler:
    """Factory function to create error handler"""
    return TablePartErrorHandler(parent_widget)


# Decorator for automatic error handling
def handle_table_part_errors(
    category: ErrorCategory,
    operation: str,
    component: str,
    show_to_user: bool = True
):
    """
    Decorator for automatic error handling in table part methods.
    
    Usage:
        @handle_table_part_errors(ErrorCategory.COMMAND_EXECUTION, "add_row", "table_part")
        def add_row(self):
            # Method implementation
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Get error handler from instance or create new one
                error_handler = getattr(self, 'error_handler', None)
                if not error_handler:
                    error_handler = create_error_handler()
                
                # Handle the error
                error_handler.handle_error(
                    exception=e,
                    category=category,
                    operation=operation,
                    component=component,
                    user_action=func.__name__,
                    show_to_user=show_to_user
                )
                
                # Re-raise for caller to handle if needed
                raise
        
        return wrapper
    return decorator