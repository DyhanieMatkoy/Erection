"""
Example demonstrating the automatic calculation engine for table parts.

This example shows how to use the calculation engine to automatically
calculate field values and document totals with performance monitoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

from src.services.table_part_calculation_engine import (
    create_calculation_engine, create_quantity_price_rule, create_sum_total_rule,
    CalculationRule, TotalCalculationRule, CalculationType
)
from src.views.widgets.calculation_performance_monitor import create_performance_monitor


class CalculationEngineDemo(QMainWindow):
    """Demo application for the calculation engine"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculation Engine Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create calculation engine
        self.engine = create_calculation_engine()
        
        # Create performance monitor
        self.performance_monitor = create_performance_monitor()
        
        # Connect engine signals to monitor
        self.engine.calculationCompleted.connect(self.performance_monitor.add_calculation_result)
        self.engine.calculationError.connect(self._on_calculation_error)
        self.engine.performanceAlert.connect(self._on_performance_alert)
        
        self._setup_ui()
        self._setup_demo_data()
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Automatic Calculation Engine Demo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Demo buttons
        self.demo_button1 = QPushButton("Demo 1: Basic Quantity × Price Calculation")
        self.demo_button1.clicked.connect(self.demo_basic_calculation)
        layout.addWidget(self.demo_button1)
        
        self.demo_button2 = QPushButton("Demo 2: Document Totals Calculation")
        self.demo_button2.clicked.connect(self.demo_totals_calculation)
        layout.addWidget(self.demo_button2)
        
        self.demo_button3 = QPushButton("Demo 3: Custom Calculation Rules")
        self.demo_button3.clicked.connect(self.demo_custom_calculation)
        layout.addWidget(self.demo_button3)
        
        self.demo_button4 = QPushButton("Demo 4: Performance Monitoring")
        self.demo_button4.clicked.connect(self.demo_performance_monitoring)
        layout.addWidget(self.demo_button4)
        
        self.demo_button5 = QPushButton("Demo 5: Error Handling")
        self.demo_button5.clicked.connect(self.demo_error_handling)
        layout.addWidget(self.demo_button5)
        
        # Results display
        self.results_label = QLabel("Click a demo button to see results...")
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; margin: 10px;")
        self.results_label.setWordWrap(True)
        layout.addWidget(self.results_label)
        
        # Performance monitor
        layout.addWidget(self.performance_monitor)
    
    def _setup_demo_data(self):
        """Setup demo data and custom rules"""
        # Add a custom discount calculation rule
        discount_rule = CalculationRule(
            id="discount_calculation",
            name="10% Discount Calculation",
            source_columns=["sum"],
            target_column="discounted_sum",
            calculation_type=CalculationType.CUSTOM,
            custom_function=self._calculate_discount,
            trigger_on_change=True,
            precision=2,
            enabled=True
        )
        self.engine.add_calculation_rule(discount_rule)
        
        # Add a custom total rule for discounted amounts
        discount_total = TotalCalculationRule(
            column="discounted_sum",
            calculation_type=CalculationType.SUM,
            precision=2,
            enabled=True
        )
        self.engine.add_total_rule("discount_total", discount_total)
    
    def _calculate_discount(self, row_data, all_data):
        """Custom function to calculate 10% discount"""
        sum_value = row_data.get('sum', 0)
        try:
            return float(sum_value) * 0.9
        except (ValueError, TypeError):
            return 0
    
    def demo_basic_calculation(self):
        """Demo basic quantity × price calculation"""
        self.results_label.setText("Demo 1: Basic Quantity × Price Calculation\n\n")
        
        # Test data
        test_cases = [
            {"quantity": 10, "price": 25.50, "sum": 0},
            {"quantity": 5, "price": 12.75, "sum": 0},
            {"quantity": 20, "price": 8.00, "sum": 0}
        ]
        
        results_text = "Demo 1: Basic Quantity × Price Calculation\n\n"
        
        for i, row_data in enumerate(test_cases, 1):
            original_data = row_data.copy()
            
            # Trigger calculation by changing quantity
            result = self.engine.calculate_field(row_data, 'quantity')
            
            results_text += f"Test Case {i}:\n"
            results_text += f"  Input: Quantity={original_data['quantity']}, Price={original_data['price']}\n"
            results_text += f"  Result: Sum={row_data['sum']}\n"
            results_text += f"  Success: {result.success}\n"
            results_text += f"  Execution Time: {result.execution_time_ms:.2f}ms\n\n"
        
        self.results_label.setText(results_text)
    
    def demo_totals_calculation(self):
        """Demo document totals calculation"""
        # Test data
        all_data = [
            {"quantity": 10, "price": 5.00, "sum": 50.00},
            {"quantity": 20, "price": 3.50, "sum": 70.00},
            {"quantity": 5, "price": 8.00, "sum": 40.00},
            {"quantity": 15, "price": 6.00, "sum": 90.00}
        ]
        
        # Calculate totals
        totals = self.engine.calculate_totals(all_data)
        
        results_text = "Demo 2: Document Totals Calculation\n\n"
        results_text += "Input Data:\n"
        for i, row in enumerate(all_data, 1):
            results_text += f"  Row {i}: Qty={row['quantity']}, Price={row['price']}, Sum={row['sum']}\n"
        
        results_text += "\nCalculated Totals:\n"
        for column, total_info in totals.items():
            results_text += f"  {column.title()}: {total_info['formatted']} (Rule: {total_info['rule_id']})\n"
        
        self.results_label.setText(results_text)
    
    def demo_custom_calculation(self):
        """Demo custom calculation rules"""
        # Test data with discount calculation
        row_data = {"quantity": 10, "price": 15.00, "sum": 0, "discounted_sum": 0}
        
        results_text = "Demo 3: Custom Calculation Rules\n\n"
        results_text += f"Input: Quantity={row_data['quantity']}, Price={row_data['price']}\n\n"
        
        # First calculate the sum
        result1 = self.engine.calculate_field(row_data, 'quantity')
        results_text += f"Step 1 - Calculate Sum:\n"
        results_text += f"  Sum = {row_data['sum']}\n"
        results_text += f"  Execution Time: {result1.execution_time_ms:.2f}ms\n\n"
        
        # Then trigger discount calculation
        result2 = self.engine.calculate_field(row_data, 'sum')
        results_text += f"Step 2 - Calculate 10% Discount:\n"
        results_text += f"  Discounted Sum = {row_data['discounted_sum']}\n"
        results_text += f"  Execution Time: {result2.execution_time_ms:.2f}ms\n\n"
        
        # Calculate totals including discount
        all_data = [row_data]
        totals = self.engine.calculate_totals(all_data)
        
        results_text += "Totals with Custom Rules:\n"
        for column, total_info in totals.items():
            results_text += f"  {column.title()}: {total_info['formatted']}\n"
        
        self.results_label.setText(results_text)
    
    def demo_performance_monitoring(self):
        """Demo performance monitoring features"""
        results_text = "Demo 4: Performance Monitoring\n\n"
        
        # Perform multiple calculations to generate metrics
        test_data = [
            {"quantity": i, "price": i * 2.5, "sum": 0}
            for i in range(1, 11)
        ]
        
        results_text += "Performing 10 calculations...\n\n"
        
        for row_data in test_data:
            self.engine.calculate_field(row_data, 'quantity')
        
        # Get performance metrics
        metrics = self.engine.get_performance_metrics()
        
        results_text += "Performance Metrics:\n"
        results_text += f"  Individual Calculation Time: {metrics.individual_calculation_time_ms:.2f}ms\n"
        results_text += f"  Total Calculation Time: {metrics.total_calculation_time_ms:.2f}ms\n"
        results_text += f"  Calculations Per Second: {metrics.calculations_per_second:.2f}\n"
        results_text += f"  Error Count: {metrics.error_count}\n"
        results_text += f"  Memory Usage: {metrics.memory_usage_mb:.2f}MB\n\n"
        
        results_text += "Performance Status: "
        status = self.performance_monitor.get_current_status()
        results_text += status.value.title()
        
        self.results_label.setText(results_text)
    
    def demo_error_handling(self):
        """Demo error handling capabilities"""
        results_text = "Demo 5: Error Handling\n\n"
        
        # Test cases with various error conditions
        error_cases = [
            {"quantity": "invalid", "price": 10.00, "sum": 0, "description": "Invalid quantity"},
            {"quantity": None, "price": 15.00, "sum": 0, "description": "Null quantity"},
            {"quantity": 5, "price": "not_a_number", "sum": 0, "description": "Invalid price"},
            {"quantity": "", "price": 20.00, "sum": 0, "description": "Empty quantity"}
        ]
        
        for i, test_case in enumerate(error_cases, 1):
            description = test_case.pop("description")
            result = self.engine.calculate_field(test_case, 'quantity')
            
            results_text += f"Error Test {i} - {description}:\n"
            results_text += f"  Input: Quantity={test_case['quantity']}, Price={test_case['price']}\n"
            results_text += f"  Success: {result.success}\n"
            
            if result.success:
                results_text += f"  Result: Sum={test_case['sum']}\n"
            else:
                results_text += f"  Error: {result.error}\n"
            
            results_text += f"  Execution Time: {result.execution_time_ms:.2f}ms\n\n"
        
        self.results_label.setText(results_text)
    
    def _on_calculation_error(self, error_type, message):
        """Handle calculation errors"""
        print(f"Calculation Error ({error_type}): {message}")
    
    def _on_performance_alert(self, metric_name, value):
        """Handle performance alerts"""
        print(f"Performance Alert - {metric_name}: {value:.2f}")


def main():
    """Main function to run the demo"""
    app = QApplication(sys.argv)
    
    # Create and show the demo window
    demo = CalculationEngineDemo()
    demo.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()