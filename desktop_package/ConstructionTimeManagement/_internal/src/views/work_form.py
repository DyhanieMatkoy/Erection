
"""Work form"""
from typing import List, Tuple, Optional
import configparser
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QMessageBox, QDoubleSpinBox, 
                             QTabWidget, QLabel, QDialog, QCheckBox, QFileDialog, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository
from ..data.repositories.cost_item_repository import CostItemRepository
from ..data.repositories.material_repository import MaterialRepository
from ..data.repositories.cost_item_material_repository import CostItemMaterialRepository
from ..data.repositories.work_specification_repository import WorkSpecificationRepository
from ..data.repositories.unit_repository import UnitRepository
from ..data.models.sqlalchemy_models import Work, CostItem, Material
from ..services.work_specification_excel_service import WorkSpecificationExcelService

from .widgets.cost_items_table import CostItemsTable
from .widgets.materials_table import MaterialsTable
from .widgets.work_specification_widget import WorkSpecificationWidget
from .dialogs.cost_item_selector_dialog import CostItemSelectorDialog
from .dialogs.material_add_dialog import MaterialAddDialog
from .dialogs.specification_entry_dialog import SpecificationEntryDialog
from .reference_picker_dialog import ReferencePickerDialog
from .cost_item_form import CostItemForm

class WorkForm(QWidget):
    def __init__(self, work_id=0, is_group=False, parent_id=None):
        super().__init__()
        self.work_id = work_id
        self.is_group = is_group
        self.parent_id = parent_id
        
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.get_connection()
        
        # Repositories
        self.work_repo = WorkRepository(self.db_manager)
        self.cost_item_repo = CostItemRepository()
        self.material_repo = MaterialRepository()
        self.cim_repo = CostItemMaterialRepository()
        self.spec_repo = WorkSpecificationRepository(self.db_manager)
        self.unit_repo = UnitRepository(self.db_manager)
        self.excel_service = WorkSpecificationExcelService()
        
        # Feature Flag
        self.use_simplified_specifications = False
        try:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(__file__), '../../env.ini')
            if os.path.exists(config_path):
                config.read(config_path)
                if 'Features' in config and 'use_simplified_specifications' in config['Features']:
                    self.use_simplified_specifications = config['Features'].getboolean('use_simplified_specifications')
        except Exception as e:
            print(f"Error reading config: {e}")

        # Data
        self.cost_items: List[Tuple[CostItem, float]] = []
        self.materials: List[Tuple[Material, float, CostItem]] = []
        self.specifications: List[dict] = []
        
        self.is_modified = False
        
        self.setup_ui()
        
        if self.work_id > 0:
            self.load_data()
        elif self.parent_id:
            self.load_parent(self.parent_id)

    def setup_ui(self):
        if self.work_id == 0:
            title = "Новая группа работ" if self.is_group else "Новый вид работ"
        else:
            title = "Редактирование группы работ" if self.is_group else "Редактирование вида работ"
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        layout = QVBoxLayout()
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        
        self.tab_widget.addTab(self.setup_basic_info_tab(), "Основные данные")
        
        if self.use_simplified_specifications:
            self.tab_widget.addTab(self.setup_specifications_tab(), "Спецификация")
        else:
            self.tab_widget.addTab(self.setup_cost_items_tab(), "Статьи затрат")
            self.tab_widget.addTab(self.setup_materials_tab(), "Материалы")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить (Ctrl+S)")
        self.save_button.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_button)
        
        self.save_close_button = QPushButton("Сохранить и закрыть (Ctrl+Shift+S)")
        self.save_close_button.clicked.connect(self.on_save_and_close)
        self.save_close_button.setDefault(True)
        button_layout.addWidget(self.save_close_button)
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.name_edit.setFocus()

    def setup_basic_info_tab(self):
        tab = QWidget()
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
        # self.parent_id = None
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
        
        # Unit
        unit_layout = QHBoxLayout()
        self.unit_edit = QLineEdit()
        self.unit_edit.setReadOnly(True)
        self.unit_id = None
        unit_layout.addWidget(self.unit_edit)
        self.unit_button = QPushButton("...")
        self.unit_button.setMaximumWidth(30)
        self.unit_button.clicked.connect(self.on_select_unit)
        unit_layout.addWidget(self.unit_button)
        self.clear_unit_button = QPushButton("✕")
        self.clear_unit_button.setMaximumWidth(30)
        self.clear_unit_button.clicked.connect(self.on_clear_unit)
        unit_layout.addWidget(self.clear_unit_button)
        form_layout.addRow("Единица измерения:", unit_layout)
        
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
        
        # Is Group checkbox
        self.is_group_checkbox = QCheckBox("Это группа работ")
        self.is_group_checkbox.stateChanged.connect(lambda: setattr(self, 'is_modified', True))
        self.is_group_checkbox.stateChanged.connect(self.on_is_group_changed)
        form_layout.addRow("", self.is_group_checkbox)
        
        # Restore Groups button
        restore_groups_layout = QHBoxLayout()
        self.restore_groups_button = QPushButton("Восстановить группы")
        self.restore_groups_button.setToolTip("Пометить как группы все работы, которые указаны в качестве родителей")
        self.restore_groups_button.clicked.connect(self.on_restore_groups)
        restore_groups_layout.addWidget(self.restore_groups_button)
        restore_groups_layout.addStretch()
        form_layout.addRow("", restore_groups_layout)
        
        tab.setLayout(form_layout)
        return tab

    def setup_cost_items_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.cost_items_table = CostItemsTable()
        self.cost_items_table.quantityChanged.connect(self.on_cost_item_quantity_changed)
        self.cost_items_table.addCostItemRequested.connect(self.on_add_cost_item)
        self.cost_items_table.createNewCostItemRequested.connect(self.on_create_new_cost_item)
        self.cost_items_table.deleteCostItemRequested.connect(self.on_remove_cost_item)
        layout.addWidget(self.cost_items_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить статью затрат")
        add_btn.clicked.connect(self.on_add_cost_item)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(self.on_remove_cost_item)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab

    def setup_materials_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.materials_table = MaterialsTable()
        self.materials_table.quantityChanged.connect(self.on_material_quantity_changed)
        self.materials_table.addMaterialRequested.connect(self.on_add_material)
        self.materials_table.deleteMaterialRequested.connect(self.on_remove_material)
        layout.addWidget(self.materials_table)
        
        self.total_cost_label = QLabel("Общая стоимость: 0.00 руб.")
        self.total_cost_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        font = self.total_cost_label.font()
        font.setBold(True)
        self.total_cost_label.setFont(font)
        layout.addWidget(self.total_cost_label)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить материал")
        add_btn.clicked.connect(self.on_add_material)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(self.on_remove_material)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab

    def setup_specifications_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.spec_widget = WorkSpecificationWidget()
        self.spec_widget.addRequested.connect(self.on_add_spec)
        self.spec_widget.editRequested.connect(self.on_edit_spec)
        self.spec_widget.deleteRequested.connect(self.on_delete_spec)
        self.spec_widget.copyRequested.connect(self.on_copy_spec)
        self.spec_widget.importRequested.connect(self.on_import_spec)
        self.spec_widget.exportRequested.connect(self.on_export_spec)
        self.spec_widget.saveTemplateRequested.connect(self.on_save_template)
        self.spec_widget.entryChanged.connect(self.on_spec_entry_changed)
        
        layout.addWidget(self.spec_widget)
        
        self.spec_total_label = QLabel("Общая стоимость: 0.00 руб.")
        self.spec_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        font = self.spec_total_label.font()
        font.setBold(True)
        self.spec_total_label.setFont(font)
        layout.addWidget(self.spec_total_label)
        
        tab.setLayout(layout)
        return tab

    def on_add_spec(self):
        units = self.unit_repo.find_all()
        dialog = SpecificationEntryDialog(self, units=units)
        if dialog.exec():
            data = dialog.get_data()
            # Temporary ID for new items (can be negative or just None/0, but we need to track them)
            # We'll use negative index or just None.
            # But the table uses ID to identify rows.
            # If ID is None, we can't select it easily by ID.
            # Let's generate a temp ID.
            temp_id = -len(self.specifications) - 1
            data['id'] = temp_id
            data['work_id'] = self.work_id
            
            self.specifications.append(data)
            self.spec_widget.load_data(self.specifications)
            self.calculate_spec_total()
            self.is_modified = True

    def on_edit_spec(self, spec_id):
        # Find spec in list
        spec = next((s for s in self.specifications if s.get('id') == spec_id), None)
        if not spec:
            return
            
        units = self.unit_repo.find_all()
        dialog = SpecificationEntryDialog(self, units=units, data=spec)
        if dialog.exec():
            data = dialog.get_data()
            # Update spec
            spec.update(data)
            # Recalculate total cost
            spec['total_cost'] = float(spec['consumption_rate']) * float(spec['unit_price'])
            
            self.spec_widget.load_data(self.specifications)
            self.calculate_spec_total()
            self.is_modified = True

    def on_delete_spec(self, spec_id):
        if QMessageBox.question(self, "Подтверждение", "Удалить компонент?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            # Filter out
            self.specifications = [s for s in self.specifications if s.get('id') != spec_id]
            self.spec_widget.load_data(self.specifications)
            self.calculate_spec_total()
            self.is_modified = True

    def on_spec_entry_changed(self, row, column_name, new_value):
        """Handle inline edits from the table"""
        if row >= 0 and row < len(self.specifications):
            spec = self.specifications[row]
            spec[column_name] = new_value
            
            # Recalculate total for this item
            rate = float(spec.get('consumption_rate', 0))
            price = float(spec.get('unit_price', 0))
            spec['total_cost'] = rate * price
            
            self.calculate_spec_total()
            self.is_modified = True

    def on_copy_spec(self):
        # Show work picker
        dialog = ReferencePickerDialog("works", "Выберите работу для копирования спецификации", self)
        if dialog.exec():
            source_id, _ = dialog.get_selected()
            if source_id == self.work_id:
                QMessageBox.warning(self, "Ошибка", "Нельзя копировать из текущей работы")
                return
                
            # Fetch specs from source
            source_specs = self.spec_repo.get_by_work_id(source_id)
            if not source_specs:
                QMessageBox.information(self, "Информация", "У выбранной работы нет спецификации")
                return
                
            # Add to current specs
            for spec in source_specs:
                new_spec = spec.copy()
                # Remove ID so it's treated as new
                temp_id = -len(self.specifications) - 1
                new_spec['id'] = temp_id
                new_spec['work_id'] = self.work_id
                self.specifications.append(new_spec)
                
            self.spec_widget.load_data(self.specifications)
            self.calculate_spec_total()
            self.is_modified = True

    def on_import_spec(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Импорт спецификации", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        if not file_path:
            return
            
        specs, error = self.excel_service.import_specifications(file_path)
        if error:
            QMessageBox.critical(self, "Ошибка импорта", f"Не удалось импортировать файл: {error}")
            return
            
        if not specs:
            QMessageBox.information(self, "Импорт", "Файл не содержит данных для импорта")
            return
            
        # Add imported specs
        # We need to resolve units if possible
        # We have unit name from excel. We check against DB units.
        units = self.unit_repo.find_all()
        # Create map name -> id
        unit_map = {u.name.lower(): u.id for u in units} if hasattr(units[0], 'name') else {u['name'].lower(): u['id'] for u in units}
        
        count = 0
        for spec in specs:
            new_spec = spec.copy()
            # Resolve unit
            unit_name = new_spec.get('unit_name', '').lower()
            if unit_name in unit_map:
                new_spec['unit_id'] = unit_map[unit_name]
            
            temp_id = -len(self.specifications) - 1
            new_spec['id'] = temp_id
            new_spec['work_id'] = self.work_id
            
            # Calc total if missing
            rate = float(new_spec.get('consumption_rate', 0))
            price = float(new_spec.get('unit_price', 0))
            new_spec['total_cost'] = rate * price
            
            self.specifications.append(new_spec)
            count += 1
            
        self.spec_widget.load_data(self.specifications)
        self.calculate_spec_total()
        self.is_modified = True
        QMessageBox.information(self, "Импорт", f"Импортировано записей: {count}")

    def on_export_spec(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт спецификации", f"spec_{self.work_id}.xlsx", "Excel Files (*.xlsx);;All Files (*)"
        )
        if not file_path:
            return
            
        # Enrich specs with unit names if missing
        export_specs = []
        # Get units map
        units = self.unit_repo.find_all()
        unit_map = {u.id: u.name for u in units} if hasattr(units[0], 'id') else {u['id']: u['name'] for u in units}
        
        for spec in self.specifications:
            s = spec.copy()
            if 'unit_name' not in s and s.get('unit_id'):
                s['unit_name'] = unit_map.get(s['unit_id'], '')
            export_specs.append(s)
            
        if self.excel_service.export_specifications(export_specs, file_path):
            QMessageBox.information(self, "Экспорт", "Экспорт выполнен успешно")
        else:
            QMessageBox.critical(self, "Ошибка экспорта", "Не удалось сохранить файл")

    def on_save_template(self):
        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Введите название шаблона:")
        if not ok or not name.strip():
            return
            
        template_name = name.strip()
        
        # Find or create Templates group
        group_name = "Шаблоны спецификаций"
        templates_group = self.work_repo.find_by_name(group_name)
        
        if not templates_group:
            # Create group
            group = Work()
            group.name = group_name
            group.is_group = True
            group.parent_id = None
            group_id = self.work_repo.save(group)
            if not group_id:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать группу шаблонов")
                return
        else:
            group_id = templates_group['id']
            
        # Check if template exists
        existing = self.work_repo.find_by_name(template_name, parent_id=group_id)
        if existing:
            if QMessageBox.question(self, "Подтверждение", 
                                  f"Шаблон '{template_name}' уже существует. Перезаписать?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            
            template_id = existing['id']
            
            # Delete existing specs
            existing_specs = self.spec_repo.get_by_work_id(template_id)
            for s in existing_specs:
                self.spec_repo.delete(s['id'])
                
        else:
            # Create new work
            template = Work()
            template.name = template_name
            template.parent_id = group_id
            template.is_group = False
            template.unit_id = self.unit_id
            
            template_id = self.work_repo.save(template)
            if not template_id:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать шаблон")
                return
                
        # Copy specifications
        count = 0
        for spec in self.specifications:
            new_spec = spec.copy()
            new_spec['work_id'] = template_id
            # Remove ID to create new
            if 'id' in new_spec:
                del new_spec['id']
            # Ensure required fields
            if 'component_type' not in new_spec: new_spec['component_type'] = 'Material'
            if 'component_name' not in new_spec: new_spec['component_name'] = 'Unknown'
            if 'consumption_rate' not in new_spec: new_spec['consumption_rate'] = 0
            if 'unit_price' not in new_spec: new_spec['unit_price'] = 0
                
            self.spec_repo.create(new_spec)
            count += 1
            
        QMessageBox.information(self, "Успех", f"Шаблон сохранен ({count} позиций)")

    def calculate_spec_total(self):
        total = sum(float(s.get('consumption_rate', 0)) * float(s.get('unit_price', 0)) for s in self.specifications)
        self.spec_total_label.setText(f"Общая стоимость: {total:,.2f} руб.")

    def load_parent(self, parent_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM works WHERE id = ?", (parent_id,))
        row = cursor.fetchone()
        if row:
            self.parent_id = parent_id
            self.parent_edit.setText(row['name'])

    def on_select_parent(self):
        dialog = ReferencePickerDialog("works", "Выбор родительской группы", self, current_id=self.parent_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            if self.work_id > 0 and selected_id == self.work_id:
                QMessageBox.warning(self, "Ошибка", "Нельзя выбрать элемент в качестве родителя самого себя")
                return
            self.parent_id = selected_id
            self.parent_edit.setText(selected_name)
            self.is_modified = True

    def on_clear_parent(self):
        self.parent_id = None
        self.parent_edit.setText("")
        self.is_modified = True

    def load_unit(self, unit_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM units WHERE id = ?", (unit_id,))
        row = cursor.fetchone()
        if row:
            self.unit_id = unit_id
            self.unit_edit.setText(row['name'])

    def on_select_unit(self):
        dialog = ReferencePickerDialog("units", "Выбор единицы измерения", self, current_id=self.unit_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.unit_id = selected_id
            self.unit_edit.setText(selected_name)
            self.is_modified = True

    def on_clear_unit(self):
        self.unit_id = None
        self.unit_edit.clear()
        self.is_modified = True

    def on_is_group_changed(self, state):
        """Handle is_group checkbox change"""
        self.is_group = self.is_group_checkbox.isChecked()
        
        # If this is now a group, clear price and labor rate
        if self.is_group:
            self.price_spinbox.setValue(0.0)
            self.labor_rate_spinbox.setValue(0.0)
            # Disable price and labor rate for groups
            self.price_spinbox.setEnabled(False)
            self.labor_rate_spinbox.setEnabled(False)
        else:
            # Enable price and labor rate for regular works
            self.price_spinbox.setEnabled(True)
            self.labor_rate_spinbox.setEnabled(True)

    def on_restore_groups(self):
        """Restore groups by marking all parent works as is_group=True"""
        reply = QMessageBox.question(
            self, "Восстановление групп",
            "Пометить как группы все работы, которые указаны в качестве родителей?\n\n"
            "Это действие найдет все работы, которые используются как parent_id, "
            "и установит для них is_group=True.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # Find all works that are used as parents
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE works 
                SET is_group = 1 
                WHERE id IN (
                    SELECT DISTINCT parent_id 
                    FROM works 
                    WHERE parent_id IS NOT NULL 
                    AND parent_id != 0 
                    AND marked_for_deletion = 0
                )
                AND marked_for_deletion = 0
            """)
            
            affected_rows = cursor.rowcount
            self.db.commit()
            
            QMessageBox.information(
                self, "Успех", 
                f"Восстановлено {affected_rows} групп работ.\n\n"
                "Все работы, которые используются как родители, "
                "теперь помечены как группы (is_group=True)."
            )
            
            # Reload current work data if it was affected
            if self.work_id > 0:
                self.load_data()
                
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", 
                f"Не удалось восстановить группы: {str(e)}"
            )

    def on_add_cost_item(self):
        dialog = CostItemSelectorDialog(self, work_id=self.work_id, filter_by_work=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cost_item_id = dialog.get_selected_cost_item_id()
            if not cost_item_id:
                return
                
            if any(ci.id == cost_item_id for ci, _ in self.cost_items):
                QMessageBox.warning(self, "Ошибка", "Эта статья затрат уже добавлена к работе")
                return
                
            cost_item = self.cost_item_repo.find_by_id(cost_item_id)
            if cost_item:
                self.cost_items.append((cost_item, 0.0))
                self.cost_items_table.load_cost_items(self.cost_items)
                self.is_modified = True
                self.calculate_total_cost()

    def on_create_new_cost_item(self):
        """Create new cost item and add to work"""
        form = CostItemForm(cost_item_id=0)
        form.setModal(True)
        if form.exec() == QDialog.DialogCode.Accepted:
            # Get the newly created cost item ID
            new_cost_item_id = form.cost_item_id
            if new_cost_item_id > 0:
                # Check if already added
                if any(ci.id == new_cost_item_id for ci, _ in self.cost_items):
                    QMessageBox.warning(self, "Ошибка", "Эта статья затрат уже добавлена к работе")
                    return
                    
                # Load and add the new cost item
                cost_item = self.cost_item_repo.find_by_id(new_cost_item_id)
                if cost_item:
                    self.cost_items.append((cost_item, 0.0))
                    self.cost_items_table.load_cost_items(self.cost_items)
                    self.is_modified = True
                    self.calculate_total_cost()
                    QMessageBox.information(self, "Успех", "Новая статья затрат создана и добавлена к работе")

    def on_remove_cost_item(self):
        selected_id = self.cost_items_table.get_selected_cost_item_id()
        if not selected_id:
            return
            
        if any(ci.id == selected_id for _, _, ci in self.materials):
             QMessageBox.warning(self, "Ошибка", 
                                 "Невозможно удалить статью затрат с привязанными материалами. Сначала удалите материалы.")
             return

        if QMessageBox.question(self, "Подтверждение", "Удалить статью затрат?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.cost_items = [x for x in self.cost_items if x[0].id != selected_id]
            self.cost_items_table.load_cost_items(self.cost_items)
            self.is_modified = True
            self.calculate_total_cost()

    def on_add_material(self):
        # Allow adding material even if no cost items are selected yet (will be added automatically)
             
        dialog = MaterialAddDialog(self, work_id=self.work_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ci_id, mat_id, qty = dialog.get_result()
            
            if any(m.id == mat_id and ci.id == ci_id for m, _, ci in self.materials):
                 QMessageBox.warning(self, "Ошибка", "Этот материал уже добавлен к этой статье затрат")
                 return
                 
            material = self.material_repo.find_by_id(mat_id)
            cost_item = self.cost_item_repo.find_by_id(ci_id)
            
            if material and cost_item:
                # If cost item is not in the list yet, add it
                if not any(ci.id == ci_id for ci, _ in self.cost_items):
                    self.cost_items.append((cost_item, 0.0))
                    self.cost_items_table.load_cost_items(self.cost_items)

                self.materials.append((material, qty, cost_item))
                self.materials_table.load_materials(self.materials)
                self.is_modified = True
                self.calculate_total_cost()

    def on_remove_material(self):
        selected_id = self.materials_table.get_selected_material_id()
        if not selected_id:
            return
            
        if QMessageBox.question(self, "Подтверждение", "Удалить материал?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            # Current implementation of table only allows single selection
            # We use currentRow to find which one to delete
            row = self.materials_table.currentRow()
            if row >= 0 and row < len(self.materials):
                del self.materials[row]
                self.materials_table.load_materials(self.materials)
                self.is_modified = True
                self.calculate_total_cost()

    def on_material_quantity_changed(self, row, new_qty):
        if row >= 0 and row < len(self.materials):
            if new_qty <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше нуля")
                self.materials_table.load_materials(self.materials)
                return
                
            mat, _, ci = self.materials[row]
            self.materials[row] = (mat, new_qty, ci)
            
            total = mat.price * new_qty
            self.materials_table.item(row, 6).setText(f"{total:.2f}")
            
            self.is_modified = True
            self.calculate_total_cost()

    def on_cost_item_quantity_changed(self, row, new_qty):
        if row >= 0 and row < len(self.cost_items):
            if new_qty < 0:
                QMessageBox.warning(self, "Ошибка", "Количество не может быть отрицательным")
                self.cost_items_table.load_cost_items(self.cost_items)
                return
                
            ci, _ = self.cost_items[row]
            self.cost_items[row] = (ci, new_qty)
            
            self.is_modified = True
            self.calculate_total_cost()

    def calculate_total_cost(self):
        total = 0.0
        for ci, _ in self.cost_items:
            total += ci.price
        for mat, qty, _ in self.materials:
            total += mat.price * qty
        self.total_cost_label.setText(f"Общая стоимость: {total:,.2f} руб.")

    def load_data(self):
        work_data = self.work_repo.find_by_id(self.work_id)
        if work_data:
            self.name_edit.setText(work_data['name'])
            self.code_edit.setText(work_data['code'] or "")
            
            # Unit
            self.unit_id = work_data.get('unit_id')
            if self.unit_id:
                self.load_unit(self.unit_id)
            else:
                self.unit_edit.setText(work_data['unit'] or "") # Fallback to legacy string if id is missing
            
            self.price_spinbox.setValue(work_data['price'] or 0.0)
            self.labor_rate_spinbox.setValue(work_data['labor_rate'] or 0.0)
            self.is_group = work_data['is_group']
            
            # Set is_group checkbox
            self.is_group_checkbox.setChecked(self.is_group)
            
            # Enable/disable price and labor rate based on group status
            if self.is_group:
                self.price_spinbox.setEnabled(False)
                self.labor_rate_spinbox.setEnabled(False)
            else:
                self.price_spinbox.setEnabled(True)
                self.labor_rate_spinbox.setEnabled(True)
            
            if work_data['parent_id']:
                self.load_parent(work_data['parent_id'])
                
        if self.use_simplified_specifications:
            self.specifications = self.spec_repo.get_by_work_id(self.work_id)
            self.spec_widget.load_data(self.specifications)
            self.calculate_spec_total()
        else:
            self.cost_items = self.cim_repo.get_cost_items_for_work(self.work_id)
            self.cost_items_table.load_cost_items(self.cost_items)
            
            self.materials = self.cim_repo.get_materials_for_work(self.work_id)
            self.materials_table.load_materials(self.materials)
            
            self.calculate_total_cost()
            
        self.is_modified = False

    def save_data(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование обязательно для заполнения")
            self.name_edit.setFocus()
            return False
            
        try:
            work = Work()
            if self.work_id > 0:
                work.id = self.work_id
                existing = self.work_repo.find_by_id(self.work_id)
                work.marked_for_deletion = existing['marked_for_deletion']
            
            work.name = self.name_edit.text()
            work.code = self.code_edit.text()
            # Legacy unit column removed - only use unit_id foreign key
            work.unit_id = self.unit_id
            work.price = self.price_spinbox.value()
            work.labor_rate = self.labor_rate_spinbox.value()
            work.parent_id = self.parent_id
            work.is_group = self.is_group_checkbox.isChecked()
            
            if self.work_id > 0:
                if not self.work_repo.update(work):
                    raise Exception("Failed to update work")
            else:
                new_id = self.work_repo.save(work)
                if not new_id:
                    raise Exception("Failed to save work")
                self.work_id = new_id
                
            if self.use_simplified_specifications:
                # Handle specifications
                existing_specs = self.spec_repo.get_by_work_id(self.work_id)
                existing_ids = {s['id'] for s in existing_specs}
                current_ids = {s.get('id') for s in self.specifications if s.get('id') is not None and int(s.get('id')) > 0}
                
                # Delete removed
                for spec_id in existing_ids - current_ids:
                    self.spec_repo.delete(spec_id)
                    
                # Update or Insert
                for spec in self.specifications:
                    spec_id = spec.get('id')
                    spec['work_id'] = self.work_id # Ensure work_id is set (especially for new work)
                    
                    if spec_id is None or int(spec_id) <= 0:
                        # Insert
                        new_spec_id = self.spec_repo.create(spec)
                        if new_spec_id:
                            spec['id'] = new_spec_id
                    else:
                        # Update
                        self.spec_repo.update(spec_id, spec)
                        
                # Reload to refresh IDs and calculated fields
                self.specifications = self.spec_repo.get_by_work_id(self.work_id)
                self.spec_widget.load_data(self.specifications)
                self.calculate_spec_total()
            else:
                # Handle old system (Cost Items & Materials)
                existing_cis = self.cim_repo.get_cost_items_for_work(self.work_id)
                existing_ci_ids = {ci.id for ci, _ in existing_cis}
                current_ci_ids = {ci.id for ci, _ in self.cost_items}
                
                for ci_id in existing_ci_ids - current_ci_ids:
                    self.cim_repo.remove_association_by_work_cost_item_material(self.work_id, ci_id, None)
                
                # Update all current cost items
                for ci, qty in self.cost_items:
                    self.cim_repo.create_or_update_association(self.work_id, ci.id, None, qty)
                    
                existing_mats = self.cim_repo.get_materials_for_work(self.work_id)
                existing_mat_map = {(m.id, ci.id): qty for m, qty, ci in existing_mats}
                current_mat_map = {(m.id, ci.id): qty for m, qty, ci in self.materials}
                
                for key in set(existing_mat_map.keys()) - set(current_mat_map.keys()):
                    mat_id, ci_id = key
                    self.cim_repo.remove_association_by_work_cost_item_material(self.work_id, ci_id, mat_id)
                for key, qty in current_mat_map.items():
                    mat_id, ci_id = key
                    self.cim_repo.create_or_update_association(self.work_id, ci_id, mat_id, qty)
                
            self.is_modified = False
            title = "Редактирование группы работ" if self.is_group else "Редактирование вида работ"
            self.setWindowTitle(title)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")
            return False

    def on_save(self):
        self.save_data()

    def on_save_and_close(self):
        if self.save_data():
            self.close()

    def on_close(self):
        self.close()

    def closeEvent(self, event):
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
        if event.matches(QKeySequence.StandardKey.Save):
            self.on_save()
        elif event.key() == Qt.Key.Key_S and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Escape:
            self.on_close()
        else:
            super().keyPressEvent(event)
