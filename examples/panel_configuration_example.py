"""
Panel Configuration Example for PyQt6 Desktop Application.

This example demonstrates how to use the panel configuration dialog
to customize row control panel commands.

Requirements: 9.1, 9.2, 9.3, 9.4
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

from src.views.widgets.row_control_panel import RowControlPanel
from src.views.dialogs.panel_configuration_dialog import (
    PanelConfigurationDialog, CommandTreeNode
)


class PanelConfigurationExample(QMainWindow):
    """Example window demonstrating panel configuration functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel Configuration Example")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create row control panel with default commands
        self.panel = RowControlPanel()
        layout.addWidget(self.panel)
        
        # Connect customization signal
        self.panel.customizeRequested.connect(self.on_customize_requested)
        
        # Add a button to manually open configuration
        config_button = QPushButton("Open Configuration Dialog")
        config_button.clicked.connect(self.show_configuration_dialog)
        layout.addWidget(config_button)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        print("Panel Configuration Example initialized")
        print("Available commands:", self.panel.get_visible_commands())
    
    def on_customize_requested(self):
        """Handle customization request from panel"""
        print("Customization requested from panel")
        self.show_configuration_dialog()
    
    def show_configuration_dialog(self):
        """Show the panel configuration dialog"""
        print("Opening panel configuration dialog...")
        
        # Get current panel configuration
        current_config = {
            'visible_commands': self.panel.get_visible_commands(),
            'show_tooltips': True,
            'compact_mode': False
        }
        
        # Create available commands from panel's standard buttons
        available_commands = {}
        for cmd_id, button_config in self.panel.standard_buttons.items():
            available_commands[cmd_id] = CommandTreeNode(
                id=cmd_id,
                name=button_config.name,
                icon=button_config.icon,
                tooltip=button_config.tooltip,
                visible=cmd_id in current_config['visible_commands'],
                enabled=button_config.enabled,
                is_standard=True
            )
        
        # Create and show dialog
        dialog = PanelConfigurationDialog(
            current_config=current_config,
            available_commands=available_commands,
            parent=self
        )
        
        # Connect preview signal for real-time updates
        dialog.previewRequested.connect(self.on_preview_configuration)
        
        # Show dialog and handle result
        if dialog.exec() == PanelConfigurationDialog.DialogCode.Accepted:
            new_config = dialog.get_configuration()
            self.apply_configuration(new_config)
            print("Configuration applied:", new_config)
        else:
            print("Configuration dialog cancelled")
    
    def on_preview_configuration(self, visible_commands):
        """Handle preview configuration changes"""
        print(f"Preview configuration: {visible_commands}")
        # In a real application, you might temporarily update the panel
        # For this example, we'll just log the preview
    
    def apply_configuration(self, config):
        """Apply the new panel configuration"""
        print(f"Applying configuration: {config}")
        
        # Update visible commands
        new_visible_commands = config.get('visible_commands', [])
        self.panel.set_visible_commands(new_visible_commands)
        
        # TODO: Apply other settings like show_tooltips and compact_mode
        # This would require extending the panel to support these options
        
        print(f"Panel updated with visible commands: {self.panel.get_visible_commands()}")


def main():
    """Main function to run the example"""
    app = QApplication(sys.argv)
    
    # Create and show the example window
    window = PanelConfigurationExample()
    window.show()
    
    print("\nPanel Configuration Example")
    print("=" * 50)
    print("This example demonstrates:")
    print("1. Row control panel with customizable commands")
    print("2. Panel configuration dialog with command tree")
    print("3. Real-time preview of configuration changes")
    print("4. Save/Reset functionality")
    print("\nTry:")
    print("- Click the ⚙️ button on the panel to customize")
    print("- Use the 'Open Configuration Dialog' button")
    print("- Check/uncheck commands to see preview")
    print("- Use Reset to restore defaults")
    print("- Save to apply changes")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()