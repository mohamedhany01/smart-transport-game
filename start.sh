#!/bin/bash

# 1. Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "uv is not installed. Please install it from https://docs.astral.sh/uv/"
    exit 1
fi

# 2. Create venv using Python 3.8 if .venv does not exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv (Python 3.8)..."

    # Create venv with Python 3.8
    uv venv -p python3.8

    echo "Activating environment..."
    source .venv/bin/activate

    echo "Installing dependencies with uv..."
    uv pip install -r requirements.txt
else
    echo "Activating existing environment..."
    source .venv/bin/activate
fi

# 3. Run the game using uv
echo "Starting Game..."
cd src/
uv run python main.py
