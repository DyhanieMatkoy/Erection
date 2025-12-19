"""
Table Part Print Dialog

This module provides a print dialog specifically designed for table parts,
with preview functionality and print configuration options.
"""

from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QRadioButton, QSpinBox, QCheckBox, QTextEdit, QSplitter,
    QScrollArea, QWidget, QButtonGroup, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextDocument, QTextCursor, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from ...services.table_part_print_service import (
    TablePartPrintService, PrintConfiguration, PrintFormat,
    PageOrientation, create_print_service
)


class PrintPreviewWidget(QWidget):
    """Widget for displaying print preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = QTextDocument()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview UI"""
        layout = QVBoxLayout(self)
        
        # Create scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create preview text edit (read-only)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setDocument(self.document)
        
        # Set preview styling
        font = QFont("Courier New", 10)
        self.preview_text.setFont(font)
        
        scroll_area.setWidget(self.preview_text)
        layout.addWidget(scroll_area)
    
    def set_content(self, html_content: str):
        """Set the preview content"""
        self.document.setHtml(html_content)
    
    def clear_content(self):
        """Clear the preview content"""
        self.document.clear()


class PrintWorkerThread(QThread):
    """Worker thread for generating print content"""
    
    contentReady = pyqtSignal(str)  # HTML content
    errorOccurred = pyqtSignal(str)  # Error message
    progressUpdated = pyqtSignal(int)  # Progress percentage
    
    def __init__(self, print_service: TablePartPrintService, 
                 table_data: List[Dict[str, Any]], 
                 config: PrintConfiguration):
        super().__init__()
        self.print_service = print_service
        self.table_data = table_data
        self.config = config
    
    def run(self):
        """Generate print content in background thread"""
        try:
            self.progressUpdated.emit(10)
            
            # Generate HTML content
            html_content = self.print_service.generate_html_preview(
                self.table_data, self.config
            )
            
            self.progressUpdated.emit(100)
            self.contentReady.emit(html_content)
            
        except Exception as e:
            self.errorOccurred.emit(str(e))


class TablePartPrintDialog(QDialog):
    """
    Print dialog for table parts with preview and configuration options.
    
    Provides:
    - Print configuration (orientation, margins, headers)
    - Live preview of print output
    - Page setup options
    - Print to printer or PDF
    """
    
    printRequested = pyqtSignal(dict)  # Print configuration
    
    def __init__(self, table_data: List[Dict[str, Any]], 
                 table_name: str = "Табличная часть", 
                 parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.table_name = table_name
        self.print_service = create_print_service()
        self.worker_thread = None
        
        self.setWindowTitle(f"Печать: {table_name}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.connect_signals()
        self.load_default_settings()
        self.update_preview()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QHBoxLayout(self)
        
        # Create splitter for settings and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Print settings
        settings_widget = self.create_settings_panel()
        splitter.addWidget(settings_widget)
        
        # Right panel - Preview
        preview_widget = self.create_preview_panel()
        splitter.addWidget(preview_widget)
        
        # Set splitter proportions (30% settings, 70% preview)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def create_settings_panel(self) -> QWidget:
        """Create the print settings panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Page setup group
        page_group = QGroupBox("Настройки страницы")
        page_layout = QVBoxLayout(page_group)
        
        # Orientation
        orientation_layout = QHBoxLayout()
        orientation_layout.addWidget(QLabel("Ориентация:"))
        
        self.orientation_group = QButtonGroup(self)
        self.portrait_radio = QRadioButton("Книжная")
        self.landscape_radio = QRadioButton("Альбомная")
        
        self.orientation_group.addButton(self.portrait_radio, 0)
        self.orientation_group.addButton(self.landscape_radio, 1)
        
        orientation_layout.addWidget(self.portrait_radio)
        orientation_layout.addWidget(self.landscape_radio)
        orientation_layout.addStretch()
        
        page_layout.addLayout(orientation_layout)
        
        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Масштаб:"))
        
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(25, 200)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix("%")
        
        scale_layout.addWidget(self.scale_spin)
        scale_layout.addStretch()
        
        page_layout.addLayout(scale_layout)
        
        # Margins
        margins_layout = QVBoxLayout()
        margins_layout.addWidget(QLabel("Поля (мм):"))
        
        margins_grid = QHBoxLayout()
        
        self.top_margin = QSpinBox()
        self.top_margin.setRange(0, 50)
        self.top_margin.setValue(20)
        margins_grid.addWidget(QLabel("Верх:"))
        margins_grid.addWidget(self.top_margin)
        
        self.bottom_margin = QSpinBox()
        self.bottom_margin.setRange(0, 50)
        self.bottom_margin.setValue(20)
        margins_grid.addWidget(QLabel("Низ:"))
        margins_grid.addWidget(self.bottom_margin)
        
        margins_layout.addLayout(margins_grid)
        
        margins_grid2 = QHBoxLayout()
        
        self.left_margin = QSpinBox()
        self.left_margin.setRange(0, 50)
        self.left_margin.setValue(15)
        margins_grid2.addWidget(QLabel("Лево:"))
        margins_grid2.addWidget(self.left_margin)
        
        self.right_margin = QSpinBox()
        self.right_margin.setRange(0, 50)
        self.right_margin.setValue(15)
        margins_grid2.addWidget(QLabel("Право:"))
        margins_grid2.addWidget(self.right_margin)
        
        margins_layout.addLayout(margins_grid2)
        page_layout.addLayout(margins_layout)
        
        layout.addWidget(page_group)
        
        # Table options group
        table_group = QGroupBox("Настройки таблицы")
        table_layout = QVBoxLayout(table_group)
        
        # Headers on each page
        self.repeat_headers_check = QCheckBox("Повторять заголовки на каждой странице")
        self.repeat_headers_check.setChecked(True)
        table_layout.addWidget(self.repeat_headers_check)
        
        # Show grid lines
        self.show_grid_check = QCheckBox("Показывать линии сетки")
        self.show_grid_check.setChecked(True)
        table_layout.addWidget(self.show_grid_check)
        
        # Fit to page width
        self.fit_width_check = QCheckBox("Подогнать по ширине страницы")
        self.fit_width_check.setChecked(False)
        table_layout.addWidget(self.fit_width_check)
        
        layout.addWidget(table_group)
        
        # Output format group
        format_group = QGroupBox("Формат вывода")
        format_layout = QVBoxLayout(format_group)
        
        self.format_group = QButtonGroup(self)
        self.printer_radio = QRadioButton("Принтер")
        self.pdf_radio = QRadioButton("PDF файл")
        
        self.format_group.addButton(self.printer_radio, 0)
        self.format_group.addButton(self.pdf_radio, 1)
        
        format_layout.addWidget(self.printer_radio)
        format_layout.addWidget(self.pdf_radio)
        
        layout.addWidget(format_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.preview_button = QPushButton("Обновить просмотр")
        self.preview_button.clicked.connect(self.update_preview)
        button_layout.addWidget(self.preview_button)
        
        self.print_button = QPushButton("Печать")
        self.print_button.clicked.connect(self.print_document)
        button_layout.addWidget(self.print_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return widget
    
    def create_preview_panel(self) -> QWidget:
        """Create the preview panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview title
        title_label = QLabel("Предварительный просмотр")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        # Preview widget
        self.preview_widget = PrintPreviewWidget()
        layout.addWidget(self.preview_widget)
        
        return widget
    
    def connect_signals(self):
        """Connect UI signals"""
        # Connect all settings controls to preview update
        self.orientation_group.buttonClicked.connect(self.on_settings_changed)
        self.scale_spin.valueChanged.connect(self.on_settings_changed)
        self.top_margin.valueChanged.connect(self.on_settings_changed)
        self.bottom_margin.valueChanged.connect(self.on_settings_changed)
        self.left_margin.valueChanged.connect(self.on_settings_changed)
        self.right_margin.valueChanged.connect(self.on_settings_changed)
        self.repeat_headers_check.toggled.connect(self.on_settings_changed)
        self.show_grid_check.toggled.connect(self.on_settings_changed)
        self.fit_width_check.toggled.connect(self.on_settings_changed)
    
    def load_default_settings(self):
        """Load default print settings"""
        # Set default values
        self.portrait_radio.setChecked(True)
        self.printer_radio.setChecked(True)
    
    def on_settings_changed(self):
        """Handle settings change with debounced preview update"""
        # Use timer to debounce rapid changes
        if not hasattr(self, 'update_timer'):
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(self.update_preview)
        
        self.update_timer.stop()
        self.update_timer.start(500)  # 500ms delay
    
    def get_print_configuration(self) -> PrintConfiguration:
        """Get current print configuration"""
        return PrintConfiguration(
            orientation=PageOrientation.PORTRAIT if self.portrait_radio.isChecked() else PageOrientation.LANDSCAPE,
            scale_percent=self.scale_spin.value(),
            top_margin_mm=self.top_margin.value(),
            bottom_margin_mm=self.bottom_margin.value(),
            left_margin_mm=self.left_margin.value(),
            right_margin_mm=self.right_margin.value(),
            repeat_headers=self.repeat_headers_check.isChecked(),
            show_grid=self.show_grid_check.isChecked(),
            fit_to_width=self.fit_width_check.isChecked(),
            format=PrintFormat.PRINTER if self.printer_radio.isChecked() else PrintFormat.PDF,
            table_name=self.table_name
        )
    
    def update_preview(self):
        """Update the print preview"""
        if not self.table_data:
            self.preview_widget.set_content("<p>Нет данных для предварительного просмотра</p>")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.preview_button.setEnabled(False)
        
        # Stop any existing worker
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Start background preview generation
        config = self.get_print_configuration()
        self.worker_thread = PrintWorkerThread(self.print_service, self.table_data, config)
        self.worker_thread.contentReady.connect(self.on_preview_ready)
        self.worker_thread.errorOccurred.connect(self.on_preview_error)
        self.worker_thread.progressUpdated.connect(self.progress_bar.setValue)
        self.worker_thread.start()
    
    @pyqtSlot(str)
    def on_preview_ready(self, html_content: str):
        """Handle preview content ready"""
        self.preview_widget.set_content(html_content)
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)
    
    @pyqtSlot(str)
    def on_preview_error(self, error_message: str):
        """Handle preview generation error"""
        self.preview_widget.set_content(f"<p style='color: red;'>Ошибка генерации просмотра: {error_message}</p>")
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)
        
        QMessageBox.warning(
            self,
            "Ошибка просмотра",
            f"Не удалось создать предварительный просмотр:\n{error_message}"
        )
    
    def print_document(self):
        """Print the document"""
        if not self.table_data:
            QMessageBox.information(self, "Нет данных", "Нет данных для печати")
            return
        
        config = self.get_print_configuration()
        
        try:
            if config.format == PrintFormat.PRINTER:
                self._print_to_printer(config)
            else:
                self._print_to_pdf(config)
            
            # Emit signal with configuration
            self.printRequested.emit(config.__dict__)
            
            # Close dialog on successful print
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка печати",
                f"Ошибка при печати документа:\n{str(e)}"
            )
    
    def _print_to_printer(self, config: PrintConfiguration):
        """Print to physical printer"""
        # Create printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        # Configure printer
        if config.orientation == PageOrientation.LANDSCAPE:
            printer.setPageOrientation(QPageSize.Orientation.Landscape)
        else:
            printer.setPageOrientation(QPageSize.Orientation.Portrait)
        
        # Set margins (convert mm to points: 1mm = 2.83465 points)
        margins = (
            config.left_margin_mm * 2.83465,
            config.top_margin_mm * 2.83465,
            config.right_margin_mm * 2.83465,
            config.bottom_margin_mm * 2.83465
        )
        printer.setPageMargins(*margins, QPrinter.Unit.Point)
        
        # Show print dialog
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            # Generate and print content
            success = self.print_service.print_to_printer(
                self.table_data, config, printer
            )
            
            if not success:
                raise Exception("Не удалось отправить документ на печать")
    
    def _print_to_pdf(self, config: PrintConfiguration):
        """Print to PDF file"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить как PDF",
            f"{self.table_name}.pdf",
            "PDF файлы (*.pdf)"
        )
        
        if file_path:
            success = self.print_service.print_to_pdf(
                self.table_data, config, file_path
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "PDF создан",
                    f"PDF файл успешно создан:\n{file_path}"
                )
            else:
                raise Exception("Не удалось создать PDF файл")
    
    def closeEvent(self, event):
        """Handle dialog close"""
        # Stop worker thread if running
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        super().closeEvent(event)


def create_table_part_print_dialog(table_data: List[Dict[str, Any]], 
                                  table_name: str = "Табличная часть",
                                  parent=None) -> TablePartPrintDialog:
    """
    Factory function to create a table part print dialog.
    
    Args:
        table_data: List of dictionaries representing table rows
        table_name: Name of the table for display
        parent: Parent widget
        
    Returns:
        Configured TablePartPrintDialog instance
    """
    return TablePartPrintDialog(table_data, table_name, parent)