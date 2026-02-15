"""Synchronization Settings Dialog

This dialog allows users to configure synchronization settings
including server connection, node registration, and sync schedule.
"""

import os
import configparser
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QGroupBox, QFormLayout, QTextEdit, QProgressBar,
    QMessageBox, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QIcon


class SyncTestThread(QThread):
    """Thread for testing sync connection"""
    
    test_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, sync_service, server_url, node_code):
        super().__init__()
        self.sync_service = sync_service
        self.server_url = server_url
        self.node_code = node_code
    
    def run(self):
        """Test connection to sync server"""
        try:
            # Temporarily update sync service settings
            old_url = self.sync_service.server_url
            old_code = self.sync_service.node_code
            
            self.sync_service.server_url = self.server_url
            self.sync_service.node_code = self.node_code
            
            # Try to register node (this tests connectivity)
            self.sync_service._register_node()
            
            # Restore old settings
            self.sync_service.server_url = old_url
            self.sync_service.node_code = old_code
            
            self.test_completed.emit(True, "Подключение успешно!")
            
        except Exception as e:
            self.test_completed.emit(False, f"Ошибка подключения: {str(e)}")


class SyncSettingsDialog(QDialog):
    """Synchronization settings dialog"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, sync_service, parent=None):
        super().__init__(parent)
        self.sync_service = sync_service
        self.test_thread = None
        
        self.setup_ui()
        self.load_settings()
        self.setup_connections()
        
        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Настройки синхронизации")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Connection tab
        self.connection_tab = self.create_connection_tab()
        self.tab_widget.addTab(self.connection_tab, "Подключение")
        
        # Schedule tab
        self.schedule_tab = self.create_schedule_tab()
        self.tab_widget.addTab(self.schedule_tab, "Расписание")
        
        # Status tab
        self.status_tab = self.create_status_tab()
        self.tab_widget.addTab(self.status_tab, "Статус")
        
        # Advanced tab
        self.advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "Дополнительно")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Проверить подключение")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        self.diagnostics_button = QPushButton("Диагностика сети")
        self.diagnostics_button.clicked.connect(self.show_network_diagnostics)
        button_layout.addWidget(self.diagnostics_button)
        
        self.force_reconnect_button = QPushButton("Переподключиться")
        self.force_reconnect_button.clicked.connect(self.force_reconnect)
        button_layout.addWidget(self.force_reconnect_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_connection_tab(self) -> QWidget:
        """Create connection settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Server connection group
        server_group = QGroupBox("Настройки сервера")
        server_layout = QFormLayout()
        
        self.server_url_edit = QLineEdit()
        self.server_url_edit.setPlaceholderText("https://your-server.com")
        server_layout.addRow("URL сервера:", self.server_url_edit)
        
        self.node_code_edit = QLineEdit()
        self.node_code_edit.setPlaceholderText("DESKTOP-USER-1")
        server_layout.addRow("Код узла:", self.node_code_edit)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Authentication group
        auth_group = QGroupBox("Аутентификация")
        auth_layout = QFormLayout()
        
        self.auth_token_edit = QLineEdit()
        self.auth_token_edit.setReadOnly(True)
        self.auth_token_edit.setPlaceholderText("Токен будет получен автоматически")
        auth_layout.addRow("Токен:", self.auth_token_edit)
        
        self.register_button = QPushButton("Зарегистрировать узел")
        self.register_button.clicked.connect(self.register_node)
        auth_layout.addRow("", self.register_button)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Connection status
        self.connection_status_label = QLabel("Статус: Не подключен")
        self.connection_status_label.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.connection_status_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_schedule_tab(self) -> QWidget:
        """Create schedule settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Auto sync group
        auto_sync_group = QGroupBox("Автоматическая синхронизация")
        auto_sync_layout = QFormLayout()
        
        self.auto_sync_checkbox = QCheckBox("Включить автоматическую синхронизацию")
        auto_sync_layout.addRow(self.auto_sync_checkbox)
        
        self.sync_interval_spinbox = QSpinBox()
        self.sync_interval_spinbox.setMinimum(1)
        self.sync_interval_spinbox.setMaximum(1440)  # Max 24 hours
        self.sync_interval_spinbox.setValue(5)
        self.sync_interval_spinbox.setSuffix(" мин")
        auto_sync_layout.addRow("Интервал синхронизации:", self.sync_interval_spinbox)
        
        auto_sync_group.setLayout(auto_sync_layout)
        layout.addWidget(auto_sync_group)
        
        # Manual sync group
        manual_sync_group = QGroupBox("Ручная синхронизация")
        manual_sync_layout = QVBoxLayout()
        
        self.sync_now_button = QPushButton("Синхронизировать сейчас")
        self.sync_now_button.clicked.connect(self.sync_now)
        manual_sync_layout.addWidget(self.sync_now_button)
        
        self.sync_progress = QProgressBar()
        self.sync_progress.setVisible(False)
        manual_sync_layout.addWidget(self.sync_progress)
        
        manual_sync_group.setLayout(manual_sync_layout)
        layout.addWidget(manual_sync_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Create status information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Current status group
        status_group = QGroupBox("Текущий статус")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("Не подключен")
        status_layout.addRow("Статус:", self.status_label)
        
        self.last_sync_label = QLabel("Никогда")
        status_layout.addRow("Последняя синхронизация:", self.last_sync_label)
        
        self.pending_changes_label = QLabel("0")
        status_layout.addRow("Ожидающих изменений:", self.pending_changes_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Statistics group
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        self.refresh_stats_button = QPushButton("Обновить статистику")
        self.refresh_stats_button.clicked.connect(self.refresh_statistics)
        stats_layout.addWidget(self.refresh_stats_button)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Conflict resolution group
        conflict_group = QGroupBox("Разрешение конфликтов")
        conflict_layout = QFormLayout()
        
        self.conflict_strategy_combo = QComboBox()
        self.conflict_strategy_combo.addItems([
            "Приоритет сервера",
            "Приоритет времени изменения",
            "Ручное разрешение"
        ])
        conflict_layout.addRow("Стратегия разрешения:", self.conflict_strategy_combo)
        
        self.version_history_checkbox = QCheckBox("Сохранять историю версий")
        conflict_layout.addRow(self.version_history_checkbox)
        
        conflict_group.setLayout(conflict_layout)
        layout.addWidget(conflict_group)
        
        # Performance group
        performance_group = QGroupBox("Производительность")
        performance_layout = QFormLayout()
        
        self.compression_checkbox = QCheckBox("Включить сжатие данных")
        performance_layout.addRow(self.compression_checkbox)
        
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setMinimum(10)
        self.batch_size_spinbox.setMaximum(1000)
        self.batch_size_spinbox.setValue(100)
        performance_layout.addRow("Размер пакета:", self.batch_size_spinbox)
        
        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)
        
        # Debug group
        debug_group = QGroupBox("Отладка")
        debug_layout = QFormLayout()
        
        self.debug_logging_checkbox = QCheckBox("Включить отладочное логирование")
        debug_layout.addRow(self.debug_logging_checkbox)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ERROR", "WARNING", "INFO", "DEBUG"])
        debug_layout.addRow("Уровень логирования:", self.log_level_combo)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        # Enable/disable sync interval based on auto sync checkbox
        self.auto_sync_checkbox.toggled.connect(
            self.sync_interval_spinbox.setEnabled
        )
        
        # Connect sync service signals
        self.sync_service.sync_started.connect(self.on_sync_started)
        self.sync_service.sync_completed.connect(self.on_sync_completed)
        self.sync_service.sync_failed.connect(self.on_sync_failed)
        self.sync_service.status_changed.connect(self.update_status)
    
    def load_settings(self):
        """Load settings from configuration"""
        try:
            # Load from env.ini file
            config_path = "env.ini"
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path)
                
                if 'Sync' in config:
                    sync_config = config['Sync']
                    
                    self.server_url_edit.setText(
                        sync_config.get('server_url', 'http://localhost:8000')
                    )
                    self.node_code_edit.setText(
                        sync_config.get('node_code', 'DESKTOP-CLIENT')
                    )
                    self.auth_token_edit.setText(
                        sync_config.get('auth_token', '')
                    )
                    
                    self.auto_sync_checkbox.setChecked(
                        sync_config.getboolean('auto_sync', True)
                    )
                    self.sync_interval_spinbox.setValue(
                        sync_config.getint('sync_interval', 300) // 60  # Convert to minutes
                    )
                    
                    self.compression_checkbox.setChecked(
                        sync_config.getboolean('compression_enabled', True)
                    )
                    self.version_history_checkbox.setChecked(
                        sync_config.getboolean('version_history', True)
                    )
                    self.debug_logging_checkbox.setChecked(
                        sync_config.getboolean('debug_logging', False)
                    )
                    
                    # Set conflict resolution strategy
                    strategy = sync_config.get('conflict_resolution', 'server_wins')
                    if strategy == 'server_wins':
                        self.conflict_strategy_combo.setCurrentIndex(0)
                    elif strategy == 'timestamp_wins':
                        self.conflict_strategy_combo.setCurrentIndex(1)
                    else:
                        self.conflict_strategy_combo.setCurrentIndex(2)
                    
                    self.batch_size_spinbox.setValue(
                        sync_config.getint('batch_size', 100)
                    )
                    
                    log_level = sync_config.get('log_level', 'INFO')
                    self.log_level_combo.setCurrentText(log_level)
            
            # Update sync interval enabled state
            self.sync_interval_spinbox.setEnabled(self.auto_sync_checkbox.isChecked())
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить настройки: {str(e)}")
    
    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Load existing config
            config_path = "env.ini"
            config = configparser.ConfigParser()
            if os.path.exists(config_path):
                config.read(config_path)
            
            # Ensure Sync section exists
            if 'Sync' not in config:
                config.add_section('Sync')
            
            # Update sync settings
            sync_config = config['Sync']
            sync_config['enabled'] = 'true'
            sync_config['server_url'] = self.server_url_edit.text().strip()
            sync_config['node_code'] = self.node_code_edit.text().strip()
            sync_config['auth_token'] = self.auth_token_edit.text().strip()
            sync_config['auto_sync'] = str(self.auto_sync_checkbox.isChecked()).lower()
            sync_config['sync_interval'] = str(self.sync_interval_spinbox.value() * 60)  # Convert to seconds
            sync_config['compression_enabled'] = str(self.compression_checkbox.isChecked()).lower()
            sync_config['version_history'] = str(self.version_history_checkbox.isChecked()).lower()
            sync_config['debug_logging'] = str(self.debug_logging_checkbox.isChecked()).lower()
            sync_config['batch_size'] = str(self.batch_size_spinbox.value())
            sync_config['log_level'] = self.log_level_combo.currentText()
            
            # Set conflict resolution strategy
            strategy_index = self.conflict_strategy_combo.currentIndex()
            if strategy_index == 0:
                sync_config['conflict_resolution'] = 'server_wins'
            elif strategy_index == 1:
                sync_config['conflict_resolution'] = 'timestamp_wins'
            else:
                sync_config['conflict_resolution'] = 'manual'
            
            # Save config
            with open(config_path, 'w') as f:
                config.write(f)
            
            # Update sync service settings
            self.sync_service.server_url = self.server_url_edit.text().strip()
            self.sync_service.node_code = self.node_code_edit.text().strip()
            self.sync_service.auth_token = self.auth_token_edit.text().strip()
            self.sync_service.set_sync_interval(self.sync_interval_spinbox.value() * 60)
            
            # Emit settings changed signal
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Успех", "Настройки сохранены успешно!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {str(e)}")
    
    def test_connection(self):
        """Test connection to sync server"""
        server_url = self.server_url_edit.text().strip()
        node_code = self.node_code_edit.text().strip()
        
        if not server_url or not node_code:
            QMessageBox.warning(self, "Ошибка", "Заполните URL сервера и код узла")
            return
        
        # Disable test button and show progress
        self.test_button.setEnabled(False)
        self.test_button.setText("Проверка...")
        
        # Start test thread
        self.test_thread = SyncTestThread(self.sync_service, server_url, node_code)
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()
    
    def on_test_completed(self, success: bool, message: str):
        """Handle test completion"""
        self.test_button.setEnabled(True)
        self.test_button.setText("Проверить подключение")
        
        if success:
            QMessageBox.information(self, "Тест подключения", message)
            self.connection_status_label.setText("Статус: Подключен")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            QMessageBox.warning(self, "Тест подключения", message)
            self.connection_status_label.setText("Статус: Ошибка подключения")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def register_node(self):
        """Register node with server"""
        try:
            server_url = self.server_url_edit.text().strip()
            node_code = self.node_code_edit.text().strip()
            
            if not server_url or not node_code:
                QMessageBox.warning(self, "Ошибка", "Заполните URL сервера и код узла")
                return
            
            # Update sync service settings temporarily
            old_url = self.sync_service.server_url
            old_code = self.sync_service.node_code
            
            self.sync_service.server_url = server_url
            self.sync_service.node_code = node_code
            
            # Register node
            self.sync_service._register_node()
            
            # Update auth token field
            if self.sync_service.auth_token:
                self.auth_token_edit.setText(self.sync_service.auth_token)
                QMessageBox.information(self, "Успех", "Узел зарегистрирован успешно!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить токен аутентификации")
                # Restore old settings
                self.sync_service.server_url = old_url
                self.sync_service.node_code = old_code
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось зарегистрировать узел: {str(e)}")
    
    def sync_now(self):
        """Trigger immediate synchronization"""
        if not self.sync_service.sync_now():
            QMessageBox.warning(self, "Ошибка", "Не удалось запустить синхронизацию")
    
    def on_sync_started(self):
        """Handle sync started"""
        self.sync_progress.setVisible(True)
        self.sync_progress.setRange(0, 0)  # Indeterminate progress
        self.sync_now_button.setEnabled(False)
        self.sync_now_button.setText("Синхронизация...")
    
    def on_sync_completed(self, result):
        """Handle sync completed"""
        self.sync_progress.setVisible(False)
        self.sync_now_button.setEnabled(True)
        self.sync_now_button.setText("Синхронизировать сейчас")
        
        processed = result.get('processed_count', 0)
        errors = result.get('error_count', 0)
        
        if errors == 0:
            QMessageBox.information(
                self, "Синхронизация завершена", 
                f"Обработано записей: {processed}"
            )
        else:
            QMessageBox.warning(
                self, "Синхронизация завершена с ошибками",
                f"Обработано записей: {processed}\nОшибок: {errors}"
            )
    
    def on_sync_failed(self, error):
        """Handle sync failed"""
        self.sync_progress.setVisible(False)
        self.sync_now_button.setEnabled(True)
        self.sync_now_button.setText("Синхронизировать сейчас")
        
        QMessageBox.critical(self, "Ошибка синхронизации", error)
    
    def update_status(self):
        """Update status information"""
        try:
            status = self.sync_service.get_sync_status()
            
            # Update status label
            status_text = status.get('status', 'Unknown').title()
            if status.get('is_registered', False):
                if status_text == 'Online':
                    self.status_label.setText("Онлайн")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                elif status_text == 'Syncing':
                    self.status_label.setText("Синхронизация")
                    self.status_label.setStyleSheet("color: blue; font-weight: bold;")
                else:
                    self.status_label.setText("Офлайн")
                    self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.status_label.setText("Не зарегистрирован")
                self.status_label.setStyleSheet("color: gray; font-weight: bold;")
            
            # Update last sync time
            last_sync = status.get('last_sync_time')
            if last_sync:
                self.last_sync_label.setText(last_sync)
            else:
                self.last_sync_label.setText("Никогда")
            
            # Update pending changes
            pending = status.get('pending_changes', 0)
            self.pending_changes_label.setText(str(pending))
            
        except Exception as e:
            self.status_label.setText("Ошибка")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def refresh_statistics(self):
        """Refresh synchronization statistics"""
        try:
            status = self.sync_service.get_sync_status()
            
            stats_text = f"""Узел: {status.get('node_code', 'Не задан')}
ID узла: {status.get('node_id', 'Не зарегистрирован')}
Статус: {status.get('status', 'Неизвестен')}
Последняя синхронизация: {status.get('last_sync_time', 'Никогда')}
Ожидающих изменений: {status.get('pending_changes', 0)}
Зарегистрирован: {'Да' if status.get('is_registered', False) else 'Нет'}"""
            
            self.stats_text.setText(stats_text)
            
        except Exception as e:
            self.stats_text.setText(f"Ошибка получения статистики: {str(e)}")
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        
        self.status_timer.stop()
        super().closeEvent(event)
    
    def show_network_diagnostics(self):
        """Show network diagnostics dialog"""
        if not self.sync_service:
            QMessageBox.warning(self, "Ошибка", "Сервис синхронизации недоступен")
            return
        
        try:
            diagnostics = self.sync_service.get_network_diagnostics()
            
            # Format diagnostics for display
            info_lines = [
                f"URL сервера: {diagnostics.get('server_url', 'Не задан')}",
                f"Статус: {'Онлайн' if diagnostics.get('is_online') else 'Офлайн'}",
                f"Синхронизация: {'Выполняется' if diagnostics.get('is_syncing') else 'Не выполняется'}",
                f"Узел зарегистрирован: {'Да' if diagnostics.get('node_registered') else 'Нет'}",
                "",
                f"Попытки переподключения: {diagnostics.get('retry_count', 0)} из {diagnostics.get('max_retries', 0)}",
                f"Интервал повтора: {diagnostics.get('current_retry_interval', 0):.1f} сек",
                "",
                f"Тест подключения: {diagnostics.get('connectivity_test', 'Не выполнен')}",
            ]
            
            if diagnostics.get('response_time_ms'):
                info_lines.append(f"Время отклика: {diagnostics.get('response_time_ms')} мс")
            
            if diagnostics.get('server_status_code'):
                info_lines.append(f"Код ответа сервера: {diagnostics.get('server_status_code')}")
            
            if diagnostics.get('error'):
                info_lines.append(f"Ошибка: {diagnostics.get('error')}")
            
            if diagnostics.get('last_sync_time'):
                info_lines.append(f"Последняя синхронизация: {diagnostics.get('last_sync_time')}")
            
            info_text = "\n".join(info_lines)
            
            QMessageBox.information(self, "Диагностика сети", info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить диагностику: {str(e)}")
    
    def force_reconnect(self):
        """Force reconnection to server"""
        if not self.sync_service:
            QMessageBox.warning(self, "Ошибка", "Сервис синхронизации недоступен")
            return
        
        reply = QMessageBox.question(
            self, 
            "Переподключение", 
            "Вы уверены, что хотите принудительно переподключиться к серверу?\n"
            "Это сбросит текущую аутентификацию и попытается зарегистрировать узел заново.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.sync_service.force_reconnect()
                
                if success:
                    QMessageBox.information(self, "Успех", "Переподключение инициировано")
                    self.load_settings()  # Refresh display
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось инициировать переподключение")
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при переподключении: {str(e)}")