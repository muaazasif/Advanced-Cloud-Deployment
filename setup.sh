#!/bin/bash

# Setup script for local development

set -e  # Exit on any error

echo "Setting up the Todo Chatbot development environment..."

# Check if Python 3.9+ is installed
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 9 ]); then
    echo "Python 3.9 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Start Kafka locally (using Docker)
echo "Starting Kafka with Docker..."
if command -v docker &> /dev/null; then
    docker-compose up -d
else
    echo "Docker is not installed. Please install Docker to run Kafka locally."
fi

echo "Setup complete!"
echo "To start the API, run: poetry run dev"
echo "To run tests, run: poetry run pytest"
