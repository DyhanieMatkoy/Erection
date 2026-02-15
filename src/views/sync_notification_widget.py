"""Sync Notification Widget

This widget provides non-intrusive notifications about synchronization
status, conflicts, and other sync-related events.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from typing import Optional


class SyncNotification(QFrame):
    """Individual sync notification widget"""
    
    closed = pyqtSignal()
    action_clicked = pyqtSignal(str)  # action_id
    
    def __init__(self, title: str, message: str, notification_type: str = "info", 
                 action_text: str = "", action_id: str = "", parent=None):
        super().__init__(parent)
        self.notification_type = notification_type
        self.action_id = action_id
        
        self.setup_ui(title, message, action_text)
        self.setup_animations()
        
        # Auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.close_notification)
        
        # Set auto-close time based on type
        if notification_type == "error":
            self.auto_close_timer.start(10000)  # 10 seconds for errors
        elif notification_type == "warning":
            self.auto_close_timer.start(7000)   # 7 seconds for warnings
        else:
            self.auto_close_timer.start(5000)   # 5 seconds for info
    
    def setup_ui(self, title: str, message: str, action_text: str):
        """Setup user interface"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMaximumWidth(350)
        self.setMinimumWidth(300)
        
        # Set style based on notification type
        if self.notification_type == "error":
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        elif self.notification_type == "warning":
            self.setStyleSheet("""
                QFrame {
                    background-color: #fff3e0;
                    border: 1px solid #ff9800;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        elif self.notification_type == "success":
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:  # info
            self.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_button = QPushButton("×")
        close_button.setMaximumSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 14px;
                color: #666;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
        """)
        close_button.clicked.connect(self.close_notification)
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #333; font-size: 9pt;")
        layout.addWidget(message_label)
        
        # Action button (if provided)
        if action_text:
            action_button = QPushButton(action_text)
            action_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.2);
                }
            """)
            action_button.clicked.connect(self.on_action_clicked)
            layout.addWidget(action_button)
        
        self.setLayout(layout)
    
    def setup_animations(self):
        """Setup fade in/out animations"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.on_fade_out_finished)
        
        # Start with fade in
        self.fade_in_animation.start()
    
    def on_action_clicked(self):
        """Handle action button click"""
        self.action_clicked.emit(self.action_id)
        self.close_notification()
    
    def close_notification(self):
        """Close notification with fade out"""
        self.auto_close_timer.stop()
        self.fade_out_animation.start()
    
    def on_fade_out_finished(self):
        """Handle fade out completion"""
        self.closed.emit()
        self.deleteLater()
    
    def enterEvent(self, event):
        """Handle mouse enter - pause auto-close"""
        self.auto_close_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - resume auto-close"""
        if self.notification_type == "error":
            self.auto_close_timer.start(3000)  # Shorter time after hover
        else:
            self.auto_close_timer.start(2000)
        super().leaveEvent(event)


class SyncNotificationManager(QWidget):
    """Manager for sync notifications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.notifications = []
        
        self.setup_ui()
        
        # Position in top-right corner of parent
        if parent:
            self.position_widget()
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.addStretch()  # Push notifications to bottom
        
        self.setLayout(self.layout)
        
        # Initially hidden
        self.hide()
    
    def position_widget(self):
        """Position widget in top-right corner of parent"""
        if not self.parent_widget:
            return
        
        parent_rect = self.parent_widget.geometry()
        self.setGeometry(
            parent_rect.right() - 370,  # 350 width + 20 margin
            parent_rect.top() + 50,     # Below title bar
            360,
            parent_rect.height() - 100
        )
    
    def show_notification(self, title: str, message: str, notification_type: str = "info",
                         action_text: str = "", action_id: str = ""):
        """Show a new notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            action_text: Text for action button (optional)
            action_id: ID for action button (optional)
        """
        # Limit number of notifications
        if len(self.notifications) >= 5:
            # Remove oldest notification
            oldest = self.notifications[0]
            oldest.close_notification()
        
        # Create notification
        notification = SyncNotification(
            title, message, notification_type, action_text, action_id, self
        )
        notification.closed.connect(lambda: self.remove_notification(notification))
        notification.action_clicked.connect(self.on_notification_action)
        
        # Add to layout (insert before stretch)
        self.layout.insertWidget(self.layout.count() - 1, notification)
        self.notifications.append(notification)
        
        # Show widget if hidden
        if not self.isVisible():
            self.show()
        
        # Reposition if parent changed
        if self.parent_widget:
            self.position_widget()
    
    def remove_notification(self, notification: SyncNotification):
        """Remove notification from list"""
        if notification in self.notifications:
            self.notifications.remove(notification)
        
        # Hide widget if no notifications
        if not self.notifications:
            self.hide()
    
    def on_notification_action(self, action_id: str):
        """Handle notification action"""
        # Emit signal to parent or handle specific actions
        if hasattr(self.parent_widget, 'handle_sync_notification_action'):
            self.parent_widget.handle_sync_notification_action(action_id)
    
    def clear_all_notifications(self):
        """Clear all notifications"""
        for notification in self.notifications[:]:  # Copy list to avoid modification during iteration
            notification.close_notification()
    
    def show_sync_started(self):
        """Show sync started notification"""
        self.show_notification(
            "Синхронизация",
            "Начата синхронизация с сервером...",
            "info"
        )
    
    def show_sync_completed(self, processed_count: int, error_count: int = 0):
        """Show sync completed notification"""
        if error_count == 0:
            self.show_notification(
                "Синхронизация завершена",
                f"Успешно обработано записей: {processed_count}",
                "success"
            )
        else:
            self.show_notification(
                "Синхронизация завершена с ошибками",
                f"Обработано: {processed_count}, ошибок: {error_count}",
                "warning"
            )
    
    def show_sync_failed(self, error: str):
        """Show sync failed notification"""
        self.show_notification(
            "Ошибка синхронизации",
            f"Не удалось выполнить синхронизацию: {error}",
            "error",
            "Настройки",
            "open_sync_settings"
        )
    
    def show_conflict_detected(self, conflict_count: int = 1):
        """Show conflict detected notification"""
        self.show_notification(
            "Конфликт синхронизации",
            f"Обнаружено конфликтов: {conflict_count}. Требуется ручное разрешение.",
            "warning",
            "Разрешить",
            "resolve_conflicts"
        )
    
    def show_connection_lost(self):
        """Show connection lost notification"""
        self.show_notification(
            "Потеряно соединение",
            "Соединение с сервером синхронизации потеряно. Работа продолжается в автономном режиме.",
            "warning"
        )
    
    def show_connection_restored(self):
        """Show connection restored notification"""
        self.show_notification(
            "Соединение восстановлено",
            "Соединение с сервером синхронизации восстановлено.",
            "success"
        )
    
    def show_network_error(self, error_type: str, retry_in: int = 0):
        """Show network error notification
        
        Args:
            error_type: Type of network error
            retry_in: Seconds until next retry attempt
        """
        if error_type == "timeout":
            title = "Таймаут соединения"
            message = "Сервер не отвечает в течение установленного времени."
        elif error_type == "connection_error":
            title = "Ошибка подключения"
            message = "Не удается подключиться к серверу синхронизации."
        elif error_type == "server_error":
            title = "Ошибка сервера"
            message = "Сервер синхронизации временно недоступен."
        else:
            title = "Сетевая ошибка"
            message = f"Произошла сетевая ошибка: {error_type}"
        
        if retry_in > 0:
            message += f" Повторная попытка через {retry_in} сек."
        
        self.show_notification(title, message, "error")
    
    def show_retry_notification(self, attempt: int, max_attempts: int, next_retry: int):
        """Show retry attempt notification
        
        Args:
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            next_retry: Seconds until next retry
        """
        self.show_notification(
            "Повторная попытка синхронизации",
            f"Попытка {attempt} из {max_attempts}. Следующая попытка через {next_retry} сек.",
            "info"
        )