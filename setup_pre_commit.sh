#!/bin/bash

# Setup script for pre-commit hooks
# This script installs pre-commit and sets up the hooks

echo "Setting up pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
else
    echo "pre-commit is already installed"
fi

# Install the pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Update hooks to latest versions
echo "Updating pre-commit hooks..."
pre-commit autoupdate

echo "Pre-commit setup complete!"
echo ""
echo "The following hooks are now active:"
echo "- black (code formatting)"
echo "- isort (import sorting)"
echo "- trailing-whitespace (remove trailing whitespace)"
echo "- end-of-file-fixer (ensure files end with newline)"
echo "- check-yaml (validate YAML files)"
echo "- check-added-large-files (prevent large files)"
echo "- check-merge-conflict (prevent merge conflicts)"
echo ""
echo "These hooks will automatically run on every commit and modify files as needed."
