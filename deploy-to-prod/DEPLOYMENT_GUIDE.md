# Complete Production Deployment Guide

## Overview

This guide walks you through deploying the Construction Time Management System to production using the automated deployment script.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Configuration](#configuration)
4. [Running Deployment](#running-deployment)
5. [Post-Deployment](#post-deployment)
6. [Production Server Setup](#production-server-setup)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements

#### Development Machine (where you build)
- Python 3.11 or higher
- Node.js 20 LTS or higher
- npm (comes with Node.js)
- Git
- Internet connection (for downloading dependencies)

#### Production Server
- PostgreSQL 12+ or MSSQL Server 2019+ (recommended)
- Web server (nginx, Apache, or IIS)
- Operating system: Windows Server or Linux

### Database Setup

Before deployment, set up your production database:

#### PostgreSQL
```bash
# Install PostgreSQL
# Create database
createdb construction_prod

# Create user
createuser -P construction_user

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE construction_prod TO construction_user;"
```

#### MSSQL
```sql
-- Create database
CREATE DATABASE construction_prod;

-- Create login
CREATE LOGIN construction_user WITH PASSWORD = 'YourSecurePassword';

-- Create user and grant permissions
USE construction_prod;
CREATE USER construction_user FOR LOGIN construction_user;
ALTER ROLE db_owner ADD MEMBER construction_user;
```

## Initial Setup

### 1. Clone or Update Repository

```bash
cd /path/to/project
git pull origin main
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd web-client
npm install
cd ..
```

### 3. Navigate to Deployment Folder

```bash
cd deploy-to-prod
```

## Configuration

### 1. Create Configuration File

```bash
# Windows
copy deploy_config.ini.example deploy_config.ini

# Linux/Mac
cp deploy_config.ini.example deploy_config.ini
```

### 2. Edit Configuration

Open `deploy_config.ini` in your text editor:

```ini
[Database]
type = postgresql
source_db = ../construction.db

# PostgreSQL settings
postgres_host = your-db-server.com
postgres_port = 5432
postgres_database = construction_prod
postgres_user = construction_user
postgres_password = YourSecurePassword

[API]
host = 0.0.0.0
port = 8000

# CRITICAL: Generate a secure secret!
jwt_secret = YOUR_SECURE_SECRET_HERE

# Set your production domains
cors_origins = https://yourdomain.com,https://www.yourdomain.com

[WebClient]
# Set your production API URL
api_base_url = https://yourdomain.com/api

[Desktop]
app_name = ConstructionTimeManagement
icon_path = ../fonts/icon.ico

[Paths]
project_root = ..
web_client_dir = ../web-client
output_dir = ./output
```

### 3. Generate Secure JWT Secret

**IMPORTANT**: Never use the default JWT secret in production!

Generate a secure secret:

```bash
# Python method
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL method
openssl rand -base64 32
```

Copy the generated string to `jwt_secret` in your config.

## Running Deployment

### Option 1: Interactive Script (Recommended)

#### Windows
```cmd
deploy.bat
```

#### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

Select option 1 for full deployment.

### Option 2: Command Line

#### Full Deployment
```bash
python deploy.py --all
```

#### Individual Components
```bash
# Database migration only
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

### Deployment Process

The script will:

1. **Migrate Database** (5-15 minutes)
   - Connect to source SQLite database
   - Create schema in target database
   - Transfer all data
   - Verify migration

2. **Build Web Client** (2-5 minutes)
   - Install npm dependencies
   - Build production bundle
   - Optimize and minify assets
   - Copy to output directory

3. **Build Desktop Application** (5-10 minutes)
   - Create PyInstaller spec
   - Bundle Python interpreter
   - Include all dependencies
   - Create standalone executable

4. **Build API Server** (5-10 minutes)
   - Create API startup script
   - Bundle FastAPI application
   - Include database drivers
   - Create standalone executable

5. **Configure Components** (< 1 minute)
   - Generate env.ini files
   - Create API .env file
   - Set up web client config
   - Create deployment README

### Expected Output

```
output/
├── web-client/          # Production SPA
│   ├── index.html
│   ├── assets/
│   │   ├── index-[hash].js
│   │   └── index-[hash].css
│   └── config.json
├── desktop/             # Desktop executable
│   ├── ConstructionTimeManagement.exe
│   ├── env.ini
│   ├── PrnForms/
│   └── fonts/
├── api-server/          # API server executable
│   ├── APIServer.exe
│   ├── env.ini
│   ├── .env
│   └── api/
└── README.md            # Deployment instructions
```

## Post-Deployment

### 1. Test Locally

Before deploying to production, test all components:

#### Test Desktop Application
```bash
cd output/desktop
./ConstructionTimeManagement.exe
```

- Verify login works
- Check database connection
- Test main features

#### Test API Server
```bash
cd output/api-server
./APIServer.exe
```

- Server should start on configured port
- Test API endpoints: http://localhost:8000/docs
- Verify database queries work

#### Test Web Client
```bash
cd output/web-client
python -m http.server 8080
```

- Open http://localhost:8080
- Test login
- Verify API calls work

### 2. Package for Distribution

#### Create Archive
```bash
# Windows (using 7-Zip)
7z a -tzip deployment-package.zip output/*

# Linux/Mac
tar -czf deployment-package.tar.gz output/
```

#### Transfer to Production
```bash
# Using SCP
scp deployment-package.tar.gz user@server:/path/to/deploy/

# Using SFTP
sftp user@server
put deployment-package.tar.gz
```

## Production Server Setup

### Web Client Deployment

#### Nginx Configuration

Create `/etc/nginx/sites-available/construction-app`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Web client root
    root /var/www/construction-app;
    index index.html;
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/construction-app /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

#### Apache Configuration

Create `/etc/apache2/sites-available/construction-app.conf`:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    DocumentRoot /var/www/construction-app
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.com/privkey.pem
    
    <Directory /var/www/construction-app>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        # SPA routing
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
    
    # API proxy
    ProxyPass /api http://localhost:8000/api
    ProxyPassReverse /api http://localhost:8000/api
</VirtualHost>
```

Enable site:
```bash
a2enmod ssl rewrite proxy proxy_http
a2ensite construction-app
systemctl reload apache2
```

### API Server Deployment

#### Linux (systemd service)

Create `/etc/systemd/system/construction-api.service`:

```ini
[Unit]
Description=Construction Time Management API Server
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/construction-api
ExecStart=/opt/construction-api/APIServer
Restart=always
RestartSec=10

# Environment
Environment="PATH=/opt/construction-api"

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Deploy and start:
```bash
# Copy files
sudo cp -r output/api-server /opt/construction-api
sudo chown -R www-data:www-data /opt/construction-api

# Start service
sudo systemctl daemon-reload
sudo systemctl enable construction-api
sudo systemctl start construction-api

# Check status
sudo systemctl status construction-api
```

#### Windows (NSSM service)

Download NSSM: https://nssm.cc/download

```cmd
REM Install service
nssm install ConstructionAPI "C:\Apps\construction-api\APIServer.exe"
nssm set ConstructionAPI AppDirectory "C:\Apps\construction-api"
nssm set ConstructionAPI DisplayName "Construction Time Management API"
nssm set ConstructionAPI Description "Backend API for Construction Time Management System"
nssm set ConstructionAPI Start SERVICE_AUTO_START

REM Start service
nssm start ConstructionAPI

REM Check status
nssm status ConstructionAPI
```

### Desktop Application Deployment

#### Windows
1. Copy `output/desktop/` folder to target machine
2. Create desktop shortcut to `ConstructionTimeManagement.exe`
3. Edit `env.ini` if needed (for database connection)

#### Network Deployment
```cmd
REM Copy to network share
xcopy /E /I output\desktop \\server\share\ConstructionApp\

REM Create batch file for users
echo @echo off > \\server\share\ConstructionApp\run.bat
echo cd /d "%~dp0" >> \\server\share\ConstructionApp\run.bat
echo start ConstructionTimeManagement.exe >> \\server\share\ConstructionApp\run.bat
```

## Troubleshooting

### Database Migration Issues

**Problem**: Connection refused
```
Solution: Check database server is running and accessible
- Verify host and port
- Check firewall rules
- Test connection: psql -h host -U user -d database
```

**Problem**: Authentication failed
```
Solution: Verify credentials
- Check username and password
- Ensure user has necessary permissions
- For PostgreSQL: check pg_hba.conf
```

### Build Issues

**Problem**: PyInstaller fails
```
Solution:
pip install --upgrade pyinstaller
pip install --upgrade setuptools
```

**Problem**: npm build fails
```
Solution:
cd ../web-client
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Runtime Issues

**Problem**: API server won't start
```
Solution:
- Check port is not in use: netstat -an | grep 8000
- Verify env.ini configuration
- Check logs in deploy.log
```

**Problem**: Desktop app database error
```
Solution:
- Verify env.ini database settings
- Test database connection
- Check database server is accessible
```

## Security Checklist

Before going live:

- [ ] Changed default admin password
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configured CORS_ORIGINS properly
- [ ] Enabled HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Secured database credentials
- [ ] Enabled database backups
- [ ] Configured log rotation
- [ ] Set up monitoring
- [ ] Tested disaster recovery

## Maintenance

### Regular Tasks

**Daily**
- Monitor logs
- Check system resources
- Verify backups

**Weekly**
- Review security logs
- Update dependencies (if needed)
- Test backup restoration

**Monthly**
- Security updates
- Performance review
- Capacity planning

### Updates

To deploy updates:

1. Update source code
2. Run deployment script again
3. Test in staging environment
4. Deploy to production
5. Restart services

```bash
# Quick update
cd deploy-to-prod
python deploy.py --all

# Deploy to production
sudo systemctl restart construction-api
sudo systemctl reload nginx
```

## Support

For issues:
1. Check `deploy.log`
2. Review configuration
3. Test components individually
4. Consult project documentation

## Appendix

### Useful Commands

```bash
# Check API server status
curl http://localhost:8000/api/health

# View API logs
sudo journalctl -u construction-api -f

# Test database connection
psql -h localhost -U construction_user -d construction_prod

# Check nginx configuration
nginx -t

# Reload nginx
sudo systemctl reload nginx

# View nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Environment Variables

API Server (.env):
```
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourdomain.com
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Connection Strings

PostgreSQL:
```
postgresql://user:password@host:5432/database
```

MSSQL:
```
mssql+pyodbc://user:password@host:1433/database?driver=ODBC+Driver+17+for+SQL+Server
```

SQLite (development):
```
sqlite:///construction.db
```
