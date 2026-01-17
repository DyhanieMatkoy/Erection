from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence
from typing import Optional, List, Dict, Any, Callable
from src.controllers.list_form_controller import ListFormController
from src.views.components.document_list_table import DocumentListTable
from src.views.components.filter_bar import FilterBar
from src.views.dialogs.bulk_operation_progress_dialog import BulkOperationProgressDialog
from src.views.utils.button_styler import get_button_styler
from src.services.table_part_keyboard_handler import TablePartKeyboardHandler, ShortcutAction, create_table_context

class GenericListForm(QWidget):
    """
    Generic List Form implementation using Controller and Components.
    (Task 7 Integration)
    """
    
    # Signal when a document needs to be opened
    open_document_requested = pyqtSignal(int) # id (0 for new)
    
    def __init__(self, form_id: str, user_id: int, model_class: Any, controller: Optional[ListFormController] = None):
        super().__init__()
        self.form_id = form_id
        self.user_id = user_id
        self.model_class = model_class
        
        # Initialize controller
        if controller:
            self.controller = controller
        elif model_class:
            self.controller = ListFormController(form_id, user_id, model_class)
        else:
            raise ValueError("Either controller or model_class must be provided")

        self.command_buttons = {}
        
        # Hierarchical navigation support
        self.is_hierarchical = False
        self.current_parent_id = None
        self.navigation_path = []  # Stack of parent IDs for navigation
        
        # Initialize keyboard handler for hierarchical navigation
        self.keyboard_handler = TablePartKeyboardHandler(self)
        self.setup_hierarchical_shortcuts()
        
        self.setup_ui()
        self.setup_callbacks()
        self.setup_bulk_operations()
        
        # Initialize
        self.controller.initialize()
        self.refresh_commands()
        # self.load_data() - moved to subclasses or explicit call, as columns might not be configured yet

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar (Commands)
        self.toolbar_layout = QHBoxLayout()
        layout.addLayout(self.toolbar_layout)
        
        # Filter Bar
        self.filter_bar = FilterBar()
        self.filter_bar.search_changed.connect(self.on_search)
        self.filter_bar.filter_changed.connect(self.on_filter)
        self.filter_bar.navigation_up_clicked.connect(self.on_navigation_up)
        layout.addWidget(self.filter_bar)
        
        # Table
        self.table = DocumentListTable()
        self.table.row_double_clicked.connect(self.on_row_double_click)
        self.table.selection_changed.connect(self.on_selection_change)
        self.table.sort_requested.connect(self.on_sort)
        self.table.column_resized.connect(self.on_column_resize)
        
        # Set style callback
        self.table.set_row_style_callback(self.get_row_style)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def setup_callbacks(self):
        self.controller.set_callbacks(
            on_data_loaded=self.on_data_loaded,
            on_error=self.on_error
        )

    def setup_bulk_operations(self):
        self.controller.bulk_service.operation_started.connect(self.on_bulk_started)
        self.controller.bulk_service.progress_updated.connect(self.on_bulk_progress)
        self.controller.bulk_service.operation_completed.connect(self.on_bulk_completed)
        self.controller.bulk_service.operation_failed.connect(self.on_bulk_failed)
        self.active_progress_dialogs = {}

    def on_bulk_started(self, op_id, name, total):
        dialog = BulkOperationProgressDialog(self, name)
        # Use default argument to capture op_id
        dialog.on_cancel_requested = lambda oid=op_id: self.controller.bulk_service.cancel_operation(oid)
        dialog.show()
        self.active_progress_dialogs[op_id] = dialog

    def on_bulk_progress(self, op_id, name, current, total):
        if op_id in self.active_progress_dialogs:
            self.active_progress_dialogs[op_id].update_progress(current, total)

    def on_bulk_completed(self, op_id, name, results):
        if op_id in self.active_progress_dialogs:
            self.active_progress_dialogs[op_id].show_results(results)
            # Remove from active list after some time or keep it until user closes? 
            # The dialog stays open until user closes it.
            # We just need to know we are done.
            if results.get('success_count', 0) > 0:
                self.load_data()

    def on_bulk_failed(self, op_id, name, error):
        if op_id in self.active_progress_dialogs:
            # Construct a result-like object for show_results
            results = {
                'success_count': 0,
                'failure_count': 1,
                'critical_error': error
            }
            self.active_progress_dialogs[op_id].show_results(results)

    def configure_columns(self, columns: List[Dict]):
        """Configure columns from outside"""
        # Apply permission filtering
        filtered_columns = self.controller.filter_columns(columns)
        self.table.configure_columns(filtered_columns, self.controller.column_settings)
        
    def add_filter(self, key: str, label: str, options: list):
        """Add a filter to the bar"""
        self.filter_bar.add_filter(key, label, options)

    def refresh_commands(self):
        """Rebuild toolbar based on available commands"""
        # Clear existing
        while self.toolbar_layout.count():
            item = self.toolbar_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.command_buttons = {}
        
        # Get commands (pass current selection context)
        # Context usually includes selected items, but controller handles state
        # We might need to pass selection explicitly if controller doesn't track it fully sync?
        # Controller tracks selection in self.selection
        selection_context = {'selected_ids': list(self.controller.selection), 'selection_count': len(self.controller.selection)}
        commands = self.controller.get_available_commands(selection_context)
        
        styler = get_button_styler()
        
        for cmd in commands:
            cmd_id = cmd['id']
            label = cmd.get('label') or cmd.get('name') or cmd.get('id')
            
            btn = QPushButton()
            styler.apply_style(btn, cmd_id, label)
            
            # Enable/Disable based on command state
            btn.setEnabled(cmd.get('is_enabled', True))
            
            # Connect
            # We need to capture cmd_id
            btn.clicked.connect(lambda checked, cid=cmd_id: self.on_command(cid))
            
            self.toolbar_layout.addWidget(btn)
            self.command_buttons[cmd_id] = btn
            
        self.toolbar_layout.addStretch()

    def on_command(self, command_id: str):
        """Handle command execution"""
        if command_id == 'create':
            self.open_document_requested.emit(0)
        elif command_id == 'open':
            # Get selection
            sel = self.controller.get_selection()
            if len(sel) == 1:
                self.open_document_requested.emit(sel[0])
        elif command_id == 'refresh':
            self.load_data()
        else:
            # Delegate to subclass methods first (e.g. on_command_copy, on_command_post)
            handler_name = f"on_command_{command_id}"
            if hasattr(self, handler_name):
                getattr(self, handler_name)()
                return

            # Delegate to controller/command manager
            try:
                # This assumes command manager executes logic. 
                # But command manager usually returns 'is_enabled'. 
                # Execution logic might be separate. 
                # Task 8 description said CommandManager handles logic.
                # Let's check CommandManager implementation.
                result = self.controller.execute_command(command_id)
                
                if result.get('success'):
                    if result.get('message'):
                        # Show status?
                        pass
                    if result.get('refresh_needed'):
                        self.load_data()
                else:
                    QMessageBox.warning(self, "Ошибка", result.get('error', "Unknown error"))
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def get_row_style(self, item: Any) -> Dict:
        """
        Determine row style based on item state.
        Default implementation handles common fields like is_posted, marked_for_deletion.
        """
        style = {}
        
        # Handle dict or object
        get_val = lambda k: item.get(k) if isinstance(item, dict) else getattr(item, k, None)
        
        if get_val('is_posted'):
            style['font_bold'] = True
            
        if get_val('marked_for_deletion'):
            style['foreground'] = "#A0A0A0" # Gray
            style['font_strike'] = True # Not implemented in table yet, but let's imagine
            
        return style

    def load_data(self):
        self.controller.load_data()

    def on_data_loaded(self, result: Dict):
        """Handle data loaded from controller"""
        items = result.get('items', [])
        self.table.set_data(items)
        # Update pagination controls (not implemented in UI yet)

    def on_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)

    def on_search(self, text: str):
        # We assume controller has set_filter logic or we use specific search method
        # Controller has set_filter, but specific search might be separate or special filter key
        # Let's map search to a filter named 'search_text' or similar, 
        # or controller could have search method.
        # Controller has set_filter.
        # But wait, BaseListForm had explicit search param in load_data.
        # Controller implementation uses filters dict.
        # DataService uses filters dict.
        # Let's assume 'search' key is handled by DataService if needed, or we implement 'search' filter logic.
        # Actually DataService.get_documents takes filters.
        # We can pass 'search_text' filter?
        # Let's use 'search_text' as key.
        self.controller.set_filter('search_text', text)

    def on_filter(self, key: str, value: Any):
        self.controller.set_filter(key, value)

    def on_sort(self, column_id: str):
        self.controller.handle_sorting(column_id)

    def on_column_resize(self, column_id: str, width: int):
        self.controller.handle_column_resize(column_id, width)

    def on_row_double_click(self, item_id: int):
        # Open document
        pass

    def on_selection_change(self, selected_ids: List[int]):
        self.controller.update_selection(selected_ids)
        # Update keyboard context
        self.update_keyboard_context()
        # Update command bar
        self.refresh_commands()

    def on_navigation_up(self):
        """Handle navigation up - to be overridden by subclasses"""
        pass

    def go_up(self):
        """Navigate up in hierarchy - to be overridden by subclasses with hierarchy support"""
        pass

    def go_down(self):
        """Navigate down in hierarchy - to be overridden by subclasses with hierarchy support"""
        # Default behavior: open selected item (drill down into group)
        sel = self.controller.get_selection()
        if len(sel) == 1:
            self.open_document_requested.emit(sel[0])

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Handle Ctrl+Up/Down for hierarchy navigation
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Up:
            self.go_up()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Down:
            self.go_down()
        # Handle standard shortcuts
        elif event.key() == Qt.Key.Key_Insert or event.key() == Qt.Key.Key_F9:
            # Create new item
            self.open_document_requested.emit(0)
        elif event.key() == Qt.Key.Key_F2:
            # Edit selected item
            sel = self.controller.get_selection()
            if len(sel) == 1:
                self.open_document_requested.emit(sel[0])
        elif event.key() == Qt.Key.Key_Delete:
            # Delete selected item
            result = self.controller.execute_command("delete")
            if not result.get('success'):
                QMessageBox.warning(self, "Ошибка", result.get('error', "Failed to delete item"))
            else:
                self.load_data()
        elif event.key() == Qt.Key.Key_F5:
            # Refresh data
            self.load_data()
        elif event.key() == Qt.Key.Key_F8:
            # Print
            result = self.controller.execute_command("print")
            if not result.get('success'):
                QMessageBox.warning(self, "Ошибка", result.get('error', "Failed to print"))
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Open selected item (like double-click)
            sel = self.controller.get_selection()
            if len(sel) == 1:
                self.open_document_requested.emit(sel[0])
        else:
            super().keyPressEvent(event)

    def setup_hierarchical_shortcuts(self):
        """Setup hierarchical navigation keyboard shortcuts"""
        # Register handlers for hierarchical navigation actions
        self.keyboard_handler.register_action_handler(
            ShortcutAction.EXPAND_NODE, self.on_expand_node
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.COLLAPSE_NODE, self.on_collapse_node
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.EXPAND_ALL_CHILDREN, self.on_expand_all_children
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.COLLAPSE_ALL_CHILDREN, self.on_collapse_all_children
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.GO_TO_FIRST, self.on_go_to_first
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.GO_TO_LAST, self.on_go_to_last
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.GO_TO_ROOT, self.on_go_to_root
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.GO_TO_LAST_IN_HIERARCHY, self.on_go_to_last_in_hierarchy
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.PAGE_UP, self.on_page_up
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.PAGE_DOWN, self.on_page_down
        )

    def enable_hierarchical_navigation(self, enabled: bool = True):
        """
        Enable or disable hierarchical navigation for this form.
        
        Args:
            enabled: True to enable hierarchical navigation, False to disable
        """
        self.is_hierarchical = enabled
        self.update_keyboard_context()

    def update_keyboard_context(self):
        """Update keyboard handler context with current state"""
        selected_ids = self.controller.get_selection() if hasattr(self.controller, 'get_selection') else []
        current_row = None
        if selected_ids and len(selected_ids) == 1:
            # Find row index of selected item
            for i, item in enumerate(self.table.data_map):
                item_id = item.get('id') if isinstance(item, dict) else getattr(item, 'id', None)
                if item_id == selected_ids[0]:
                    current_row = i
                    break
        
        context = create_table_context(
            widget=self,
            selected_rows=list(range(len(selected_ids))),  # Convert to row indices
            current_row=current_row,
            is_hierarchical=self.is_hierarchical,
            is_editing=False
        )
        self.keyboard_handler.update_context(context)

    # Hierarchical navigation action handlers
    
    def on_expand_node(self, context):
        """Handle Ctrl+→ - expand current node"""
        if not self.is_hierarchical:
            return
        
        selected_ids = self.controller.get_selection() if hasattr(self.controller, 'get_selection') else []
        if len(selected_ids) == 1:
            selected_id = selected_ids[0]
            # Find the selected item
            selected_item = None
            for item in self.table.data_map:
                item_id = item.get('id') if isinstance(item, dict) else getattr(item, 'id', None)
                if item_id == selected_id:
                    selected_item = item
                    break
            
            if selected_item:
                # Check if it's a group/folder that can be expanded
                is_group = selected_item.get('is_group') if isinstance(selected_item, dict) else getattr(selected_item, 'is_group', False)
                if is_group:
                    self.drill_down_into_group(selected_id, selected_item)

    def on_collapse_node(self, context):
        """Handle Ctrl+← - collapse current node (go up one level)"""
        if not self.is_hierarchical:
            return
        self.go_up()

    def on_expand_all_children(self, context):
        """Handle Ctrl+Shift+→ - expand all children of current node"""
        if not self.is_hierarchical:
            return
        # For table-based hierarchical views, this might not be applicable
        # Could be implemented for tree views in the future
        pass

    def on_collapse_all_children(self, context):
        """Handle Ctrl+Shift+← - collapse all children of current node"""
        if not self.is_hierarchical:
            return
        # For table-based hierarchical views, this might not be applicable
        # Could be implemented for tree views in the future
        pass

    def on_go_to_first(self, context):
        """Handle Home - go to first item in current level"""
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
            self.table.scrollToTop()

    def on_go_to_last(self, context):
        """Handle End - go to last item in current level"""
        if self.table.rowCount() > 0:
            last_row = self.table.rowCount() - 1
            self.table.selectRow(last_row)
            self.table.scrollToBottom()

    def on_go_to_root(self, context):
        """Handle Ctrl+Home - go to root level"""
        if not self.is_hierarchical:
            return
        self.go_to_root()

    def on_go_to_last_in_hierarchy(self, context):
        """Handle Ctrl+End - go to last item in expanded hierarchy"""
        if not self.is_hierarchical:
            return
        # For table-based views, this is same as go to last in current level
        self.on_go_to_last(context)

    def on_page_up(self, context):
        """Handle Page Up - scroll up one page"""
        visible_rows = self.table.height() // self.table.rowHeight(0) if self.table.rowCount() > 0 else 10
        current_row = self.table.currentRow()
        new_row = max(0, current_row - visible_rows)
        if new_row != current_row:
            self.table.selectRow(new_row)
            self.table.scrollToItem(self.table.item(new_row, 0))

    def on_page_down(self, context):
        """Handle Page Down - scroll down one page"""
        visible_rows = self.table.height() // self.table.rowHeight(0) if self.table.rowCount() > 0 else 10
        current_row = self.table.currentRow()
        new_row = min(self.table.rowCount() - 1, current_row + visible_rows)
        if new_row != current_row:
            self.table.selectRow(new_row)
            self.table.scrollToItem(self.table.item(new_row, 0))

    # Hierarchical navigation methods (to be overridden by subclasses)
    
    def drill_down_into_group(self, group_id: int, group_item: Any):
        """
        Drill down into a group/folder.
        To be overridden by subclasses that support hierarchical navigation.
        
        Args:
            group_id: ID of the group to enter
            group_item: The group item data
        """
        # Default implementation for hierarchical forms
        if hasattr(self, 'enter_group'):
            group_name = group_item.get('name') if isinstance(group_item, dict) else getattr(group_item, 'name', f'Group {group_id}')
            self.enter_group(group_id, group_name)

    def go_to_root(self):
        """
        Navigate to root level.
        To be overridden by subclasses that support hierarchical navigation.
        """
        if self.current_parent_id is not None:
            self.current_parent_id = None
            self.navigation_path.clear()
            self.controller.set_filter('parent_id', None)
            if hasattr(self.filter_bar, 'set_navigation_state'):
                self.filter_bar.set_navigation_state(False, "Корень")

    def closeEvent(self, event):
        if hasattr(self, 'keyboard_handler'):
            self.keyboard_handler.cleanup()
        self.controller.close()
        super().closeEvent(event)
