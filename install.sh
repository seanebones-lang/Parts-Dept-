#!/bin/bash

echo "======================================"
echo "Parts Department System - Installation"
echo "======================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip in virtual environment
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing requirements..."
echo "Attempting full requirements first..."

if pip install -r requirements.txt; then
    echo "✓ Full requirements installed successfully"
else
    echo "⚠️  Full requirements failed, trying minimal requirements..."
    if pip install -r requirements-minimal.txt; then
        echo "✓ Minimal requirements installed successfully"
    else
        echo "❌ Installation failed"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To start the system:"
echo "  ./quickstart.sh"
echo ""

