"""Base document form"""
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import Qt


class BaseDocumentForm(QWidget):
    def __init__(self):
        super().__init__()
        self.modified = False
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.on_save()
        elif event.key() == Qt.Key.Key_S and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Enter - trigger default button (usually save and close)
            self.on_save_and_close()
        elif event.key() == Qt.Key.Key_Escape:
            self.on_close()
        elif event.key() == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.on_print()
        else:
            super().keyPressEvent(event)
    
    def on_save(self):
        """Handle save"""
        pass
    
    def on_save_and_close(self):
        """Handle save and close"""
        self.on_save()
        self.close()
    
    def on_close(self):
        """Handle close"""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Есть несохраненные изменения. Сохранить?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.on_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self.close()
    
    def on_print(self):
        """Handle print"""
        pass
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self.modified
