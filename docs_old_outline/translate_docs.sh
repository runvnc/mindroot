#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define directories
DOCS_DIR="/files/ah/docs"
BUILD_DIR="/files/ah/docs/_build"
GETTEXT_DIR="$BUILD_DIR/gettext"

# Generate .pot files
echo "Generating .pot files..."
python3 "$DOCS_DIR/generate_pot_files.py"

# Run translation script
echo "Translating documentation..."
python3 "$DOCS_DIR/translate_docs.py"

echo "Translation process completed successfully!"
