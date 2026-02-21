#!/bin/bash
# First-time setup for DevRel TUI Inbox
# Run this once after cloning the repo. Then use ./start.sh to launch.

set -e

echo "============================================================"
echo "  DevRel TUI Inbox - First-Time Setup"
echo "============================================================"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Install Python 3.10+ and try again."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

echo "Found $PYTHON_CMD $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10+ is required (found $PYTHON_VERSION)."
    echo "The 1Password SDK requires Python 3.10 or later."
    exit 1
fi

echo ""

# Create virtual environment
if [ -d ".venv" ]; then
    echo "Virtual environment already exists at .venv/"
    echo "To recreate it, delete .venv/ and run this script again."
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "Done."
fi

echo ""

# Activate and install dependencies
echo "Installing dependencies..."
source ./.venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "Done."

echo ""

# Copy config template if config.toml doesn't exist
if [ ! -f "config.toml" ]; then
    echo "Creating config.toml from template..."
    cp config.example.toml config.toml
    echo "Done."
    echo ""
    echo "IMPORTANT: Edit config.toml with your settings before running the app."
    echo "  - Set your 1Password account name"
    echo "  - Set your Khoros community hostname"
    echo "  - Add 1Password secret references (op://vault/item/field) for credentials"
    echo "  - See the README for details on each integration"
else
    echo "config.toml already exists. Skipping."
fi

echo ""

# Check for 1Password desktop app
if command -v op &> /dev/null; then
    echo "1Password CLI detected."
else
    echo "Note: 1Password CLI (op) not found in PATH."
    echo "The app uses the 1Password SDK (not the CLI), so this is fine"
    echo "as long as the 1Password desktop app is installed with SDK integration enabled."
fi

echo ""
echo "============================================================"
echo "  Setup complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Edit config.toml with your credentials and settings"
echo "  2. Make sure the 1Password desktop app is running and unlocked"
echo "  3. Run ./start.sh to launch the app"
echo ""
