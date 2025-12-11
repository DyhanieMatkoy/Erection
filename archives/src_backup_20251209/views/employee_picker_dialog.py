"""Employee picker dialog with brigade filter"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QHeaderView, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt
from ..data.database_manager import DatabaseManager


class EmployeePickerDialog(QDialog):
    """Dialog for selecting employees with brigade filter
    
    Allows foreman to filter employees by brigade membership or show all employees.
    The filter preference is saved to user settings.
    """
    
    def __init__(self, parent=None, foreman_id=None, show_all=None):
        """Initialize employee picker dialog
        
        Args:
            parent: Parent widget
            foreman_id: ID of the foreman (person_id) for brigade filtering
            show_all: Override for show all setting (None = load from settings)
        """
        super().__init__(parent)
        self.db = DatabaseManager().get_connection()
        self.foreman_id = foreman_id
        self.selected_id = None
        self.selected_name = None
        self.selected_rate = 0.0
        
        # Load show_all preference from settings if not provided
        if show_all is None:
            self.show_all = self._load_filter_preference()
        else:
            self.show_all = show_all
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI with table, filter checkbox, and buttons"""
        self.setWindowTitle("Выбор сотрудника")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Filter checkbox
        self.show_all_checkbox = QCheckBox("Показать всех сотрудников")
        self.show_all_checkbox.setChecked(self.show_all)
        self.show_all_checkbox.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.show_all_checkbox)
        
        # Table with columns: Name, Position, Rate
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Должность", "Ставка", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(3, True)  # Hide ID column
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons: OK and Cancel
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.on_select)
        self.select_button.setDefault(True)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def on_filter_changed(self):
        """Handle filter checkbox change"""
        self.show_all = self.show_all_checkbox.isChecked()
        self._save_filter_preference(self.show_all)
        self.load_data()
    
    def load_data(self):
        """Load employees based on filter setting
        
        If show_all is False and foreman_id is set:
            - Show employees where parent_id = foreman_id (brigade members)
            - Show employees where parent_id IS NULL (employees without supervisor)
        
        If show_all is True or foreman_id is not set:
            - Show all employees
        """
        cursor = self.db.cursor()
        
        if self.show_all or not self.foreman_id:
            # Show all employees
            cursor.execute("""
                SELECT id, full_name, position, hourly_rate
                FROM persons
                WHERE marked_for_deletion = 0
                ORDER BY full_name
            """)
        else:
            # Show only brigade members (where foreman is supervisor) or employees without supervisor
            cursor.execute("""
                SELECT id, full_name, position, hourly_rate
                FROM persons
                WHERE marked_for_deletion = 0
                  AND (parent_id = ? OR parent_id IS NULL)
                ORDER BY full_name
            """, (self.foreman_id,))
        
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            # Column 0: Name
            self.table.setItem(row_idx, 0, QTableWidgetItem(row['full_name'] or ""))
            
            # Column 1: Position
            self.table.setItem(row_idx, 1, QTableWidgetItem(row['position'] or ""))
            
            # Column 2: Rate
            rate = row['hourly_rate'] if row['hourly_rate'] else 0.0
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{rate:.2f}"))
            
            # Column 3: ID (hidden)
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row['id'])))
        
        # Select first row if available
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
    
    def on_row_double_clicked(self, index):
        """Handle row double click - select employee"""
        self.on_select()
    
    def on_select(self):
        """Handle select button - get selected employee and close dialog"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            id_item = self.table.item(current_row, 3)
            name_item = self.table.item(current_row, 0)
            rate_item = self.table.item(current_row, 2)
            
            if id_item and name_item:
                self.selected_id = int(id_item.text())
                self.selected_name = name_item.text()
                
                if rate_item:
                    try:
                        self.selected_rate = float(rate_item.text())
                    except ValueError:
                        self.selected_rate = 0.0
                
                self.accept()
    
    def get_selected(self):
        """Get selected employee as tuple (id, name, rate)
        
        Returns:
            Tuple of (employee_id, employee_name, hourly_rate)
        """
        return self.selected_id, self.selected_name, self.selected_rate
    
    def _load_filter_preference(self):
        """Load filter preference from user settings
        
        Returns:
            bool: True if show all employees, False if show only brigade
        """
        cursor = self.db.cursor()
        
        # Check if settings table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_settings'
        """)
        
        if not cursor.fetchone():
            # Settings table doesn't exist, return default (False = show only brigade)
            return False
        
        # Load setting
        cursor.execute("""
            SELECT setting_value FROM user_settings
            WHERE setting_key = 'employee_picker_show_all'
        """)
        
        row = cursor.fetchone()
        if row:
            return row['setting_value'] == '1' or row['setting_value'].lower() == 'true'
        
        # Default: show only brigade
        return False
    
    def _save_filter_preference(self, show_all):
        """Save filter preference to user settings
        
        Args:
            show_all: True if show all employees, False if show only brigade
        """
        cursor = self.db.cursor()
        
        # Ensure settings table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT
            )
        """)
        
        # Save or update setting
        setting_value = '1' if show_all else '0'
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings (setting_key, setting_value)
            VALUES ('employee_picker_show_all', ?)
        """, (setting_value,))
        
        self.db.commit()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_select()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
