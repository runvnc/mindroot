#!/bin/bash

# Display banner
echo "========================================"
echo "   MindRoot Deployment Script"
echo "========================================"
echo ""

# Check if credentials already exist
if [ ! -f .env ]; then
    echo "No credentials found. Generating new credentials..."
    ./generate_credentials.sh
else
    echo "Existing credentials found in .env file."
    echo "To generate new credentials, delete the .env file and run this script again."
    echo ""
    
    # Load existing credentials for display
    source .env
    echo "Current Admin Username: $ADMIN_USER"
    echo "Current Admin Password: $ADMIN_PASS"
    echo ""
 fi

# Make sure generate_credentials.sh is executable
chmod +x generate_credentials.sh

# Start Docker Compose
echo "Starting MindRoot with Docker Compose..."
docker-compose up -d

# Check if startup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "MindRoot is now running!"
    echo "Access the web interface at: http://localhost:8010"
    echo ""
    echo "Admin credentials can be found in credentials.txt"
    echo ""
    echo "To stop MindRoot, run: docker-compose down"
    echo "========================================"
else
    echo ""
    echo "Error: Failed to start MindRoot."
    echo "Please check the logs with: docker-compose logs"
    echo "========================================"
    exit 1
fi
