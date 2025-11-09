#!/bin/bash

# Simple startup script for the Data Visualization Platform

echo "Starting Data Visualization Platform..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env and add your OPENROUTER_API_KEY"
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Check if OPENROUTER_API_KEY is set
if ! grep -q "OPENROUTER_API_KEY=.*[^=]$" .env 2>/dev/null; then
    echo "Warning: OPENROUTER_API_KEY not set in .env file"
    echo "Please add your OpenRouter API key to .env"
fi

# Create necessary directories
mkdir -p app/uploads
mkdir -p app/static

# Run the application
echo "Starting server on port ${PORT:-8000}..."
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload

