#!/bin/bash
# Setup script for local development environment

set -e

echo "Setting up AgriBridge AI local development environment..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Start LocalStack and databases
echo "Starting LocalStack, PostgreSQL, and OpenSearch..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Create DynamoDB tables in LocalStack
echo "Creating DynamoDB tables..."
python scripts/create_dynamodb_tables.py

# Initialize PostgreSQL database
echo "Initializing PostgreSQL database..."
python scripts/init_postgres.py

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run tests: pytest tests/"
echo "3. Start development: python -m uvicorn src.main:app --reload"
echo ""
