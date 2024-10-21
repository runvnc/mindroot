#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Remove any existing distributions
rm -rf dist/ build/ *.egg-info

# Install or upgrade build and twine
pip install --upgrade build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

echo "Package uploaded to TestPyPI successfully!"
echo "To install from TestPyPI, run:"
echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple ah-framework"

# Upload to PyPI
# Uncomment the following lines when you're ready to publish to the main PyPI repository
# twine upload dist/*
# echo "Package uploaded to PyPI successfully!"
# echo "To install from PyPI, run:"
# echo "pip install ah-framework"
