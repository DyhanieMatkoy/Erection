"""
Test suite for table part infrastructure components.

Tests the core table part functionality including:
- Data models and configuration
- Settings service
- Database schema
"""

import pytest
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models.sqlalchemy_models import Base, User, UserTablePartSettings, TablePartCommandConfig
from src.data.models.table_part_models import (
    TablePartConfiguration, TablePartSettingsData, TablePartCommand,
    PanelSettings, ShortcutSettings, TableColumn, ColumnType, CommandType,
    TablePartFactory
)
from src.services.table_part_settings_service import TablePartSettingsService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    test_user = User(
        id=1,
        username="test_user",
        password_hash="test_hash",
        role="user",
        is_active=True
    )
    session.add(test_user)
    session.commit()
    
    yield session
    session.close()


class TestTablePartModels:
    """Test table part data models"""
    
    def test_table_column_serialization(self):
        """Test TableColumn serialization and deserialization"""
        column = TableColumn(
            id="quantity",
            name="Количество",
            type=ColumnType.NUMBER,
            width="100px",
            sortable=True,
            editable=True,
            show_total=True
        )
        
        # Test to_dict
        column_dict = column.to_dict()
        assert column_dict['id'] == "quantity"
        assert column_dict['name'] == "Количество"
        assert column_dict['type'] == "number"
        assert column_dict['show_total'] is True
        
        # Test from_dict
        restored_column = TableColumn.from_dict(column_dict)
        assert restored_column.id == column.id
        assert restored_column.name == column.name
        assert restored_column.type == column.type
        assert restored_column.show_total == column.show_total
    
    def test_table_part_command_serialization(self):
        """Test TablePartCommand serialization and deserialization"""
        command = TablePartCommand(
            id="add_row",
            name="Добавить",
            icon="➕",
            tooltip="Добавить новую строку",
            shortcut="Insert",
            enabled=True,
            visible=True,
            position=1
        )
        
        # Test to_dict
        command_dict = command.to_dict()
        assert command_dict['id'] == "add_row"
        assert command_dict['name'] == "Добавить"
        assert command_dict['icon'] == "➕"
        assert command_dict['shortcut'] == "Insert"
        
        # Test from_dict
        restored_command = TablePartCommand.from_dict(command_dict)
        assert restored_command.id == command.id
        assert restored_command.name == command.name
        assert restored_command.icon == command.icon
        assert restored_command.shortcut == command.shortcut
    
    def test_table_part_settings_data_json(self):
        """Test TablePartSettingsData JSON serialization"""
        panel_settings = PanelSettings(
            visible_commands=["add_row", "delete_row"],
            button_size="medium",
            show_tooltips=True
        )
        
        shortcuts = ShortcutSettings(
            enabled=True,
            custom_mappings={"F2": "edit_cell"}
        )
        
        settings = TablePartSettingsData(
            column_widths={"name": 200, "quantity": 100},
            column_order=["name", "quantity", "price"],
            panel_settings=panel_settings,
            shortcuts=shortcuts,
            sort_column="name",
            sort_direction="asc"
        )
        
        # Test JSON serialization
        json_str = settings.to_json()
        assert isinstance(json_str, str)
        
        # Test JSON deserialization
        restored_settings = TablePartSettingsData.from_json(json_str)
        assert restored_settings.column_widths == settings.column_widths
        assert restored_settings.column_order == settings.column_order
        assert restored_settings.panel_settings.visible_commands == settings.panel_settings.visible_commands
        assert restored_settings.shortcuts.enabled == settings.shortcuts.enabled
        assert restored_settings.sort_column == settings.sort_column
    
    def test_table_part_configuration(self):
        """Test TablePartConfiguration creation and serialization"""
        columns = [
            TableColumn(id="name", name="Наименование", type=ColumnType.TEXT),
            TableColumn(id="quantity", name="Количество", type=ColumnType.NUMBER, show_total=True),
            TableColumn(id="price", name="Цена", type=ColumnType.CURRENCY, show_total=True)
        ]
        
        commands = TablePartFactory.create_standard_commands()
        
        config = TablePartConfiguration(
            table_id="estimate_lines",
            document_type="estimate",
            columns=columns,
            available_commands=commands,
            visible_commands=["add_row", "delete_row", "move_up", "move_down"],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=True,
            show_totals=True
        )
        
        # Test serialization
        config_dict = config.to_dict()
        assert config_dict['table_id'] == "estimate_lines"
        assert config_dict['document_type'] == "estimate"
        assert len(config_dict['columns']) == 3
        assert len(config_dict['available_commands']) == 7  # Standard commands
        assert config_dict['show_totals'] is True
        
        # Test deserialization
        restored_config = TablePartConfiguration.from_dict(config_dict)
        assert restored_config.table_id == config.table_id
        assert restored_config.document_type == config.document_type
        assert len(restored_config.columns) == len(config.columns)
        assert len(restored_config.available_commands) == len(config.available_commands)


class TestTablePartFactory:
    """Test table part factory methods"""
    
    def test_create_standard_commands(self):
        """Test creation of standard commands"""
        commands = TablePartFactory.create_standard_commands()
        
        assert len(commands) == 7
        
        # Check that all standard command types are present
        command_ids = [cmd.id for cmd in commands]
        expected_ids = [
            CommandType.ADD_ROW.value,
            CommandType.DELETE_ROW.value,
            CommandType.MOVE_UP.value,
            CommandType.MOVE_DOWN.value,
            CommandType.IMPORT_DATA.value,
            CommandType.EXPORT_DATA.value,
            CommandType.PRINT_DATA.value
        ]
        
        for expected_id in expected_ids:
            assert expected_id in command_ids
        
        # Check command properties
        add_command = next(cmd for cmd in commands if cmd.id == CommandType.ADD_ROW.value)
        assert add_command.name == "Добавить"
        assert add_command.icon == "➕"
        assert add_command.shortcut == "Insert"
        assert add_command.requires_selection is False
        
        delete_command = next(cmd for cmd in commands if cmd.id == CommandType.DELETE_ROW.value)
        assert delete_command.requires_selection is True
    
    def test_create_default_configuration(self):
        """Test creation of default configuration"""
        config = TablePartFactory.create_default_configuration("estimate", "lines")
        
        assert config.table_id == "lines"
        assert config.document_type == "estimate"
        assert len(config.available_commands) == 7
        assert len(config.visible_commands) == 4  # First 4 commands visible by default
        assert config.keyboard_shortcuts_enabled is True
        assert config.auto_calculation_enabled is True
        assert config.drag_drop_enabled is True
    
    def test_create_columns(self):
        """Test column creation methods"""
        # Test regular column
        text_column = TablePartFactory.create_column(
            "description", "Описание", ColumnType.TEXT, width="300px"
        )
        assert text_column.id == "description"
        assert text_column.name == "Описание"
        assert text_column.type == ColumnType.TEXT
        assert text_column.width == "300px"
        
        # Test reference column
        ref_column = TablePartFactory.create_reference_column(
            "work_id", "Работа", "works", editable=True
        )
        assert ref_column.id == "work_id"
        assert ref_column.type == ColumnType.REFERENCE
        assert ref_column.reference_type == "works"
        assert ref_column.editable is True
        
        # Test currency column
        currency_column = TablePartFactory.create_currency_column(
            "sum", "Сумма", show_total=True
        )
        assert currency_column.id == "sum"
        assert currency_column.type == ColumnType.CURRENCY
        assert currency_column.show_total is True


class TestTablePartSettingsService:
    """Test table part settings service"""
    
    def test_save_and_get_user_settings(self, db_session):
        """Test saving and retrieving user settings"""
        service = TablePartSettingsService(db_session)
        
        # Create test settings
        panel_settings = PanelSettings(
            visible_commands=["add_row", "delete_row"],
            button_size="large",
            show_tooltips=False
        )
        
        settings = TablePartSettingsData(
            column_widths={"name": 250, "quantity": 120},
            panel_settings=panel_settings,
            sort_column="name",
            sort_direction="desc"
        )
        
        # Save settings
        success = service.save_user_settings(1, "estimate", "lines", settings)
        assert success is True
        
        # Retrieve settings
        retrieved_settings = service.get_user_settings(1, "estimate", "lines")
        assert retrieved_settings is not None
        assert retrieved_settings.column_widths == settings.column_widths
        assert retrieved_settings.panel_settings.button_size == "large"
        assert retrieved_settings.panel_settings.show_tooltips is False
        assert retrieved_settings.sort_column == "name"
        assert retrieved_settings.sort_direction == "desc"
    
    def test_get_nonexistent_settings(self, db_session):
        """Test retrieving non-existent settings returns None"""
        service = TablePartSettingsService(db_session)
        
        settings = service.get_user_settings(999, "nonexistent", "table")
        assert settings is None
    
    def test_update_existing_settings(self, db_session):
        """Test updating existing settings"""
        service = TablePartSettingsService(db_session)
        
        # Create initial settings
        initial_settings = TablePartSettingsData(
            column_widths={"name": 200},
            sort_column="name"
        )
        
        service.save_user_settings(1, "estimate", "lines", initial_settings)
        
        # Update settings
        updated_settings = TablePartSettingsData(
            column_widths={"name": 300, "quantity": 100},
            sort_column="quantity",
            sort_direction="desc"
        )
        
        success = service.save_user_settings(1, "estimate", "lines", updated_settings)
        assert success is True
        
        # Verify update
        retrieved_settings = service.get_user_settings(1, "estimate", "lines")
        assert retrieved_settings.column_widths == {"name": 300, "quantity": 100}
        assert retrieved_settings.sort_column == "quantity"
        assert retrieved_settings.sort_direction == "desc"
    
    def test_reset_user_settings(self, db_session):
        """Test resetting user settings"""
        service = TablePartSettingsService(db_session)
        
        # Create settings
        settings = TablePartSettingsData(column_widths={"name": 200})
        service.save_user_settings(1, "estimate", "lines", settings)
        
        # Verify settings exist
        retrieved_settings = service.get_user_settings(1, "estimate", "lines")
        assert retrieved_settings is not None
        
        # Reset settings
        success = service.reset_user_settings(1, "estimate", "lines")
        assert success is True
        
        # Verify settings are gone
        retrieved_settings = service.get_user_settings(1, "estimate", "lines")
        assert retrieved_settings is None
    
    def test_get_default_settings(self, db_session):
        """Test getting default settings"""
        service = TablePartSettingsService(db_session)
        
        default_settings = service.get_default_settings("estimate", "lines")
        
        assert isinstance(default_settings, TablePartSettingsData)
        assert isinstance(default_settings.panel_settings, PanelSettings)
        assert isinstance(default_settings.shortcuts, ShortcutSettings)
        assert default_settings.panel_settings.show_tooltips is True
        assert default_settings.shortcuts.enabled is True
        
        # Check default visible commands for estimate
        visible_commands = default_settings.panel_settings.visible_commands
        assert CommandType.ADD_ROW.value in visible_commands
        assert CommandType.DELETE_ROW.value in visible_commands
        assert CommandType.IMPORT_DATA.value in visible_commands
    
    def test_get_all_user_settings(self, db_session):
        """Test getting all settings for a user"""
        service = TablePartSettingsService(db_session)
        
        # Create multiple settings
        settings1 = TablePartSettingsData(column_widths={"name": 200})
        settings2 = TablePartSettingsData(column_widths={"description": 300})
        
        service.save_user_settings(1, "estimate", "lines", settings1)
        service.save_user_settings(1, "daily_report", "lines", settings2)
        
        # Get all settings
        all_settings = service.get_all_user_settings(1)
        
        assert len(all_settings) == 2
        
        # Check structure
        for setting in all_settings:
            assert 'document_type' in setting
            assert 'table_part_id' in setting
            assert 'settings' in setting
            assert 'created_at' in setting
            assert 'updated_at' in setting


class TestDatabaseSchema:
    """Test database schema for table part settings"""
    
    def test_user_table_part_settings_crud(self, db_session):
        """Test CRUD operations on UserTablePartSettings"""
        # Create
        settings_data = json.dumps({
            "column_widths": {"name": 200, "quantity": 100},
            "visible_commands": ["add_row", "delete_row"]
        })
        
        settings_record = UserTablePartSettings(
            user_id=1,
            document_type="estimate",
            table_part_id="lines",
            settings_data=settings_data
        )
        
        db_session.add(settings_record)
        db_session.commit()
        
        # Read
        retrieved_record = db_session.query(UserTablePartSettings).filter(
            UserTablePartSettings.user_id == 1,
            UserTablePartSettings.document_type == "estimate",
            UserTablePartSettings.table_part_id == "lines"
        ).first()
        
        assert retrieved_record is not None
        assert retrieved_record.user_id == 1
        assert retrieved_record.document_type == "estimate"
        assert retrieved_record.table_part_id == "lines"
        
        # Parse settings data
        parsed_data = json.loads(retrieved_record.settings_data)
        assert parsed_data["column_widths"]["name"] == 200
        assert "add_row" in parsed_data["visible_commands"]
        
        # Update
        new_settings_data = json.dumps({
            "column_widths": {"name": 300, "quantity": 150},
            "visible_commands": ["add_row", "delete_row", "move_up"]
        })
        
        retrieved_record.settings_data = new_settings_data
        db_session.commit()
        
        # Verify update
        updated_record = db_session.query(UserTablePartSettings).filter(
            UserTablePartSettings.user_id == 1,
            UserTablePartSettings.document_type == "estimate",
            UserTablePartSettings.table_part_id == "lines"
        ).first()
        
        updated_data = json.loads(updated_record.settings_data)
        assert updated_data["column_widths"]["name"] == 300
        assert len(updated_data["visible_commands"]) == 3
        
        # Delete
        db_session.delete(updated_record)
        db_session.commit()
        
        # Verify deletion
        deleted_record = db_session.query(UserTablePartSettings).filter(
            UserTablePartSettings.user_id == 1,
            UserTablePartSettings.document_type == "estimate",
            UserTablePartSettings.table_part_id == "lines"
        ).first()
        
        assert deleted_record is None
    
    def test_table_part_command_config_crud(self, db_session):
        """Test CRUD operations on TablePartCommandConfig"""
        # Create
        command_config = TablePartCommandConfig(
            document_type="estimate",
            table_part_id="lines",
            user_id=1,
            command_id="add_row",
            is_visible=True,
            is_enabled=True,
            position=1,
            is_in_more_menu=False
        )
        
        db_session.add(command_config)
        db_session.commit()
        
        # Read
        retrieved_config = db_session.query(TablePartCommandConfig).filter(
            TablePartCommandConfig.document_type == "estimate",
            TablePartCommandConfig.table_part_id == "lines",
            TablePartCommandConfig.user_id == 1,
            TablePartCommandConfig.command_id == "add_row"
        ).first()
        
        assert retrieved_config is not None
        assert retrieved_config.is_visible is True
        assert retrieved_config.is_enabled is True
        assert retrieved_config.position == 1
        
        # Update
        retrieved_config.is_visible = False
        retrieved_config.position = 5
        db_session.commit()
        
        # Verify update
        updated_config = db_session.query(TablePartCommandConfig).filter(
            TablePartCommandConfig.document_type == "estimate",
            TablePartCommandConfig.table_part_id == "lines",
            TablePartCommandConfig.user_id == 1,
            TablePartCommandConfig.command_id == "add_row"
        ).first()
        
        assert updated_config.is_visible is False
        assert updated_config.position == 5
        
        # Delete
        db_session.delete(updated_config)
        db_session.commit()
        
        # Verify deletion
        deleted_config = db_session.query(TablePartCommandConfig).filter(
            TablePartCommandConfig.document_type == "estimate",
            TablePartCommandConfig.table_part_id == "lines",
            TablePartCommandConfig.user_id == 1,
            TablePartCommandConfig.command_id == "add_row"
        ).first()
        
        assert deleted_config is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])