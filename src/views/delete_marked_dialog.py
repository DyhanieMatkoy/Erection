"""Dialog for deleting marked objects"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                              QHeaderView, QCheckBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from src.data.database_manager import DatabaseManager
from src.services.user_settings_service import UserSettingsService


class DeleteMarkedDialog(QDialog):
    """Dialog for viewing and deleting marked objects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.settings_service = UserSettingsService()
        self.current_user_id = 4  # Use admin user as fallback (TODO: Get from auth service)
        self.setup_ui()
        self.load_settings()
        self.load_marked_objects()
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Удаление помеченных объектов")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Здесь отображаются все объекты, помеченные на удаление.\n"
            "Выберите объекты для окончательного удаления из базы данных."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Settings group
        settings_group = QGroupBox("Настройки отображения")
        settings_layout = QGridLayout()
        
        self.show_marked_checkbox = QCheckBox("Отображать помеченные на удаление объекты в списке")
        self.show_marked_checkbox.stateChanged.connect(self.on_show_marked_changed)
        settings_layout.addWidget(self.show_marked_checkbox, 0, 0, 1, 2)
        
        # Object type checkboxes
        self.type_checkboxes = {}
        types = [
            ('show_estimates', 'Сметы'),
            ('show_daily_reports', 'Ежедневные отчеты'),
            ('show_timesheets', 'Табели'),
            ('show_counterparties', 'Контрагенты'),
            ('show_objects', 'Объекты'),
            ('show_organizations', 'Организации'),
            ('show_persons', 'Физические лица'),
            ('show_works', 'Виды работ'),
        ]
        
        for i, (key, label) in enumerate(types):
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(self.on_type_filter_changed)
            self.type_checkboxes[key] = checkbox
            row = (i // 2) + 1
            col = i % 2
            settings_layout.addWidget(checkbox, row, col)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Select all checkbox
        self.select_all_checkbox = QCheckBox("Выбрать все")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_checkbox)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Тип", "Название"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Удалить выбранные")
        self.delete_button.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_button)
        
        self.unmark_button = QPushButton("Снять пометку")
        self.unmark_button.clicked.connect(self.unmark_selected)
        button_layout.addWidget(self.unmark_button)
        
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_marked_objects)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load user settings"""
        settings = self.settings_service.get_delete_marked_settings(self.current_user_id)
        
        self.show_marked_checkbox.setChecked(settings['show_marked_objects'])
        
        for key, checkbox in self.type_checkboxes.items():
            checkbox.setChecked(settings.get(key, True))
            checkbox.setEnabled(settings['show_marked_objects'])
    
    def save_settings(self):
        """Save user settings"""
        settings = {
            'show_marked_objects': self.show_marked_checkbox.isChecked()
        }
        
        for key, checkbox in self.type_checkboxes.items():
            settings[key] = checkbox.isChecked()
        
        self.settings_service.set_delete_marked_settings(self.current_user_id, settings)
    
    def on_show_marked_changed(self, state):
        """Handle show marked objects checkbox change"""
        enabled = state == Qt.CheckState.Checked.value
        
        for checkbox in self.type_checkboxes.values():
            checkbox.setEnabled(enabled)
        
        self.save_settings()
        self.load_marked_objects()
    
    def on_type_filter_changed(self):
        """Handle type filter checkbox change"""
        self.save_settings()
        self.load_marked_objects()
    
    def toggle_select_all(self, state):
        """Toggle selection of all items"""
        checked = state == Qt.CheckState.Checked.value
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)
    
    def load_marked_objects(self):
        """Load all marked objects from database"""
        self.table.setRowCount(0)
        self.select_all_checkbox.setChecked(False)
        
        # Check if we should show marked objects at all
        if not self.show_marked_checkbox.isChecked():
            self.update_button_states()
            return
        
        # Tables to check for marked objects with their setting keys
        tables_info = [
            ("estimates", "Смета", "number", "show_estimates"),
            ("daily_reports", "Ежедневный отчет", "number", "show_daily_reports"),
            ("timesheets", "Табель", "number", "show_timesheets"),
            ("counterparties", "Контрагент", "name", "show_counterparties"),
            ("objects", "Объект", "name", "show_objects"),
            ("organizations", "Организация", "name", "show_organizations"),
            ("persons", "Физическое лицо", "full_name", "show_persons"),
            ("works", "Вид работ", "name", "show_works"),
        ]
        
        marked_objects = []
        
        for table_name, type_name, name_field, setting_key in tables_info:
            # Check if this type should be shown
            if not self.type_checkboxes[setting_key].isChecked():
                continue
                
            try:
                query = f"""
                    SELECT id, {name_field}
                    FROM {table_name}
                    WHERE marked_for_deletion = 1
                """
                results = self.db_manager.execute_query(query)
                
                for row in results:
                    marked_objects.append({
                        'table': table_name,
                        'type': type_name,
                        'id': row[0],
                        'name': row[1] or ''
                    })
            except Exception as e:
                print(f"Error loading marked objects from {table_name}: {e}")
        
        # Populate table
        self.table.setRowCount(len(marked_objects))
        
        for row, obj in enumerate(marked_objects):
            # Checkbox
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)
            
            # Type
            type_item = QTableWidgetItem(obj['type'])
            self.table.setItem(row, 1, type_item)
            
            # Name
            name_item = QTableWidgetItem(obj['name'])
            self.table.setItem(row, 2, name_item)
            
            # Store object data
            type_item.setData(Qt.ItemDataRole.UserRole, obj)
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Update button enabled states"""
        has_items = self.table.rowCount() > 0
        self.delete_button.setEnabled(has_items)
        self.unmark_button.setEnabled(has_items)
        self.select_all_checkbox.setEnabled(has_items)
    
    def get_selected_objects(self):
        """Get list of selected objects"""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    type_item = self.table.item(row, 1)
                    obj_data = type_item.data(Qt.ItemDataRole.UserRole)
                    selected.append(obj_data)
        return selected
    
    def delete_selected(self):
        """Delete selected marked objects"""
        selected = self.get_selected_objects()
        
        if not selected:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не выбрано ни одного объекта для удаления."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите окончательно удалить {len(selected)} объект(ов)?\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete objects
        deleted_count = 0
        errors = []
        
        for obj in selected:
            try:
                query = f"DELETE FROM {obj['table']} WHERE id = ?"
                self.db_manager.execute_update(query, (obj['id'],))
                deleted_count += 1
            except Exception as e:
                errors.append(f"{obj['type']} '{obj['name']}': {str(e)}")
        
        # Show result
        if errors:
            error_msg = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f"\n... и еще {len(errors) - 5} ошибок"
            
            QMessageBox.warning(
                self,
                "Ошибки при удалении",
                f"Удалено объектов: {deleted_count}\n"
                f"Ошибок: {len(errors)}\n\n"
                f"Первые ошибки:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Успешно",
                f"Успешно удалено объектов: {deleted_count}"
            )
        
        # Reload table
        self.load_marked_objects()
    
    def unmark_selected(self):
        """Unmark selected objects (remove deletion mark)"""
        selected = self.get_selected_objects()
        
        if not selected:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не выбрано ни одного объекта."
            )
            return
        
        # Confirm unmarking
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Снять пометку на удаление с {len(selected)} объект(ов)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Unmark objects
        unmarked_count = 0
        errors = []
        
        for obj in selected:
            try:
                query = f"""
                    UPDATE {obj['table']} 
                    SET marked_for_deletion = 0
                    WHERE id = ?
                """
                self.db_manager.execute_update(query, (obj['id'],))
                unmarked_count += 1
            except Exception as e:
                errors.append(f"{obj['type']} '{obj['name']}': {str(e)}")
        
        # Show result
        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... и еще {len(errors) - 5} ошибок"
            
            QMessageBox.warning(
                self,
                "Ошибки",
                f"Снято пометок: {unmarked_count}\n"
                f"Ошибок: {len(errors)}\n\n"
                f"Первые ошибки:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Успешно",
                f"Успешно снято пометок: {unmarked_count}"
            )
        
        # Reload table
        self.load_marked_objects()


# Import QWidget for checkbox container
from PyQt6.QtWidgets import QWidget
