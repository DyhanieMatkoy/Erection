# Production Deployment - Index

## 📁 Files Overview

### Main Scripts
- **`deploy.py`** - Main Python deployment script (automated deployment)
- **`deploy.bat`** - Windows batch script (interactive menu)
- **`deploy.sh`** - Linux/Mac shell script (interactive menu)

### Configuration
- **`deploy_config.ini.example`** - Example configuration file
- **`deploy_config.ini`** - Your actual configuration (create from example)

### Documentation
- **`README.md`** - Quick start guide and overview
- **`DEPLOYMENT_GUIDE.md`** - Complete step-by-step deployment guide
- **`QUICK_REFERENCE.md`** - Quick reference for common commands
- **`INDEX.md`** - This file (navigation guide)

### Output
- **`output/`** - Generated deployment files (created after running deploy)
  - `web-client/` - Production SPA build
  - `desktop/` - Desktop application executable
  - `api-server/` - API server executable
  - `README.md` - Deployment instructions for production

## 🚀 Quick Start

### First Time Setup

1. **Copy configuration**
   ```bash
   copy deploy_config.ini.example deploy_config.ini  # Windows
   cp deploy_config.ini.example deploy_config.ini    # Linux/Mac
   ```

2. **Edit configuration**
   - Set database connection details
   - Generate secure JWT secret
   - Set production API URL
   - Configure CORS origins

3. **Run deployment**
   ```bash
   python deploy.py --all
   ```

### Interactive Mode

**Windows:**
```cmd
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

## 📖 Documentation Guide

### For First-Time Users
Start here:
1. Read `README.md` - Understand what the tool does
2. Follow `DEPLOYMENT_GUIDE.md` - Step-by-step instructions
3. Use `QUICK_REFERENCE.md` - Quick commands reference

### For Experienced Users
Quick access:
- `QUICK_REFERENCE.md` - Common commands and configurations
- `deploy_config.ini.example` - Configuration template
- Run `python deploy.py --help` - Command-line options

## 🎯 What Does This Tool Do?

The deployment script automates:

1. **Database Migration**
   - Migrates from SQLite to PostgreSQL/MSSQL
   - Handles schema creation
   - Transfers all data
   - Verifies migration

2. **Web Client Build**
   - Builds production-optimized SPA
   - Minifies and optimizes assets
   - Configures API endpoints
   - Ready for web server deployment

3. **Desktop Application Build**
   - Creates standalone executable
   - Bundles Python interpreter
   - Includes all dependencies
   - No installation required on client machines

4. **API Server Build**
   - Creates standalone API server
   - Bundles FastAPI application
   - Includes database drivers
   - Ready for production deployment

5. **Configuration Management**
   - Generates configuration files
   - Sets up database connections
   - Configures API settings
   - Prepares deployment package

## 🔧 Configuration Overview

### Required Settings

```ini
[Database]
type = postgresql                    # Database type
postgres_host = your-db-host         # Database server
postgres_database = construction_prod # Database name
postgres_user = your-user            # Database user
postgres_password = your-password    # Database password

[API]
jwt_secret = YOUR_SECURE_SECRET      # JWT secret (MUST CHANGE!)
cors_origins = https://yourdomain.com # Allowed origins

[WebClient]
api_base_url = https://yourdomain.com/api # Production API URL
```

### Generate Secure JWT Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📦 Output Structure

After successful deployment:

```
output/
├── web-client/              # Deploy to web server
│   ├── index.html
│   ├── assets/
│   └── config.json
│
├── desktop/                 # Distribute to client machines
│   ├── ConstructionTimeManagement.exe
│   ├── env.ini
│   └── [dependencies]
│
├── api-server/              # Deploy to application server
│   ├── APIServer.exe
│   ├── env.ini
│   ├── .env
│   └── [dependencies]
│
└── README.md                # Deployment instructions
```

## 🎮 Usage Examples

### Full Deployment
```bash
python deploy.py --all
```

### Partial Deployment
```bash
# Database only
python deploy.py --migrate

# Web client only
python deploy.py --build-web

# Desktop app only
python deploy.py --build-desktop

# API server only
python deploy.py --build-api

# Configuration only
python deploy.py --configure
```

### With Custom Config
```bash
python deploy.py --all --config my_config.ini
```

### Verbose Mode
```bash
python deploy.py --all --verbose
```

## 🔍 Troubleshooting

### Common Issues

**Configuration not found**
- Create from example: `copy deploy_config.ini.example deploy_config.ini`

**Database connection failed**
- Check database server is running
- Verify credentials in config
- Test connection manually

**Build failed**
- Check `deploy.log` for details
- Verify all dependencies installed
- Try individual components

**PyInstaller issues**
- Update: `pip install --upgrade pyinstaller`
- Check Python version (3.11+ required)

### Getting Help

1. Check `deploy.log` for detailed error messages
2. Review `DEPLOYMENT_GUIDE.md` troubleshooting section
3. Verify configuration in `deploy_config.ini`
4. Test components individually

## 📋 Deployment Checklist

Before deploying to production:

- [ ] Created `deploy_config.ini` from example
- [ ] Set database connection details
- [ ] Generated secure JWT secret
- [ ] Configured production API URL
- [ ] Set CORS origins
- [ ] Tested database connection
- [ ] Ran full deployment successfully
- [ ] Tested all components locally
- [ ] Reviewed security settings
- [ ] Prepared production servers
- [ ] Created backup plan

## 🔐 Security Notes

**CRITICAL:**
- Never commit `deploy_config.ini` to version control
- Always change the default JWT secret
- Use strong database passwords
- Enable HTTPS in production
- Configure CORS properly
- Secure database credentials

## 📞 Support

For issues or questions:
1. Check `deploy.log`
2. Review documentation
3. Test individual components
4. Verify configuration

## 🔄 Update Process

To deploy updates:

1. Update source code
2. Run deployment script
3. Test in staging
4. Deploy to production
5. Restart services

```bash
cd deploy-to-prod
python deploy.py --all
```

## 📚 Additional Resources

- **Project Documentation**: `../docs/`
- **Database Guide**: `../docs/DATABASE_CONFIGURATION.md`
- **Migration Tool**: `../MIGRATION_TOOL_README.md`
- **Distribution Guide**: `../DISTRIBUTION_GUIDE.md`

## 🎓 Learning Path

### Beginner
1. Read `README.md`
2. Follow `DEPLOYMENT_GUIDE.md` step-by-step
3. Use interactive scripts (`deploy.bat` or `deploy.sh`)

### Intermediate
1. Use `QUICK_REFERENCE.md`
2. Run `python deploy.py` with specific options
3. Customize `deploy_config.ini`

### Advanced
1. Modify `deploy.py` for custom workflows
2. Integrate with CI/CD pipelines
3. Automate production deployments

## 🏁 Next Steps

After successful deployment:

1. **Test locally** - Verify all components work
2. **Prepare servers** - Set up production infrastructure
3. **Deploy components** - Follow `output/README.md`
4. **Configure services** - Set up systemd/NSSM services
5. **Enable monitoring** - Set up logs and alerts
6. **Create backups** - Implement backup strategy
7. **Go live** - Deploy to production
8. **Monitor** - Watch logs and performance

---

**Ready to deploy?** Start with `README.md` or run `deploy.bat` (Windows) / `deploy.sh` (Linux/Mac)!
