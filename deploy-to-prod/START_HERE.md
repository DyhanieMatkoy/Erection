# 🚀 Start Here - Production Deployment

Welcome to the Production Deployment Tool for Construction Time Management System!

## ⚡ Quick Start (3 Steps)

### Step 1: Configure
```bash
# Copy example configuration
copy deploy_config.ini.example deploy_config.ini  # Windows
cp deploy_config.ini.example deploy_config.ini    # Linux/Mac

# Edit with your settings
notepad deploy_config.ini  # Windows
nano deploy_config.ini     # Linux/Mac
```

**Important settings to change:**
- Database connection (host, user, password)
- JWT secret (generate a secure one!)
- API URL for production
- CORS origins

### Step 2: Deploy
```bash
# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Or directly
python deploy.py --all
```

### Step 3: Test & Deploy
```bash
# Test locally
cd output/desktop && ./ConstructionTimeManagement.exe
cd output/api-server && ./APIServer.exe

# Deploy to production (follow output/README.md)
```

## 📚 Documentation

### New Users
1. **[README.md](README.md)** - Overview and features
2. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands

### Experienced Users
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast reference
- **[INDEX.md](INDEX.md)** - Navigation guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 What This Tool Does

✅ **Database Migration** - SQLite → PostgreSQL/MSSQL  
✅ **Web Client Build** - Production-optimized SPA  
✅ **Desktop App Build** - Standalone executable  
✅ **API Server Build** - Standalone API executable  
✅ **Configuration** - Auto-configure all components  

## ⚙️ Prerequisites

- Python 3.11+
- Node.js 20 LTS
- PostgreSQL or MSSQL database
- Internet connection (for first build)

## 🔐 Security Checklist

Before deploying:
- [ ] Generate secure JWT secret
- [ ] Change default admin password
- [ ] Configure CORS properly
- [ ] Use HTTPS in production
- [ ] Secure database credentials

## 📦 Output Structure

After deployment:
```
output/
├── web-client/      → Deploy to web server
├── desktop/         → Distribute to users
├── api-server/      → Deploy to app server
└── README.md        → Deployment instructions
```

## 🆘 Need Help?

1. Check **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
2. Review `deploy.log` file
3. Run with `--verbose` flag
4. Check individual components

## 🎓 Learning Path

**Beginner:** README.md → DEPLOYMENT_GUIDE.md → Run deploy.bat  
**Intermediate:** QUICK_REFERENCE.md → python deploy.py  
**Advanced:** Customize deploy.py → CI/CD integration  

## 📞 Quick Commands

```bash
# Full deployment
python deploy.py --all

# Individual components
python deploy.py --migrate
python deploy.py --build-web
python deploy.py --build-desktop
python deploy.py --build-api

# Help
python deploy.py --help
```

## ⚡ Next Steps

1. ✅ Read this file (you're here!)
2. 📝 Configure `deploy_config.ini`
3. 🚀 Run deployment
4. 🧪 Test components
5. 🌐 Deploy to production

---

**Ready?** Open **[README.md](README.md)** to begin!
