"""Employee picker dialog with brigade filter"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QHeaderView, QPushButton, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from ..data.database_manager import DatabaseManager
from ..data.models.sqlalchemy_models import Person, UserSetting


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
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
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
        
        # Ensure session is closed
        self.finished.connect(lambda: self.session.close())
    
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
        """Load employees based on filter setting"""
        try:
            query = self.session.query(Person).filter(Person.marked_for_deletion == False)
            
            if not self.show_all and self.foreman_id:
                # Show only brigade members (parent_id = foreman_id) OR those with no parent (parent_id IS NULL)
                from sqlalchemy import or_
                query = query.filter(or_(Person.parent_id == self.foreman_id, Person.parent_id == None))
            
            persons = query.order_by(Person.full_name).all()
            
            self.table.setRowCount(len(persons))
            
            for row_idx, person in enumerate(persons):
                # Column 0: Name
                self.table.setItem(row_idx, 0, QTableWidgetItem(person.full_name or ""))
                
                # Column 1: Position
                self.table.setItem(row_idx, 1, QTableWidgetItem(person.position or ""))
                
                # Column 2: Rate
                rate = person.hourly_rate if person.hourly_rate else 0.0
                self.table.setItem(row_idx, 2, QTableWidgetItem(f"{rate:.2f}"))
                
                # Column 3: ID (hidden)
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(person.id)))
            
            # Select first row if available
            if self.table.rowCount() > 0:
                self.table.selectRow(0)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сотрудников: {e}")
    
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
        """Get selected employee as tuple (id, name, rate)"""
        return self.selected_id, self.selected_name, self.selected_rate
    
    def _load_filter_preference(self):
        """Load filter preference from user settings"""
        # For simplicity, let's use a fixed user ID (e.g., 1) or assume global settings if user_id is not available easily.
        # Ideally, we should pass user_id to the dialog or use AuthService.
        # But UserSetting has (user_id, form_name, setting_key) as PK.
        # Let's try to get current user from AuthService if possible, or fallback to admin user.
        
        user_id = 4  # Use admin user as fallback
        # TODO: integrate auth service properly
        
        setting = self.session.query(UserSetting).filter_by(
            user_id=user_id,
            form_name='EmployeePickerDialog',
            setting_key='show_all'
        ).first()
        
        if setting:
            return setting.setting_value == '1'
        
        return False
    
    def _save_filter_preference(self, show_all):
        """Save filter preference to user settings"""
        user_id = 1
        
        try:
            setting = self.session.query(UserSetting).filter_by(
                user_id=user_id,
                form_name='EmployeePickerDialog',
                setting_key='show_all'
            ).first()
            
            if not setting:
                setting = UserSetting(
                    user_id=user_id,
                    form_name='EmployeePickerDialog',
                    setting_key='show_all'
                )
                self.session.add(setting)
            
            setting.setting_value = '1' if show_all else '0'
            self.session.commit()
        except Exception:
            self.session.rollback()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_select()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
