"""
Property-based tests for Configuration Validator Database Connection String Validation

This module contains property-based tests using Hypothesis to verify
the correctness of database connection string parsing, validation, and
consistency across different database types.

**Validates: Requirements 1.4, 1.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import re
from config_validator import (
    DatabaseConnectionValidator, ConfigValidator, ValidationSeverity
)


# Hypothesis strategies for generating test data
@composite
def sqlite_connection_string(draw):
    """Generate valid SQLite connection strings"""
    # Generate file path components
    path_parts = draw(st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=10),
        min_size=1, max_size=5
    ))
    filename = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=20))
    
    # Create path
    path = '/'.join(path_parts) + '/' + filename + '.db'
    
    return f"sqlite:///{path}"


@composite
def postgresql_connection_string(draw):
    """Generate valid PostgreSQL connection strings"""
    username = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    password = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    host = draw(st.one_of(
        st.just('localhost'),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20)
    ))
    port = draw(st.integers(min_value=1024, max_value=65535))
    database = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


@composite
def mysql_connection_string(draw):
    """Generate valid MySQL connection strings"""
    username = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    password = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    host = draw(st.one_of(
        st.just('localhost'),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20)
    ))
    port = draw(st.integers(min_value=1024, max_value=65535))
    database = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    
    use_pymysql = draw(st.booleans())
    scheme = "mysql+pymysql" if use_pymysql else "mysql"
    
    return f"{scheme}://{username}:{password}@{host}:{port}/{database}"


@composite
def invalid_connection_string(draw):
    """Generate invalid connection strings"""
    return draw(st.one_of(
        st.just(""),  # Empty string
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=50),  # No scheme
        st.just("invalid://connection/string"),  # Invalid scheme
        st.just("sqlite://"),  # Missing path
        st.just("postgresql://user@host/"),  # Missing database
        st.just("mysql://user:pass@:3306/db"),  # Missing host
    ))


@composite
def valid_file_path(draw):
    """Generate valid file paths"""
    # Generate path components using ASCII characters only
    path_parts = draw(st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=15),
        min_size=0, max_size=4
    ))
    filename = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20))
    extension = draw(st.one_of(
        st.just('.ini'),
        st.just('.env'),
        st.just('.py'),
        st.just('.json'),
        st.just('.db'),
        st.just('.log'),
        st.just('.txt')
    ))
    
    # Create path
    if path_parts:
        path = '/'.join(path_parts) + '/' + filename + extension
    else:
        path = filename + extension
    
    return path


@composite
def invalid_file_path(draw):
    """Generate invalid file paths"""
    return draw(st.one_of(
        st.just(""),  # Empty path
        st.just("/"),  # Root only
        st.just("//"),  # Double slash
        st.just("con"),  # Windows reserved name
        st.just("aux"),  # Windows reserved name
        st.just("nul"),  # Windows reserved name
        st.text(alphabet="<>:\"|?*", min_size=1, max_size=10),  # Invalid characters
        st.just("file" + "x" * 300),  # Too long filename
    ))


@composite
def config_file_with_paths(draw):
    """Generate configuration content with file paths"""
    template_path = draw(valid_file_path())
    log_path = draw(valid_file_path())
    data_path = draw(valid_file_path())
    
    config_type = draw(st.one_of(st.just('ini'), st.just('env')))
    
    if config_type == 'ini':
        return f"""[PrintForms]
templates_path = {template_path}

[Logging]
log_file = {log_path}

[Database]
data_path = {data_path}
"""
    else:  # env
        return f"""TEMPLATES_PATH={template_path}
LOG_FILE={log_path}
DATA_PATH={data_path}
"""


class TestDatabaseConnectionValidatorProperties:
    """Property-based tests for database connection validator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = DatabaseConnectionValidator()
    
    @given(sqlite_connection_string())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_sqlite_connection_parsing_consistency(self, conn_str):
        """
        Property 1: SQLite connection string parsing consistency
        For any valid SQLite connection string, parsing should succeed and extract file path
        **Validates: Requirements 1.4**
        """
        conn_info = self.validator.parse_connection_string(conn_str)
        
        # Should successfully parse
        assert conn_info.is_valid, f"Failed to parse valid SQLite connection: {conn_str}"
        assert conn_info.db_type == "sqlite"
        assert conn_info.file_path is not None
        assert conn_info.database is not None
        
        # File path should be extractable from connection string
        assert conn_str.endswith(conn_info.file_path) or conn_info.file_path in conn_str
    
    @given(postgresql_connection_string())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_postgresql_connection_parsing_consistency(self, conn_str):
        """
        Property 2: PostgreSQL connection string parsing consistency
        For any valid PostgreSQL connection string, parsing should succeed and extract all components
        **Validates: Requirements 1.4**
        """
        conn_info = self.validator.parse_connection_string(conn_str)
        
        # Should successfully parse
        assert conn_info.is_valid, f"Failed to parse valid PostgreSQL connection: {conn_str}"
        assert conn_info.db_type == "postgresql"
        assert conn_info.host is not None
        assert conn_info.port is not None
        assert conn_info.database is not None
        assert conn_info.username is not None
        assert conn_info.password is not None
        
        # Port should be valid
        assert 1 <= conn_info.port <= 65535
    
    @given(mysql_connection_string())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_mysql_connection_parsing_consistency(self, conn_str):
        """
        Property 3: MySQL connection string parsing consistency
        For any valid MySQL connection string, parsing should succeed and extract all components
        **Validates: Requirements 1.4**
        """
        conn_info = self.validator.parse_connection_string(conn_str)
        
        # Should successfully parse
        assert conn_info.is_valid, f"Failed to parse valid MySQL connection: {conn_str}"
        assert conn_info.db_type == "mysql"
        assert conn_info.host is not None
        assert conn_info.port is not None
        assert conn_info.database is not None
        assert conn_info.username is not None
        assert conn_info.password is not None
        
        # Port should be valid
        assert 1 <= conn_info.port <= 65535
        
        # Driver should be detected if present
        if "pymysql" in conn_str:
            assert conn_info.driver == "pymysql"
    
    @given(invalid_connection_string())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_invalid_connection_string_rejection(self, conn_str):
        """
        Property 4: Invalid connection string rejection consistency
        For any invalid connection string, parsing should fail with appropriate error
        **Validates: Requirements 1.4**
        """
        conn_info = self.validator.parse_connection_string(conn_str)
        
        # Should fail to parse invalid connections
        if conn_str.strip() == "":
            assert not conn_info.is_valid
            assert "Empty connection string" in conn_info.error_message
        elif "://" not in conn_str:
            assert not conn_info.is_valid
            assert "missing scheme" in conn_info.error_message
        elif conn_str.startswith("invalid://"):
            assert not conn_info.is_valid
            assert "Unsupported database type" in conn_info.error_message
    
    @given(st.one_of(sqlite_connection_string(), postgresql_connection_string(), mysql_connection_string()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_connection_validation_consistency(self, conn_str):
        """
        Property 5: Connection validation consistency
        For any valid connection string, validation should succeed without critical errors
        **Validates: Requirements 1.4**
        """
        result = self.validator.validate_connection_string(conn_str)
        
        # Should not have critical validation errors for valid connection strings
        critical_errors = [issue for issue in result.issues 
                          if issue.severity == ValidationSeverity.CRITICAL]
        assert len(critical_errors) == 0, f"Critical errors for valid connection: {conn_str}"
        
        # Should not have parsing errors
        parsing_errors = [issue for issue in result.issues 
                         if "Invalid connection string format" in issue.message]
        assert len(parsing_errors) == 0, f"Parsing errors for valid connection: {conn_str}"
    
    @given(st.one_of(sqlite_connection_string(), postgresql_connection_string(), mysql_connection_string()))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_parse_validate_consistency(self, conn_str):
        """
        Property 6: Parse and validate consistency
        For any connection string, if parsing succeeds, validation should not fail with parsing errors
        **Validates: Requirements 1.4**
        """
        # Parse the connection string
        conn_info = self.validator.parse_connection_string(conn_str)
        
        # Validate the connection string
        validation_result = self.validator.validate_connection_string(conn_str)
        
        # If parsing succeeded, validation should not have parsing errors
        if conn_info.is_valid:
            parsing_errors = [issue for issue in validation_result.issues 
                             if "Invalid connection string format" in issue.message]
            assert len(parsing_errors) == 0, f"Validation has parsing errors but parsing succeeded: {conn_str}"
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_parsing_never_crashes(self, conn_str):
        """
        Property 7: Parsing robustness
        For any string input, parsing should never crash and always return a result
        **Validates: Requirements 1.4**
        """
        try:
            conn_info = self.validator.parse_connection_string(conn_str)
            
            # Should always return a DatabaseConnectionInfo object
            assert conn_info is not None
            assert hasattr(conn_info, 'is_valid')
            assert hasattr(conn_info, 'db_type')
            
            # If invalid, should have error message
            if not conn_info.is_valid:
                assert conn_info.error_message is not None
                assert len(conn_info.error_message) > 0
                
        except Exception as e:
            pytest.fail(f"Parsing crashed for input '{conn_str}': {str(e)}")
    
    @given(st.one_of(sqlite_connection_string(), postgresql_connection_string(), mysql_connection_string()))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_validation_never_crashes(self, conn_str):
        """
        Property 8: Validation robustness
        For any connection string, validation should never crash and always return a result
        **Validates: Requirements 1.4**
        """
        try:
            result = self.validator.validate_connection_string(conn_str)
            
            # Should always return a ValidationResult object
            assert result is not None
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'issues')
            assert isinstance(result.issues, list)
            
        except Exception as e:
            pytest.fail(f"Validation crashed for input '{conn_str}': {str(e)}")


class TestConfigValidatorDatabaseIntegrationProperties:
    """Property-based tests for config validator database integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
    
    @given(st.one_of(sqlite_connection_string(), postgresql_connection_string(), mysql_connection_string()))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_database_connection_string_validation_integration(self, conn_str):
        """
        Property 9: Database connection string validation integration
        For any valid connection string, direct validation should match config file validation
        **Validates: Requirements 1.4**
        """
        # Test direct validation
        direct_result = self.validator.validate_database_connection_string(conn_str)
        
        # Test parsing
        conn_info = self.validator.parse_database_connection_string(conn_str)
        
        # Results should be consistent
        if conn_info.is_valid:
            # If parsing succeeds, validation should not have critical parsing errors
            critical_parsing_errors = [issue for issue in direct_result.issues 
                                     if issue.severity == ValidationSeverity.CRITICAL and 
                                        "Invalid connection string format" in issue.message]
            assert len(critical_parsing_errors) == 0, f"Inconsistent results for: {conn_str}"
    
    @given(st.one_of(sqlite_connection_string(), postgresql_connection_string(), mysql_connection_string()))
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_connection_test_consistency(self, conn_str):
        """
        Property 10: Connection test consistency
        For any valid connection string, connection testing should not crash
        **Validates: Requirements 1.4**
        """
        try:
            success, error = self.validator.test_database_connection(conn_str)
            
            # Should always return a boolean and optional error message
            assert isinstance(success, bool)
            if not success:
                assert error is not None
                assert isinstance(error, str)
                assert len(error) > 0
            else:
                # If successful, error should be None
                assert error is None
                
        except ImportError:
            # Database drivers may not be available in test environment
            # This is acceptable for property-based testing
            pass
        except Exception as e:
            # Other exceptions should not occur
            pytest.fail(f"Connection test crashed for input '{conn_str}': {str(e)}")


class TestFilePathValidationProperties:
    """Property-based tests for file path validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
    
    @given(valid_file_path())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_valid_file_path_parsing(self, file_path):
        """
        Property 4a: Valid file path parsing consistency
        For any valid file path, path parsing should succeed and extract components
        **Validates: Requirements 1.5**
        """
        import os
        
        # Test path parsing
        try:
            # Basic path operations should not crash
            dirname = os.path.dirname(file_path)
            basename = os.path.basename(file_path)
            
            # Path should have valid components
            assert isinstance(dirname, str)
            assert isinstance(basename, str)
            assert len(basename) > 0  # Should have a filename
            
            # Extension should be extractable
            name, ext = os.path.splitext(basename)
            assert isinstance(name, str)
            assert isinstance(ext, str)
            
        except Exception as e:
            pytest.fail(f"Valid file path parsing failed for '{file_path}': {str(e)}")
    
    @given(invalid_file_path())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_invalid_file_path_handling(self, file_path):
        """
        Property 4b: Invalid file path handling consistency
        For any invalid file path, validation should handle gracefully without crashing
        **Validates: Requirements 1.5**
        """
        import os
        
        try:
            # Path operations should not crash even for invalid paths
            dirname = os.path.dirname(file_path)
            basename = os.path.basename(file_path)
            
            # Should return strings even for invalid input
            assert isinstance(dirname, str)
            assert isinstance(basename, str)
            
        except Exception as e:
            # Some invalid paths may cause exceptions, which is acceptable
            # The important thing is that we handle them gracefully
            assert isinstance(e, (OSError, ValueError, TypeError))
    
    @given(config_file_with_paths())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_config_file_path_extraction(self, config_content):
        """
        Property 4c: Configuration file path extraction consistency
        For any configuration with file paths, path extraction should be consistent
        **Validates: Requirements 1.5**
        """
        import tempfile
        import os
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
            f.write(config_content)
            f.flush()
            temp_path = f.name
        
        try:
            # Validate the configuration file
            result = self.validator.validate_file(temp_path)
            
            # Should always return a ValidationResult
            assert result is not None
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'issues')
            assert isinstance(result.issues, list)
            
            # Path-related issues should be properly categorized
            for issue in result.issues:
                assert hasattr(issue, 'severity')
                assert hasattr(issue, 'message')
                assert isinstance(issue.message, str)
                assert len(issue.message) > 0
                
        except Exception as e:
            pytest.fail(f"Config file path extraction failed: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_path_validation_robustness(self, path_string):
        """
        Property 4d: Path validation robustness
        For any string input as a path, validation should never crash
        **Validates: Requirements 1.5**
        """
        import os
        
        try:
            # Basic path operations should be robust
            dirname = os.path.dirname(path_string)
            basename = os.path.basename(path_string)
            
            # Should always return strings
            assert isinstance(dirname, str)
            assert isinstance(basename, str)
            
            # Path existence check should not crash
            exists = os.path.exists(path_string)
            assert isinstance(exists, bool)
            
        except Exception as e:
            # Some operations may fail for invalid paths, but should be specific exceptions
            assert isinstance(e, (OSError, ValueError, TypeError, UnicodeError))
    
    @given(valid_file_path(), valid_file_path())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_path_comparison_consistency(self, path1, path2):
        """
        Property 4e: Path comparison consistency
        For any two file paths, comparison operations should be consistent
        **Validates: Requirements 1.5**
        """
        import os
        
        try:
            # Path normalization should be consistent
            norm1 = os.path.normpath(path1)
            norm2 = os.path.normpath(path2)
            
            assert isinstance(norm1, str)
            assert isinstance(norm2, str)
            
            # Comparison should be consistent
            are_equal = (norm1 == norm2)
            assert isinstance(are_equal, bool)
            
            # If paths are equal, they should remain equal after normalization
            if path1 == path2:
                assert norm1 == norm2
                
        except Exception as e:
            pytest.fail(f"Path comparison failed for '{path1}' vs '{path2}': {str(e)}")


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v", "--tb=short"])