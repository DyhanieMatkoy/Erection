from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtCore import Qt

class BulkOperationProgressDialog(QDialog):
    """
    Dialog to show progress of bulk operations.
    """
    def __init__(self, parent=None, title="Operation in progress"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        self.setup_ui()
        self.is_completed = False
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Starting...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setVisible(False) # Show only on error or completion
        layout.addWidget(self.details_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processing item {current} of {total}...")
        
    def show_results(self, results):
        self.is_completed = True
        self.progress_bar.setValue(self.progress_bar.maximum())
        
        success = results.get('success_count', 0)
        failure = results.get('failure_count', 0)
        cancelled = results.get('is_cancelled', False)
        
        status = "Completed"
        if cancelled:
            status = "Cancelled"
        elif failure > 0:
            status = "Completed with errors"
            
        self.status_label.setText(f"{status}. Success: {success}, Failed: {failure}")
        
        # Show details if there are errors
        if failure > 0 or results.get('critical_error'):
            self.details_text.setVisible(True)
            text = "Errors:\n"
            if results.get('critical_error'):
                text += f"CRITICAL: {results['critical_error']}\n\n"
                
            for err in results.get('errors', []):
                text += f"- {err}\n"
            self.details_text.setText(text)
            
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
        
    def reject(self):
        if not self.is_completed:
            # Emit signal or callback to cancel operation
            if hasattr(self, 'on_cancel_requested'):
                self.on_cancel_requested()
            self.status_label.setText("Cancelling...")
            self.cancel_button.setEnabled(False)
        else:
            super().reject()
