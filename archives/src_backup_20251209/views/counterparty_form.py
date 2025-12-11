"""Counterparty form"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from ..data.database_manager import DatabaseManager


class CounterpartyForm(QWidget):
    def __init__(self, counterparty_id=0, is_group=False):
        super().__init__()
        self.counterparty_id = counterparty_id
        self.is_group = is_group
        self.db = DatabaseManager().get_connection()
        self.is_modified = False
        self.setup_ui()
        
        if self.counterparty_id > 0:
            self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        if self.counterparty_id == 0:
            title = "Новая группа контрагентов" if self.is_group else "Новый контрагент"
        else:
            title = "Редактирование группы контрагентов" if self.is_group else "Редактирование контрагента"
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        layout = QVBoxLayout()
        
        # Form
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Наименование*:", self.name_edit)
        
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
        
        self.inn_edit = QLineEdit()
        self.inn_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("ИНН:", self.inn_edit)
        
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Контактное лицо:", self.contact_person_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Телефон:", self.phone_edit)
        
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
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT name, inn, contact_person, phone, parent_id, is_group
            FROM counterparties
            WHERE id = ?
        """, (self.counterparty_id,))
        
        row = cursor.fetchone()
        if row:
            self.name_edit.setText(row['name'])
            self.inn_edit.setText(row['inn'] or "")
            self.contact_person_edit.setText(row['contact_person'] or "")
            self.phone_edit.setText(row['phone'] or "")
            self.is_group = bool(row['is_group'])
            
            # Load parent
            if row['parent_id']:
                self.load_parent(row['parent_id'])
            
            self.is_modified = False
    
    def load_parent(self, parent_id):
        """Load parent by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM counterparties WHERE id = ?", (parent_id,))
        row = cursor.fetchone()
        if row:
            self.parent_id = parent_id
            self.parent_edit.setText(row['name'])
    
    def on_select_parent(self):
        """Select parent"""
        from .reference_picker_dialog import ReferencePickerDialog
        dialog = ReferencePickerDialog("counterparties", "Выбор родительской группы", self, current_id=self.parent_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            
            # Check for circular reference
            if self.counterparty_id > 0 and selected_id == self.counterparty_id:
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
        
        cursor = self.db.cursor()
        
        try:
            if self.counterparty_id > 0:
                cursor.execute("""
                    UPDATE counterparties
                    SET name = ?, inn = ?, contact_person = ?, phone = ?, parent_id = ?, is_group = ?
                    WHERE id = ?
                """, (self.name_edit.text(), self.inn_edit.text(),
                      self.contact_person_edit.text(), self.phone_edit.text(),
                      self.parent_id, 1 if self.is_group else 0, self.counterparty_id))
            else:
                cursor.execute("""
                    INSERT INTO counterparties (name, inn, contact_person, phone, parent_id, is_group)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.name_edit.text(), self.inn_edit.text(),
                      self.contact_person_edit.text(), self.phone_edit.text(),
                      self.parent_id, 1 if self.is_group else 0))
                self.counterparty_id = cursor.lastrowid
            
            self.db.commit()
            self.is_modified = False
            title = "Редактирование группы контрагентов" if self.is_group else "Редактирование контрагента"
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
