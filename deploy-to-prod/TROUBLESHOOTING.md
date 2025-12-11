# Troubleshooting Guide

## Common Issues and Solutions

### Configuration Issues

#### Issue: Configuration file not found
```
Error: deploy_config.ini not found
```

**Solution:**
```bash
# Create from example
copy deploy_config.ini.example deploy_config.ini  # Windows
cp deploy_config.ini.example deploy_config.ini    # Linux/Mac

# Edit with your settings
notepad deploy_config.ini  # Windows
nano deploy_config.ini     # Linux/Mac
```

#### Issue: Invalid configuration format
```
Error: ConfigParser error
```

**Solution:**
- Check INI file syntax
- Ensure no missing `=` signs
- Verify section headers have `[brackets]`
- Remove any special characters

Example correct format:
```ini
[Database]
type = postgresql
postgres_host = localhost
```

### Database Migration Issues

#### Issue: Database connection refused
```
Error: Connection refused to database server
```

**Solutions:**

1. **Check database server is running**
   ```bash
   # PostgreSQL
   sudo systemctl status postgresql
   
   # MSSQL
   sudo systemctl status mssql-server
   ```

2. **Verify host and port**
   ```bash
   # Test PostgreSQL connection
   psql -h localhost -U postgres -d postgres
   
   # Test MSSQL connection
   sqlcmd -S localhost -U sa
   ```

3. **Check firewall**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 5432/tcp  # PostgreSQL
   sudo ufw allow 1433/tcp  # MSSQL
   
   # Windows
   netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432
   ```

#### Issue: Authentication failed
```
Error: password authentication failed for user
```

**Solutions:**

1. **Verify credentials**
   - Check username and password in `deploy_config.ini`
   - Ensure no extra spaces

2. **PostgreSQL: Check pg_hba.conf**
   ```bash
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   
   # Add line:
   host    all    all    0.0.0.0/0    md5
   
   # Restart
   sudo systemctl restart postgresql
   ```

3. **MSSQL: Check authentication mode**
   ```sql
   -- Enable mixed mode authentication
   USE master;
   GO
   EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE', 
        N'Software\Microsoft\MSSQLServer\MSSQLServer',
        N'LoginMode', REG_DWORD, 2;
   GO
   ```

#### Issue: Database does not exist
```
Error: database "construction_prod" does not exist
```

**Solution:**
```bash
# PostgreSQL
createdb construction_prod

# Or using psql
psql -U postgres -c "CREATE DATABASE construction_prod;"

# MSSQL
sqlcmd -S localhost -U sa -Q "CREATE DATABASE construction_prod;"
```

#### Issue: Permission denied
```
Error: permission denied for database
```

**Solution:**
```sql
-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE construction_prod TO your_user;

-- MSSQL
USE construction_prod;
ALTER ROLE db_owner ADD MEMBER your_user;
```

#### Issue: Source database not found
```
Error: Source database not found: ../construction.db
```

**Solution:**
```bash
# Check if file exists
ls -la ../construction.db  # Linux/Mac
dir ..\construction.db     # Windows

# Update path in deploy_config.ini
[Database]
source_db = /full/path/to/construction.db
```

### Build Issues

#### Issue: PyInstaller not found
```
Error: No module named 'PyInstaller'
```

**Solution:**
```bash
pip install pyinstaller
# Or
pip install -r ../requirements.txt
```

#### Issue: PyInstaller build fails
```
Error: Failed to execute script
```

**Solutions:**

1. **Update PyInstaller**
   ```bash
   pip install --upgrade pyinstaller
   pip install --upgrade setuptools
   ```

2. **Clear cache**
   ```bash
   # Remove build artifacts
   rm -rf build/ dist/ __pycache__/  # Linux/Mac
   rmdir /s build dist                # Windows
   ```

3. **Check Python version**
   ```bash
   python --version
   # Should be 3.11 or higher
   ```

4. **Install missing dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

#### Issue: npm build fails
```
Error: npm ERR! code ELIFECYCLE
```

**Solutions:**

1. **Clear npm cache**
   ```bash
   cd ../web-client
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

2. **Check Node.js version**
   ```bash
   node --version
   # Should be 20.x or higher
   ```

3. **Fix permissions (Linux/Mac)**
   ```bash
   sudo chown -R $USER:$USER ~/.npm
   ```

4. **Check for syntax errors**
   ```bash
   npm run lint
   ```

#### Issue: Module not found during build
```
Error: ModuleNotFoundError: No module named 'xxx'
```

**Solution:**
```bash
# Install missing module
pip install xxx

# Or reinstall all dependencies
pip install -r ../requirements.txt --force-reinstall
```

### Runtime Issues

#### Issue: API server won't start
```
Error: Address already in use
```

**Solutions:**

1. **Find process using port**
   ```bash
   # Linux/Mac
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

2. **Kill process**
   ```bash
   # Linux/Mac
   kill -9 <PID>
   
   # Windows
   taskkill /PID <PID> /F
   ```

3. **Change port in config**
   ```ini
   [API]
   port = 8001
   ```

#### Issue: Desktop app database error
```
Error: Unable to connect to database
```

**Solutions:**

1. **Check env.ini in desktop folder**
   ```bash
   cd output/desktop
   cat env.ini  # Linux/Mac
   type env.ini # Windows
   ```

2. **Verify database settings**
   ```ini
   [Database]
   type = postgresql
   postgres_host = your-db-host
   postgres_port = 5432
   postgres_database = construction_prod
   postgres_user = your_user
   postgres_password = your_password
   ```

3. **Test database connection**
   ```bash
   psql -h your-db-host -U your_user -d construction_prod
   ```

#### Issue: Web client shows blank page
```
Browser console: Failed to load resource
```

**Solutions:**

1. **Check API URL in config.json**
   ```bash
   cd output/web-client
   cat config.json
   ```

2. **Verify API server is running**
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **Check browser console for errors**
   - Open Developer Tools (F12)
   - Check Console tab
   - Check Network tab

4. **Check CORS settings**
   ```ini
   [API]
   cors_origins = https://yourdomain.com
   ```

#### Issue: JWT token errors
```
Error: Invalid token or Token expired
```

**Solutions:**

1. **Check JWT secret matches**
   - API server `.env` file
   - Should be same across all API instances

2. **Clear browser cache**
   - Clear cookies and local storage
   - Try incognito mode

3. **Check token expiration**
   ```ini
   # In API .env
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

### Deployment Issues

#### Issue: Permission denied when copying files
```
Error: Permission denied
```

**Solution:**
```bash
# Linux/Mac
sudo chown -R $USER:$USER output/
chmod -R 755 output/

# Windows (run as Administrator)
icacls output /grant Everyone:F /t
```

#### Issue: Disk space full
```
Error: No space left on device
```

**Solutions:**

1. **Check disk space**
   ```bash
   df -h  # Linux/Mac
   ```

2. **Clean up**
   ```bash
   # Remove old builds
   rm -rf output/ dist/ build/
   
   # Clean npm cache
   npm cache clean --force
   
   # Clean pip cache
   pip cache purge
   ```

#### Issue: Out of memory during build
```
Error: MemoryError
```

**Solutions:**

1. **Increase swap space (Linux)**
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. **Close other applications**

3. **Build components separately**
   ```bash
   python deploy.py --build-web
   python deploy.py --build-desktop
   python deploy.py --build-api
   ```

### Network Issues

#### Issue: Cannot download dependencies
```
Error: Connection timeout
```

**Solutions:**

1. **Check internet connection**
   ```bash
   ping google.com
   ```

2. **Configure proxy (if needed)**
   ```bash
   # npm
   npm config set proxy http://proxy:port
   npm config set https-proxy http://proxy:port
   
   # pip
   pip install --proxy http://proxy:port package
   ```

3. **Use alternative registry**
   ```bash
   # npm
   npm config set registry https://registry.npmjs.org/
   
   # pip
   pip install --index-url https://pypi.org/simple/ package
   ```

#### Issue: SSL certificate verification failed
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

1. **Update certificates**
   ```bash
   # Linux
   sudo update-ca-certificates
   
   # Mac
   /Applications/Python\ 3.11/Install\ Certificates.command
   ```

2. **Temporary workaround (not recommended for production)**
   ```bash
   # npm
   npm config set strict-ssl false
   
   # pip
   pip install --trusted-host pypi.org package
   ```

### Production Issues

#### Issue: 502 Bad Gateway (nginx)
```
Error: 502 Bad Gateway
```

**Solutions:**

1. **Check API server is running**
   ```bash
   sudo systemctl status construction-api
   ```

2. **Check nginx error log**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Verify proxy settings**
   ```nginx
   location /api {
       proxy_pass http://localhost:8000;
   }
   ```

4. **Check firewall**
   ```bash
   sudo ufw allow 8000/tcp
   ```

#### Issue: Service won't start (systemd)
```
Error: Failed to start service
```

**Solutions:**

1. **Check service status**
   ```bash
   sudo systemctl status construction-api
   sudo journalctl -u construction-api -n 50
   ```

2. **Verify service file**
   ```bash
   sudo nano /etc/systemd/system/construction-api.service
   ```

3. **Check file permissions**
   ```bash
   ls -la /opt/construction-api/
   sudo chown -R www-data:www-data /opt/construction-api/
   ```

4. **Reload systemd**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart construction-api
   ```

#### Issue: High memory usage
```
Warning: High memory consumption
```

**Solutions:**

1. **Check process memory**
   ```bash
   top
   # or
   htop
   ```

2. **Optimize database connections**
   ```ini
   [Database]
   pool_size = 5
   max_overflow = 10
   ```

3. **Enable connection pooling**

4. **Restart services periodically**
   ```bash
   # Add to crontab
   0 3 * * * systemctl restart construction-api
   ```

## Diagnostic Commands

### Check System Status

```bash
# Python version
python --version

# Node.js version
node --version

# npm version
npm --version

# Check installed packages
pip list
npm list -g --depth=0

# Check running processes
ps aux | grep python
ps aux | grep node

# Check ports
netstat -tulpn | grep LISTEN

# Check disk space
df -h

# Check memory
free -h
```

### Check Logs

```bash
# Deployment log
cat deploy.log
tail -f deploy.log

# API server log (systemd)
sudo journalctl -u construction-api -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Test Components

```bash
# Test database connection
psql -h localhost -U postgres -d construction_prod

# Test API server
curl http://localhost:8000/api/health
curl http://localhost:8000/docs

# Test web server
curl http://localhost

# Test DNS
nslookup yourdomain.com

# Test SSL certificate
openssl s_client -connect yourdomain.com:443
```

## Getting Help

### Information to Collect

When reporting issues, include:

1. **Error message** (full text)
2. **Log files** (deploy.log, system logs)
3. **Configuration** (sanitized, no passwords)
4. **System information**
   ```bash
   python --version
   node --version
   uname -a  # Linux/Mac
   systeminfo  # Windows
   ```
5. **Steps to reproduce**

### Debug Mode

Run deployment with verbose logging:

```bash
python deploy.py --all --verbose
```

Check detailed logs:
```bash
cat deploy.log
```

### Test Individual Components

```bash
# Test migration only
python deploy.py --migrate --verbose

# Test web build only
python deploy.py --build-web --verbose

# Test desktop build only
python deploy.py --build-desktop --verbose

# Test API build only
python deploy.py --build-api --verbose
```

## Prevention

### Best Practices

1. **Always backup before deployment**
   ```bash
   pg_dump construction_prod > backup_$(date +%Y%m%d).sql
   ```

2. **Test in staging first**
   - Deploy to staging environment
   - Run tests
   - Verify functionality

3. **Use version control**
   ```bash
   git tag v1.0.0
   git push --tags
   ```

4. **Monitor logs**
   - Set up log monitoring
   - Configure alerts

5. **Regular updates**
   - Keep dependencies updated
   - Apply security patches

6. **Document changes**
   - Keep deployment notes
   - Document configuration changes

### Health Checks

Create monitoring script:

```bash
#!/bin/bash
# health_check.sh

# Check API
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✓ API is healthy"
else
    echo "✗ API is down"
    systemctl restart construction-api
fi

# Check database
if psql -h localhost -U postgres -d construction_prod -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Database is healthy"
else
    echo "✗ Database is down"
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠ Disk usage is high: ${DISK_USAGE}%"
fi
```

Run periodically:
```bash
# Add to crontab
*/5 * * * * /path/to/health_check.sh
```

## Emergency Procedures

### Rollback

If deployment fails:

1. **Stop services**
   ```bash
   sudo systemctl stop construction-api
   ```

2. **Restore previous version**
   ```bash
   cp -r output.backup/* output/
   ```

3. **Restore database**
   ```bash
   psql -U postgres -d construction_prod < backup.sql
   ```

4. **Restart services**
   ```bash
   sudo systemctl start construction-api
   ```

### Quick Recovery

```bash
# Stop everything
sudo systemctl stop construction-api
sudo systemctl stop nginx

# Clear and rebuild
cd deploy-to-prod
rm -rf output/
python deploy.py --all

# Redeploy
sudo cp -r output/api-server /opt/construction-api
sudo cp -r output/web-client /var/www/construction-app

# Restart
sudo systemctl start construction-api
sudo systemctl start nginx
```

---

**Still having issues?** Check `deploy.log` for detailed error messages and stack traces.
