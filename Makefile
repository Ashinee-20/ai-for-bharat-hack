.PHONY: help setup test clean docker-up docker-down lint format

help:
	@echo "AgriBridge AI Platform - Development Commands"
	@echo ""
	@echo "setup          - Set up local development environment"
	@echo "test           - Run all tests"
	@echo "test-unit      - Run unit tests only"
	@echo "test-property  - Run property-based tests only"
	@echo "docker-up      - Start LocalStack and databases"
	@echo "docker-down    - Stop LocalStack and databases"
	@echo "lint           - Run linters"
	@echo "format         - Format code with black"
	@echo "clean          - Clean up generated files"
	@echo "deploy         - Deploy infrastructure with CDK"

setup:
	@bash scripts/setup_local.sh

test:
	@pytest tests/ -v

test-unit:
	@pytest tests/ -v -m unit

test-property:
	@pytest tests/ -v -m property

docker-up:
	@docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo "Services are ready!"

docker-down:
	@docker-compose down

lint:
	@flake8 src/ tests/
	@mypy src/

format:
	@black src/ tests/ scripts/

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache .coverage htmlcov .mypy_cache
	@echo "Cleaned up generated files"

deploy:
	@cd infrastructure && cdk deploy
