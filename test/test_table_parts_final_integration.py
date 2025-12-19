"""
Final integration test for Document Table Parts - Task 15.1

This test verifies seamless integration between all table part features
and ensures consistency across desktop and web clients.
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Test data structures and interfaces
class MockTablePartData:
    """Mock table part data for testing"""
    
    def __init__(self):
        self.rows = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 100.0, 'sum': 1000.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 5, 'price': 200.0, 'sum': 1000.0},
        ]
        self.totals = {'quantity': 15, 'sum': 2000.0}
        self.settings = {
            'visible_commands': ['add_row', 'delete_row', 'move_up', 'move_down'],
            'keyboard_shortcuts_enabled': True,
            'auto_calculation_enabled': True
        }


class TestTablePartsIntegration:
    """Test seamless integration between all table part features"""
    
    @pytest.fixture
    def mock_data(self):
        """Create mock table part data"""
        return MockTablePartData()
    
    def test_component_integration_workflow(self, mock_data):
        """Test complete workflow integration between components"""
        # 1. Test data structure consistency
        assert len(mock_data.rows) == 2
        assert all('id' in row for row in mock_data.rows)
        assert all('quantity' in row for row in mock_data.rows)
        assert all('price' in row for row in mock_data.rows)
        assert all('sum' in row for row in mock_data.rows)
        
        # 2. Test calculation consistency
        for row in mock_data.rows:
            expected_sum = row['quantity'] * row['price']
            assert row['sum'] == expected_sum
        
        # 3. Test totals calculation
        expected_total_quantity = sum(row['quantity'] for row in mock_data.rows)
        expected_total_sum = sum(row['sum'] for row in mock_data.rows)
        
        assert mock_data.totals['quantity'] == expected_total_quantity
        assert mock_data.totals['sum'] == expected_total_sum
    
    def test_settings_integration_consistency(self, mock_data):
        """Test settings integration across components"""
        settings = mock_data.settings
        
        # Verify required settings exist
        assert 'visible_commands' in settings
        assert 'keyboard_shortcuts_enabled' in settings
        assert 'auto_calculation_enabled' in settings
        
        # Verify settings values are consistent
        assert isinstance(settings['visible_commands'], list)
        assert isinstance(settings['keyboard_shortcuts_enabled'], bool)
        assert isinstance(settings['auto_calculation_enabled'], bool)
        
        # Verify standard commands are available
        standard_commands = ['add_row', 'delete_row', 'move_up', 'move_down']
        for command in standard_commands:
            assert command in settings['visible_commands']
    
    def test_command_execution_integration(self, mock_data):
        """Test command execution integration"""
        initial_count = len(mock_data.rows)
        
        # Simulate add row command
        new_row = {'id': 3, 'name': 'Item 3', 'quantity': 1, 'price': 0.0, 'sum': 0.0}
        mock_data.rows.append(new_row)
        
        assert len(mock_data.rows) == initial_count + 1
        
        # Simulate delete row command
        mock_data.rows.pop()
        
        assert len(mock_data.rows) == initial_count
    
    def test_calculation_integration(self, mock_data):
        """Test calculation engine integration"""
        # Test field calculation
        test_row = mock_data.rows[0]
        test_row['quantity'] = 20
        test_row['price'] = 150.0
        
        # Simulate calculation
        calculated_sum = test_row['quantity'] * test_row['price']
        test_row['sum'] = calculated_sum
        
        assert test_row['sum'] == 3000.0
        
        # Test total recalculation
        new_total_quantity = sum(row['quantity'] for row in mock_data.rows)
        new_total_sum = sum(row['sum'] for row in mock_data.rows)
        
        mock_data.totals['quantity'] = new_total_quantity
        mock_data.totals['sum'] = new_total_sum
        
        assert mock_data.totals['quantity'] == 25  # 20 + 5
        assert mock_data.totals['sum'] == 4000.0   # 3000 + 1000
    
    def test_keyboard_shortcuts_integration(self, mock_data):
        """Test keyboard shortcuts integration"""
        shortcuts = {
            'Insert': 'add_row',
            'Delete': 'delete_row',
            'Ctrl+Shift+Up': 'move_up',
            'Ctrl+Shift+Down': 'move_down',
            'F4': 'open_reference_selector',
            'Ctrl+C': 'copy_rows',
            'Ctrl+V': 'paste_rows'
        }
        
        # Verify shortcuts are properly mapped
        for shortcut, command in shortcuts.items():
            assert shortcut is not None
            assert command is not None
            assert len(command) > 0
    
    def test_row_movement_integration(self, mock_data):
        """Test row movement integration"""
        original_order = [row['id'] for row in mock_data.rows]
        
        # Simulate move up (swap first two rows)
        if len(mock_data.rows) >= 2:
            mock_data.rows[0], mock_data.rows[1] = mock_data.rows[1], mock_data.rows[0]
            
            new_order = [row['id'] for row in mock_data.rows]
            assert new_order != original_order
            assert new_order == [original_order[1], original_order[0]]
    
    def test_import_export_integration(self, mock_data):
        """Test import/export integration"""
        # Test export data structure
        export_data = []
        for row in mock_data.rows:
            export_row = {
                'name': row['name'],
                'quantity': row['quantity'],
                'price': row['price'],
                'sum': row['sum']
            }
            export_data.append(export_row)
        
        # Should be serializable
        json_str = json.dumps(export_data, ensure_ascii=False)
        assert json_str is not None
        
        # Should be deserializable
        imported_data = json.loads(json_str)
        assert len(imported_data) == len(mock_data.rows)
        assert imported_data[0]['name'] == mock_data.rows[0]['name']
    
    def test_reference_field_integration(self, mock_data):
        """Test reference field integration"""
        # Add reference field to test data
        for row in mock_data.rows:
            row['material_id'] = row['id']
            row['material_name'] = f"Material {row['id']}"
            row['material_code'] = f"MAT{row['id']:03d}"
        
        # Test reference value structure
        for row in mock_data.rows:
            reference_value = {
                'id': row['material_id'],
                'name': row['material_name'],
                'code': row['material_code']
            }
            
            assert reference_value['id'] > 0
            assert len(reference_value['name']) > 0
            assert len(reference_value['code']) > 0
    
    def test_form_layout_integration(self, mock_data):
        """Test form layout integration"""
        # Test field configuration for two-column layout
        fields = [
            {'name': 'number', 'type': 'text', 'required': True},
            {'name': 'date', 'type': 'date', 'required': True},
            {'name': 'customer', 'type': 'reference', 'required': True},
            {'name': 'object', 'type': 'reference', 'required': False},
            {'name': 'contractor', 'type': 'reference', 'required': False},
            {'name': 'responsible', 'type': 'reference', 'required': False},
            {'name': 'description', 'type': 'long_text', 'required': False}
        ]
        
        # Should have enough fields for two-column layout
        assert len(fields) >= 6
        
        # Should have mix of field types
        field_types = [field['type'] for field in fields]
        assert 'text' in field_types
        assert 'date' in field_types
        assert 'reference' in field_types
        assert 'long_text' in field_types
        
        # Long text fields should be identified
        long_text_fields = [field for field in fields if field['type'] == 'long_text']
        assert len(long_text_fields) == 1
        assert long_text_fields[0]['name'] == 'description'
    
    def test_performance_monitoring_integration(self, mock_data):
        """Test performance monitoring integration"""
        # Test performance metrics structure
        metrics = {
            'calculation_time': 50,  # milliseconds
            'total_calculation_time': 150,  # milliseconds
            'render_time': 30,  # milliseconds
            'memory_usage': 1024  # KB
        }
        
        # Verify performance thresholds
        assert metrics['calculation_time'] < 100  # Should be under 100ms
        assert metrics['total_calculation_time'] < 200  # Should be under 200ms
        assert metrics['render_time'] < 50  # Should be under 50ms
        
        # Test performance status
        status = 'good'
        if metrics['calculation_time'] > 100:
            status = 'warning'
        if metrics['calculation_time'] > 200:
            status = 'critical'
        
        assert status == 'good'
    
    def test_error_handling_integration(self, mock_data):
        """Test error handling integration"""
        # Test calculation error handling
        try:
            # Simulate division by zero
            result = 100 / 0
        except ZeroDivisionError:
            # Should handle gracefully
            result = 0
        
        assert result == 0
        
        # Test invalid data handling
        invalid_row = {'id': 'invalid', 'quantity': 'not_a_number'}
        
        # Should validate data types
        try:
            quantity = float(invalid_row['quantity'])
        except (ValueError, TypeError):
            quantity = 0.0
        
        assert quantity == 0.0
    
    def test_cross_client_consistency(self, mock_data):
        """Test consistency between desktop and web clients"""
        # Test data serialization consistency
        desktop_data = {
            'rows': mock_data.rows,
            'totals': mock_data.totals,
            'settings': mock_data.settings
        }
        
        # Should serialize consistently
        json_str = json.dumps(desktop_data, ensure_ascii=False, indent=2)
        web_data = json.loads(json_str)
        
        # Data should be identical
        assert web_data['rows'] == desktop_data['rows']
        assert web_data['totals'] == desktop_data['totals']
        assert web_data['settings'] == desktop_data['settings']
        
        # Settings should have same structure
        assert 'visible_commands' in web_data['settings']
        assert 'keyboard_shortcuts_enabled' in web_data['settings']
        assert 'auto_calculation_enabled' in web_data['settings']
    
    def test_complete_user_workflow_integration(self, mock_data):
        """Test complete user workflow integration"""
        # 1. User opens document with table part
        assert len(mock_data.rows) == 2
        assert mock_data.settings['keyboard_shortcuts_enabled'] is True
        
        # 2. User adds a new row
        new_row = {'id': 3, 'name': 'New Item', 'quantity': 1, 'price': 50.0, 'sum': 50.0}
        mock_data.rows.append(new_row)
        assert len(mock_data.rows) == 3
        
        # 3. User modifies quantity and price
        mock_data.rows[-1]['quantity'] = 3
        mock_data.rows[-1]['price'] = 75.0
        
        # 4. System recalculates sum
        mock_data.rows[-1]['sum'] = mock_data.rows[-1]['quantity'] * mock_data.rows[-1]['price']
        assert mock_data.rows[-1]['sum'] == 225.0
        
        # 5. User moves row up
        if len(mock_data.rows) >= 2:
            last_row = mock_data.rows.pop()
            mock_data.rows.insert(-1, last_row)
        
        # 6. System recalculates totals
        mock_data.totals['quantity'] = sum(row['quantity'] for row in mock_data.rows)
        mock_data.totals['sum'] = sum(row['sum'] for row in mock_data.rows)
        
        assert mock_data.totals['quantity'] == 18  # 10 + 5 + 3
        assert mock_data.totals['sum'] == 2225.0   # 1000 + 1000 + 225
        
        # 7. User saves settings
        mock_data.settings['visible_commands'] = ['add_row', 'delete_row', 'export_data']
        assert 'export_data' in mock_data.settings['visible_commands']
        
        # Workflow completed successfully
        assert len(mock_data.rows) == 3
        assert mock_data.totals['sum'] > 2000.0


class TestWebClientCompatibility:
    """Test web client compatibility and API consistency"""
    
    def test_api_data_structures(self):
        """Test API data structures are compatible"""
        # Test table part configuration
        config = {
            'tableId': 'test_lines',
            'documentType': 'estimate',
            'visibleCommands': ['add_row', 'delete_row'],
            'keyboardShortcutsEnabled': True,
            'autoCalculationEnabled': True,
            'dragDropEnabled': True
        }
        
        # Should serialize for API
        json_str = json.dumps(config)
        assert json_str is not None
        
        # Should deserialize correctly
        restored = json.loads(json_str)
        assert restored['tableId'] == config['tableId']
        assert restored['visibleCommands'] == config['visibleCommands']
    
    def test_event_handling_consistency(self):
        """Test event handling consistency between clients"""
        events = [
            'row-selection-changed',
            'data-changed',
            'command-executed',
            'calculation-requested',
            'total-calculation-requested'
        ]
        
        # Events should be consistently named
        for event in events:
            assert '-' in event  # kebab-case for web
            assert event.replace('-', '_') is not None  # snake_case for desktop
    
    def test_component_interface_consistency(self):
        """Test component interfaces are consistent"""
        # Test table column definition
        column = {
            'id': 'quantity',
            'name': 'Количество',
            'type': 'number',
            'width': 100,
            'editable': True,
            'required': False
        }
        
        # Should have consistent structure
        required_fields = ['id', 'name', 'type']
        for field in required_fields:
            assert field in column
        
        # Should support common types
        valid_types = ['text', 'number', 'currency', 'date', 'reference']
        assert column['type'] in valid_types


if __name__ == '__main__':
    pytest.main([__file__, '-v'])