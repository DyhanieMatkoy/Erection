"""
Диалог отображения прогресса импорта данных
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class ProgressDialog(QDialog):
    """Диалог отображения прогресса импорта данных"""
    
    def __init__(self, title: str = "Импорт данных", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        """Инициализирует пользовательский интерфейс"""
        self.setWindowTitle(self.title)
        self.setMinimumSize(500, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self.title_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Метка статуса
        self.status_label = QLabel("Готов к работе")
        layout.addWidget(self.status_label)
        
        # Текстовое поле для лога
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)  # Изначально скрываем кнопку
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
    
    def update_progress(self, value: int, status: str = ""):
        """Обновляет прогресс-бар и статус"""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
    
    def add_log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_text.append(message)
        # Прокрутка к последнему сообщению
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_indeterminate(self):
        """Устанавливает неопределенный прогресс"""
        self.progress_bar.setRange(0, 0)
    
    def set_determinate(self):
        """Устанавливает определенный прогресс"""
        self.progress_bar.setRange(0, 100)
    
    def set_finished(self, message: str = "Операция завершена"):
        """Устанавливает состояние завершения"""
        self.progress_bar.setValue(100)
        self.status_label.setText(message)
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
    
    def reset(self):
        """Сбрасывает диалог в начальное состояние"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Готов к работе")
        self.log_text.clear()
        self.cancel_button.setVisible(True)
        self.close_button.setVisible(False)