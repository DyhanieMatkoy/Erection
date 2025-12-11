#!/usr/bin/env python3
"""
Production Deployment Script
Construction Time Management System

This script automates the complete production deployment process:
1. Database migration management
2. Build production SPA (web client)
3. Build Desktop version (PyQt6 executable)
4. Build Backend API (FastAPI executable)
5. Configure database and backend connections for each component

Usage:
    python deploy.py --all                    # Full deployment
    python deploy.py --migrate                # Database migration only
    python deploy.py --build-web              # Build web client only
    python deploy.py --build-desktop          # Build desktop app only
    python deploy.py --build-api              # Build API server only
    python deploy.py --configure              # Configure connections only
    python deploy.py --help                   # Show help
"""

import os
import sys
import argparse
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, List
import configparser
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeploymentConfig:
    """Deployment configuration manager"""
    
    def __init__(self, config_file: str = "deploy_config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load deployment configuration"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            logger.info(f"Loaded configuration from {self.config_file}")
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file"""
        self.config['Database'] = {
            'type': 'postgresql',
            'postgres_host': 'localhost',
            'postgres_port': '5432',
            'postgres_database': 'construction_prod',
            'postgres_user': 'postgres',
            'postgres_password': 'your_password_here',
            'source_db': '../construction.db'
        }
        
        self.config['API'] = {
            'host': '0.0.0.0',
            'port': '8000',
            'jwt_secret': 'CHANGE_THIS_SECRET_KEY_IN_PRODUCTION',
            'cors_origins': 'http://localhost:3000,https://yourdomain.com'
        }
        
        self.config['WebClient'] = {
            'api_base_url': 'http://servut.npksarmat.ru:65002/api',
            'build_output': '../web-client/dist'
        }
        
        self.config['Desktop'] = {
            'app_name': 'ConstructionTimeManagement',
            'icon_path': '../fonts/icon.ico',
            'output_dir': '../build/desktop'
        }
        
        self.config['Paths'] = {
            'project_root': '..',
            'web_client_dir': '../web-client',
            'api_dir': '../api',
            'src_dir': '../src',
            'output_dir': './output'
        }
        
        self.save_config()
        logger.info(f"Created default configuration: {self.config_file}")
        logger.warning("Please edit deploy_config.ini with your production settings!")
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)


class DatabaseMigrator:
    """Handle database migration"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def migrate(self) -> bool:
        """Run database migration"""
        logger.info("=" * 60)
        logger.info("Starting Database Migration")
        logger.info("=" * 60)
        
        try:
            # Create target env.ini for migration
            target_config = self._create_migration_config()
            
            # Get source database path
            source_db = self.config.config.get('Database', 'source_db')
            project_root = self.config.config.get('Paths', 'project_root')
            source_db_path = os.path.join(project_root, source_db)
            
            if not os.path.exists(source_db_path):
                logger.error(f"Source database not found: {source_db_path}")
                return False
            
            # Run migration script
            migrate_script = os.path.join(project_root, 'migrate_database.py')
            
            cmd = [
                sys.executable,
                migrate_script,
                '--source', source_db_path,
                '--target-config', target_config,
                '--verify'
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ Database migration completed successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error("✗ Database migration failed")
                logger.error(result.stderr)
                return False
        
        except Exception as e:
            logger.error(f"Migration error: {e}", exc_info=True)
            return False
    
    def _create_migration_config(self) -> str:
        """Create temporary env.ini for migration"""
        config = configparser.ConfigParser()
        
        db_type = self.config.config.get('Database', 'type')
        
        config['Database'] = {'type': db_type}
        
        if db_type == 'postgresql':
            config['Database'].update({
                'postgres_host': self.config.config.get('Database', 'postgres_host'),
                'postgres_port': self.config.config.get('Database', 'postgres_port'),
                'postgres_database': self.config.config.get('Database', 'postgres_database'),
                'postgres_user': self.config.config.get('Database', 'postgres_user'),
                'postgres_password': self.config.config.get('Database', 'postgres_password')
            })
        elif db_type == 'mssql':
            config['Database'].update({
                'mssql_host': self.config.config.get('Database', 'mssql_host'),
                'mssql_port': self.config.config.get('Database', 'mssql_port'),
                'mssql_database': self.config.config.get('Database', 'mssql_database'),
                'mssql_user': self.config.config.get('Database', 'mssql_user'),
                'mssql_password': self.config.config.get('Database', 'mssql_password')
            })
        
        config_path = 'env_migration_temp.ini'
        with open(config_path, 'w') as f:
            config.write(f)
        
        logger.info(f"Created migration config: {config_path}")
        return config_path


class WebClientBuilder:
    """Build production web client (SPA)"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def build(self) -> bool:
        """Build web client"""
        logger.info("=" * 60)
        logger.info("Building Web Client (SPA)")
        logger.info("=" * 60)
        
        try:
            web_dir = self.config.config.get('Paths', 'web_client_dir')
            
            if not os.path.exists(web_dir):
                logger.error(f"Web client directory not found: {web_dir}")
                return False
            
            # Update .env.production
            self._update_env_production()
            
            # Install dependencies
            logger.info("Installing dependencies...")
            result = subprocess.run(
                ['npm', 'install'],
                cwd=web_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Failed to install dependencies")
                logger.error(result.stderr)
                return False
            
            # Build production bundle
            logger.info("Building production bundle...")
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=web_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Build failed")
                logger.error(result.stderr)
                return False
            
            logger.info("✓ Web client built successfully")
            
            # Copy to output directory
            self._copy_to_output()
            
            return True
        
        except Exception as e:
            logger.error(f"Web build error: {e}", exc_info=True)
            return False
    
    def _update_env_production(self):
        """Update .env.production with deployment settings"""
        web_dir = self.config.config.get('Paths', 'web_client_dir')
        env_file = os.path.join(web_dir, '.env.production')
        
        api_url = self.config.config.get('WebClient', 'api_base_url')
        
        with open(env_file, 'w') as f:
            f.write(f"# Production environment - Generated by deploy.py\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"VITE_API_BASE_URL={api_url}\n")
        
        logger.info(f"Updated {env_file}")
    
    def _copy_to_output(self):
        """Copy built files to output directory"""
        web_dir = self.config.config.get('Paths', 'web_client_dir')
        output_dir = self.config.config.get('Paths', 'output_dir')
        
        dist_dir = os.path.join(web_dir, 'dist')
        target_dir = os.path.join(output_dir, 'web-client')
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        shutil.copytree(dist_dir, target_dir)
        logger.info(f"Copied web client to: {target_dir}")


class DesktopBuilder:
    """Build desktop application executable"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def build(self) -> bool:
        """Build desktop application using PyInstaller"""
        logger.info("=" * 60)
        logger.info("Building Desktop Application")
        logger.info("=" * 60)
        
        try:
            # Check if PyInstaller is installed
            try:
                import PyInstaller
            except ImportError:
                logger.info("Installing PyInstaller...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            
            # Create PyInstaller spec
            spec_file = self._create_spec_file()
            
            # Run PyInstaller
            logger.info("Running PyInstaller...")
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("PyInstaller build failed")
                logger.error(result.stderr)
                return False
            
            logger.info("✓ Desktop application built successfully")
            
            # Copy to output directory
            self._copy_to_output()
            
            return True
        
        except Exception as e:
            logger.error(f"Desktop build error: {e}", exc_info=True)
            return False
    
    def _create_spec_file(self) -> str:
        """Create PyInstaller spec file"""
        project_root = self.config.config.get('Paths', 'project_root')
        app_name = self.config.config.get('Desktop', 'app_name')
        icon_path = self.config.config.get('Desktop', 'icon_path', fallback='')
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Generated by deploy.py

block_cipher = None

a = Analysis(
    ['{project_root}/main.py'],
    pathex=['{project_root}'],
    binaries=[],
    datas=[
        ('{project_root}/PrnForms', 'PrnForms'),
        ('{project_root}/fonts', 'fonts'),
        ('{project_root}/env.ini', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'openpyxl',
        'reportlab',
        'sqlalchemy',
        'psycopg2',
        'pyodbc',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}' if '{icon_path}' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)
'''
        
        spec_file = f'{app_name}.spec'
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        logger.info(f"Created spec file: {spec_file}")
        return spec_file
    
    def _copy_to_output(self):
        """Copy built executable to output directory"""
        app_name = self.config.config.get('Desktop', 'app_name')
        output_dir = self.config.config.get('Paths', 'output_dir')
        
        dist_dir = os.path.join('dist', app_name)
        target_dir = os.path.join(output_dir, 'desktop')
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        shutil.copytree(dist_dir, target_dir)
        logger.info(f"Copied desktop app to: {target_dir}")


class APIBuilder:
    """Build backend API executable"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def build(self) -> bool:
        """Build API server using PyInstaller"""
        logger.info("=" * 60)
        logger.info("Building Backend API Server")
        logger.info("=" * 60)
        
        try:
            # Check if PyInstaller is installed
            try:
                import PyInstaller
            except ImportError:
                logger.info("Installing PyInstaller...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            
            # Create API startup script
            startup_script = self._create_startup_script()
            
            # Create PyInstaller spec
            spec_file = self._create_spec_file(startup_script)
            
            # Run PyInstaller
            logger.info("Running PyInstaller...")
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("PyInstaller build failed")
                logger.error(result.stderr)
                return False
            
            logger.info("✓ API server built successfully")
            
            # Copy to output directory
            self._copy_to_output()
            
            return True
        
        except Exception as e:
            logger.error(f"API build error: {e}", exc_info=True)
            return False
    
    def _create_startup_script(self) -> str:
        """Create API startup script"""
        project_root = self.config.config.get('Paths', 'project_root')
        
        script_content = '''#!/usr/bin/env python3
"""API Server Startup Script"""
import uvicorn
import os
import sys

# Add project root to path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

if __name__ == "__main__":
    # Load configuration
    import configparser
    config = configparser.ConfigParser()
    config_path = os.path.join(application_path, 'env.ini')
    
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Get host and port from config or use defaults
    host = config.get('API', 'host', fallback='0.0.0.0')
    port = config.getint('API', 'port', fallback=8000)
    
    print(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
'''
        
        script_path = 'api_server.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"Created startup script: {script_path}")
        return script_path
    
    def _create_spec_file(self, startup_script: str) -> str:
        """Create PyInstaller spec file for API"""
        project_root = self.config.config.get('Paths', 'project_root')
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Generated by deploy.py

block_cipher = None

a = Analysis(
    ['{startup_script}'],
    pathex=['{project_root}'],
    binaries=[],
    datas=[
        ('{project_root}/api', 'api'),
        ('{project_root}/src', 'src'),
        ('{project_root}/env.ini', '.'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sqlalchemy',
        'psycopg2',
        'pyodbc',
        'passlib.handlers.bcrypt',
        'jose',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='APIServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='APIServer',
)
'''
        
        spec_file = 'APIServer.spec'
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        logger.info(f"Created spec file: {spec_file}")
        return spec_file
    
    def _copy_to_output(self):
        """Copy built API server to output directory"""
        output_dir = self.config.config.get('Paths', 'output_dir')
        
        dist_dir = os.path.join('dist', 'APIServer')
        target_dir = os.path.join(output_dir, 'api-server')
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        shutil.copytree(dist_dir, target_dir)
        logger.info(f"Copied API server to: {target_dir}")


class ConfigurationManager:
    """Manage configuration for all components"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def configure_all(self) -> bool:
        """Configure all components"""
        logger.info("=" * 60)
        logger.info("Configuring All Components")
        logger.info("=" * 60)
        
        try:
            self._configure_database()
            self._configure_api()
            self._configure_web_client()
            self._configure_desktop()
            
            logger.info("✓ All components configured successfully")
            return True
        
        except Exception as e:
            logger.error(f"Configuration error: {e}", exc_info=True)
            return False
    
    def _configure_database(self):
        """Configure database settings"""
        logger.info("Configuring database...")
        
        output_dir = self.config.config.get('Paths', 'output_dir')
        
        # Create env.ini for each component
        for component in ['desktop', 'api-server']:
            component_dir = os.path.join(output_dir, component)
            if os.path.exists(component_dir):
                env_file = os.path.join(component_dir, 'env.ini')
                self._create_env_ini(env_file)
                logger.info(f"  Created {env_file}")
    
    def _create_env_ini(self, path: str):
        """Create env.ini file"""
        config = configparser.ConfigParser()
        
        # Database configuration
        db_type = self.config.config.get('Database', 'type')
        config['Database'] = {'type': db_type}
        
        if db_type == 'postgresql':
            config['Database'].update({
                'postgres_host': self.config.config.get('Database', 'postgres_host'),
                'postgres_port': self.config.config.get('Database', 'postgres_port'),
                'postgres_database': self.config.config.get('Database', 'postgres_database'),
                'postgres_user': self.config.config.get('Database', 'postgres_user'),
                'postgres_password': self.config.config.get('Database', 'postgres_password')
            })
        elif db_type == 'mssql':
            config['Database'].update({
                'mssql_host': self.config.config.get('Database', 'mssql_host'),
                'mssql_port': self.config.config.get('Database', 'mssql_port'),
                'mssql_database': self.config.config.get('Database', 'mssql_database'),
                'mssql_user': self.config.config.get('Database', 'mssql_user'),
                'mssql_password': self.config.config.get('Database', 'mssql_password')
            })
        elif db_type == 'sqlite':
            config['Database']['sqlite_path'] = 'construction.db'
        
        # Auth configuration
        config['Auth'] = {
            'login': 'admin',
            'password': 'admin'
        }
        
        # Print forms configuration
        config['PrintForms'] = {
            'format': 'EXCEL',
            'templates_path': 'PrnForms'
        }
        
        with open(path, 'w') as f:
            config.write(f)
    
    def _configure_api(self):
        """Configure API server"""
        logger.info("Configuring API server...")
        
        output_dir = self.config.config.get('Paths', 'output_dir')
        api_dir = os.path.join(output_dir, 'api-server')
        
        if not os.path.exists(api_dir):
            logger.warning(f"API directory not found: {api_dir}")
            return
        
        # Create .env file for API
        env_file = os.path.join(api_dir, '.env')
        
        jwt_secret = self.config.config.get('API', 'jwt_secret')
        cors_origins = self.config.config.get('API', 'cors_origins')
        
        with open(env_file, 'w') as f:
            f.write(f"# API Configuration - Generated by deploy.py\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
            f.write(f"CORS_ORIGINS={cors_origins}\n")
            f.write(f"ALGORITHM=HS256\n")
            f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES=30\n")
        
        logger.info(f"  Created {env_file}")
    
    def _configure_web_client(self):
        """Configure web client"""
        logger.info("Configuring web client...")
        
        output_dir = self.config.config.get('Paths', 'output_dir')
        web_dir = os.path.join(output_dir, 'web-client')
        
        if not os.path.exists(web_dir):
            logger.warning(f"Web client directory not found: {web_dir}")
            return
        
        # Create config.json for runtime configuration
        config_file = os.path.join(web_dir, 'config.json')
        
        api_url = self.config.config.get('WebClient', 'api_base_url')
        
        config_data = {
            'apiBaseUrl': api_url,
            'version': '1.0.0',
            'buildDate': datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"  Created {config_file}")
    
    def _configure_desktop(self):
        """Configure desktop application"""
        logger.info("Configuring desktop application...")
        # Desktop app uses env.ini which is already created
        logger.info("  Desktop app configured via env.ini")


class DeploymentOrchestrator:
    """Main deployment orchestrator"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.db_migrator = DatabaseMigrator(config)
        self.web_builder = WebClientBuilder(config)
        self.desktop_builder = DesktopBuilder(config)
        self.api_builder = APIBuilder(config)
        self.config_manager = ConfigurationManager(config)
    
    def deploy_all(self) -> bool:
        """Run complete deployment"""
        logger.info("=" * 60)
        logger.info("STARTING FULL DEPLOYMENT")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Create output directory
        output_dir = self.config.config.get('Paths', 'output_dir')
        os.makedirs(output_dir, exist_ok=True)
        
        steps = [
            ("Database Migration", self.db_migrator.migrate),
            ("Web Client Build", self.web_builder.build),
            ("Desktop App Build", self.desktop_builder.build),
            ("API Server Build", self.api_builder.build),
            ("Configuration", self.config_manager.configure_all),
        ]
        
        results = {}
        
        for step_name, step_func in steps:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Step: {step_name}")
            logger.info(f"{'=' * 60}")
            
            try:
                success = step_func()
                results[step_name] = success
                
                if not success:
                    logger.error(f"✗ {step_name} failed!")
                    logger.warning("Deployment stopped due to failure")
                    self._print_summary(results, start_time)
                    return False
                
                logger.info(f"✓ {step_name} completed")
            
            except Exception as e:
                logger.error(f"✗ {step_name} failed with exception: {e}", exc_info=True)
                results[step_name] = False
                self._print_summary(results, start_time)
                return False
        
        self._print_summary(results, start_time)
        self._create_deployment_package()
        
        return all(results.values())
    
    def _print_summary(self, results: Dict[str, bool], start_time: datetime):
        """Print deployment summary"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 60)
        
        for step, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"{status}: {step}")
        
        logger.info("-" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if all(results.values()):
            logger.info("\n✓ DEPLOYMENT COMPLETED SUCCESSFULLY!")
            output_dir = self.config.config.get('Paths', 'output_dir')
            logger.info(f"\nOutput directory: {output_dir}")
        else:
            logger.error("\n✗ DEPLOYMENT FAILED!")
        
        logger.info("=" * 60)
    
    def _create_deployment_package(self):
        """Create deployment package with instructions"""
        output_dir = self.config.config.get('Paths', 'output_dir')
        
        readme_content = f"""# Production Deployment Package
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Package Contents

### 1. Web Client (`web-client/`)
- Production-ready SPA build
- Optimized and minified
- Ready to deploy to web server (nginx, Apache, etc.)

### 2. Desktop Application (`desktop/`)
- Standalone executable
- No Python installation required
- Includes all dependencies

### 3. API Server (`api-server/`)
- Standalone API server executable
- FastAPI backend
- No Python installation required

## Deployment Instructions

### Web Client
1. Copy `web-client/` contents to your web server
2. Configure web server to serve static files
3. Set up reverse proxy to API server (if needed)

Example nginx configuration:
```nginx
server {{
    listen 80;
    server_name yourdomain.com;
    
    root /path/to/web-client;
    index index.html;
    
    location / {{
        try_files $uri $uri/ /index.html;
    }}
    
    location /api {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
```

### Desktop Application
1. Copy `desktop/` folder to target machine
2. Run the executable
3. Configure database connection in `env.ini`

### API Server
1. Copy `api-server/` folder to server
2. Edit `env.ini` for database configuration
3. Edit `.env` for API settings
4. Run `APIServer.exe` (Windows) or `APIServer` (Linux)

For production, use a process manager:
- Windows: NSSM (Non-Sucking Service Manager)
- Linux: systemd

Example systemd service:
```ini
[Unit]
Description=Construction Time Management API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/api-server
ExecStart=/path/to/api-server/APIServer
Restart=always

[Install]
WantedBy=multi-user.target
```

## Database Configuration

All components use `env.ini` for database configuration.

Example for PostgreSQL:
```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction_prod
postgres_user = postgres
postgres_password = your_secure_password
```

## Security Checklist

- [ ] Change default admin password
- [ ] Set strong JWT_SECRET_KEY in API .env
- [ ] Configure CORS_ORIGINS properly
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Keep database credentials secure

## Support

For issues or questions, refer to the project documentation.
"""
        
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Created deployment README: {readme_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Production Deployment Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full deployment
  python deploy.py --all
  
  # Individual steps
  python deploy.py --migrate
  python deploy.py --build-web
  python deploy.py --build-desktop
  python deploy.py --build-api
  python deploy.py --configure
  
  # Custom configuration
  python deploy.py --all --config my_config.ini
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Run full deployment')
    parser.add_argument('--migrate', action='store_true', help='Run database migration only')
    parser.add_argument('--build-web', action='store_true', help='Build web client only')
    parser.add_argument('--build-desktop', action='store_true', help='Build desktop app only')
    parser.add_argument('--build-api', action='store_true', help='Build API server only')
    parser.add_argument('--configure', action='store_true', help='Configure all components')
    parser.add_argument('--config', default='deploy_config.ini', help='Configuration file')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = DeploymentConfig(args.config)
    orchestrator = DeploymentOrchestrator(config)
    
    try:
        # Determine what to run
        if args.all:
            success = orchestrator.deploy_all()
        elif args.migrate:
            success = orchestrator.db_migrator.migrate()
        elif args.build_web:
            success = orchestrator.web_builder.build()
        elif args.build_desktop:
            success = orchestrator.desktop_builder.build()
        elif args.build_api:
            success = orchestrator.api_builder.build()
        elif args.configure:
            success = orchestrator.config_manager.configure_all()
        else:
            parser.print_help()
            return 0
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.warning("\nDeployment interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
