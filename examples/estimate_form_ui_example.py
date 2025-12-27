"""Example demonstrating the new estimate form UI improvements"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from src.views.estimate_document_form import EstimateDocumentForm
from src.data.database_manager import DatabaseManager


def main():
    """Demonstrate estimate form UI improvements"""
    print("Estimate Form UI Improvements Demo")
    print("=" * 40)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    app = QApplication(sys.argv)
    
    try:
        # Create form
        form = EstimateDocumentForm()
        
        print("New features demonstrated:")
        print("1. Collapsible header group - click the 'Реквизиты' checkbox to collapse/expand")
        print("2. Resource print checkbox - enables printing with resource statement")
        print("3. Dynamic tooltips - tooltip changes based on checkbox state")
        print("4. Print method integration - uses checkbox value to determine print variant")
        
        # Show the form
        form.show()
        
        # Demonstrate programmatic control
        print("\nProgrammatic demonstration:")
        print(f"- Header is collapsible: {form.header_group.isCheckable()}")
        print(f"- Header is initially expanded: {form.header_group.isChecked()}")
        print(f"- Resource checkbox exists: {hasattr(form, 'print_resources_checkbox')}")
        print(f"- Resource flag is initially: {form.print_with_resources}")
        
        # Toggle resource checkbox
        form.print_resources_checkbox.setChecked(True)
        print(f"- After checking resource box: {form.print_with_resources}")
        
        # Show tooltip change
        tooltip = form.print_resources_checkbox.toolTip()
        print(f"- Current tooltip: {tooltip}")
        
        print("\nForm is now displayed. Try the following:")
        print("- Click the 'Реквизиты' checkbox to collapse/expand the header")
        print("- Toggle the 'Печатать с ресурсной ведомостью' checkbox")
        print("- Notice how the header physically collapses to save space")
        print("- The table part will expand to use the freed space")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    main()