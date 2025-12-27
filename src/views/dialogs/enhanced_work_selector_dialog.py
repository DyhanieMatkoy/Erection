"""Enhanced work selector dialog with user settings support"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, 
                              QLabel, QMenu, QToolButton, QSplitter, QTextEdit)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ...data.database_manager import DatabaseManager
from ...services.user_settings_service import UserSettingsService
from .work_selector_settings_dialog import WorkSelectorSettingsDialog


class EnhancedWorkSelectorDialog(QDialog):
    """Enhanced work selector dialog with user settings support"""
    
    work_selected = pyqtSignal(int, str)  # work_id, work_name
    
    def __init__(self, parent=None, current_work_id=None, user_id=4):
        super().__init__(parent)
        self.current_work_id = current_work_id
        self.user_id = user_id
        self.settings_service = UserSettingsService()
        self.settings = {}
        self.current_parent_id = None
        self.last_selected_work_id = None
        
        self.db = DatabaseManager().get_connection()
        self._selected_id = 0
        self._selected_value = ""
        
        self.load_user_settings()
        self.setup_ui()
        self.apply_settings()
        self.load_data()
        
        self.setWindowTitle("Выбор работы")
        self.resize(900, 600)
        
        # Ensure dialog can receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        
        # Set focus to table after setup
        QTimer.singleShot(100, self.set_initial_focus)
    
    def set_initial_focus(self):
        """Set initial focus to table view"""
        if self.table_view.rowCount() > 0:
            self.table_view.setFocus()
            if self.table_view.currentRow() < 0:
                self.table_view.selectRow(0)
        else:
            self.search_edit.setFocus()
    
    def showEvent(self, event):
        """Handle show event to ensure proper focus"""
        super().showEvent(event)
        # Ensure focus is set when dialog is shown
        QTimer.singleShot(50, self.set_initial_focus)
    
    def load_user_settings(self):
        """Load user settings"""
        try:
            self.settings = self.settings_service.get_work_selector_settings(self.user_id)
        except Exception as e:
            print(f"Error loading work selector settings: {e}")
            # Use defaults
            self.settings = {
                'open_modal': True,
                'default_hierarchy_mode': 'tree',
                'show_hierarchy_controls': True,
                'auto_expand_groups': True,
                'remember_last_position': True
            }
    
    def apply_settings(self):
        """Apply user settings to dialog behavior"""
        # Set modal/non-modal mode
        is_modal = self.settings.get('open_modal', True)
        self.setModal(is_modal)
        
        # For non-modal dialogs, set proper window flags to ensure they stay on top
        if not is_modal:
            from PyQt6.QtCore import Qt
            self.setWindowFlags(
                Qt.WindowType.Dialog | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            # Ensure proper parent relationship for z-order
            if self.parent():
                self.setParent(self.parent())
        else:
            # For modal dialogs, ensure proper flags and focus handling
            from PyQt6.QtCore import Qt
            self.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.WindowCloseButtonHint
            )
            # Ensure modal dialogs can receive keyboard events
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Load last position if enabled
        if self.settings.get('remember_last_position', True):
            self.last_selected_work_id = self.settings_service.get_setting(
                self.user_id, 'work_selector.last_selected_work_id', None
            )
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Settings button
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙️")
        self.settings_button.setToolTip("Настройки селектора работ")
        self.settings_button.clicked.connect(self.on_open_settings)
        toolbar_layout.addWidget(self.settings_button)
        
        toolbar_layout.addStretch()
        
        # Mode indicator
        self.mode_label = QLabel()
        self.update_mode_label()
        toolbar_layout.addWidget(self.mode_label)
        
        layout.addLayout(toolbar_layout)
        
        # Navigation bar (for hierarchical mode)
        self.nav_layout = QHBoxLayout()
        
        self.up_button = QPushButton("↑ Вверх")
        self.up_button.clicked.connect(self.on_navigate_up)
        self.up_button.setEnabled(False)
        self.nav_layout.addWidget(self.up_button)
        
        self.parent_label = QLabel("Корень")
        self.nav_layout.addWidget(self.parent_label)
        
        self.nav_layout.addStretch()
        
        # Hierarchy mode buttons
        self.flat_mode_button = QPushButton("📋 Плоский")
        self.flat_mode_button.setCheckable(True)
        self.flat_mode_button.clicked.connect(lambda: self.set_hierarchy_mode('flat'))
        self.nav_layout.addWidget(self.flat_mode_button)
        
        self.tree_mode_button = QPushButton("🌳 Дерево")
        self.tree_mode_button.setCheckable(True)
        self.tree_mode_button.clicked.connect(lambda: self.set_hierarchy_mode('tree'))
        self.nav_layout.addWidget(self.tree_mode_button)
        
        self.breadcrumb_mode_button = QPushButton("🗂️ Пути")
        self.breadcrumb_mode_button.setCheckable(True)
        self.breadcrumb_mode_button.clicked.connect(lambda: self.set_hierarchy_mode('breadcrumb'))
        self.nav_layout.addWidget(self.breadcrumb_mode_button)
        
        layout.addLayout(self.nav_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.setPlaceholderText("Введите название или код работы...")
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Main content area
        if self.settings.get('default_hierarchy_mode') == 'breadcrumb':
            # Use splitter for breadcrumb mode to show work details
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # Table
            self.table_view = self.create_table()
            splitter.addWidget(self.table_view)
            
            # Details panel
            details_widget = QVBoxLayout()
            details_label = QLabel("Детали работы:")
            details_widget.addWidget(details_label)
            
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setMaximumWidth(300)
            details_widget.addWidget(self.details_text)
            
            layout.addWidget(splitter)
        else:
            # Just table
            self.table_view = self.create_table()
            layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.drill_down_button = QPushButton("Открыть группу (Enter)")
        self.drill_down_button.clicked.connect(self.on_drill_down)
        button_layout.addWidget(self.drill_down_button)
        
        self.add_button = QPushButton("Добавить (Ins)")
        self.add_button.clicked.connect(self.on_add)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Изменить (F4)")
        self.edit_button.clicked.connect(self.on_edit)
        button_layout.addWidget(self.edit_button)
        
        button_layout.addStretch()
        
        self.select_button = QPushButton("Выбрать (Ctrl+Enter)")
        self.select_button.clicked.connect(self.on_select)
        self.select_button.setDefault(True)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Отмена (Esc)")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Update visibility based on settings
        self.update_controls_visibility()
    
    def create_table(self):
        """Create and configure table widget"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ID", "Наименование", "Код", "Ед.изм.", "Цена", "parent_id"])
        
        # Set column widths
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(2, 100)  # Code
        table.setColumnWidth(3, 80)   # Unit
        table.setColumnWidth(4, 100)  # Price
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.doubleClicked.connect(self.on_row_double_clicked)
        table.currentItemChanged.connect(self.on_current_row_changed)
        
        # Context menu
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.on_context_menu)
        
        return table
    
    def update_mode_label(self):
        """Update mode indicator label"""
        mode = "Модальный" if self.settings.get('open_modal', True) else "Немодальный"
        hierarchy = self.settings.get('default_hierarchy_mode', 'tree').title()
        self.mode_label.setText(f"Режим: {mode} | Иерархия: {hierarchy}")
    
    def update_controls_visibility(self):
        """Update visibility of controls based on settings"""
        show_controls = self.settings.get('show_hierarchy_controls', True)
        
        # Hide/show navigation controls
        self.up_button.setVisible(show_controls)
        self.parent_label.setVisible(show_controls)
        self.flat_mode_button.setVisible(show_controls)
        self.tree_mode_button.setVisible(show_controls)
        self.breadcrumb_mode_button.setVisible(show_controls)
        self.drill_down_button.setVisible(show_controls)
        
        # Update hierarchy mode buttons
        current_mode = self.settings.get('default_hierarchy_mode', 'tree')
        self.flat_mode_button.setChecked(current_mode == 'flat')
        self.tree_mode_button.setChecked(current_mode == 'tree')
        self.breadcrumb_mode_button.setChecked(current_mode == 'breadcrumb')
    
    def set_hierarchy_mode(self, mode):
        """Set hierarchy display mode"""
        self.settings['default_hierarchy_mode'] = mode
        self.update_controls_visibility()
        self.update_mode_label()
        self.load_data()
        
        # Save the preference
        try:
            self.settings_service.set_setting(self.user_id, 'work_selector.temp_hierarchy_mode', mode)
        except Exception as e:
            print(f"Error saving temporary hierarchy mode: {e}")
    
    def load_data(self, search_text=""):
        """Load works data based on current settings"""
        try:
            cursor = self.db.cursor()
            
            # Try different column names based on database schema
            where_clauses = []
            deletion_filter_applied = False
            
            # Try marked_for_deletion first (most common)
            try:
                cursor.execute("SELECT marked_for_deletion FROM works LIMIT 1")
                where_clauses = ["(w.marked_for_deletion = 0 OR w.marked_for_deletion IS NULL)"]
                deletion_filter_applied = True
            except Exception as e:
                print(f"marked_for_deletion column not found: {e}")
                try:
                    # Then try is_deleted
                    cursor.execute("SELECT is_deleted FROM works LIMIT 1") 
                    where_clauses = ["(w.is_deleted = 0 OR w.is_deleted IS NULL)"]
                    deletion_filter_applied = True
                except Exception as e2:
                    print(f"is_deleted column not found: {e2}")
                    # Fallback - no deletion filter
                    where_clauses = ["1=1"]
            
            params = []
            
            hierarchy_mode = self.settings.get('default_hierarchy_mode', 'tree')
            
            # If we have a current work ID and we're in tree mode, try to navigate to its parent
            if (self.current_work_id and hierarchy_mode == 'tree' and 
                not search_text and self.current_parent_id is None):
                self._navigate_to_work_parent()
            
            if search_text:
                # When searching, show all levels
                where_clauses.append("(w.name LIKE ? OR w.code LIKE ?)")
                params.append(f"%{search_text}%")
                params.append(f"%{search_text}%")
            elif hierarchy_mode == 'tree':
                # Tree mode - show only current level
                if self.current_parent_id is None:
                    where_clauses.append("(w.parent_id IS NULL OR w.parent_id = 0)")
                else:
                    where_clauses.append("w.parent_id = ?")
                    params.append(self.current_parent_id)
            # For flat and breadcrumb modes, show all works
            
            where_clause = " AND ".join(where_clauses)
            
            # Build query based on hierarchy mode
            if hierarchy_mode == 'breadcrumb':
                # Include full path in breadcrumb mode
                # Note: Simplified breadcrumb query without CTE for better compatibility
                query = f"""
                    SELECT w.id, w.name, w.code, u.name as unit, w.price, w.parent_id,
                           CASE 
                               WHEN w.parent_id IS NULL OR w.parent_id = 0 THEN w.name
                               ELSE w.name
                           END as path
                    FROM works w
                    LEFT JOIN units u ON w.unit_id = u.id
                    WHERE {where_clause}
                    ORDER BY w.name
                """
            else:
                query = f"""
                    SELECT w.id, w.name, w.code, u.name as unit, w.price, w.parent_id
                    FROM works w
                    LEFT JOIN units u ON w.unit_id = u.id
                    WHERE {where_clause}
                    ORDER BY w.name
                """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.table_view.setRowCount(len(rows))
            
            row_to_select = None
            for row_idx, row in enumerate(rows):
                self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
                
                # Check if this work has children (is a group)
                has_children = False
                if hierarchy_mode == 'tree':
                    try:
                        if deletion_filter_applied:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ? AND (marked_for_deletion = 0 OR marked_for_deletion IS NULL)
                            """, (row['id'],))
                        else:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ?
                            """, (row['id'],))
                        has_children = cursor.fetchone()['cnt'] > 0
                    except Exception as e:
                        print(f"Error checking children: {e}")
                        has_children = False
                
                # Format name based on mode
                name_text = row['name']
                if hierarchy_mode == 'breadcrumb' and 'path' in row:
                    name_text = row['path']
                elif has_children:
                    name_text = "📁 " + name_text
                
                self.table_view.setItem(row_idx, 1, QTableWidgetItem(name_text))
                self.table_view.setItem(row_idx, 2, QTableWidgetItem(row['code'] if row['code'] else ''))
                self.table_view.setItem(row_idx, 3, QTableWidgetItem(row['unit'] if row['unit'] else ''))
                self.table_view.setItem(row_idx, 4, QTableWidgetItem(str(row['price'] if row['price'] else 0)))
                self.table_view.setItem(row_idx, 5, QTableWidgetItem(str(row['parent_id']) if row['parent_id'] else ""))
                
                # Select current work or last selected work
                if ((self.current_work_id and row['id'] == self.current_work_id) or
                    (self.last_selected_work_id and row['id'] == self.last_selected_work_id)):
                    row_to_select = row_idx
            
            # Hide ID and parent_id columns
            self.table_view.setColumnHidden(0, True)
            self.table_view.setColumnHidden(5, True)
            
            # Position cursor
            if row_to_select is not None:
                self.table_view.selectRow(row_to_select)
                self.table_view.scrollToItem(self.table_view.item(row_to_select, 1))
                print(f"Selected row {row_to_select} for work {self.current_work_id}")
            elif self.table_view.rowCount() > 0:
                self.table_view.selectRow(0)
                # If we have a current work ID but didn't find it, try to switch to flat mode
                if self.current_work_id and hierarchy_mode == 'tree':
                    print(f"Work {self.current_work_id} not found in current tree view, trying flat mode")
                    self._try_find_work_in_flat_mode()
            
            self.update_navigation_state()
            
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            # Set empty table on error
            self.table_view.setRowCount(0)
    
    def _try_find_work_in_flat_mode(self):
        """Try to find current work by temporarily switching to flat mode"""
        if not self.current_work_id:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Check if the work exists at all
            cursor.execute("SELECT id, name FROM works WHERE id = ?", (self.current_work_id,))
            work_row = cursor.fetchone()
            
            if work_row:
                print(f"Work {self.current_work_id} exists: {work_row['name']}")
                
                # Show a message to user that we're switching to flat mode to show the work
                if hasattr(self, 'mode_label'):
                    original_text = self.mode_label.text()
                    self.mode_label.setText(f"{original_text} | Переключено в плоский режим для отображения выбранной работы")
                
                # Temporarily switch to flat mode
                original_mode = self.settings.get('default_hierarchy_mode', 'tree')
                self.settings['default_hierarchy_mode'] = 'flat'
                self.update_controls_visibility()
                
                # Reload data in flat mode
                self.load_data()
                
                # Restore original mode setting (but keep UI in flat mode)
                self.settings['default_hierarchy_mode'] = original_mode
                
        except Exception as e:
            print(f"Error trying to find work in flat mode: {e}")
    
    def _navigate_to_work_parent(self):
        """Navigate to the parent group of the current work"""
        if not self.current_work_id:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Get the parent_id of the current work
            cursor.execute("SELECT parent_id FROM works WHERE id = ?", (self.current_work_id,))
            row = cursor.fetchone()
            
            if row and row['parent_id']:
                # Set current parent to the work's parent
                self.current_parent_id = row['parent_id']
                print(f"Navigated to parent group {self.current_parent_id} for work {self.current_work_id}")
            else:
                # Work is at root level
                self.current_parent_id = None
                print(f"Work {self.current_work_id} is at root level")
                
        except Exception as e:
            print(f"Error navigating to work parent: {e}")
            # Keep current parent as is
    
    def on_current_row_changed(self, current, previous):
        """Handle current row change - update details if in breadcrumb mode"""
        if (self.settings.get('default_hierarchy_mode') == 'breadcrumb' and 
            hasattr(self, 'details_text')):
            
            current_row = self.table_view.currentRow()
            if current_row >= 0:
                id_item = self.table_view.item(current_row, 0)
                if id_item:
                    work_id = int(id_item.text())
                    self.update_work_details(work_id)
    
    def update_work_details(self, work_id):
        """Update work details panel"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT w.*, u.name as unit_name
                FROM works w
                LEFT JOIN units u ON w.unit_id = u.id
                WHERE w.id = ?
            """, (work_id,))
            
            work = cursor.fetchone()
            if work:
                details = f"""
Код: {work['code'] or 'Не указан'}
Наименование: {work['name']}
Единица измерения: {work['unit_name'] or 'Не указана'}
Цена: {work['price'] or 0:.2f}
Норма трудозатрат: {work['labor_rate'] or 0:.2f}
                """.strip()
                
                self.details_text.setText(details)
        except Exception as e:
            print(f"Error updating work details: {e}")
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_navigate_up(self):
        """Navigate to parent level"""
        if self.current_parent_id is not None:
            cursor = self.db.cursor()
            cursor.execute("SELECT parent_id FROM works WHERE id = ?", (self.current_parent_id,))
            row = cursor.fetchone()
            
            if row:
                self.current_parent_id = row['parent_id'] if row['parent_id'] else None
            else:
                self.current_parent_id = None
            
            self.load_data()
    
    def on_drill_down(self):
        """Drill down into selected group"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                try:
                    # Check if this item has children
                    cursor = self.db.cursor()
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) as cnt FROM works
                            WHERE parent_id = ? AND (marked_for_deletion = 0 OR marked_for_deletion IS NULL)
                        """, (selected_id,))
                    except:
                        try:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)
                            """, (selected_id,))
                        except:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ?
                            """, (selected_id,))
                    
                    has_children = cursor.fetchone()['cnt'] > 0
                    
                    if has_children:
                        self.current_parent_id = selected_id
                        self.load_data()
                except Exception as e:
                    print(f"Error drilling down: {e}")
                    import traceback
                    traceback.print_exc()
    
    def on_row_double_clicked(self, index):
        """Handle row double click"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                try:
                    # Check if this item has children
                    cursor = self.db.cursor()
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) as cnt FROM works
                            WHERE parent_id = ? AND (marked_for_deletion = 0 OR marked_for_deletion IS NULL)
                        """, (selected_id,))
                    except:
                        try:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)
                            """, (selected_id,))
                        except:
                            cursor.execute("""
                                SELECT COUNT(*) as cnt FROM works
                                WHERE parent_id = ?
                            """, (selected_id,))
                    
                    has_children = cursor.fetchone()['cnt'] > 0
                    
                    if has_children and self.settings.get('default_hierarchy_mode') == 'tree':
                        # Drill down
                        self.current_parent_id = selected_id
                        self.load_data()
                    else:
                        # Select
                        self.on_select()
                except Exception as e:
                    print(f"Error on double click: {e}")
                    import traceback
                    traceback.print_exc()
                    # Just select on error
                    self.on_select()
    
    def update_navigation_state(self):
        """Update navigation buttons and label"""
        hierarchy_mode = self.settings.get('default_hierarchy_mode', 'tree')
        
        # Enable/disable up button
        self.up_button.setEnabled(self.current_parent_id is not None and hierarchy_mode == 'tree')
        
        # Update parent label
        if self.current_parent_id is None:
            self.parent_label.setText("Корень")
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM works WHERE id = ?", (self.current_parent_id,))
            row = cursor.fetchone()
            if row:
                self.parent_label.setText(f"Группа: {row['name']}")
    
    def on_select(self):
        """Handle select button"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            value_item = self.table_view.item(current_row, 1)
            if id_item and value_item:
                self._selected_id = int(id_item.text())
                self._selected_value = value_item.text().replace("📁 ", "")
                
                # Save last selected work if enabled
                if self.settings.get('remember_last_position', True):
                    try:
                        self.settings_service.set_setting(
                            self.user_id, 'work_selector.last_selected_work_id', self._selected_id
                        )
                    except Exception as e:
                        print(f"Error saving last selected work: {e}")
                
                self.work_selected.emit(self._selected_id, self._selected_value)
                self.accept()
    
    def on_context_menu(self, position):
        """Handle context menu"""
        menu = QMenu()
        
        add_action = QAction("Добавить", self)
        add_action.triggered.connect(self.on_add)
        menu.addAction(add_action)
        
        menu.addSeparator()
        
        edit_action = QAction("Изменить", self)
        edit_action.triggered.connect(self.on_edit)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.on_open_settings)
        menu.addAction(settings_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))
    
    def on_add(self):
        """Handle add button"""
        try:
            from ..work_form import WorkForm
            form = WorkForm(0)  # 0 for new item
            
            # Store reference to prevent garbage collection
            self._add_form = form
            
            # For non-modal work selector, ensure edit form appears on top
            if not self.isModal():
                form.setWindowFlags(
                    form.windowFlags() | 
                    Qt.WindowType.WindowStaysOnTopHint
                )
            
            # Connect to form closed signal to refresh data
            if hasattr(form, 'finished'):
                form.finished.connect(self._on_add_form_closed)
            elif hasattr(form, 'destroyed'):
                form.destroyed.connect(self._on_add_form_closed)
            
            form.show()
            form.raise_()
            form.activateWindow()
        except ImportError as e:
            print(f"Work form not available: {e}")
        except Exception as e:
            print(f"Error opening add form: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_add_form_closed(self):
        """Handle add form closed"""
        self.load_data()
        self._add_form = None
    
    def on_edit(self):
        """Handle edit button"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                try:
                    from ..work_form import WorkForm
                    form = WorkForm(selected_id)
                    
                    # Store reference to prevent garbage collection
                    self._edit_form = form
                    
                    # For non-modal work selector, ensure edit form appears on top
                    if not self.isModal():
                        form.setWindowFlags(
                            form.windowFlags() | 
                            Qt.WindowType.WindowStaysOnTopHint
                        )
                    
                    # Connect to form closed signal to refresh data
                    if hasattr(form, 'finished'):
                        form.finished.connect(self._on_edit_form_closed)
                    elif hasattr(form, 'destroyed'):
                        form.destroyed.connect(self._on_edit_form_closed)
                    
                    form.show()
                    form.raise_()
                    form.activateWindow()
                except ImportError as e:
                    print(f"Work form not available: {e}")
                except Exception as e:
                    print(f"Error opening edit form: {e}")
                    import traceback
                    traceback.print_exc()
    
    def _on_edit_form_closed(self):
        """Handle edit form closed"""
        self.load_data()
        self._edit_form = None
    
    def on_open_settings(self):
        """Open settings dialog"""
        dialog = WorkSelectorSettingsDialog(self, self.user_id)
        if dialog.exec():
            # Reload settings and apply them
            self.load_user_settings()
            self.apply_settings()
            self.update_controls_visibility()
            self.update_mode_label()
            self.load_data()
    
    def get_selected(self):
        """Get selected work ID and name"""
        return (self._selected_id, self._selected_value)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Ensure the dialog can receive focus and keyboard events
        if not self.hasFocus():
            self.setFocus()
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.on_select()
            else:
                # Enter - drill down or select based on mode
                if self.settings.get('default_hierarchy_mode') == 'tree':
                    current_row = self.table_view.currentRow()
                    if current_row >= 0:
                        id_item = self.table_view.item(current_row, 0)
                        if id_item:
                            selected_id = int(id_item.text())
                            
                            try:
                                cursor = self.db.cursor()
                                try:
                                    cursor.execute("""
                                        SELECT COUNT(*) as cnt FROM works
                                        WHERE parent_id = ? AND (marked_for_deletion = 0 OR marked_for_deletion IS NULL)
                                    """, (selected_id,))
                                except:
                                    try:
                                        cursor.execute("""
                                            SELECT COUNT(*) as cnt FROM works
                                            WHERE parent_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)
                                        """, (selected_id,))
                                    except:
                                        cursor.execute("""
                                            SELECT COUNT(*) as cnt FROM works
                                            WHERE parent_id = ?
                                        """, (selected_id,))
                                
                                has_children = cursor.fetchone()['cnt'] > 0
                                
                                if has_children:
                                    self.on_drill_down()
                                else:
                                    self.on_select()
                            except Exception as e:
                                print(f"Error checking children in keyPressEvent: {e}")
                                import traceback
                                traceback.print_exc()
                                # Just select on error
                                self.on_select()
                else:
                    self.on_select()
        elif event.key() == Qt.Key.Key_F4:
            self.on_edit()
        elif event.key() == Qt.Key.Key_Insert:
            self.on_add()
        elif event.key() == Qt.Key.Key_Backspace:
            if self.current_parent_id is not None:
                self.on_navigate_up()
        elif event.key() == Qt.Key.Key_Home:
            # Go to first item
            if self.table_view.rowCount() > 0:
                self.table_view.selectRow(0)
                self.table_view.scrollToTop()
        elif event.key() == Qt.Key.Key_End:
            # Go to last item
            if self.table_view.rowCount() > 0:
                last_row = self.table_view.rowCount() - 1
                self.table_view.selectRow(last_row)
                self.table_view.scrollToBottom()
        elif event.key() == Qt.Key.Key_PageUp:
            # Page up
            current_row = self.table_view.currentRow()
            if current_row > 0:
                new_row = max(0, current_row - 10)
                self.table_view.selectRow(new_row)
                self.table_view.scrollToItem(self.table_view.item(new_row, 1))
        elif event.key() == Qt.Key.Key_PageDown:
            # Page down
            current_row = self.table_view.currentRow()
            if current_row >= 0:
                new_row = min(self.table_view.rowCount() - 1, current_row + 10)
                self.table_view.selectRow(new_row)
                self.table_view.scrollToItem(self.table_view.item(new_row, 1))
        elif event.key() == Qt.Key.Key_F1:
            # Switch to flat mode
            self.set_hierarchy_mode('flat')
        elif event.key() == Qt.Key.Key_F2:
            # Switch to tree mode
            self.set_hierarchy_mode('tree')
        elif event.key() == Qt.Key.Key_F3:
            # Switch to breadcrumb mode
            self.set_hierarchy_mode('breadcrumb')
        elif event.key() == Qt.Key.Key_F5:
            # Refresh data
            self.load_data()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
