
"""Work form"""
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QMessageBox, QDoubleSpinBox, 
                             QTabWidget, QLabel, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository
from ..data.repositories.cost_item_repository import CostItemRepository
from ..data.repositories.material_repository import MaterialRepository
from ..data.repositories.cost_item_material_repository import CostItemMaterialRepository
from ..data.models.sqlalchemy_models import Work, CostItem, Material

from .widgets.cost_items_table import CostItemsTable
from .widgets.materials_table import MaterialsTable
from .dialogs.cost_item_selector_dialog import CostItemSelectorDialog
from .dialogs.material_add_dialog import MaterialAddDialog
from .reference_picker_dialog import ReferencePickerDialog

class WorkForm(QWidget):
    def __init__(self, work_id=0, is_group=False):
        super().__init__()
        self.work_id = work_id
        self.is_group = is_group
        
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.get_connection()
        
        # Repositories
        self.work_repo = WorkRepository(self.db_manager)
        self.cost_item_repo = CostItemRepository()
        self.material_repo = MaterialRepository()
        self.cim_repo = CostItemMaterialRepository()
        
        # Data
        self.cost_items: List[Tuple[CostItem, float]] = []
        self.materials: List[Tuple[Material, float, CostItem]] = []
        
        self.is_modified = False
        
        self.setup_ui()
        
        if self.work_id > 0:
            self.load_data()

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
        
        tab.setLayout(form_layout)
        return tab

    def setup_cost_items_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.cost_items_table = CostItemsTable()
        self.cost_items_table.quantityChanged.connect(self.on_cost_item_quantity_changed)
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
            if work_data['parent_id']:
                self.load_parent(work_data['parent_id'])
                
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
            work.unit = self.unit_edit.text() # Keep legacy string populated for now
            work.unit_id = self.unit_id
            work.price = self.price_spinbox.value()
            work.labor_rate = self.labor_rate_spinbox.value()
            work.parent_id = self.parent_id
            work.is_group = self.is_group
            
            if self.work_id > 0:
                if not self.work_repo.update(work):
                    raise Exception("Failed to update work")
            else:
                new_id = self.work_repo.save(work)
                if not new_id:
                    raise Exception("Failed to save work")
                self.work_id = new_id
                
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
