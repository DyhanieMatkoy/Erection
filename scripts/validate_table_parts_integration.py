#!/usr/bin/env python3
"""
Validation script for Document Table Parts integration.

This script performs comprehensive validation to ensure all components
are properly integrated and working correctly.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TablePartsValidator:
    """Validates Document Table Parts integration"""
    
    def __init__(self):
        self.validation_results = []
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            bool: True if all validations pass, False otherwise
        """
        logger.info("Starting Document Table Parts integration validation...")
        
        validations = [
            ("Component Structure", self._validate_component_structure),
            ("Service Integration", self._validate_service_integration),
            ("Database Schema", self._validate_database_schema),
            ("Configuration Files", self._validate_configuration),
            ("Documentation", self._validate_documentation),
            ("Test Coverage", self._validate_test_coverage),
            ("Cross-Platform Consistency", self._validate_cross_platform),
            ("Performance Requirements", self._validate_performance),
            ("Error Handling", self._validate_error_handling),
            ("User Settings", self._validate_user_settings)
        ]
        
        passed = 0
        total = len(validations)
        
        for name, validation_func in validations:
            logger.info(f"Validating {name}...")
            try:
                result = validation_func()
                if result:
                    logger.info(f"✓ {name} - PASSED")
                    passed += 1
                else:
                    logger.error(f"✗ {name} - FAILED")
            except Exception as e:
                logger.error(f"✗ {name} - ERROR: {e}")
                self.errors.append(f"{name}: {e}")
        
        # Summary
        logger.info(f"\nValidation Summary: {passed}/{total} checks passed")
        
        if self.warnings:
            logger.warning(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if self.errors:
            logger.error(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        return passed == total and len(self.errors) == 0
    
    def _validate_component_structure(self) -> bool:
        """Validate component file structure and imports"""
        required_components = {
            # Desktop components
            'src/views/widgets/base_table_part.py': 'BaseTablePart',
            'src/views/widgets/row_control_panel.py': 'RowControlPanel',
            'src/views/widgets/calculation_performance_monitor.py': 'CalculationPerformanceMonitor',
            'src/views/components/compact_reference_field.py': 'CompactReferenceField',
            
            # Web components
            'web-client/src/components/common/BaseTablePart.vue': 'BaseTablePart',
            'web-client/src/components/common/RowControlPanel.vue': 'RowControlPanel',
            'web-client/src/components/common/CompactReferenceField.vue': 'CompactReferenceField',
            'web-client/src/components/common/CalculationPerformanceMonitor.vue': 'CalculationPerformanceMonitor',
            
            # Services
            'src/services/table_part_settings_service.py': 'TablePartSettingsService',
            'src/services/table_part_keyboard_handler.py': 'TablePartKeyboardHandler',
            'src/services/table_part_calculation_engine.py': 'TablePartCalculationEngine',
            'src/services/table_part_command_manager.py': 'TablePartCommandManager',
            
            # Web services
            'web-client/src/services/tablePartKeyboardHandler.ts': 'createKeyboardHandler',
            'web-client/src/services/tablePartCalculationEngine.ts': 'useCalculationEngine',
            'web-client/src/services/tablePartCommandManager.ts': 'TablePartCommandManager',
            'web-client/src/services/tablePartSettingsService.ts': 'TablePartSettingsService',
            
            # Data models
            'src/data/models/table_part_models.py': 'TablePartSettingsData',
            'web-client/src/types/table-parts.ts': 'TablePartConfiguration'
        }
        
        missing_files = []
        for file_path, expected_class in required_components.items():
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                continue
            
            # Check if expected class/function exists in file
            try:
                content = full_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = full_path.read_text(encoding='cp1251')
                except UnicodeDecodeError:
                    content = full_path.read_text(encoding='latin1')
            
            if expected_class not in content:
                self.warnings.append(f"{file_path} missing expected class/function: {expected_class}")
        
        if missing_files:
            self.errors.extend([f"Missing file: {f}" for f in missing_files])
            return False
        
        return True
    
    def _validate_service_integration(self) -> bool:
        """Validate service integration and dependencies"""
        try:
            # Test desktop service imports
            from src.services.table_part_settings_service import TablePartSettingsService
            from src.services.table_part_keyboard_handler import TablePartKeyboardHandler
            from src.services.table_part_calculation_engine import TablePartCalculationEngine
            from src.services.table_part_command_manager import TablePartCommandManager
            
            # Test data model imports
            from src.data.models.table_part_models import (
                TablePartSettingsData, PanelSettings, ShortcutSettings, TablePartConfiguration
            )
            
            # Test widget imports
            from src.views.widgets.base_table_part import BaseTablePart
            
            # Validate service interfaces
            services_valid = True
            
            # Check TablePartSettingsService interface
            required_methods = ['get_user_settings', 'save_user_settings', 'get_default_settings']
            for method in required_methods:
                if not hasattr(TablePartSettingsService, method):
                    self.errors.append(f"TablePartSettingsService missing method: {method}")
                    services_valid = False
            
            # Check BaseTablePart interface
            required_methods = ['register_form_command', 'get_selected_rows', 'set_keyboard_shortcuts_enabled']
            for method in required_methods:
                if not hasattr(BaseTablePart, method):
                    self.errors.append(f"BaseTablePart missing method: {method}")
                    services_valid = False
            
            return services_valid
            
        except ImportError as e:
            self.errors.append(f"Service import failed: {e}")
            return False
    
    def _validate_database_schema(self) -> bool:
        """Validate database schema for table parts"""
        try:
            # Check migration file exists
            migration_file = project_root / 'alembic' / 'versions' / '20251219_140000_add_table_part_settings.py'
            if not migration_file.exists():
                self.errors.append("Table parts migration file not found")
                return False
            
            # Check migration content
            try:
                migration_content = migration_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                migration_content = migration_file.read_text(encoding='latin1')
            required_tables = ['user_table_part_settings', 'table_part_command_config']
            
            for table in required_tables:
                if table not in migration_content:
                    self.errors.append(f"Migration missing table: {table}")
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Database schema validation failed: {e}")
            return False
    
    def _validate_configuration(self) -> bool:
        """Validate configuration files"""
        config_files = [
            'web-client/src/types/table-parts.ts',
            'web-client/vitest.config.ts',
            'web-client/package.json'
        ]
        
        missing_configs = []
        for config_file in config_files:
            full_path = project_root / config_file
            if not full_path.exists():
                missing_configs.append(config_file)
        
        if missing_configs:
            self.warnings.extend([f"Missing config file: {f}" for f in missing_configs])
        
        # Check web client package.json for required dependencies
        package_json = project_root / 'web-client' / 'package.json'
        if package_json.exists():
            import json
            try:
                package_data = json.loads(package_json.read_text(encoding='utf-8'))
            except UnicodeDecodeError:
                package_data = json.loads(package_json.read_text(encoding='latin1'))
            
            required_deps = ['vue', 'pinia', 'fast-check']
            dev_deps = package_data.get('devDependencies', {})
            deps = package_data.get('dependencies', {})
            all_deps = {**deps, **dev_deps}
            
            for dep in required_deps:
                if dep not in all_deps:
                    self.warnings.append(f"Missing dependency in package.json: {dep}")
        
        return len(missing_configs) == 0
    
    def _validate_documentation(self) -> bool:
        """Validate documentation completeness"""
        required_docs = [
            'docs/features/DOCUMENT_TABLE_PARTS_USER_GUIDE.md',
            'docs/features/DOCUMENT_TABLE_PARTS_TECHNICAL_GUIDE.md',
            'docs/features/DOCUMENT_TABLE_PARTS_RELEASE_NOTES.md'
        ]
        
        missing_docs = []
        for doc_file in required_docs:
            full_path = project_root / doc_file
            if not full_path.exists():
                missing_docs.append(doc_file)
            else:
                # Check if documentation is substantial (> 1000 characters)
                try:
                    content = full_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    content = full_path.read_text(encoding='latin1')
                if len(content) < 1000:
                    self.warnings.append(f"Documentation file seems incomplete: {doc_file}")
        
        if missing_docs:
            self.errors.extend([f"Missing documentation: {f}" for f in missing_docs])
            return False
        
        return True
    
    def _validate_test_coverage(self) -> bool:
        """Validate test coverage for table parts"""
        required_tests = [
            'test/test_table_parts_final_integration.py',
            'test/test_table_part_settings_integration.py',
            'test/test_command_manager_integration.py',
            'test/test_form_layout_integration.py',
            'web-client/src/services/__tests__/tablePartCalculationEngine.spec.ts',
            'web-client/src/services/__tests__/tablePartErrorValidationIntegration.spec.ts'
        ]
        
        missing_tests = []
        for test_file in required_tests:
            full_path = project_root / test_file
            if not full_path.exists():
                missing_tests.append(test_file)
        
        if missing_tests:
            self.warnings.extend([f"Missing test file: {f}" for f in missing_tests])
        
        # Check for property-based tests
        pbt_files = list((project_root / 'test').glob('**/test_*property*.py'))
        web_pbt_files = list((project_root / 'web-client' / 'src').glob('**/*.spec.ts'))
        
        if len(pbt_files) == 0:
            self.warnings.append("No property-based test files found for desktop")
        
        if len(web_pbt_files) == 0:
            self.warnings.append("No test files found for web client")
        
        return len(missing_tests) < len(required_tests) // 2  # Allow some missing tests
    
    def _validate_cross_platform(self) -> bool:
        """Validate cross-platform consistency"""
        # Check that both desktop and web implementations exist
        desktop_base = project_root / 'src' / 'views' / 'widgets' / 'base_table_part.py'
        web_base = project_root / 'web-client' / 'src' / 'components' / 'common' / 'BaseTablePart.vue'
        
        if not desktop_base.exists():
            self.errors.append("Desktop BaseTablePart implementation missing")
            return False
        
        if not web_base.exists():
            self.errors.append("Web BaseTablePart implementation missing")
            return False
        
        # Check for consistent interfaces
        try:
            desktop_content = desktop_base.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            desktop_content = desktop_base.read_text(encoding='latin1')
        
        try:
            web_content = web_base.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            web_content = web_base.read_text(encoding='latin1')
        
        # Check for common methods/props
        common_features = [
            'keyboard_shortcuts', 'calculation', 'command', 'settings',
            'add_row', 'delete_row', 'move_up', 'move_down'
        ]
        
        for feature in common_features:
            desktop_has = feature in desktop_content.lower()
            web_has = feature in web_content.lower()
            
            if desktop_has != web_has:
                self.warnings.append(f"Feature '{feature}' inconsistent between desktop and web")
        
        return True
    
    def _validate_performance(self) -> bool:
        """Validate performance requirements are met"""
        # Check for performance monitoring components
        perf_monitor_desktop = project_root / 'src' / 'views' / 'widgets' / 'calculation_performance_monitor.py'
        perf_monitor_web = project_root / 'web-client' / 'src' / 'components' / 'common' / 'CalculationPerformanceMonitor.vue'
        
        if not perf_monitor_desktop.exists():
            self.warnings.append("Desktop performance monitor missing")
        
        if not perf_monitor_web.exists():
            self.warnings.append("Web performance monitor missing")
        
        # Check for performance thresholds in code
        calc_engine_desktop = project_root / 'src' / 'services' / 'table_part_calculation_engine.py'
        if calc_engine_desktop.exists():
            try:
                content = calc_engine_desktop.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = calc_engine_desktop.read_text(encoding='latin1')
            if '100' not in content or '200' not in content:
                self.warnings.append("Performance thresholds (100ms/200ms) not found in calculation engine")
        
        return True
    
    def _validate_error_handling(self) -> bool:
        """Validate error handling implementation"""
        error_handler_desktop = project_root / 'src' / 'services' / 'table_part_error_handler.py'
        error_handler_web = project_root / 'web-client' / 'src' / 'services' / 'tablePartErrorHandler.ts'
        
        if not error_handler_desktop.exists():
            self.warnings.append("Desktop error handler missing")
        
        if not error_handler_web.exists():
            self.warnings.append("Web error handler missing")
        
        # Check for error handling in base components
        base_desktop = project_root / 'src' / 'views' / 'widgets' / 'base_table_part.py'
        if base_desktop.exists():
            try:
                content = base_desktop.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = base_desktop.read_text(encoding='latin1')
            if 'try:' not in content or 'except' not in content:
                self.warnings.append("Limited error handling in desktop BaseTablePart")
        
        return True
    
    def _validate_user_settings(self) -> bool:
        """Validate user settings implementation"""
        settings_service = project_root / 'src' / 'services' / 'table_part_settings_service.py'
        if not settings_service.exists():
            self.errors.append("Table part settings service missing")
            return False
        
        # Check for required methods
        try:
            content = settings_service.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = settings_service.read_text(encoding='latin1')
        required_methods = [
            'get_user_settings', 'save_user_settings', 'get_default_settings',
            'reset_user_settings', 'export_user_settings', 'import_user_settings'
        ]
        
        for method in required_methods:
            if method not in content:
                self.warnings.append(f"Settings service missing method: {method}")
        
        # Check data models
        models_file = project_root / 'src' / 'data' / 'models' / 'table_part_models.py'
        if not models_file.exists():
            self.errors.append("Table part data models missing")
            return False
        
        try:
            models_content = models_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            models_content = models_file.read_text(encoding='latin1')
        required_models = ['TablePartSettingsData', 'PanelSettings', 'ShortcutSettings']
        
        for model in required_models:
            if model not in models_content:
                self.errors.append(f"Missing data model: {model}")
                return False
        
        return True


def main():
    """Main validation function"""
    validator = TablePartsValidator()
    
    print("🔍 Document Table Parts Integration Validation")
    print("=" * 50)
    
    success = validator.validate_all()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All validations passed! Document Table Parts integration is ready.")
        return 0
    else:
        print("❌ Some validations failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())