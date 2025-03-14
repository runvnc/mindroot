#!/bin/bash

# pm2startmr.sh - PM2 Startup Script for MindRoot
# 
# This script starts MindRoot using PM2 process manager
# It passes through any provided arguments to the MindRoot server

# Display help information
show_help() {
    echo "MindRoot PM2 Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT           Port to run the server on (default: 8010)"
    echo "  -u, --admin-user USER     Admin username"
    echo "  -pw, --admin-password PW  Admin password"
    echo "  -n, --name NAME           PM2 process name (default: mindroot)"
    echo "  -h, --help                Display this help message and exit"
    echo ""
}

# Default values
PORT=8010
ADMIN_USER=""
ADMIN_PASSWORD=""
PM2_NAME="mindroot"
ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            ARGS="$ARGS -p $2"
            shift 2
            ;;
        -u|--admin-user)
            ADMIN_USER="$2"
            ARGS="$ARGS -u $2"
            shift 2
            ;;
        -pw|--admin-password)
            ADMIN_PASSWORD="$2"
            ARGS="$ARGS -pw $2"
            shift 2
            ;;
        -n|--name)
            PM2_NAME="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # Add any other arguments as is
            ARGS="$ARGS $1"
            shift
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "PM2 is not installed. Please install it using: npm install -g pm2"
    exit 1
fi

echo "Starting MindRoot with PM2..."
echo "Port: $PORT"
if [ ! -z "$ADMIN_USER" ]; then
    echo "Admin User: $ADMIN_USER"
fi
echo "PM2 Process Name: $PM2_NAME"

# Start MindRoot with PM2
cd "$SCRIPT_DIR"

# Starting MindRoot using the same approach as in start.sh but with custom arguments
pm2 start mindroot --name "$PM2_NAME" --interpreter python -- $ARGS

# Check if startup was successful
if [ $? -eq 0 ]; then
    echo "MindRoot started successfully with PM2"
    echo "Monitor with: pm2 monit"
    echo "View logs with: pm2 logs $PM2_NAME"
    echo "Stop with: pm2 stop $PM2_NAME"
else
    echo "Failed to start MindRoot with PM2"
fi
