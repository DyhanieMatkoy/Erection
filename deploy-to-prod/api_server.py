#!/usr/bin/env python3
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
