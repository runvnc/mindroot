#!/bin/bash
set -e

# If /app is empty, copy template
if [ -z "$(ls -A /app)" ]; then
	echo "Initializing MindRoot from template..."
	cp -r /app-template/* /app/
	cp -r /app-template/.* /app/ 2>/dev/null || :

	echo "Fixing virtual environment paths..."
	if [ -d "/app/.venv/bin" ]; then
		cd /app/.venv/bin
		sed -i 's|/app-template/.venv|/app/.venv|g' *
		echo "Virtual environment paths updated"
		cd /app
	fi

	echo "Initialization complete"
else
	echo "Using existing MindRoot installation"
fi

# Check if .venv exists, if not, copy it from template
if [ ! -d "/app/.venv" ]; then
	echo "Virtual environment missing, copying from template..."
	if [ -d "/app-template/.venv" ]; then
		cp -r /app-template/.venv /app/

		echo "Fixing virtual environment paths..."
		if [ -d "/app/.venv/bin" ]; then
			cd /app/.venv/bin
			sed -i 's|/app-template/.venv|/app/.venv|g' *
			echo "Virtual environment paths updated"
			cd /app/
		fi

		echo "Virtual environment copied from template"
	else
		echo "ERROR: Virtual environment not found in template either!"
		echo "Contents of /app-template/:"
		ls -la /app-template/
		exit 1
	fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source /app/.venv/bin/activate

# Run the application
exec "$@"
