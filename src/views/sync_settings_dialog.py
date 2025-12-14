"""Synchronization Settings Dialog

This module provides a dialog for configuring synchronization settings
in the desktop client application.
"""

import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QPushButton, QLabel, QGroupBox,
    QCheckBox, QTextEdit, QTabWidget, QWidget, QMessageBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from ..services.sync_service import SyncService

logger = logging.getLogger(__name__)


class SyncSettingsDialog(QDialog):
    """Dialog for configuring synchronization settings"""
    
    def __init__(self, sync_service: SyncService, parent=None):
        """Initialize sync settings dialog
        
        Args:
            sync_service: Sync service instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.sync_service = sync_service
        
        self.setWindowTitle("Synchronization Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_settings()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self._setup_connection_tab()
        self._setup_schedule_tab()
        self._setup_status_tab()
        self._setup_conflicts_tab()
        self._setup_advanced_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _setup_connection_tab(self):
        """Setup connection settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Server settings group
        server_group = QGroupBox("Server Connection")
        server_layout = QFormLayout(server_group)
        
        self.server_url_edit = QLineEdit()
        self.server_url_edit.setPlaceholderText("https://server.example.com")
        server_layout.addRow("Server URL:", self.server_url_edit)
        
        self.node_code_edit = QLineEdit()
        self.node_code_edit.setPlaceholderText("DESKTOP-USER-1")
        server_layout.addRow("Node Code:", self.node_code_edit)
        
        layout.addWidget(server_group)
        
        # Authentication info group
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout(auth_group)
        
        self.node_id_label = QLabel("Not registered")
        self.auth_token_label = QLabel("Not registered")
        auth_layout.addRow("Node ID:", self.node_id_label)
        auth_layout.addRow("Auth Token:", self.auth_token_label)
        
        # Register button
        self.register_btn = QPushButton("Register Node")
        self.register_btn.clicked.connect(self._register_node)
        auth_layout.addRow(self.register_btn)
        
        layout.addWidget(auth_group)
        
        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_connection_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Connection")
    
    def _setup_schedule_tab(self):
        """Setup schedule settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sync schedule group
        schedule_group = QGroupBox("Sync Schedule")
        schedule_layout = QFormLayout(schedule_group)
        
        self.auto_sync_check = QCheckBox("Enable automatic synchronization")
        schedule_layout.addRow(self.auto_sync_check)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setMinimum(60)  # 1 minute
        self.sync_interval_spin.setMaximum(3600)  # 1 hour
        self.sync_interval_spin.setSuffix(" seconds")
        schedule_layout.addRow("Sync Interval:", self.sync_interval_spin)
        
        layout.addWidget(schedule_group)
        
        # Retry settings group
        retry_group = QGroupBox("Retry Settings")
        retry_layout = QFormLayout(retry_group)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setMinimum(1)
        self.max_retries_spin.setMaximum(10)
        retry_layout.addRow("Max Retries:", self.max_retries_spin)
        
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setMinimum(30)
        self.retry_interval_spin.setMaximum(300)
        self.retry_interval_spin.setSuffix(" seconds")
        retry_layout.addRow("Retry Interval:", self.retry_interval_spin)
        
        layout.addWidget(retry_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Schedule")
    
    def _setup_status_tab(self):
        """Setup status tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Current status group
        status_group = QGroupBox("Current Status")
        status_layout = QFormLayout(status_group)
        
        self.status_label = QLabel("Unknown")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addRow("Status:", self.status_label)
        
        self.last_sync_label = QLabel("Never")
        status_layout.addRow("Last Sync:", self.last_sync_label)
        
        self.pending_changes_label = QLabel("0")
        status_layout.addRow("Pending Changes:", self.pending_changes_label)
        
        layout.addWidget(status_group)
        
        # Sync controls
        controls_group = QGroupBox("Sync Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        self.sync_now_btn = QPushButton("Sync Now")
        self.sync_now_btn.clicked.connect(self._sync_now)
        controls_layout.addWidget(self.sync_now_btn)
        
        self.export_btn = QPushButton("Export Pending Changes")
        self.export_btn.clicked.connect(self._export_changes)
        controls_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Changes")
        self.import_btn.clicked.connect(self._import_changes)
        controls_layout.addWidget(self.import_btn)
        
        layout.addWidget(controls_group)
        
        # Progress bar
        self.sync_progress = QProgressBar()
        self.sync_progress.setVisible(False)
        layout.addWidget(self.sync_progress)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Status")
    
    def _setup_conflicts_tab(self):
        """Setup conflicts tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Conflicts table
        self.conflicts_table = QTableWidget()
        self.conflicts_table.setColumnCount(5)
        self.conflicts_table.setHorizontalHeaderLabels([
            "Entity Type", "Entity UUID", "Source Node", "Arrival Time", "Resolution"
        ])
        
        # Configure table
        header = self.conflicts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.conflicts_table)
        
        # Conflict controls
        controls_layout = QHBoxLayout()
        
        self.refresh_conflicts_btn = QPushButton("Refresh")
        self.refresh_conflicts_btn.clicked.connect(self._refresh_conflicts)
        controls_layout.addWidget(self.refresh_conflicts_btn)
        
        self.resolve_conflict_btn = QPushButton("Resolve Selected")
        self.resolve_conflict_btn.clicked.connect(self._resolve_conflict)
        self.resolve_conflict_btn.setEnabled(False)
        controls_layout.addWidget(self.resolve_conflict_btn)
        
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(tab, "Conflicts")
    
    def _setup_advanced_tab(self):
        """Setup advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(10)
        self.batch_size_spin.setMaximum(1000)
        advanced_layout.addRow("Batch Size:", self.batch_size_spin)
        
        self.packet_timeout_spin = QSpinBox()
        self.packet_timeout_spin.setMinimum(60)
        self.packet_timeout_spin.setMaximum(600)
        self.packet_timeout_spin.setSuffix(" seconds")
        advanced_layout.addRow("Packet Timeout:", self.packet_timeout_spin)
        
        self.compression_check = QCheckBox("Enable compression")
        self.compression_check.setChecked(True)
        advanced_layout.addRow(self.compression_check)
        
        layout.addWidget(advanced_group)
        
        # Debug group
        debug_group = QGroupBox("Debug Information")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setReadOnly(True)
        debug_layout.addWidget(self.debug_text)
        
        self.clear_debug_btn = QPushButton("Clear Debug Log")
        self.clear_debug_btn.clicked.connect(self.debug_text.clear)
        debug_layout.addWidget(self.clear_debug_btn)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Advanced")
    
    def _connect_signals(self):
        """Connect signals from sync service"""
        self.sync_service.status_changed.connect(self._on_status_changed)
        self.sync_service.sync_started.connect(self._on_sync_started)
        self.sync_service.sync_completed.connect(self._on_sync_completed)
        self.sync_service.sync_failed.connect(self._on_sync_failed)
        self.sync_service.sync_progress.connect(self._on_sync_progress)
        self.sync_service.conflict_detected.connect(self._on_conflict_detected)
    
    def _load_settings(self):
        """Load current settings"""
        # Connection settings
        self.server_url_edit.setText(getattr(self.sync_service, 'server_url', ''))
        self.node_code_edit.setText(self.sync_service.node_code)
        
        # Update auth info
        if self.sync_service.node_id:
            self.node_id_label.setText(self.sync_service.node_id)
            self.auth_token_label.setText("Registered" if self.sync_service.auth_token else "No token")
            self.register_btn.setEnabled(False)
        else:
            self.node_id_label.setText("Not registered")
            self.auth_token_label.setText("Not registered")
            self.register_btn.setEnabled(True)
        
        # Schedule settings
        self.sync_interval_spin.setValue(self.sync_service.sync_interval)
        
        # Update status
        self._update_status_display()
    
    def _apply_settings(self):
        """Apply current settings"""
        # Update sync service
        self.sync_service.server_url = self.server_url_edit.text().strip()
        self.sync_service.node_code = self.node_code_edit.text().strip()
        self.sync_service.set_sync_interval(self.sync_interval_spin.value())
        
        # Save settings (would integrate with app settings)
        logger.info("Applied sync settings")
    
    @pyqtSlot()
    def _register_node(self):
        """Register node with server"""
        self.register_btn.setEnabled(False)
        self.register_btn.setText("Registering...")
        
        # This will trigger async registration
        self.sync_service._register_node()
    
    @pyqtSlot()
    def _test_connection(self):
        """Test connection to server"""
        server_url = self.server_url_edit.text().strip()
        if not server_url:
            QMessageBox.warning(self, "Warning", "Please enter a server URL")
            return
        
        # Simple test - try to reach server health endpoint
        try:
            import requests
            response = requests.get(f"{server_url}/api/health", timeout=10)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Connection test successful")
            else:
                QMessageBox.warning(self, "Warning", f"Server returned: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed: {str(e)}")
    
    @pyqtSlot()
    def _sync_now(self):
        """Trigger immediate sync"""
        if self.sync_service.sync_now():
            self.sync_now_btn.setEnabled(False)
            self.sync_progress.setVisible(True)
            self.sync_progress.setRange(0, 0)  # Indeterminate progress
    
    @pyqtSlot()
    def _export_changes(self):
        """Export pending changes to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Changes", "sync_changes.json", "JSON Files (*.json)"
        )
        
        if filename:
            if self.sync_service.export_pending_changes(filename):
                QMessageBox.information(self, "Success", f"Changes exported to {filename}")
            else:
                QMessageBox.warning(self, "Warning", "Failed to export changes")
    
    @pyqtSlot()
    def _import_changes(self):
        """Import changes from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Changes", "", "JSON Files (*.json)"
        )
        
        if filename:
            if self.sync_service.import_changes(filename):
                QMessageBox.information(self, "Success", f"Changes imported from {filename}")
                # Trigger sync to apply imported changes
                self.sync_service.sync_now()
            else:
                QMessageBox.warning(self, "Warning", "Failed to import changes")
    
    @pyqtSlot()
    def _refresh_conflicts(self):
        """Refresh conflicts table"""
        # TODO: Implement conflict refresh
        self.conflicts_table.setRowCount(0)
    
    @pyqtSlot()
    def _resolve_conflict(self):
        """Resolve selected conflict"""
        # TODO: Implement conflict resolution dialog
        QMessageBox.information(self, "Info", "Conflict resolution not implemented yet")
    
    @pyqtSlot(str)
    def _on_status_changed(self, status):
        """Handle status change"""
        self._update_status_display()
    
    @pyqtSlot()
    def _on_sync_started(self):
        """Handle sync started"""
        self.sync_now_btn.setEnabled(False)
        self.sync_progress.setVisible(True)
        self.sync_progress.setRange(0, 0)  # Indeterminate progress
        self.debug_text.append("Sync started")
    
    @pyqtSlot(dict)
    def _on_sync_completed(self, result):
        """Handle sync completed"""
        self.sync_now_btn.setEnabled(True)
        self.sync_progress.setVisible(False)
        self._update_status_display()
        
        processed = result.get('processed_count', 0)
        errors = result.get('error_count', 0)
        
        self.debug_text.append(f"Sync completed: {processed} processed, {errors} errors")
    
    @pyqtSlot(str)
    def _on_sync_failed(self, error):
        """Handle sync failed"""
        self.sync_now_btn.setEnabled(True)
        self.sync_progress.setVisible(False)
        self.debug_text.append(f"Sync failed: {error}")
    
    @pyqtSlot(int, int)
    def _on_sync_progress(self, current, total):
        """Handle sync progress"""
        self.sync_progress.setVisible(True)
        self.sync_progress.setRange(0, total)
        self.sync_progress.setValue(current)
    
    @pyqtSlot(dict)
    def _on_conflict_detected(self, conflict):
        """Handle conflict detected"""
        self.debug_text.append(f"Conflict detected: {conflict['entity_type']} {conflict['entity_uuid']}")
        self._refresh_conflicts()
    
    def _update_status_display(self):
        """Update status display"""
        status = self.sync_service.get_sync_status()
        
        # Update status label
        self.status_label.setText(status['status'].title())
        
        # Update last sync
        if status['last_sync_time']:
            self.last_sync_label.setText(status['last_sync_time'])
        else:
            self.last_sync_label.setText("Never")
        
        # Update pending changes
        self.pending_changes_label.setText(str(status['pending_changes']))
        
        # Update registration info
        if status['is_registered']:
            self.node_id_label.setText(status['node_id'])
            self.auth_token_label.setText("Registered")
            self.register_btn.setEnabled(False)
        else:
            self.node_id_label.setText("Not registered")
            self.auth_token_label.setText("Not registered")
            self.register_btn.setEnabled(True)
    
    def accept(self):
        """Handle dialog acceptance"""
        self._apply_settings()
        super().accept()