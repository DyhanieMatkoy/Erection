# Quick Reference - Production Deployment

## One-Line Commands

### Full Deployment
```bash
python deploy.py --all
```

### Individual Components
```bash
python deploy.py --migrate          # Database migration
python deploy.py --build-web        # Web client
python deploy.py --build-desktop    # Desktop app
python deploy.py --build-api        # API server
python deploy.py --configure        # Configuration
```

## Configuration Quick Edit

```ini
[Database]
type = postgresql
postgres_host = YOUR_DB_HOST
postgres_database = construction_prod
postgres_user = YOUR_DB_USER
postgres_password = YOUR_DB_PASSWORD

[API]
jwt_secret = YOUR_SECURE_SECRET
cors_origins = https://yourdomain.com

[WebClient]
api_base_url = https://yourdomain.com/api
```

## Generate Secure JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Test Components

```bash
# Desktop app
cd output/desktop && ./ConstructionTimeManagement.exe

# API server
cd output/api-server && ./APIServer.exe

# Web client (local test)
cd output/web-client && python -m http.server 8080
```

## Production Server Setup

### Nginx (Web Client)
```bash
sudo cp -r output/web-client /var/www/construction-app
sudo nano /etc/nginx/sites-available/construction-app
sudo ln -s /etc/nginx/sites-available/construction-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Systemd Service (API)
```bash
sudo cp -r output/api-server /opt/construction-api
sudo nano /etc/systemd/system/construction-api.service
sudo systemctl daemon-reload
sudo systemctl enable construction-api
sudo systemctl start construction-api
```

## Common Issues

### Database Connection Failed
```bash
# Test connection
psql -h HOST -U USER -d DATABASE

# Check firewall
sudo ufw status
```

### Port Already in Use
```bash
# Find process
netstat -tulpn | grep :8000

# Kill process
kill -9 PID
```

### Build Failed
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
cd web-client && npm install --force
```

## Monitoring

```bash
# API logs
sudo journalctl -u construction-api -f

# Nginx logs
tail -f /var/log/nginx/access.log

# Check API health
curl http://localhost:8000/api/health
```

## Backup Database

```bash
# PostgreSQL
pg_dump -h HOST -U USER DATABASE > backup.sql

# Restore
psql -h HOST -U USER DATABASE < backup.sql
```

## Update Deployment

```bash
cd deploy-to-prod
python deploy.py --all
sudo systemctl restart construction-api
sudo systemctl reload nginx
```

## File Locations

```
output/
├── web-client/          → /var/www/construction-app
├── api-server/          → /opt/construction-api
└── desktop/             → Copy to client machines
```

## Security Checklist

- [ ] Change admin password
- [ ] Set JWT_SECRET_KEY
- [ ] Configure CORS
- [ ] Enable HTTPS
- [ ] Set firewall rules
- [ ] Secure database
- [ ] Enable backups

## Support

- Check: `deploy.log`
- Docs: `DEPLOYMENT_GUIDE.md`
- Config: `deploy_config.ini`
