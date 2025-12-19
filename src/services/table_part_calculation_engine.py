"""
Automatic calculation engine for document table parts.

This module provides real-time calculation capabilities for table parts,
including automatic sum calculations (Quantity × Price) and document totals
with performance monitoring and error handling.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class CalculationType(Enum):
    """Types of calculations supported by the engine"""
    MULTIPLY = "multiply"
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    CUSTOM = "custom"


@dataclass
class CalculationRule:
    """Configuration for a calculation rule"""
    id: str
    name: str
    source_columns: List[str]
    target_column: str
    calculation_type: CalculationType
    formula: Optional[str] = None
    custom_function: Optional[Callable] = None
    trigger_on_change: bool = True
    dependencies: List[str] = field(default_factory=list)
    precision: int = 3
    enabled: bool = True


@dataclass
class CalculationResult:
    """Result of a calculation operation"""
    success: bool
    value: Optional[Union[Decimal, float, int]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    rule_id: Optional[str] = None


@dataclass
class TotalCalculationRule:
    """Configuration for document total calculations"""
    column: str
    calculation_type: CalculationType
    custom_function: Optional[Callable] = None
    format_function: Optional[Callable] = None
    precision: int = 2
    enabled: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics for calculation operations"""
    individual_calculation_time_ms: float = 0.0
    total_calculation_time_ms: float = 0.0
    calculations_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    error_count: int = 0
    last_calculation_timestamp: Optional[float] = None


class TablePartCalculationEngine(QObject):
    """
    Automatic calculation engine for table parts.
    
    Provides real-time calculations with performance monitoring:
    - Individual field calculations (< 100ms target)
    - Document total calculations (< 200ms target)
    - Error handling and recovery
    - Performance metrics tracking
    """
    
    # Signals
    calculationCompleted = pyqtSignal(int, str, CalculationResult)  # row, column, result
    totalCalculationCompleted = pyqtSignal(dict)  # totals dict
    calculationError = pyqtSignal(str, str)  # error_type, message
    performanceAlert = pyqtSignal(str, float)  # metric_name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.individual_timeout_ms = 100
        self.total_timeout_ms = 200
        self.performance_monitoring_enabled = True
        
        # Calculation rules
        self.calculation_rules: Dict[str, CalculationRule] = {}
        self.total_rules: Dict[str, TotalCalculationRule] = {}
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.calculation_history: List[float] = []
        self.max_history_size = 100
        
        # Error handling
        self.error_recovery_enabled = True
        self.max_retry_attempts = 3
        
        # Setup standard calculation rules
        self._setup_standard_rules()
    
    def _setup_standard_rules(self):
        """Setup standard calculation rules for common scenarios"""
        
        # Quantity × Price = Sum calculation
        quantity_price_rule = CalculationRule(
            id="quantity_price_sum",
            name="Quantity × Price Sum",
            source_columns=["quantity", "price"],
            target_column="sum",
            calculation_type=CalculationType.MULTIPLY,
            precision=2
        )
        self.add_calculation_rule(quantity_price_rule)
        
        # Standard total calculations
        sum_total = TotalCalculationRule(
            column="sum",
            calculation_type=CalculationType.SUM,
            precision=2
        )
        self.add_total_rule("sum_total", sum_total)
        
        quantity_total = TotalCalculationRule(
            column="quantity",
            calculation_type=CalculationType.SUM,
            precision=3
        )
        self.add_total_rule("quantity_total", quantity_total)
    
    def add_calculation_rule(self, rule: CalculationRule):
        """Add a calculation rule to the engine"""
        self.calculation_rules[rule.id] = rule
        logger.debug(f"Added calculation rule: {rule.id}")
    
    def remove_calculation_rule(self, rule_id: str):
        """Remove a calculation rule from the engine"""
        if rule_id in self.calculation_rules:
            del self.calculation_rules[rule_id]
            logger.debug(f"Removed calculation rule: {rule_id}")
    
    def add_total_rule(self, rule_id: str, rule: TotalCalculationRule):
        """Add a total calculation rule"""
        self.total_rules[rule_id] = rule
        logger.debug(f"Added total rule: {rule_id}")
    
    def remove_total_rule(self, rule_id: str):
        """Remove a total calculation rule"""
        if rule_id in self.total_rules:
            del self.total_rules[rule_id]
            logger.debug(f"Removed total rule: {rule_id}")
    
    def calculate_field(self, row_data: Dict[str, Any], column: str, 
                       all_data: Optional[List[Dict[str, Any]]] = None) -> CalculationResult:
        """
        Calculate a single field value based on calculation rules.
        
        Args:
            row_data: Data for the current row
            column: Column that was changed (trigger column)
            all_data: All table data for context-dependent calculations
            
        Returns:
            CalculationResult with the calculated value and performance metrics
        """
        start_time = time.perf_counter()
        
        try:
            # Find applicable calculation rules
            applicable_rules = self._find_applicable_rules(column)
            
            if not applicable_rules:
                return CalculationResult(
                    success=True,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )
            
            # Execute calculations for each applicable rule
            results = []
            failed_results = []
            
            for rule in applicable_rules:
                if not rule.enabled:
                    continue
                    
                result = self._execute_calculation_rule(rule, row_data, all_data)
                if result.success and result.value is not None:
                    # Update row data with calculated value
                    row_data[rule.target_column] = result.value
                    results.append(result)
                elif not result.success:
                    logger.warning(f"Calculation failed for rule {rule.id}: {result.error}")
                    self.calculationError.emit("calculation_error", result.error or "Unknown error")
                    failed_results.append(result)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance metrics
            self._update_performance_metrics(execution_time, is_total=False)
            
            # Check performance thresholds
            if execution_time > self.individual_timeout_ms:
                self.performanceAlert.emit("individual_calculation_timeout", execution_time)
                logger.warning(f"Individual calculation exceeded timeout: {execution_time:.2f}ms")
            
            # Return the primary result
            if results:
                # Return first successful calculation
                primary_result = results[0]
                primary_result.execution_time_ms = execution_time
                return primary_result
            elif failed_results:
                # Return first failed calculation
                primary_result = failed_results[0]
                primary_result.execution_time_ms = execution_time
                return primary_result
            else:
                # No applicable rules, return success
                return CalculationResult(
                    success=True,
                    execution_time_ms=execution_time
                )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            error_msg = f"Calculation engine error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return CalculationResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def calculate_totals(self, all_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate document totals based on all table data.
        
        Args:
            all_data: All rows of table data
            
        Returns:
            Dictionary with calculated totals
        """
        start_time = time.perf_counter()
        totals = {}
        
        try:
            for rule_id, rule in self.total_rules.items():
                if not rule.enabled:
                    continue
                
                try:
                    total_value = self._calculate_total_for_rule(rule, all_data)
                    if total_value is not None:
                        # Apply formatting if specified
                        if rule.format_function:
                            formatted_value = rule.format_function(total_value)
                        else:
                            formatted_value = self._format_decimal(total_value, rule.precision)
                        
                        totals[rule.column] = {
                            'value': total_value,
                            'formatted': formatted_value,
                            'rule_id': rule_id
                        }
                        
                except Exception as e:
                    error_msg = f"Total calculation failed for {rule_id}: {str(e)}"
                    logger.error(error_msg)
                    self.calculationError.emit("total_calculation_error", error_msg)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance metrics
            self._update_performance_metrics(execution_time, is_total=True)
            
            # Check performance thresholds
            if execution_time > self.total_timeout_ms:
                self.performanceAlert.emit("total_calculation_timeout", execution_time)
                logger.warning(f"Total calculation exceeded timeout: {execution_time:.2f}ms")
            
            # Emit completion signal
            self.totalCalculationCompleted.emit(totals)
            
            return totals
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            error_msg = f"Total calculation engine error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.calculationError.emit("total_calculation_error", error_msg)
            return {}
    
    def _find_applicable_rules(self, changed_column: str) -> List[CalculationRule]:
        """Find calculation rules that should be triggered by a column change"""
        applicable_rules = []
        
        for rule in self.calculation_rules.values():
            if not rule.trigger_on_change:
                continue
                
            # Check if the changed column is a source column for this rule
            if changed_column in rule.source_columns:
                applicable_rules.append(rule)
            
            # Check dependencies
            if changed_column in rule.dependencies:
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _execute_calculation_rule(self, rule: CalculationRule, row_data: Dict[str, Any], 
                                 all_data: Optional[List[Dict[str, Any]]]) -> CalculationResult:
        """Execute a single calculation rule"""
        try:
            if rule.calculation_type == CalculationType.MULTIPLY:
                return self._calculate_multiply(rule, row_data)
            elif rule.calculation_type == CalculationType.CUSTOM and rule.custom_function:
                return self._calculate_custom(rule, row_data, all_data)
            else:
                return CalculationResult(
                    success=False,
                    error=f"Unsupported calculation type: {rule.calculation_type}",
                    rule_id=rule.id
                )
                
        except Exception as e:
            return CalculationResult(
                success=False,
                error=f"Calculation execution error: {str(e)}",
                rule_id=rule.id
            )
    
    def _calculate_multiply(self, rule: CalculationRule, row_data: Dict[str, Any]) -> CalculationResult:
        """Calculate multiplication of source columns"""
        try:
            if len(rule.source_columns) < 2:
                return CalculationResult(
                    success=False,
                    error="Multiply calculation requires at least 2 source columns",
                    rule_id=rule.id
                )
            
            result = Decimal('1')
            for column in rule.source_columns:
                value = row_data.get(column)
                if value is None or value == '':
                    # Return 0 if any value is missing
                    return CalculationResult(
                        success=True,
                        value=Decimal('0'),
                        rule_id=rule.id
                    )
                
                try:
                    decimal_value = Decimal(str(value))
                    result *= decimal_value
                except (InvalidOperation, ValueError) as e:
                    return CalculationResult(
                        success=False,
                        error=f"Invalid numeric value in column {column}: {value}",
                        rule_id=rule.id
                    )
            
            # Round to specified precision
            rounded_result = result.quantize(
                Decimal('0.1') ** rule.precision,
                rounding=ROUND_HALF_UP
            )
            
            return CalculationResult(
                success=True,
                value=rounded_result,
                rule_id=rule.id
            )
            
        except Exception as e:
            return CalculationResult(
                success=False,
                error=f"Multiply calculation error: {str(e)}",
                rule_id=rule.id
            )
    
    def _calculate_custom(self, rule: CalculationRule, row_data: Dict[str, Any], 
                         all_data: Optional[List[Dict[str, Any]]]) -> CalculationResult:
        """Execute custom calculation function"""
        try:
            if not rule.custom_function:
                return CalculationResult(
                    success=False,
                    error="Custom function not provided",
                    rule_id=rule.id
                )
            
            result = rule.custom_function(row_data, all_data)
            
            # Convert to Decimal if numeric
            if isinstance(result, (int, float)):
                decimal_result = Decimal(str(result)).quantize(
                    Decimal('0.1') ** rule.precision,
                    rounding=ROUND_HALF_UP
                )
                result = decimal_result
            
            return CalculationResult(
                success=True,
                value=result,
                rule_id=rule.id
            )
            
        except Exception as e:
            return CalculationResult(
                success=False,
                error=f"Custom calculation error: {str(e)}",
                rule_id=rule.id
            )
    
    def _calculate_total_for_rule(self, rule: TotalCalculationRule, 
                                 all_data: List[Dict[str, Any]]) -> Optional[Decimal]:
        """Calculate total for a specific rule"""
        if not all_data:
            return Decimal('0')
        
        values = []
        for row in all_data:
            value = row.get(rule.column)
            if value is not None and value != '':
                try:
                    decimal_value = Decimal(str(value))
                    values.append(decimal_value)
                except (InvalidOperation, ValueError):
                    # Skip invalid values
                    continue
        
        if not values:
            return Decimal('0')
        
        if rule.calculation_type == CalculationType.SUM:
            result = sum(values)
        elif rule.calculation_type == CalculationType.AVERAGE:
            result = sum(values) / len(values)
        elif rule.calculation_type == CalculationType.COUNT:
            result = Decimal(len(values))
        elif rule.calculation_type == CalculationType.MIN:
            result = min(values)
        elif rule.calculation_type == CalculationType.MAX:
            result = max(values)
        elif rule.calculation_type == CalculationType.CUSTOM and rule.custom_function:
            result = rule.custom_function(values)
            if isinstance(result, (int, float)):
                result = Decimal(str(result))
        else:
            return None
        
        # Round to specified precision
        return result.quantize(
            Decimal('0.1') ** rule.precision,
            rounding=ROUND_HALF_UP
        )
    
    def _format_decimal(self, value: Decimal, precision: int) -> str:
        """Format decimal value for display"""
        format_str = f"{{:.{precision}f}}"
        return format_str.format(float(value))
    
    def _update_performance_metrics(self, execution_time_ms: float, is_total: bool):
        """Update performance metrics"""
        current_time = time.time()
        
        if is_total:
            self.metrics.total_calculation_time_ms = execution_time_ms
        else:
            self.metrics.individual_calculation_time_ms = execution_time_ms
        
        # Update calculation history for rate calculation
        self.calculation_history.append(current_time)
        if len(self.calculation_history) > self.max_history_size:
            self.calculation_history.pop(0)
        
        # Calculate calculations per second
        if len(self.calculation_history) > 1:
            time_span = current_time - self.calculation_history[0]
            if time_span > 0:
                self.metrics.calculations_per_second = len(self.calculation_history) / time_span
        
        self.metrics.last_calculation_timestamp = current_time
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return self.metrics
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.metrics = PerformanceMetrics()
        self.calculation_history.clear()
    
    def set_performance_thresholds(self, individual_timeout_ms: int, total_timeout_ms: int):
        """Set performance thresholds for calculations"""
        self.individual_timeout_ms = individual_timeout_ms
        self.total_timeout_ms = total_timeout_ms
    
    def enable_performance_monitoring(self, enabled: bool):
        """Enable or disable performance monitoring"""
        self.performance_monitoring_enabled = enabled
    
    def validate_calculation_rules(self) -> List[str]:
        """Validate all calculation rules and return list of issues"""
        issues = []
        
        for rule_id, rule in self.calculation_rules.items():
            if not rule.source_columns:
                issues.append(f"Rule {rule_id}: No source columns specified")
            
            if not rule.target_column:
                issues.append(f"Rule {rule_id}: No target column specified")
            
            if rule.calculation_type == CalculationType.CUSTOM and not rule.custom_function:
                issues.append(f"Rule {rule_id}: Custom calculation type requires custom_function")
            
            if rule.calculation_type == CalculationType.MULTIPLY and len(rule.source_columns) < 2:
                issues.append(f"Rule {rule_id}: Multiply calculation requires at least 2 source columns")
        
        return issues


def create_calculation_engine() -> TablePartCalculationEngine:
    """Factory function to create a calculation engine with standard configuration"""
    engine = TablePartCalculationEngine()
    
    # Add common calculation rules
    # These can be customized based on specific document types
    
    return engine


def create_quantity_price_rule(quantity_column: str = "quantity", 
                              price_column: str = "price",
                              sum_column: str = "sum",
                              precision: int = 2) -> CalculationRule:
    """Create a standard quantity × price calculation rule"""
    return CalculationRule(
        id=f"{quantity_column}_{price_column}_{sum_column}",
        name=f"{quantity_column.title()} × {price_column.title()} = {sum_column.title()}",
        source_columns=[quantity_column, price_column],
        target_column=sum_column,
        calculation_type=CalculationType.MULTIPLY,
        precision=precision
    )


def create_sum_total_rule(column: str, precision: int = 2) -> TotalCalculationRule:
    """Create a standard sum total calculation rule"""
    return TotalCalculationRule(
        column=column,
        calculation_type=CalculationType.SUM,
        precision=precision
    )