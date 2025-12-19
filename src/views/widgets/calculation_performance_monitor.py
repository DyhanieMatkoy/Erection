"""
Performance monitoring widget for table part calculations.

This module provides visual indicators and monitoring for calculation
performance, including timing metrics, error tracking, and performance alerts.
"""

import time
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGridLayout, QPushButton, QTextEdit, QTabWidget,
    QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
from dataclasses import dataclass
from enum import Enum

from ...services.table_part_calculation_engine import PerformanceMetrics, CalculationResult


class PerformanceStatus(Enum):
    """Performance status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceThresholds:
    """Performance thresholds for different status levels"""
    excellent_individual_ms: float = 50.0
    good_individual_ms: float = 80.0
    warning_individual_ms: float = 100.0
    
    excellent_total_ms: float = 100.0
    good_total_ms: float = 150.0
    warning_total_ms: float = 200.0
    
    max_error_rate: float = 0.05  # 5% error rate threshold


class CalculationPerformanceMonitor(QWidget):
    """
    Performance monitoring widget for calculation engine.
    
    Provides real-time monitoring of:
    - Calculation timing metrics
    - Error rates and counts
    - Performance status indicators
    - Historical performance data
    """
    
    # Signals
    performanceStatusChanged = pyqtSignal(PerformanceStatus)
    thresholdExceeded = pyqtSignal(str, float)  # metric_name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.thresholds = PerformanceThresholds()
        self.current_status = PerformanceStatus.EXCELLENT
        self.calculation_history: List[CalculationResult] = []
        self.max_history_size = 1000
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Update every second
        
        # Animation for status indicator
        self.status_animation = QPropertyAnimation(self, b"windowOpacity")
        self.status_animation.setDuration(300)
        self.status_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self._setup_ui()
        self._setup_styles()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create tabs for different monitoring views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Real-time metrics tab
        self._create_realtime_tab()
        
        # Historical data tab
        self._create_history_tab()
        
        # Settings tab
        self._create_settings_tab()
    
    def _create_realtime_tab(self):
        """Create real-time metrics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Status indicator
        status_group = QGroupBox("Статус производительности")
        status_layout = QHBoxLayout(status_group)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 24))
        self.status_label = QLabel("Отлично")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_group)
        
        # Metrics grid
        metrics_group = QGroupBox("Метрики производительности")
        metrics_layout = QGridLayout(metrics_group)
        
        # Individual calculation time
        metrics_layout.addWidget(QLabel("Время расчета поля:"), 0, 0)
        self.individual_time_label = QLabel("0.0 мс")
        self.individual_time_bar = QProgressBar()
        self.individual_time_bar.setMaximum(100)  # Will be adjusted based on thresholds
        metrics_layout.addWidget(self.individual_time_label, 0, 1)
        metrics_layout.addWidget(self.individual_time_bar, 0, 2)
        
        # Total calculation time
        metrics_layout.addWidget(QLabel("Время расчета итогов:"), 1, 0)
        self.total_time_label = QLabel("0.0 мс")
        self.total_time_bar = QProgressBar()
        self.total_time_bar.setMaximum(200)  # Will be adjusted based on thresholds
        metrics_layout.addWidget(self.total_time_label, 1, 1)
        metrics_layout.addWidget(self.total_time_bar, 1, 2)
        
        # Calculations per second
        metrics_layout.addWidget(QLabel("Расчетов в секунду:"), 2, 0)
        self.calc_rate_label = QLabel("0.0")
        metrics_layout.addWidget(self.calc_rate_label, 2, 1)
        
        # Error count
        metrics_layout.addWidget(QLabel("Количество ошибок:"), 3, 0)
        self.error_count_label = QLabel("0")
        metrics_layout.addWidget(self.error_count_label, 3, 1)
        
        # Memory usage
        metrics_layout.addWidget(QLabel("Использование памяти:"), 4, 0)
        self.memory_label = QLabel("0.0 МБ")
        metrics_layout.addWidget(self.memory_label, 4, 1)
        
        layout.addWidget(metrics_group)
        
        # Performance indicators
        indicators_group = QGroupBox("Индикаторы")
        indicators_layout = QHBoxLayout(indicators_group)
        
        self.calculation_indicator = QLabel("⚪")
        self.calculation_indicator.setToolTip("Индикатор активных расчетов")
        self.calculation_indicator.setFont(QFont("Arial", 16))
        
        self.error_indicator = QLabel("⚪")
        self.error_indicator.setToolTip("Индикатор ошибок")
        self.error_indicator.setFont(QFont("Arial", 16))
        
        indicators_layout.addWidget(QLabel("Расчеты:"))
        indicators_layout.addWidget(self.calculation_indicator)
        indicators_layout.addWidget(QLabel("Ошибки:"))
        indicators_layout.addWidget(self.error_indicator)
        indicators_layout.addStretch()
        
        layout.addWidget(indicators_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Реальное время")
    
    def _create_history_tab(self):
        """Create historical data tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.clear_history_btn = QPushButton("Очистить историю")
        self.clear_history_btn.clicked.connect(self._clear_history)
        
        self.export_history_btn = QPushButton("Экспорт данных")
        self.export_history_btn.clicked.connect(self._export_history)
        
        controls_layout.addWidget(self.clear_history_btn)
        controls_layout.addWidget(self.export_history_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # History display
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.history_text)
        
        self.tab_widget.addTab(tab, "История")
    
    def _create_settings_tab(self):
        """Create settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Threshold settings
        thresholds_group = QGroupBox("Пороговые значения")
        thresholds_layout = QGridLayout(thresholds_group)
        
        # Individual calculation thresholds
        thresholds_layout.addWidget(QLabel("Расчет поля - Отлично (мс):"), 0, 0)
        self.individual_excellent_input = QLabel(str(self.thresholds.excellent_individual_ms))
        thresholds_layout.addWidget(self.individual_excellent_input, 0, 1)
        
        thresholds_layout.addWidget(QLabel("Расчет поля - Хорошо (мс):"), 1, 0)
        self.individual_good_input = QLabel(str(self.thresholds.good_individual_ms))
        thresholds_layout.addWidget(self.individual_good_input, 1, 1)
        
        thresholds_layout.addWidget(QLabel("Расчет поля - Предупреждение (мс):"), 2, 0)
        self.individual_warning_input = QLabel(str(self.thresholds.warning_individual_ms))
        thresholds_layout.addWidget(self.individual_warning_input, 2, 1)
        
        # Total calculation thresholds
        thresholds_layout.addWidget(QLabel("Расчет итогов - Отлично (мс):"), 3, 0)
        self.total_excellent_input = QLabel(str(self.thresholds.excellent_total_ms))
        thresholds_layout.addWidget(self.total_excellent_input, 3, 1)
        
        thresholds_layout.addWidget(QLabel("Расчет итогов - Хорошо (мс):"), 4, 0)
        self.total_good_input = QLabel(str(self.thresholds.good_total_ms))
        thresholds_layout.addWidget(self.total_good_input, 4, 1)
        
        thresholds_layout.addWidget(QLabel("Расчет итогов - Предупреждение (мс):"), 5, 0)
        self.total_warning_input = QLabel(str(self.thresholds.warning_total_ms))
        thresholds_layout.addWidget(self.total_warning_input, 5, 1)
        
        layout.addWidget(thresholds_group)
        
        # Monitoring settings
        monitoring_group = QGroupBox("Настройки мониторинга")
        monitoring_layout = QGridLayout(monitoring_group)
        
        monitoring_layout.addWidget(QLabel("Размер истории:"), 0, 0)
        self.history_size_label = QLabel(str(self.max_history_size))
        monitoring_layout.addWidget(self.history_size_label, 0, 1)
        
        monitoring_layout.addWidget(QLabel("Интервал обновления:"), 1, 0)
        self.update_interval_label = QLabel("1000 мс")
        monitoring_layout.addWidget(self.update_interval_label, 1, 1)
        
        layout.addWidget(monitoring_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Настройки")
    
    def _setup_styles(self):
        """Setup widget styles"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            
            QLabel {
                color: #333333;
            }
        """)
    
    def update_metrics(self, metrics: PerformanceMetrics):
        """Update display with new performance metrics"""
        # Update labels
        self.individual_time_label.setText(f"{metrics.individual_calculation_time_ms:.1f} мс")
        self.total_time_label.setText(f"{metrics.total_calculation_time_ms:.1f} мс")
        self.calc_rate_label.setText(f"{metrics.calculations_per_second:.1f}")
        self.error_count_label.setText(str(metrics.error_count))
        self.memory_label.setText(f"{metrics.memory_usage_mb:.2f} МБ")
        
        # Update progress bars
        individual_percentage = min(100, (metrics.individual_calculation_time_ms / self.thresholds.warning_individual_ms) * 100)
        self.individual_time_bar.setValue(int(individual_percentage))
        
        total_percentage = min(100, (metrics.total_calculation_time_ms / self.thresholds.warning_total_ms) * 100)
        self.total_time_bar.setValue(int(total_percentage))
        
        # Update status
        new_status = self._calculate_performance_status(metrics)
        if new_status != self.current_status:
            self.current_status = new_status
            self._update_status_display()
            self.performanceStatusChanged.emit(new_status)
        
        # Update progress bar colors based on performance
        self._update_progress_bar_colors(metrics)
    
    def add_calculation_result(self, result: CalculationResult):
        """Add a calculation result to the history"""
        self.calculation_history.append(result)
        
        # Limit history size
        if len(self.calculation_history) > self.max_history_size:
            self.calculation_history.pop(0)
        
        # Show calculation indicator
        self._show_calculation_activity()
        
        # Show error indicator if calculation failed
        if not result.success:
            self._show_error_activity()
    
    def show_calculation_indicator(self, duration_ms: int = 500):
        """Show visual indicator for active calculation"""
        self.calculation_indicator.setText("🟢")
        QTimer.singleShot(duration_ms, lambda: self.calculation_indicator.setText("⚪"))
    
    def show_error_indicator(self, duration_ms: int = 2000):
        """Show visual indicator for calculation error"""
        self.error_indicator.setText("🔴")
        QTimer.singleShot(duration_ms, lambda: self.error_indicator.setText("⚪"))
    
    def _calculate_performance_status(self, metrics: PerformanceMetrics) -> PerformanceStatus:
        """Calculate overall performance status based on metrics"""
        individual_time = metrics.individual_calculation_time_ms
        total_time = metrics.total_calculation_time_ms
        
        # Check for critical performance issues
        if (individual_time > self.thresholds.warning_individual_ms or 
            total_time > self.thresholds.warning_total_ms):
            return PerformanceStatus.CRITICAL
        
        # Check for warning conditions
        if (individual_time > self.thresholds.good_individual_ms or 
            total_time > self.thresholds.good_total_ms):
            return PerformanceStatus.WARNING
        
        # Check for good performance
        if (individual_time > self.thresholds.excellent_individual_ms or 
            total_time > self.thresholds.excellent_total_ms):
            return PerformanceStatus.GOOD
        
        return PerformanceStatus.EXCELLENT
    
    def _update_status_display(self):
        """Update the status indicator display"""
        status_colors = {
            PerformanceStatus.EXCELLENT: ("#4CAF50", "Отлично"),
            PerformanceStatus.GOOD: ("#8BC34A", "Хорошо"),
            PerformanceStatus.WARNING: ("#FF9800", "Предупреждение"),
            PerformanceStatus.CRITICAL: ("#F44336", "Критично")
        }
        
        color, text = status_colors[self.current_status]
        self.status_indicator.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")
    
    def _update_progress_bar_colors(self, metrics: PerformanceMetrics):
        """Update progress bar colors based on performance thresholds"""
        # Individual calculation progress bar
        if metrics.individual_calculation_time_ms > self.thresholds.warning_individual_ms:
            color = "#F44336"  # Red
        elif metrics.individual_calculation_time_ms > self.thresholds.good_individual_ms:
            color = "#FF9800"  # Orange
        else:
            color = "#4CAF50"  # Green
        
        self.individual_time_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        
        # Total calculation progress bar
        if metrics.total_calculation_time_ms > self.thresholds.warning_total_ms:
            color = "#F44336"  # Red
        elif metrics.total_calculation_time_ms > self.thresholds.good_total_ms:
            color = "#FF9800"  # Orange
        else:
            color = "#4CAF50"  # Green
        
        self.total_time_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
    
    def _show_calculation_activity(self):
        """Show visual feedback for calculation activity"""
        self.show_calculation_indicator()
    
    def _show_error_activity(self):
        """Show visual feedback for calculation errors"""
        self.show_error_indicator()
    
    def _update_display(self):
        """Update the display with current data"""
        # Update history display
        if self.calculation_history:
            history_text = "Последние расчеты:\n\n"
            for i, result in enumerate(self.calculation_history[-10:]):  # Show last 10
                status = "✓" if result.success else "✗"
                time_str = f"{result.execution_time_ms:.1f}мс"
                error_str = f" - {result.error}" if result.error else ""
                history_text += f"{status} {time_str}{error_str}\n"
            
            self.history_text.setPlainText(history_text)
    
    def _clear_history(self):
        """Clear calculation history"""
        self.calculation_history.clear()
        self.history_text.clear()
    
    def _export_history(self):
        """Export calculation history to file"""
        # This would open a file dialog and export the history
        # Implementation depends on specific requirements
        pass
    
    def set_thresholds(self, thresholds: PerformanceThresholds):
        """Set new performance thresholds"""
        self.thresholds = thresholds
        
        # Update threshold displays
        self.individual_excellent_input.setText(str(thresholds.excellent_individual_ms))
        self.individual_good_input.setText(str(thresholds.good_individual_ms))
        self.individual_warning_input.setText(str(thresholds.warning_individual_ms))
        
        self.total_excellent_input.setText(str(thresholds.excellent_total_ms))
        self.total_good_input.setText(str(thresholds.good_total_ms))
        self.total_warning_input.setText(str(thresholds.warning_total_ms))
        
        # Update progress bar maximums
        self.individual_time_bar.setMaximum(int(thresholds.warning_individual_ms))
        self.total_time_bar.setMaximum(int(thresholds.warning_total_ms))
    
    def get_current_status(self) -> PerformanceStatus:
        """Get current performance status"""
        return self.current_status
    
    def get_calculation_history(self) -> List[CalculationResult]:
        """Get calculation history"""
        return self.calculation_history.copy()


def create_performance_monitor() -> CalculationPerformanceMonitor:
    """Factory function to create a performance monitor"""
    return CalculationPerformanceMonitor()