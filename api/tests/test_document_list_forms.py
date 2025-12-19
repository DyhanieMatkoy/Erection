import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy.orm import Session
from src.data.models.ui_settings import UserFormSettings
from api.services.user_settings_manager import UserSettingsManager
from src.data.models.sqlalchemy_models import User
from src.data.models.sqlalchemy_models import Estimate, Counterparty, Object, Organization, Person
from api.services.command_manager import CommandManager
from api.services.command_registry import StandardCommandRegistry
from api.services.data_service import DataService
from datetime import date, timedelta
import uuid
import json

# Strategy to generate valid UserFormSettings data
@composite
def user_form_settings_strategy(draw):
    form_id = draw(st.text(min_size=1, max_size=50))
    settings_type = draw(st.sampled_from(['columns', 'filters', 'commands', 'daterange']))
    
    # Generate random JSON-compatible dictionary
    settings_data = draw(st.recursive(
        st.dictionaries(st.text(), st.text()),
        lambda children: st.dictionaries(st.text(), children | st.text() | st.integers() | st.booleans()),
        max_leaves=10
    ))
    
    return {
        "form_id": form_id,
        "settings_type": settings_type,
        "settings_data": settings_data
    }

@pytest.fixture(scope="function")
def clear_tables(db_session):
    """Clear relevant tables before/after test"""
    # Delete in order of dependency
    db_session.query(Estimate).delete()
    db_session.query(UserFormSettings).delete()
    # We don't delete references (Counterparty etc) as they are shared/setup once 
    # effectively by setup_dependencies if we want, or we can clear them too.
    # But setup_dependencies creates them.
    # Let's just clear documents and settings.
    db_session.commit()
    yield
    db_session.query(Estimate).delete()
    db_session.query(UserFormSettings).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"test_user_{unique_id}",
        password_hash="hash",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

class TestUserFormSettings:
    """Property-based tests for UserFormSettings"""

    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(data=user_form_settings_strategy())
    def test_settings_persistence_round_trip(self, db_session, test_user, data):
        """
        Property: Settings saved to the database must be retrievable 
        and exactly match the saved data.
        """
        user_settings = UserFormSettings(
            user_id=test_user.id,
            form_id=data["form_id"],
            settings_type=data["settings_type"],
            settings_data=data["settings_data"]
        )
        
        try:
            db_session.add(user_settings)
            db_session.commit()
            db_session.expire_all()
            
            retrieved = db_session.query(UserFormSettings).filter_by(
                user_id=test_user.id,
                form_id=data["form_id"],
                settings_type=data["settings_type"]
            ).first()
            
            assert retrieved is not None
            assert retrieved.form_id == data["form_id"]
            assert retrieved.settings_type == data["settings_type"]
            assert retrieved.settings_data == data["settings_data"]
            
            db_session.delete(retrieved)
            db_session.commit()
            
        except Exception as e:
            db_session.rollback()
            raise e

class TestUserSettingsManager:
    """Property-based tests for UserSettingsManager service"""

    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(data=user_form_settings_strategy())
    def test_settings_reset_to_defaults(self, db_session, test_user, data):
        """
        Property: Resetting settings should remove user overrides and return to defaults (None).
        """
        manager = UserSettingsManager(db_session)
        manager._save_generic_settings(test_user.id, data["form_id"], data["settings_type"], data["settings_data"])
        
        saved = manager._load_generic_settings(test_user.id, data["form_id"], data["settings_type"])
        assert saved == data["settings_data"]
        
        manager.reset_to_defaults(test_user.id, data["form_id"], data["settings_type"])
        
        after_reset = manager._load_generic_settings(test_user.id, data["form_id"], data["settings_type"])
        assert after_reset is None

    def test_save_error_handling(self, db_session, test_user):
        """Test error handling when saving settings fails"""
        from unittest.mock import MagicMock
        from api.services.user_settings_manager import UserSettingsError
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.commit.side_effect = SQLAlchemyError("DB Connection Lost")
        
        manager = UserSettingsManager(mock_db)
        
        with pytest.raises(UserSettingsError) as exc:
            manager.save_column_settings(test_user.id, "form_error_test", {"col": 1})
        
        assert "Failed to save settings" in str(exc.value)
        mock_db.rollback.assert_called_once()

    def test_load_error_handling(self, db_session, test_user):
        """Test error handling when loading settings fails (graceful fallback)"""
        from unittest.mock import MagicMock
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_db = MagicMock()
        mock_db.query.side_effect = SQLAlchemyError("DB Read Error")
        
        manager = UserSettingsManager(mock_db)
        
        result = manager.load_column_settings(test_user.id, "form_error_test")
        assert result is None

class TestCommandManager:
    """Tests for Command Manager service"""
    
    def test_get_available_commands_defaults(self, db_session, test_user):
        manager = CommandManager(db_session)
        commands = manager.get_available_commands(test_user.id, "test_form")
        registry_count = len(StandardCommandRegistry.get_all())
        assert len(commands) == registry_count
        create_cmd = next(c for c in commands if c['id'] == 'create')
        assert create_cmd['is_visible'] is True
        assert create_cmd['is_enabled'] is True

    def test_context_sensitive_availability(self, db_session, test_user):
        manager = CommandManager(db_session)
        
        context_none = {'selection_count': 0}
        cmds_none = manager.get_available_commands(test_user.id, "test_form", context_none)
        edit_cmd = next(c for c in cmds_none if c['id'] == 'edit')
        assert edit_cmd['is_enabled'] is False
        create_cmd = next(c for c in cmds_none if c['id'] == 'create')
        assert create_cmd['is_enabled'] is True

        context_single = {'selection_count': 1}
        cmds_single = manager.get_available_commands(test_user.id, "test_form", context_single)
        edit_cmd = next(c for c in cmds_single if c['id'] == 'edit')
        assert edit_cmd['is_enabled'] is True

        context_multi = {'selection_count': 2}
        cmds_multi = manager.get_available_commands(test_user.id, "test_form", context_multi)
        edit_cmd = next(c for c in cmds_multi if c['id'] == 'edit')
        assert edit_cmd['is_enabled'] is False
        delete_cmd = next(c for c in cmds_multi if c['id'] == 'delete')
        assert delete_cmd['is_enabled'] is True

    def test_command_configuration_persistence(self, db_session, test_user):
        manager = CommandManager(db_session)
        form_id = "custom_form"
        config = [
            {'command_id': 'create', 'is_visible': False},
            {'command_id': 'delete', 'is_in_more_menu': True}
        ]
        manager.save_command_configuration(test_user.id, form_id, config)
        commands = manager.get_available_commands(test_user.id, form_id)
        
        create_cmd = next((c for c in commands if c['id'] == 'create'), None)
        assert create_cmd is None # Hidden commands are filtered out
        
        delete_cmd = next(c for c in commands if c['id'] == 'delete')
        assert delete_cmd['is_in_more_menu'] is True
        
        manager.reset_configuration(test_user.id, form_id)
        commands_reset = manager.get_available_commands(test_user.id, form_id)
        create_cmd_reset = next(c for c in commands_reset if c['id'] == 'create')
        assert create_cmd_reset is not None

class TestDataService:
    """Tests for Data Service"""
    
    @pytest.fixture
    def setup_dependencies(self, db_session):
        """Setup foreign key dependencies for Estimate"""
        # We assume these exist or create them if not. 
        # Since we use shared session, checking existence is good.
        
        import uuid
        
        # Helper to get or create
        def get_or_create(model, **kwargs):
            obj = db_session.query(model).filter_by(name=kwargs.get('name')).first()
            if not obj:
                if 'uuid' not in kwargs:
                    kwargs['uuid'] = str(uuid.uuid4())
                obj = model(**kwargs)
                db_session.add(obj)
                db_session.commit()
                db_session.refresh(obj)
            return obj

        customer = get_or_create(Counterparty, name="Test Customer", is_deleted=False, marked_for_deletion=False)
        obj = get_or_create(Object, name="Test Object", is_deleted=False, marked_for_deletion=False)
        contractor = get_or_create(Organization, name="Test Contractor", is_deleted=False, marked_for_deletion=False)
        
        person = db_session.query(Person).filter_by(full_name="Test Person").first()
        if not person:
            person = Person(full_name="Test Person", is_deleted=False, marked_for_deletion=False, uuid=str(uuid.uuid4()))
            db_session.add(person)
            db_session.commit()
            db_session.refresh(person)
            
        return customer, obj, contractor, person

    def test_pagination_behavior(self, db_session, setup_dependencies, clear_tables):
        """Property 2: Pagination Behavior"""
        cust, obj, _, _ = setup_dependencies
        
        for i in range(25):
            est = Estimate(
                number=f"EST-{i+1:03d}",
                date=date.today(),
                customer_id=cust.id,
                object_id=obj.id
            )
            db_session.add(est)
        db_session.commit()
        
        service = DataService(db_session)
        
        result1 = service.get_documents(Estimate, page=1, page_size=10)
        assert len(result1['items']) == 10
        assert result1['total'] == 25
        assert result1['pages'] == 3
        
        result3 = service.get_documents(Estimate, page=3, page_size=10)
        assert len(result3['items']) == 5
        
        result4 = service.get_documents(Estimate, page=4, page_size=10)
        assert len(result4['items']) == 0

    def test_filtering_and_daterange(self, db_session, setup_dependencies, clear_tables):
        """Property 5 & 13: Search Filtering and Date Range"""
        cust, obj, _, _ = setup_dependencies
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        est1 = Estimate(number="FIND_ME", date=today, customer_id=cust.id, object_id=obj.id)
        est2 = Estimate(number="IGNORE_ME", date=today, customer_id=cust.id, object_id=obj.id)
        est3 = Estimate(number="OLD_ONE", date=yesterday, customer_id=cust.id, object_id=obj.id)
        
        db_session.add_all([est1, est2, est3])
        db_session.commit()
        
        service = DataService(db_session)
        
        res_filter = service.get_documents(Estimate, filters={'number': 'FIND'})
        assert len(res_filter['items']) == 1
        assert res_filter['items'][0].number == "FIND_ME"
        
        res_date = service.get_documents(Estimate, date_range={'start': today, 'end': today})
        assert len(res_date['items']) == 2
        
        res_old = service.get_documents(Estimate, date_range={'end': yesterday})
        assert len(res_old['items']) == 1

    def test_export_scope(self, db_session, setup_dependencies, clear_tables):
        """Property 11: Export Scope Accuracy"""
        cust, obj, _, _ = setup_dependencies
        
        for i in range(5):
            est = Estimate(number=f"EXP-{i}", date=date.today(), customer_id=cust.id, object_id=obj.id)
            db_session.add(est)
        db_session.commit()
        
        service = DataService(db_session)
        
        filters = {'number': 'EXP-1'}
        exported = service.export_documents(Estimate, filters=filters)
        
        assert len(exported) == 1
        assert exported[0].number == "EXP-1"
        
        exported_all = service.export_documents(Estimate)
        assert len(exported_all) >= 5
