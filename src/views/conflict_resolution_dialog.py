"""Conflict Resolution Dialog

This dialog allows users to manually resolve synchronization conflicts
by choosing between different versions of conflicted data.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QSplitter, QGroupBox, QFormLayout,
    QMessageBox, QHeaderView, QAbstractItemView,
    QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette


class ConflictDetailsWidget(QWidget):
    """Widget for displaying conflict details"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        
        # Entity info group
        entity_group = QGroupBox("Информация об объекте")
        entity_layout = QFormLayout()
        
        self.entity_type_label = QLabel("-")
        entity_layout.addRow("Тип объекта:", self.entity_type_label)
        
        self.entity_uuid_label = QLabel("-")
        entity_layout.addRow("UUID:", self.entity_uuid_label)
        
        self.conflict_time_label = QLabel("-")
        entity_layout.addRow("Время конфликта:", self.conflict_time_label)
        
        self.source_node_label = QLabel("-")
        entity_layout.addRow("Источник:", self.source_node_label)
        
        entity_group.setLayout(entity_layout)
        layout.addWidget(entity_group)
        
        # Versions comparison
        versions_group = QGroupBox("Сравнение версий")
        versions_layout = QVBoxLayout()
        
        # Version selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Выберите версию для просмотра:"))
        
        self.version_combo = QComboBox()
        self.version_combo.currentTextChanged.connect(self.on_version_changed)
        selector_layout.addWidget(self.version_combo)
        
        selector_layout.addStretch()
        versions_layout.addLayout(selector_layout)
        
        # Version data display
        self.version_text = QTextEdit()
        self.version_text.setReadOnly(True)
        self.version_text.setMaximumHeight(200)
        versions_layout.addWidget(self.version_text)
        
        versions_group.setLayout(versions_layout)
        layout.addWidget(versions_group)
        
        # Resolution controls
        resolution_group = QGroupBox("Разрешение конфликта")
        resolution_layout = QVBoxLayout()
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "Использовать версию сервера",
            "Использовать локальную версию",
            "Объединить изменения",
            "Пропустить (разрешить позже)"
        ])
        resolution_layout.addWidget(self.resolution_combo)
        
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Store conflict data
        self.conflict_data = None
        self.versions = {}
    
    def set_conflict(self, conflict_data: Dict[str, Any]):
        """Set conflict data to display"""
        self.conflict_data = conflict_data
        
        # Update entity info
        self.entity_type_label.setText(conflict_data.get('entity_type', '-'))
        self.entity_uuid_label.setText(conflict_data.get('entity_uuid', '-'))
        
        arrival_time = conflict_data.get('arrival_time', '')
        if arrival_time:
            try:
                dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
                self.conflict_time_label.setText(dt.strftime('%d.%m.%Y %H:%M:%S'))
            except:
                self.conflict_time_label.setText(arrival_time)
        else:
            self.conflict_time_label.setText('-')
        
        self.source_node_label.setText(conflict_data.get('source_node_id', '-'))
        
        # Parse serialized data to get versions
        self.versions = {}
        serialized_data = conflict_data.get('serialized_data', '{}')
        
        try:
            data = json.loads(serialized_data) if isinstance(serialized_data, str) else serialized_data
            
            # Extract different versions
            if 'server_version' in data:
                self.versions['Версия сервера'] = data['server_version']
            if 'local_version' in data:
                self.versions['Локальная версия'] = data['local_version']
            if 'incoming_version' in data:
                self.versions['Входящая версия'] = data['incoming_version']
            
            # If no specific versions, use the data itself
            if not self.versions:
                self.versions['Данные конфликта'] = data
                
        except Exception as e:
            self.versions['Ошибка парсинга'] = f"Не удалось разобрать данные: {str(e)}"
        
        # Update version combo
        self.version_combo.clear()
        self.version_combo.addItems(list(self.versions.keys()))
        
        # Show first version
        if self.versions:
            self.on_version_changed(list(self.versions.keys())[0])
    
    def on_version_changed(self, version_name: str):
        """Handle version selection change"""
        if version_name in self.versions:
            version_data = self.versions[version_name]
            
            # Format data for display
            if isinstance(version_data, dict):
                formatted_data = json.dumps(version_data, indent=2, ensure_ascii=False)
            else:
                formatted_data = str(version_data)
            
            self.version_text.setText(formatted_data)
    
    def get_resolution(self) -> str:
        """Get selected resolution strategy"""
        return self.resolution_combo.currentText()


class ConflictResolutionDialog(QDialog):
    """Dialog for resolving synchronization conflicts"""
    
    conflicts_resolved = pyqtSignal(int)  # Number of conflicts resolved
    
    def __init__(self, sync_service, parent=None):
        super().__init__(parent)
        self.sync_service = sync_service
        self.conflicts = []
        self.current_conflict_index = -1
        
        self.setup_ui()
        self.load_conflicts()
        
        # Auto-refresh conflicts
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_conflicts)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Разрешение конфликтов синхронизации")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Конфликты синхронизации")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_conflicts)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - conflicts list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Conflicts table
        conflicts_label = QLabel("Список конфликтов:")
        left_layout.addWidget(conflicts_label)
        
        self.conflicts_table = QTableWidget()
        self.conflicts_table.setColumnCount(4)
        self.conflicts_table.setHorizontalHeaderLabels([
            "Тип объекта", "Время", "Источник", "Статус"
        ])
        
        # Configure table
        header = self.conflicts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.conflicts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.conflicts_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.conflicts_table.itemSelectionChanged.connect(self.on_conflict_selected)
        
        left_layout.addWidget(self.conflicts_table)
        
        # Bulk actions
        bulk_layout = QHBoxLayout()
        
        self.resolve_all_server_button = QPushButton("Все → Сервер")
        self.resolve_all_server_button.clicked.connect(self.resolve_all_server)
        bulk_layout.addWidget(self.resolve_all_server_button)
        
        self.resolve_all_local_button = QPushButton("Все → Локально")
        self.resolve_all_local_button.clicked.connect(self.resolve_all_local)
        bulk_layout.addWidget(self.resolve_all_local_button)
        
        left_layout.addLayout(bulk_layout)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel - conflict details
        self.details_widget = ConflictDetailsWidget()
        splitter.addWidget(self.details_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.resolve_button = QPushButton("Разрешить выбранный")
        self.resolve_button.clicked.connect(self.resolve_current_conflict)
        self.resolve_button.setEnabled(False)
        button_layout.addWidget(self.resolve_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_conflicts(self):
        """Load conflicts from sync service"""
        try:
            # Get unresolved conflicts
            conflicts = self.sync_service.conflict_resolver.get_unresolved_conflicts()
            
            self.conflicts = []
            for conflict in conflicts:
                conflict_data = {
                    'id': str(conflict.id),
                    'entity_type': conflict.entity_type,
                    'entity_uuid': str(conflict.entity_uuid),
                    'source_node_id': str(conflict.source_node_id),
                    'arrival_time': conflict.arrival_time.isoformat(),
                    'conflict_resolution': conflict.conflict_resolution,
                    'serialized_data': conflict.serialized_data
                }
                self.conflicts.append(conflict_data)
            
            self.update_conflicts_table()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить конфликты: {str(e)}")
    
    def update_conflicts_table(self):
        """Update conflicts table"""
        self.conflicts_table.setRowCount(len(self.conflicts))
        
        for row, conflict in enumerate(self.conflicts):
            # Entity type
            self.conflicts_table.setItem(row, 0, QTableWidgetItem(conflict['entity_type']))
            
            # Time
            arrival_time = conflict['arrival_time']
            try:
                dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%d.%m %H:%M')
            except:
                time_str = arrival_time[:16]  # Fallback
            
            self.conflicts_table.setItem(row, 1, QTableWidgetItem(time_str))
            
            # Source
            source = conflict['source_node_id']
            if len(source) > 20:
                source = source[:17] + "..."
            self.conflicts_table.setItem(row, 2, QTableWidgetItem(source))
            
            # Status
            resolution = conflict.get('conflict_resolution', 'pending')
            status_item = QTableWidgetItem(resolution)
            
            if resolution == 'pending':
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            elif resolution == 'resolved':
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            
            self.conflicts_table.setItem(row, 3, status_item)
        
        # Update status
        if self.conflicts:
            pending_count = sum(1 for c in self.conflicts if c.get('conflict_resolution', 'pending') == 'pending')
            self.setWindowTitle(f"Разрешение конфликтов синхронизации ({pending_count} ожидают)")
        else:
            self.setWindowTitle("Разрешение конфликтов синхронизации (нет конфликтов)")
    
    def on_conflict_selected(self):
        """Handle conflict selection"""
        selected_rows = self.conflicts_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.conflicts):
                self.current_conflict_index = row
                conflict = self.conflicts[row]
                
                # Show conflict details
                self.details_widget.set_conflict(conflict)
                self.resolve_button.setEnabled(True)
            else:
                self.current_conflict_index = -1
                self.resolve_button.setEnabled(False)
        else:
            self.current_conflict_index = -1
            self.resolve_button.setEnabled(False)
    
    def resolve_current_conflict(self):
        """Resolve currently selected conflict"""
        if self.current_conflict_index < 0:
            return
        
        conflict = self.conflicts[self.current_conflict_index]
        resolution_strategy = self.details_widget.get_resolution()
        
        try:
            # Map resolution strategy to action
            if "сервера" in resolution_strategy:
                resolution_data = self._get_server_version(conflict)
                success = self.sync_service.resolve_conflict(
                    conflict['id'], resolution_data
                )
            elif "локальную" in resolution_strategy:
                resolution_data = self._get_local_version(conflict)
                success = self.sync_service.resolve_conflict(
                    conflict['id'], resolution_data
                )
            elif "Объединить" in resolution_strategy:
                # For now, use server version (could implement merge logic)
                resolution_data = self._get_server_version(conflict)
                success = self.sync_service.resolve_conflict(
                    conflict['id'], resolution_data
                )
            else:  # Skip
                QMessageBox.information(self, "Информация", "Конфликт пропущен")
                return
            
            if success:
                QMessageBox.information(self, "Успех", "Конфликт разрешен успешно!")
                self.load_conflicts()  # Refresh list
                self.conflicts_resolved.emit(1)
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось разрешить конфликт")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при разрешении конфликта: {str(e)}")
    
    def resolve_all_server(self):
        """Resolve all conflicts using server version"""
        if not self.conflicts:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Разрешить все {len(self.conflicts)} конфликтов в пользу сервера?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            resolved_count = 0
            
            for conflict in self.conflicts:
                try:
                    resolution_data = self._get_server_version(conflict)
                    if self.sync_service.resolve_conflict(conflict['id'], resolution_data):
                        resolved_count += 1
                except Exception as e:
                    print(f"Error resolving conflict {conflict['id']}: {e}")
            
            QMessageBox.information(
                self, "Результат",
                f"Разрешено конфликтов: {resolved_count} из {len(self.conflicts)}"
            )
            
            self.load_conflicts()  # Refresh list
            self.conflicts_resolved.emit(resolved_count)
    
    def resolve_all_local(self):
        """Resolve all conflicts using local version"""
        if not self.conflicts:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Разрешить все {len(self.conflicts)} конфликтов в пользу локальной версии?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            resolved_count = 0
            
            for conflict in self.conflicts:
                try:
                    resolution_data = self._get_local_version(conflict)
                    if self.sync_service.resolve_conflict(conflict['id'], resolution_data):
                        resolved_count += 1
                except Exception as e:
                    print(f"Error resolving conflict {conflict['id']}: {e}")
            
            QMessageBox.information(
                self, "Результат",
                f"Разрешено конфликтов: {resolved_count} из {len(self.conflicts)}"
            )
            
            self.load_conflicts()  # Refresh list
            self.conflicts_resolved.emit(resolved_count)
    
    def _get_server_version(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract server version from conflict data"""
        try:
            serialized_data = conflict.get('serialized_data', '{}')
            data = json.loads(serialized_data) if isinstance(serialized_data, str) else serialized_data
            
            if 'server_version' in data:
                return data['server_version']
            elif 'incoming_version' in data:
                return data['incoming_version']
            else:
                return data  # Fallback to raw data
                
        except Exception:
            return {}  # Empty data as fallback
    
    def _get_local_version(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract local version from conflict data"""
        try:
            serialized_data = conflict.get('serialized_data', '{}')
            data = json.loads(serialized_data) if isinstance(serialized_data, str) else serialized_data
            
            if 'local_version' in data:
                return data['local_version']
            else:
                return data  # Fallback to raw data
                
        except Exception:
            return {}  # Empty data as fallback
    
    def closeEvent(self, event):
        """Handle dialog close"""
        self.refresh_timer.stop()
        super().closeEvent(event)