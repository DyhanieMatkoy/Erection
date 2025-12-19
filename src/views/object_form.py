"""Object form"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from .reference_picker_dialog import ReferencePickerDialog
from ..data.database_manager import DatabaseManager


class ObjectForm(QWidget):
    def __init__(self, object_id=0, is_group=False, parent_id=None):
        super().__init__()
        self.object_id = object_id
        self.is_group = is_group
        self.db = DatabaseManager().get_connection()
        self.is_modified = False
        self.owner_id = 0
        self.parent_id = parent_id # Initial parent_id
        self.setup_ui()
        
        if self.object_id > 0:
            self.load_data()
        elif self.parent_id:
             self.load_parent(self.parent_id)
    
    def setup_ui(self):
        """Setup UI"""
        if self.object_id == 0:
            title = "Новая группа объектов" if self.is_group else "Новый объект"
        else:
            title = "Редактирование группы объектов" if self.is_group else "Редактирование объекта"
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
        # self.parent_id = None # Do not overwrite initialized value
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
        
        # Owner (FK Counterparty)
        owner_layout = QHBoxLayout()
        self.owner_edit = QLineEdit()
        self.owner_edit.setReadOnly(True)
        owner_layout.addWidget(self.owner_edit)
        
        self.owner_button = QPushButton("...")
        self.owner_button.setMaximumWidth(30)
        self.owner_button.clicked.connect(self.on_select_owner)
        owner_layout.addWidget(self.owner_button)
        
        form_layout.addRow("Владелец:", owner_layout)
        
        self.address_edit = QLineEdit()
        self.address_edit.textChanged.connect(lambda: setattr(self, 'is_modified', True))
        form_layout.addRow("Адрес:", self.address_edit)
        
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
            SELECT o.name, o.owner_id, c.name as owner_name, o.address, o.parent_id, o.is_group
            FROM objects o
            LEFT JOIN counterparties c ON o.owner_id = c.id
            WHERE o.id = ?
        """, (self.object_id,))
        
        row = cursor.fetchone()
        if row:
            self.name_edit.setText(row['name'])
            self.owner_id = row['owner_id'] or 0
            self.owner_edit.setText(row['owner_name'] or "")
            self.address_edit.setText(row['address'] or "")
            self.is_group = bool(row['is_group'])
            
            # Load parent
            if row['parent_id']:
                self.load_parent(row['parent_id'])
            
            self.is_modified = False
    
    def load_parent(self, parent_id):
        """Load parent by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM objects WHERE id = ?", (parent_id,))
        row = cursor.fetchone()
        if row:
            self.parent_id = parent_id
            self.parent_edit.setText(row['name'])
    
    def on_select_parent(self):
        """Select parent"""
        dialog = ReferencePickerDialog("objects", "Выбор родительской группы", self, current_id=self.parent_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            
            # Check for circular reference
            if self.object_id > 0 and selected_id == self.object_id:
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
    
    def on_select_owner(self):
        """Handle select owner button"""
        dialog = ReferencePickerDialog("counterparties", "name", self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.owner_id = dialog.selected_id()
            self.owner_edit.setText(dialog.selected_value())
            self.is_modified = True
    
    def save_data(self):
        """Save data to database"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование обязательно для заполнения")
            self.name_edit.setFocus()
            return False
        
        cursor = self.db.cursor()
        
        try:
            if self.object_id > 0:
                cursor.execute("""
                    UPDATE objects
                    SET name = ?, owner_id = ?, address = ?, parent_id = ?, is_group = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (self.name_edit.text(),
                      self.owner_id if self.owner_id > 0 else None,
                      self.address_edit.text(),
                      self.parent_id,
                      1 if self.is_group else 0,
                      self.object_id))
            else:
                import uuid
                new_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO objects (name, owner_id, address, parent_id, is_group, uuid, updated_at, is_deleted)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
                """, (self.name_edit.text(),
                      self.owner_id if self.owner_id > 0 else None,
                      self.address_edit.text(),
                      self.parent_id,
                      1 if self.is_group else 0,
                      new_uuid))
                self.object_id = cursor.lastrowid
            
            self.db.commit()
            self.is_modified = False
            title = "Редактирование группы объектов" if self.is_group else "Редактирование объекта"
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
