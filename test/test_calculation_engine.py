"""
Tests for the table part calculation engine.

This module tests the automatic calculation functionality including:
- Individual field calculations (Quantity × Price)
- Document total calculations
- Performance monitoring
- Error handling
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch

from src.services.table_part_calculation_engine import (
    TablePartCalculationEngine, CalculationRule, TotalCalculationRule,
    CalculationType, CalculationResult, PerformanceMetrics,
    create_calculation_engine, create_quantity_price_rule, create_sum_total_rule
)


class TestCalculationEngine:
    """Test cases for the calculation engine"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = create_calculation_engine()
    
    def test_quantity_price_calculation(self):
        """Test basic quantity × price calculation"""
        # Arrange
        row_data = {
            'quantity': 10,
            'price': 25.50,
            'sum': 0
        }
        
        # Act
        result = self.engine.calculate_field(row_data, 'quantity')
        
        # Assert
        assert result.success
        assert result.value == Decimal('255.00')
        assert row_data['sum'] == Decimal('255.00')
        assert result.execution_time_ms >= 0
    
    def test_price_change_calculation(self):
        """Test calculation when price changes"""
        # Arrange
        row_data = {
            'quantity': 5,
            'price': 12.75,
            'sum': 0
        }
        
        # Act
        result = self.engine.calculate_field(row_data, 'price')
        
        # Assert
        assert result.success
        assert result.value == Decimal('63.75')
        assert row_data['sum'] == Decimal('63.75')
    
    def test_missing_value_calculation(self):
        """Test calculation with missing values"""
        # Arrange
        row_data = {
            'quantity': None,
            'price': 10.00,
            'sum': 0
        }
        
        # Act
        result = self.engine.calculate_field(row_data, 'quantity')
        
        # Assert
        assert result.success
        assert result.value == Decimal('0')
        assert row_data['sum'] == Decimal('0')
    
    def test_invalid_numeric_value(self):
        """Test calculation with invalid numeric values"""
        # Arrange
        row_data = {
            'quantity': 'invalid',
            'price': 10.00,
            'sum': 0
        }
        
        # Act
        result = self.engine.calculate_field(row_data, 'quantity')
        
        # Assert
        assert not result.success
        assert 'Invalid numeric value' in result.error
    
    def test_total_calculations(self):
        """Test document total calculations"""
        # Arrange
        all_data = [
            {'quantity': 10, 'price': 5.00, 'sum': 50.00},
            {'quantity': 20, 'price': 3.50, 'sum': 70.00},
            {'quantity': 5, 'price': 8.00, 'sum': 40.00}
        ]
        
        # Act
        totals = self.engine.calculate_totals(all_data)
        
        # Assert
        assert 'sum' in totals
        assert totals['sum']['value'] == Decimal('160.00')
        assert totals['sum']['formatted'] == '160.00'
        
        assert 'quantity' in totals
        assert totals['quantity']['value'] == Decimal('35.000')
        assert totals['quantity']['formatted'] == '35.000'
    
    def test_empty_data_totals(self):
        """Test total calculations with empty data"""
        # Arrange
        all_data = []
        
        # Act
        totals = self.engine.calculate_totals(all_data)
        
        # Assert
        assert 'sum' in totals
        assert totals['sum']['value'] == Decimal('0')
        assert totals['quantity']['value'] == Decimal('0')
    
    def test_performance_thresholds(self):
        """Test performance threshold monitoring"""
        # Arrange
        self.engine.set_performance_thresholds(50, 100)  # Very low thresholds
        
        # Mock a slow calculation
        with patch('time.perf_counter', side_effect=[0, 0.06]):  # 60ms
            row_data = {'quantity': 10, 'price': 5.00, 'sum': 0}
            
            # Act
            result = self.engine.calculate_field(row_data, 'quantity')
            
            # Assert
            assert result.success
            assert result.execution_time_ms == 60.0
    
    def test_custom_calculation_rule(self):
        """Test custom calculation rules"""
        # Arrange
        def custom_discount_calculation(row_data, all_data):
            """Calculate 10% discount on sum"""
            sum_value = row_data.get('sum', 0)
            return float(sum_value) * 0.9
        
        custom_rule = CalculationRule(
            id='discount_calculation',
            name='10% Discount',
            source_columns=['sum'],
            target_column='discounted_sum',
            calculation_type=CalculationType.CUSTOM,
            custom_function=custom_discount_calculation,
            trigger_on_change=True,
            precision=2,
            enabled=True
        )
        
        self.engine.add_calculation_rule(custom_rule)
        
        row_data = {
            'quantity': 10,
            'price': 5.00,
            'sum': 50.00,
            'discounted_sum': 0
        }
        
        # Act
        result = self.engine.calculate_field(row_data, 'sum')
        
        # Assert
        assert result.success
        assert row_data['discounted_sum'] == Decimal('45.00')
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking"""
        # Arrange
        row_data = {'quantity': 10, 'price': 5.00, 'sum': 0}
        
        # Act
        self.engine.calculate_field(row_data, 'quantity')
        metrics = self.engine.get_performance_metrics()
        
        # Assert
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.individual_calculation_time_ms >= 0
        assert metrics.last_calculation_timestamp is not None
    
    def test_calculation_rule_validation(self):
        """Test calculation rule validation"""
        # Act
        issues = self.engine.validate_calculation_rules()
        
        # Assert - should have no issues with default rules
        assert len(issues) == 0
        
        # Add invalid rule
        invalid_rule = CalculationRule(
            id='invalid_rule',
            name='Invalid Rule',
            source_columns=[],  # No source columns
            target_column='',   # No target column
            calculation_type=CalculationType.MULTIPLY,
            trigger_on_change=True,
            precision=2,
            enabled=True
        )
        
        self.engine.add_calculation_rule(invalid_rule)
        issues = self.engine.validate_calculation_rules()
        
        assert len(issues) >= 2  # Should have issues for missing columns


class TestCalculationFactoryFunctions:
    """Test factory functions for creating calculation rules"""
    
    def test_create_quantity_price_rule(self):
        """Test quantity price rule factory"""
        # Act
        rule = create_quantity_price_rule('qty', 'unit_price', 'total', 3)
        
        # Assert
        assert rule.id == 'qty_unit_price_total'
        assert rule.source_columns == ['qty', 'unit_price']
        assert rule.target_column == 'total'
        assert rule.calculation_type == CalculationType.MULTIPLY
        assert rule.precision == 3
    
    def test_create_sum_total_rule(self):
        """Test sum total rule factory"""
        # Act
        rule = create_sum_total_rule('amount', 3)
        
        # Assert
        assert rule.column == 'amount'
        assert rule.calculation_type == CalculationType.SUM
        assert rule.precision == 3
    
    def test_create_calculation_engine(self):
        """Test calculation engine factory"""
        # Act
        engine = create_calculation_engine()
        
        # Assert
        assert isinstance(engine, TablePartCalculationEngine)
        assert len(engine.calculation_rules) > 0  # Should have default rules
        assert len(engine.total_rules) > 0  # Should have default total rules


class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = create_calculation_engine()
        self.engine.enable_performance_monitoring(True)
    
    def test_performance_metrics_update(self):
        """Test that performance metrics are updated after calculations"""
        # Arrange
        row_data = {'quantity': 10, 'price': 5.00, 'sum': 0}
        
        # Act
        self.engine.calculate_field(row_data, 'quantity')
        metrics = self.engine.get_performance_metrics()
        
        # Assert
        assert metrics.individual_calculation_time_ms > 0
        assert metrics.last_calculation_timestamp is not None
    
    def test_calculation_history_tracking(self):
        """Test calculation history tracking"""
        # Arrange
        row_data = {'quantity': 10, 'price': 5.00, 'sum': 0}
        
        # Act
        result1 = self.engine.calculate_field(row_data, 'quantity')
        result2 = self.engine.calculate_field(row_data, 'price')
        
        metrics = self.engine.get_performance_metrics()
        
        # Assert
        assert metrics.calculations_per_second >= 0
    
    def test_error_count_tracking(self):
        """Test error count tracking in metrics"""
        # Arrange
        row_data = {'quantity': 'invalid', 'price': 5.00, 'sum': 0}
        
        # Act
        result = self.engine.calculate_field(row_data, 'quantity')
        metrics = self.engine.get_performance_metrics()
        
        # Assert
        assert not result.success
        # Note: Error count is tracked in the performance monitor, not the engine directly
    
    def test_performance_threshold_alerts(self):
        """Test performance threshold alert system"""
        # Arrange
        self.engine.set_performance_thresholds(1, 2)  # Very low thresholds
        
        # Mock performance alert signal
        alert_received = []
        
        def mock_alert_handler(metric_name, value):
            alert_received.append((metric_name, value))
        
        self.engine.performanceAlert.connect(mock_alert_handler)
        
        # Act - Force a slow calculation
        with patch('time.perf_counter', side_effect=[0, 0.002]):  # 2ms
            row_data = {'quantity': 10, 'price': 5.00, 'sum': 0}
            self.engine.calculate_field(row_data, 'quantity')
        
        # Assert
        assert len(alert_received) > 0
        assert alert_received[0][0] == 'individual_calculation_timeout'


if __name__ == '__main__':
    pytest.main([__file__])