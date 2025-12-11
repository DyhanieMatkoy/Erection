"""Work form"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QMessageBox, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository



class WorkForm(QWidget):
    def __init__(self, work_id=0, is_group=False):
        super().__init__()
        self.work_id = work_id
        self.is_group = is_group
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.get_connection()  # Add self.db for compatibility
        self.work_repo = WorkRepository(self.db_manager)
        self.is_modified = False
        self.setup_ui()
        
        if self.work_id > 0:
            self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        if self.work_id == 0:
            title = "Новая группа работ" if self.is_group else "Новый вид работ"
        else:
            title = "Редактирование группы работ" if self.is_group else "Редактирование вида работ"
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        layout = QVBoxLayout()
        
        # Form
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Наименование*:", self.name_edit)
        
        self.code_edit = QLineEdit()
        self.code_edit.setMaxLength(12)
        self.code_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Код:", self.code_edit)
        
        # Parent group
        parent_layout = QHBoxLayout()
        self.parent_edit = QLineEdit()
        self.parent_edit.setReadOnly(True)
        self.parent_id = None
        parent_layout.addWidget(self.parent_edit)
        self.parent_button = QPushButton("...")
        self.parent_button.setMaximumWidth(30)
        self.parent_button.clicked.connect(self.on_select_parent)
        parent_layout.addWidget(self.parent_button)
        self.clear_parent_button = QPushButton("✕")
        self.clear_parent_button.setMaximumWidth(30)
        self.clear_parent_button.clicked.connect(self.on_clear_parent)
        parent_layout.addWidget(self.clear_parent_button)
        form_layout.addRow("Родитель:", parent_layout)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Единица измерения:", self.unit_edit)
        
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setMaximum(999999999.99)
        self.price_spinbox.setDecimals(2)
        self.price_spinbox.valueChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Цена:", self.price_spinbox)
        
        self.labor_rate_spinbox = QDoubleSpinBox()
        self.labor_rate_spinbox.setMaximum(999999.99)
        self.labor_rate_spinbox.setDecimals(2)
        self.labor_rate_spinbox.valueChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Норма трудозатрат:", self.labor_rate_spinbox)
        
        
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить (Ctrl+S)")
        self.save_button.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_button)
        
        self.save_close_button = QPushButton("Сохранить и закрыть (Ctrl+Shift+S)")
        self.save_close_button.clicked.connect(self.on_save_and_close)
        self.save_close_button.setDefault(True)  # Set as default button
        button_layout.addWidget(self.save_close_button)
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.name_edit.setFocus()
    
    def load_data(self):
        """Load data from database"""
        work_data = self.work_repo.find_by_id(self.work_id)
        if work_data:
            self.name_edit.setText(work_data['name'])
            self.code_edit.setText(work_data['code'] or "")
            self.unit_edit.setText(work_data['unit'] or "")
            self.price_spinbox.setValue(work_data['price'] or 0.0)
            self.labor_rate_spinbox.setValue(work_data['labor_rate'] or 0.0)
            self.is_group = work_data['is_group']
            
            # Load parent
            if work_data['parent_id']:
                self.load_parent(work_data['parent_id'])
            
            
            
            self.is_modified = False
    
    def load_parent(self, parent_id):
        """Load parent by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM works WHERE id = ?", (parent_id,))
        row = cursor.fetchone()
        if row:
            self.parent_id = parent_id
            self.parent_edit.setText(row['name'])
    
    def on_select_parent(self):
        """Select parent"""
        from .reference_picker_dialog import ReferencePickerDialog
        dialog = ReferencePickerDialog("works", "Выбор родительской группы", self, current_id=self.parent_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            
            # Check for circular reference
            if self.work_id > 0 and selected_id == self.work_id:
                QMessageBox.warning(self, "Ошибка", "Нельзя выбрать элемент в качестве родителя самого себя")
                return
            
            self.parent_id = selected_id
            self.parent_edit.setText(selected_name)
            self.is_modified = True
    
    def on_clear_parent(self):
        """Clear parent"""
        self.parent_id = None
        self.parent_edit.setText("")
        self.is_modified = True
    
    def save_data(self):
        """Save data to database"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование обязательно для заполнения")
            self.name_edit.setFocus()
            return False
        
        try:
            from ..data.models.sqlalchemy_models import Work
            
            
            
            if self.work_id > 0:
                # Update existing work
                work_data = self.work_repo.find_by_id(self.work_id)
                if work_data:
                    work = Work()
                    work.id = self.work_id
                    work.name = self.name_edit.text()
                    work.code = self.code_edit.text()
                    work.unit = self.unit_edit.text()
                    work.price = self.price_spinbox.value()
                    work.labor_rate = self.labor_rate_spinbox.value()
                    work.parent_id = self.parent_id
                    work.is_group = self.is_group
                    work.marked_for_deletion = work_data['marked_for_deletion']
                    
                    if not self.work_repo.update(work):
                        raise Exception("Failed to update work")
            else:
                # Create new work
                work = Work()
                work.name = self.name_edit.text()
                work.code = self.code_edit.text()
                work.unit = self.unit_edit.text()
                work.price = self.price_spinbox.value()
                work.labor_rate = self.labor_rate_spinbox.value()
                work.parent_id = self.parent_id
                work.is_group = self.is_group
                
                work_id = self.work_repo.save(work)
                if not work_id:
                    raise Exception("Failed to save work")
                self.work_id = work_id
            
            self.is_modified = False
            title = "Редактирование группы работ" if self.is_group else "Редактирование вида работ"
            self.setWindowTitle(title)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")
            return False
    
    def on_save(self):
        """Handle save button"""
        self.save_data()
    
    def on_save_and_close(self):
        """Handle save and close button"""
        if self.save_data():
            self.close()
    
    def on_close(self):
        """Handle close button"""
        self.close()
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Несохраненные изменения",
                "Документ был изменен. Сохранить изменения?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.save_data():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.matches(QKeySequence.StandardKey.Save):
            self.on_save()
        elif event.key() == Qt.Key.Key_S and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Enter - trigger default button
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Escape:
            self.on_close()
        else:
            super().keyPressEvent(event)
