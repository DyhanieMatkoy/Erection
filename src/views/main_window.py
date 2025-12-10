"""Main window"""
from PyQt6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QMdiArea, 
                              QDialog, QVBoxLayout, QLineEdit, QListWidget, 
                              QListWidgetItem, QLabel)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, pyqtSignal
from collections import deque


class QuickNavigationDialog(QDialog):
    """Quick navigation dialog for fast access to forms"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_action = None
        self.setup_ui()
        
        # Navigation items
        self.navigation_items = [
            ("Сметы", "open_estimates"),
            ("Ежедневные отчеты", "open_daily_reports"),
            ("Контрагенты", "open_counterparties"),
            ("Объекты", "open_objects"),
            ("Организации", "open_organizations"),
            ("Физические лица", "open_persons"),
            ("Виды работ", "open_works"),
            ("Выполнение работ", "open_work_execution_report"),
        ]
        
        self.populate_list()
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Быстрая навигация")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Введите название формы...")
        self.search_field.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_field)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)
        
        # Info label
        info_label = QLabel("Используйте стрелки для навигации, Enter для выбора")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # Set focus to search field
        self.search_field.setFocus()
    
    def populate_list(self, filter_text=""):
        """Populate list with navigation items"""
        self.list_widget.clear()
        
        for name, action in self.navigation_items:
            if filter_text.lower() in name.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, action)
                self.list_widget.addItem(item)
        
        # Select first item
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
    
    def filter_list(self, text):
        """Filter list based on search text"""
        self.populate_list(text)
    
    def on_item_selected(self, item):
        """Handle item selection"""
        self.selected_action = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_item_selected(current_item)
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recent_forms = deque(maxlen=10)  # Track recently opened forms
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Система управления рабочим временем")
        self.resize(1024, 768)
        
        # Create MDI area for managing multiple windows
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)  # Use tabbed view by default
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        self.setCentralWidget(self.mdi_area)
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Файл")
        
        quick_nav_action = QAction("Быстрая навигация", self)
        quick_nav_action.setShortcut(QKeySequence("Ctrl+K"))
        quick_nav_action.triggered.connect(self.show_quick_navigation)
        file_menu.addAction(quick_nav_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # References menu
        references_menu = menubar.addMenu("Справочники")
        
        counterparties_action = QAction("Контрагенты", self)
        counterparties_action.triggered.connect(self.open_counterparties)
        references_menu.addAction(counterparties_action)
        
        objects_action = QAction("Объекты", self)
        objects_action.triggered.connect(self.open_objects)
        references_menu.addAction(objects_action)
        
        organizations_action = QAction("Организации", self)
        organizations_action.triggered.connect(self.open_organizations)
        references_menu.addAction(organizations_action)
        
        persons_action = QAction("Физические лица", self)
        persons_action.triggered.connect(self.open_persons)
        references_menu.addAction(persons_action)
        
        works_action = QAction("Виды работ", self)
        works_action.triggered.connect(self.open_works)
        references_menu.addAction(works_action)
        
        # Documents menu
        documents_menu = menubar.addMenu("Документы")
        
        estimates_action = QAction("Сметы", self)
        estimates_action.triggered.connect(self.open_estimates)
        documents_menu.addAction(estimates_action)
        
        daily_reports_action = QAction("Ежедневные отчеты", self)
        daily_reports_action.triggered.connect(self.open_daily_reports)
        documents_menu.addAction(daily_reports_action)
        
        # Reports menu
        reports_menu = menubar.addMenu("Отчеты")
        
        work_execution_action = QAction("Выполнение работ", self)
        work_execution_action.triggered.connect(self.open_work_execution_report)
        reports_menu.addAction(work_execution_action)
        
        # Window menu
        self.window_menu = menubar.addMenu("Окна")
        
        cascade_action = QAction("Каскадом", self)
        cascade_action.triggered.connect(self.cascade_windows)
        self.window_menu.addAction(cascade_action)
        
        tile_action = QAction("Мозаикой", self)
        tile_action.triggered.connect(self.tile_windows)
        self.window_menu.addAction(tile_action)
        
        self.window_menu.addSeparator()
        
        tabbed_view_action = QAction("Вкладки", self)
        tabbed_view_action.setCheckable(True)
        tabbed_view_action.setChecked(True)
        tabbed_view_action.triggered.connect(self.toggle_view_mode)
        self.window_menu.addAction(tabbed_view_action)
        self.tabbed_view_action = tabbed_view_action
        
        self.window_menu.addSeparator()
        
        close_active_action = QAction("Закрыть активное окно", self)
        close_active_action.setShortcut(QKeySequence("Ctrl+W"))
        close_active_action.triggered.connect(self.close_active_window)
        self.window_menu.addAction(close_active_action)
        
        close_all_action = QAction("Закрыть все окна", self)
        close_all_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_all_action.triggered.connect(self.close_all_windows)
        self.window_menu.addAction(close_all_action)
        
        self.window_menu.addSeparator()
        
        # Recent forms submenu
        self.recent_menu = self.window_menu.addMenu("Недавние")
        self.update_recent_menu()
        
        # Settings menu
        settings_menu = menubar.addMenu("Настройки")
        
        # Create status bar
        statusbar = self.statusBar()
        statusbar.showMessage("Готов")
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Quick navigation
        quick_nav_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        quick_nav_shortcut.activated.connect(self.show_quick_navigation)
        
        # Window navigation
        next_window_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_window_shortcut.activated.connect(self.next_window)
        
        prev_window_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_window_shortcut.activated.connect(self.previous_window)
        
        # Close window
        close_window_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_window_shortcut.activated.connect(self.close_active_window)
    
    def show_quick_navigation(self):
        """Show quick navigation dialog"""
        dialog = QuickNavigationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_action:
            # Call the selected action
            if hasattr(self, dialog.selected_action):
                getattr(self, dialog.selected_action)()
    
    def add_to_recent(self, form_name, action_name):
        """Add form to recent list"""
        # Remove if already exists
        self.recent_forms = deque([item for item in self.recent_forms 
                                   if item[1] != action_name], maxlen=10)
        # Add to front
        self.recent_forms.appendleft((form_name, action_name))
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """Update recent forms menu"""
        self.recent_menu.clear()
        
        if not self.recent_forms:
            no_recent_action = QAction("Нет недавних форм", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
            return
        
        for form_name, action_name in self.recent_forms:
            action = QAction(form_name, self)
            action.triggered.connect(lambda checked, a=action_name: getattr(self, a)())
            self.recent_menu.addAction(action)
    
    def cascade_windows(self):
        """Arrange windows in cascade"""
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.cascadeSubWindows()
        self.tabbed_view_action.setChecked(False)
    
    def tile_windows(self):
        """Arrange windows in tile"""
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.tileSubWindows()
        self.tabbed_view_action.setChecked(False)
    
    def toggle_view_mode(self, checked):
        """Toggle between tabbed and subwindow view"""
        if checked:
            self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        else:
            self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
    
    def close_active_window(self):
        """Close active window"""
        active_window = self.mdi_area.activeSubWindow()
        if active_window:
            active_window.close()
    
    def close_all_windows(self):
        """Close all windows"""
        self.mdi_area.closeAllSubWindows()
    
    def next_window(self):
        """Activate next window"""
        self.mdi_area.activateNextSubWindow()
    
    def previous_window(self):
        """Activate previous window"""
        self.mdi_area.activatePreviousSubWindow()
    
    def open_estimates(self):
        """Open estimates list"""
        from .estimate_list_form import EstimateListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), EstimateListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Сметы", "open_estimates")
                return
        
        # Create new window
        form = EstimateListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Сметы", "open_estimates")
    
    def open_daily_reports(self):
        """Open daily reports list"""
        from .daily_report_list_form import DailyReportListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), DailyReportListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Ежедневные отчеты", "open_daily_reports")
                return
        
        # Create new window
        form = DailyReportListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Ежедневные отчеты", "open_daily_reports")
    
    def open_objects(self):
        """Open objects list"""
        from .object_list_form import ObjectListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), ObjectListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Объекты", "open_objects")
                return
        
        # Create new window
        form = ObjectListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Объекты", "open_objects")
    
    def open_organizations(self):
        """Open organizations list"""
        from .organization_list_form import OrganizationListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), OrganizationListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Организации", "open_organizations")
                return
        
        # Create new window
        form = OrganizationListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Организации", "open_organizations")
    
    def open_persons(self):
        """Open persons list"""
        from .person_list_form import PersonListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), PersonListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Физические лица", "open_persons")
                return
        
        # Create new window
        form = PersonListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Физические лица", "open_persons")
    
    def open_works(self):
        """Open works list"""
        from .work_list_form import WorkListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), WorkListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Виды работ", "open_works")
                return
        
        # Create new window
        form = WorkListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Виды работ", "open_works")
    
    def open_counterparties(self):
        """Open counterparties list"""
        from .counterparty_list_form import CounterpartyListForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), CounterpartyListForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Контрагенты", "open_counterparties")
                return
        
        # Create new window
        form = CounterpartyListForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Контрагенты", "open_counterparties")

    def open_work_execution_report(self):
        """Open work execution report"""
        from .work_execution_report_form import WorkExecutionReportForm
        
        # Check if already open
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), WorkExecutionReportForm):
                self.mdi_area.setActiveSubWindow(window)
                self.add_to_recent("Выполнение работ", "open_work_execution_report")
                return
        
        # Create new window
        form = WorkExecutionReportForm()
        sub_window = self.mdi_area.addSubWindow(form)
        sub_window.show()
        self.add_to_recent("Выполнение работ", "open_work_execution_report")
