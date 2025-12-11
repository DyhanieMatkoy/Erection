# Production Deployment Tool

Automated deployment script for Construction Time Management System.

## Features

This deployment script automates the entire production deployment process:

1. **Database Migration** - Migrate from SQLite to PostgreSQL/MSSQL
2. **Web Client Build** - Build production-optimized SPA
3. **Desktop Application** - Create standalone executable with PyInstaller
4. **Backend API** - Create standalone API server executable
5. **Configuration Management** - Configure database and API connections for all components

## Prerequisites

### Required Software
- Python 3.11+
- Node.js 20 LTS
- npm
- Git

### Python Packages
All required packages are in `requirements.txt`:
- PyInstaller (for building executables)
- FastAPI, uvicorn (API server)
- SQLAlchemy, psycopg2-binary, pyodbc (database)
- PyQt6 (desktop app)

### Database
- PostgreSQL 12+ or MSSQL Server 2019+ (for production)
- Source SQLite database file

## Quick Start

### 1. Setup Configuration

Copy the example configuration:
```bash
cd deploy-to-prod
copy deploy_config.ini.example deploy_config.ini
```

Edit `deploy_config.ini` with your production settings:
- Database connection details
- API server settings (host, port, JWT secret)
- Web client API URL
- Output directories

**IMPORTANT**: Change the `jwt_secret` to a secure random value!

Generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Run Full Deployment

```bash
python deploy.py --all
```

This will:
1. Migrate database from SQLite to PostgreSQL/MSSQL
2. Build web client (SPA)
3. Build desktop application executable
4. Build API server executable
5. Configure all components

### 3. Check Output

All built components will be in `deploy-to-prod/output/`:
```
output/
├── web-client/          # Production SPA build
├── desktop/             # Desktop application
├── api-server/          # API server executable
└── README.md            # Deployment instructions
```

## Individual Commands

Run specific deployment steps:

### Database Migration Only
```bash
python deploy.py --migrate
```

### Build Web Client Only
```bash
python deploy.py --build-web
```

### Build Desktop App Only
```bash
python deploy.py --build-desktop
```

### Build API Server Only
```bash
python deploy.py --build-api
```

### Configure Components Only
```bash
python deploy.py --configure
```

## Configuration Details

### Database Configuration

The script supports three database types:

#### SQLite (Development)
```ini
[Database]
type = sqlite
source_db = ../construction.db
```

#### PostgreSQL (Recommended for Production)
```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction_prod
postgres_user = postgres
postgres_password = your_password
```

#### Microsoft SQL Server
```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction_prod
mssql_user = sa
mssql_password = your_password
mssql_driver = ODBC Driver 17 for SQL Server
```

### API Configuration

```ini
[API]
host = 0.0.0.0
port = 8000
jwt_secret = your-secure-secret-key-here
cors_origins = http://localhost:3000,https://yourdomain.com
```

### Web Client Configuration

```ini
[WebClient]
api_base_url = http://servut.npksarmat.ru:65002/api
```

This URL will be embedded in the production build.

## Deployment Workflow

### Development to Production

1. **Prepare Database**
   - Ensure source SQLite database is up to date
   - Set up target PostgreSQL/MSSQL database
   - Configure connection in `deploy_config.ini`

2. **Configure Settings**
   - Edit `deploy_config.ini`
   - Set production API URL
   - Generate secure JWT secret
   - Configure CORS origins

3. **Run Deployment**
   ```bash
   python deploy.py --all
   ```

4. **Test Locally**
   - Test desktop app: `output/desktop/ConstructionTimeManagement.exe`
   - Test API server: `output/api-server/APIServer.exe`
   - Test web client: Serve `output/web-client/` with a web server

5. **Deploy to Production**
   - Copy `output/web-client/` to web server
   - Copy `output/api-server/` to application server
   - Copy `output/desktop/` to client machines
   - Follow instructions in `output/README.md`

## Troubleshooting

### PyInstaller Issues

If PyInstaller fails to build:
```bash
pip install --upgrade pyinstaller
```

### Database Migration Fails

Check:
- Database server is running
- Connection credentials are correct
- Database exists and is accessible
- Source SQLite file exists

### Web Build Fails

Check:
- Node.js and npm are installed
- Run `npm install` in web-client directory
- Check for syntax errors in web client code

### Missing Dependencies

Install all dependencies:
```bash
cd ..
pip install -r requirements.txt
cd web-client
npm install
```

## Output Structure

After successful deployment:

```
output/
├── web-client/
│   ├── index.html
│   ├── assets/
│   └── config.json
├── desktop/
│   ├── ConstructionTimeManagement.exe
│   ├── env.ini
│   ├── PrnForms/
│   └── fonts/
├── api-server/
│   ├── APIServer.exe
│   ├── env.ini
│   ├── .env
│   └── api/
└── README.md
```

## Security Checklist

Before deploying to production:

- [ ] Change default admin password
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure CORS_ORIGINS properly
- [ ] Use HTTPS in production
- [ ] Secure database credentials
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Review API access logs
- [ ] Test all components

## Logs

Deployment logs are saved to `deploy.log` in the current directory.

## Support

For issues or questions:
1. Check `deploy.log` for detailed error messages
2. Review configuration in `deploy_config.ini`
3. Refer to project documentation
4. Check database connectivity

## Advanced Usage

### Custom Configuration File

Use a different configuration file:
```bash
python deploy.py --all --config my_custom_config.ini
```

### Verbose Logging

Enable detailed logging:
```bash
python deploy.py --all --verbose
```

### Partial Rebuild

Rebuild only specific components:
```bash
# Rebuild web client and reconfigure
python deploy.py --build-web --configure

# Rebuild API server only
python deploy.py --build-api
```

## Notes

- First run will create `deploy_config.ini` with default values
- Edit configuration before running deployment
- Database migration is one-way (SQLite → PostgreSQL/MSSQL)
- Executables are platform-specific (build on target OS)
- Web client build is platform-independent

## License

Part of Construction Time Management System
