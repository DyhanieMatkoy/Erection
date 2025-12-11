#!/bin/bash
# Quick deployment script for Linux/Mac
# Construction Time Management System

set -e

echo "========================================"
echo "Production Deployment Tool"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Check if configuration exists
if [ ! -f deploy_config.ini ]; then
    echo ""
    echo "Configuration file not found!"
    echo "Creating from example..."
    cp deploy_config.ini.example deploy_config.ini
    echo ""
    echo "IMPORTANT: Edit deploy_config.ini with your settings before continuing!"
    echo ""
    echo "Opening configuration file..."
    ${EDITOR:-nano} deploy_config.ini
    echo ""
    echo "After editing, run this script again."
    exit 0
fi

# Show menu
echo "Select deployment option:"
echo ""
echo "1. Full deployment (all components)"
echo "2. Database migration only"
echo "3. Build web client only"
echo "4. Build desktop app only"
echo "5. Build API server only"
echo "6. Configure components only"
echo "7. Exit"
echo ""
read -p "Enter choice (1-7): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "Running full deployment..."
        python3 deploy.py --all
        ;;
    2)
        echo ""
        echo "Running database migration..."
        python3 deploy.py --migrate
        ;;
    3)
        echo ""
        echo "Building web client..."
        python3 deploy.py --build-web
        ;;
    4)
        echo ""
        echo "Building desktop application..."
        python3 deploy.py --build-desktop
        ;;
    5)
        echo ""
        echo "Building API server..."
        python3 deploy.py --build-api
        ;;
    6)
        echo ""
        echo "Configuring components..."
        python3 deploy.py --configure
        ;;
    7)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid choice!"
        exit 1
        ;;
esac

echo ""
echo "========================================"
if [ $? -eq 0 ]; then
    echo "Deployment completed successfully!"
    echo ""
    echo "Output directory: output/"
    echo ""
    echo "Check output/README.md for deployment instructions"
else
    echo "Deployment failed!"
    echo ""
    echo "Check deploy.log for details"
fi
echo "========================================"
echo ""
