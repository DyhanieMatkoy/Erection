import pytest
from pydantic import ValidationError
from api.models.ui_settings import UserFormSettingsCreate, FormCommandConfigurationCreate

class TestUserFormSettingsModels:
    def test_create_valid(self):
        data = {
            "form_id": "doc_list",
            "settings_type": "columns",
            "settings_data": {"col1": True}
        }
        model = UserFormSettingsCreate(**data)
        assert model.form_id == "doc_list"
        assert model.settings_data["col1"] is True

    def test_create_missing_required(self):
        with pytest.raises(ValidationError):
            UserFormSettingsCreate(form_id="doc_list")

class TestFormCommandConfigModels:
    def test_create_valid(self):
        data = {
            "form_id": "doc_list",
            "command_id": "cmd_create",
            "is_visible": False
        }
        model = FormCommandConfigurationCreate(**data)
        assert model.is_visible is False
        assert model.is_enabled is True # default

    def test_create_defaults(self):
        data = {
            "form_id": "doc_list",
            "command_id": "cmd_create"
        }
        model = FormCommandConfigurationCreate(**data)
        assert model.is_visible is True
        assert model.is_enabled is True
        assert model.is_in_more_menu is False
