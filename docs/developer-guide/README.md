# Developer Guide

This section contains comprehensive documentation for developers working with the Erection application codebase.

## Getting Started

New developers should start with the [Development Environment Setup](setup/development-environment.md) to get up and running quickly.

## Architecture Overview

The application follows a modular architecture with clear separation of concerns. See [Architecture Overview](architecture/overview.md) for detailed information.

## API Documentation

The REST API provides programmatic access to application functionality. See [API Documentation](api/README.md) for endpoints, authentication, and examples.

## Deployment

For deployment instructions and production setup, see the [Deployment Guide](deployment/).

## Table of Contents

### Setup & Configuration
- [Development Environment](setup/development-environment.md)
- [Database Setup](setup/database-setup.md)
- [Project Structure](setup/project-structure.md)

### Architecture
- [Architecture Overview](architecture/overview.md)
- [Data Model](architecture/data-model.md)
- [Sync System](architecture/sync-system.md)
- [Design Patterns](architecture/patterns.md)

### API Reference
- [API Overview](api/README.md)
- [Endpoints](api/endpoints.md)
- [Authentication](api/authentication.md)
- [Examples](api/examples.md)

### Deployment
- [Production Deployment](deployment/production.md)
- [Distribution](deployment/distribution.md)
- [Configuration](deployment/configuration.md)

### Testing & Debugging
- [Unit Testing](testing/unit-tests.md)
- [Integration Testing](testing/integration-tests.md)
- [Debugging Guide](testing/debugging.md)

## Key Components

### Frontend
- **PyQt6** for desktop application UI
- **Vue.js** for web interface (if applicable)

### Backend
- **Python** core application logic
- **FastAPI** for REST API endpoints
- **SQLAlchemy** for database ORM

### Database
- **SQLite** for local storage
- **MS SQL Server** for enterprise deployment
- **Sync system** for multi-user data synchronization

### Development Tools
- **pytest** for testing
- **Black** for code formatting
- **mypy** for type checking

## Contributing

When contributing to the codebase:
1. Follow the existing code style and conventions
2. Write tests for new functionality
3. Update relevant documentation
4. Ensure all tests pass before submitting

## Getting Help

- Check the [troubleshooting section](../user-guide/troubleshooting/)
- Review existing issues in the project tracker
- Contact the development team for technical questions

---

**Note**: This documentation is intended for developers with knowledge of Python, PyQt6, and web development concepts.