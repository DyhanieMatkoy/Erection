"""Custom exceptions for database operations"""


class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass


class DatabaseConfigurationError(Exception):
    """Raised when database configuration is invalid"""
    pass


class DatabaseOperationError(Exception):
    """Raised when a database operation fails"""
    pass
