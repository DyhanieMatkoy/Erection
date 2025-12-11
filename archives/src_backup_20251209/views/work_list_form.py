"""Work list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel)
from PyQt6.QtCore import Qt
from .base_list_form import BaseListForm
from .work_form import WorkForm
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository
from ..data.repositories.reference_repository import ReferenceRepository


class WorkListForm(BaseListForm):
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.work_repo = WorkRepository(self.db_manager)
        self.ref_repo = ReferenceRepository()
        super().__init__()
        self.setWindowTitle("Справочник: Работы")
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск (Ctrl+F):"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(6)  # Reduced from 7 (removed Nomenclature column)
        self.table_view.setHorizontalHeaderLabels(["ID", "Код", "Наименование", "Ед. изм.", "Цена", "Норма трудозатрат"])
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_enter_pressed)
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("Создать (Insert/F9)")
        self.new_button.clicked.connect(self.on_insert_pressed)
        button_layout.addWidget(self.new_button)
        
        self.new_group_button = QPushButton("Создать группу")
        self.new_group_button.clicked.connect(self.on_create_group)
        button_layout.addWidget(self.new_group_button)
        
        self.edit_button = QPushButton("Открыть (Enter)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Пометить на удаление (Delete)")
        self.delete_button.clicked.connect(self.on_delete_pressed)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self, search_text=""):
        """Load data from database"""
        if search_text:
            works = self.work_repo.search_by_name(search_text)
        else:
            works = self.work_repo.find_all()
        
        self.table_view.setRowCount(len(works))
        
        for row_idx, work in enumerate(works):
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(work['id'])))
            self.table_view.setItem(row_idx, 1, QTableWidgetItem(work['code'] or ""))
            
            name_item = QTableWidgetItem(work['name'])
            if work['marked_for_deletion']:
                name_item.setForeground(Qt.GlobalColor.red)
            self.table_view.setItem(row_idx, 2, name_item)
            
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(work['unit'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(f"{work['price']:.2f}" if work['price'] is not None else ""))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(f"{work['labor_rate']:.2f}" if work['labor_rate'] is not None else ""))
            # Nomenclature column removed - feature was deprecated
        
        # Hide ID column
        self.table_view.setColumnHidden(0, True)
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_insert_pressed(self):
        """Handle insert key - create new work"""
        form = WorkForm(0)
        form.show()
    
    def on_enter_pressed(self):
        """Handle enter key - open selected work"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                work_id = int(id_item.text())
                form = WorkForm(work_id)
                form.show()
    
    def on_delete_pressed(self):
        """Handle delete key - mark for deletion"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                work_id = int(id_item.text())
                name_item = self.table_view.item(current_row, 2)
                
                # Check if can delete
                can_delete, usages = self.ref_repo.can_delete_work(work_id)
                
                if not can_delete:
                    usage_text = "\n".join([f"- {doc_type}: {doc_info}" for doc_type, doc_info in usages])
                    QMessageBox.warning(
                        self, "Невозможно удалить",
                        f"Работа '{name_item.text()}' используется в следующих документах:\n\n{usage_text}\n\nУдаление невозможно."
                    )
                    return
                
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    f"Пометить на удаление работу '{name_item.text()}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.work_repo.delete(work_id):
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Не удалось пометить работу на удаление")
    
    def on_create_group(self):
        """Create new group"""
        form = WorkForm(0, is_group=True)
        form.show()
    
    def on_search_activated(self):
        """Handle search activation"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()
