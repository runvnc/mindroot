#!/bin/bash
set -e

# If /app is empty, copy template
if [ -z "$(ls -A /app)" ]; then
    echo "Initializing MindRoot from template..."
    cp -r /app-template/* /app/
    cp -r /app-template/.* /app/ 2>/dev/null || :
    echo "Initialization complete"
else
    echo "Using existing MindRoot installation"
fi

# Run the application
exec "$@"
