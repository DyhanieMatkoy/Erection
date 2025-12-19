"""
Example usage of the table part infrastructure.

This example demonstrates how to:
1. Create table part configurations
2. Set up user settings
3. Use the base table part components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.models.table_part_models import (
    TablePartConfiguration, TablePartSettingsData, TableColumn, 
    ColumnType, TablePartFactory, PanelSettings, ShortcutSettings
)
from src.services.table_part_settings_service import TablePartSettingsService
from src.data.models.sqlalchemy_models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_estimate_lines_configuration():
    """Create configuration for estimate lines table part"""
    
    # Define columns for estimate lines
    columns = [
        TablePartFactory.create_column(
            "line_number", "№", ColumnType.NUMBER, width="60px", editable=False
        ),
        TablePartFactory.create_reference_column(
            "work_id", "Работа", "works", width="300px"
        ),
        TablePartFactory.create_column(
            "quantity", "Количество", ColumnType.NUMBER, width="100px", show_total=True
        ),
        TablePartFactory.create_column(
            "unit", "Ед.изм", ColumnType.TEXT, width="80px", editable=False
        ),
        TablePartFactory.create_currency_column(
            "price", "Цена", width="120px"
        ),
        TablePartFactory.create_currency_column(
            "sum", "Сумма", width="120px", editable=False, show_total=True
        ),
        TablePartFactory.create_column(
            "labor_rate", "Норма труда", ColumnType.NUMBER, width="100px"
        )
    ]
    
    # Create configuration
    config = TablePartFactory.create_default_configuration("estimate", "lines")
    config.columns = columns
    config.show_totals = True
    config.auto_calculation_enabled = True
    
    return config


def create_daily_report_lines_configuration():
    """Create configuration for daily report lines table part"""
    
    columns = [
        TablePartFactory.create_column(
            "line_number", "№", ColumnType.NUMBER, width="60px", editable=False
        ),
        TablePartFactory.create_reference_column(
            "work_id", "Работа", "works", width="300px"
        ),
        TablePartFactory.create_column(
            "planned_labor", "План труда", ColumnType.NUMBER, width="100px"
        ),
        TablePartFactory.create_column(
            "actual_labor", "Факт труда", ColumnType.NUMBER, width="100px"
        ),
        TablePartFactory.create_column(
            "deviation", "Отклонение %", ColumnType.NUMBER, width="100px", editable=False
        )
    ]
    
    config = TablePartFactory.create_default_configuration("daily_report", "lines")
    config.columns = columns
    config.show_totals = False
    config.visible_commands = ["add_row", "delete_row", "import_data"]  # Customize visible commands
    
    return config


def demonstrate_user_settings():
    """Demonstrate user settings management"""
    
    # Create in-memory database for demo
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    user = User(
        id=1,
        username="demo_user",
        password_hash="demo_hash",
        role="user",
        is_active=True
    )
    session.add(user)
    session.commit()
    
    # Create settings service
    settings_service = TablePartSettingsService(session)
    
    print("=== Table Part Settings Demo ===\n")
    
    # 1. Get default settings
    print("1. Getting default settings for estimate lines:")
    default_settings = settings_service.get_default_settings("estimate", "lines")
    print(f"   Default visible commands: {default_settings.panel_settings.visible_commands}")
    print(f"   Shortcuts enabled: {default_settings.shortcuts.enabled}")
    print()
    
    # 2. Create custom settings
    print("2. Creating custom user settings:")
    custom_panel = PanelSettings(
        visible_commands=["add_row", "delete_row", "move_up", "move_down", "export_data"],
        button_size="large",
        show_tooltips=True,
        compact_mode=False
    )
    
    custom_shortcuts = ShortcutSettings(
        enabled=True,
        custom_mappings={"F2": "edit_cell", "Ctrl+D": "duplicate_row"}
    )
    
    custom_settings = TablePartSettingsData(
        column_widths={"work_id": 350, "quantity": 120, "price": 140},
        column_order=["line_number", "work_id", "quantity", "unit", "price", "sum"],
        hidden_columns=[],
        panel_settings=custom_panel,
        shortcuts=custom_shortcuts,
        sort_column="line_number",
        sort_direction="asc"
    )
    
    # 3. Save custom settings
    success = settings_service.save_user_settings(1, "estimate", "lines", custom_settings)
    print(f"   Settings saved: {success}")
    
    # 4. Retrieve saved settings
    print("3. Retrieving saved settings:")
    retrieved_settings = settings_service.get_user_settings(1, "estimate", "lines")
    if retrieved_settings:
        print(f"   Column widths: {retrieved_settings.column_widths}")
        print(f"   Visible commands: {retrieved_settings.panel_settings.visible_commands}")
        print(f"   Button size: {retrieved_settings.panel_settings.button_size}")
        print(f"   Custom shortcuts: {retrieved_settings.shortcuts.custom_mappings}")
    print()
    
    # 5. Get all user settings
    print("4. All user settings:")
    all_settings = settings_service.get_all_user_settings(1)
    for setting in all_settings:
        print(f"   Document: {setting['document_type']}, Table: {setting['table_part_id']}")
    print()
    
    session.close()


def demonstrate_configuration_serialization():
    """Demonstrate configuration serialization"""
    
    print("=== Configuration Serialization Demo ===\n")
    
    # Create estimate lines configuration
    config = create_estimate_lines_configuration()
    
    print("1. Original configuration:")
    print(f"   Table ID: {config.table_id}")
    print(f"   Document Type: {config.document_type}")
    print(f"   Number of columns: {len(config.columns)}")
    print(f"   Number of commands: {len(config.available_commands)}")
    print(f"   Visible commands: {config.visible_commands}")
    print(f"   Auto calculation: {config.auto_calculation_enabled}")
    print()
    
    # Serialize to dictionary
    config_dict = config.to_dict()
    print("2. Serialized to dictionary (showing columns):")
    for col_dict in config_dict['columns']:
        print(f"   Column: {col_dict['name']} ({col_dict['type']}) - Width: {col_dict.get('width', 'auto')}")
    print()
    
    # Deserialize from dictionary
    restored_config = TablePartConfiguration.from_dict(config_dict)
    print("3. Restored from dictionary:")
    print(f"   Table ID: {restored_config.table_id}")
    print(f"   Columns match: {len(restored_config.columns) == len(config.columns)}")
    print(f"   Commands match: {len(restored_config.available_commands) == len(config.available_commands)}")
    print()


def demonstrate_factory_methods():
    """Demonstrate factory methods for creating components"""
    
    print("=== Factory Methods Demo ===\n")
    
    # 1. Create standard commands
    print("1. Standard commands:")
    standard_commands = TablePartFactory.create_standard_commands()
    for cmd in standard_commands:
        selection_req = " (requires selection)" if cmd.requires_selection else ""
        print(f"   {cmd.icon} {cmd.name} - {cmd.tooltip}{selection_req}")
    print()
    
    # 2. Create different column types
    print("2. Different column types:")
    
    text_col = TablePartFactory.create_column("description", "Описание", ColumnType.TEXT, width="300px")
    print(f"   Text column: {text_col.name} ({text_col.type.value})")
    
    number_col = TablePartFactory.create_column("quantity", "Количество", ColumnType.NUMBER, show_total=True)
    print(f"   Number column: {number_col.name} ({number_col.type.value}) - Show total: {number_col.show_total}")
    
    ref_col = TablePartFactory.create_reference_column("work_id", "Работа", "works")
    print(f"   Reference column: {ref_col.name} ({ref_col.type.value}) - Ref type: {ref_col.reference_type}")
    
    currency_col = TablePartFactory.create_currency_column("price", "Цена", show_total=True)
    print(f"   Currency column: {currency_col.name} ({currency_col.type.value}) - Show total: {currency_col.show_total}")
    print()
    
    # 3. Create default configurations for different document types
    print("3. Default configurations:")
    
    estimate_config = TablePartFactory.create_default_configuration("estimate", "lines")
    print(f"   Estimate lines: {len(estimate_config.visible_commands)} visible commands")
    
    daily_report_config = TablePartFactory.create_default_configuration("daily_report", "lines")
    print(f"   Daily report lines: {len(daily_report_config.visible_commands)} visible commands")
    print()


def main():
    """Run all demonstrations"""
    print("Table Part Infrastructure Usage Examples")
    print("=" * 50)
    print()
    
    demonstrate_factory_methods()
    demonstrate_configuration_serialization()
    demonstrate_user_settings()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    main()