"""Login form"""
import os
import configparser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                              QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from ..services.auth_service import AuthService


class LoginForm(QDialog):
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()
        # Try auto-login after UI is shown
        QTimer.singleShot(100, self.try_auto_login)
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Вход в систему")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.on_login_clicked)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)
        
        # Set focus to username
        self.username_edit.setFocus()
    
    def on_login_clicked(self):
        """Handle login button click"""
        username = self.username_edit.text()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        user = self.auth_service.login(username, password)
        if user:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
    
    def try_auto_login(self):
        """Try to auto-login from env.ini file"""
        env_file = os.path.join(os.getcwd(), 'env.ini')
        
        if not os.path.exists(env_file):
            return
        
        try:
            username = None
            password = None
            
            # Read as simple key=value file
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'login':
                            username = value
                        elif key == 'password':
                            password = value
            
            if username and password:
                # Fill in the fields
                self.username_edit.setText(username)
                self.password_edit.setText(password)
                
                # Attempt auto-login
                user = self.auth_service.login(username, password)
                if user:
                    self.accept()
        except Exception as e:
            # Silently fail - user can login manually
            pass
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_login_clicked()
        else:
            super().keyPressEvent(event)
