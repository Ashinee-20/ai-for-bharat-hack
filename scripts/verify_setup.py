#!/usr/bin/env python3
"""Verify that the project structure is set up correctly."""

import os
import sys
from pathlib import Path

def check_file(path: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} missing: {path}")
        return False

def check_directory(path: str, description: str) -> bool:
    """Check if a directory exists."""
    if os.path.isdir(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} missing: {path}")
        return False

def main():
    """Run verification checks."""
    print("Verifying AgriBridge AI project setup...\n")
    
    checks = []
    
    # Core files
    print("Core Files:")
    checks.append(check_file("requirements.txt", "Requirements file"))
    checks.append(check_file("setup.py", "Setup file"))
    checks.append(check_file(".gitignore", "Gitignore"))
    checks.append(check_file("README.md", "README"))
    checks.append(check_file("docker-compose.yml", "Docker Compose"))
    checks.append(check_file(".env.example", "Environment template"))
    checks.append(check_file("pytest.ini", "Pytest config"))
    checks.append(check_file("Makefile", "Makefile"))
    
    print("\nSource Code:")
    checks.append(check_directory("src", "Source directory"))
    checks.append(check_directory("src/models", "Models directory"))
    checks.append(check_directory("src/services", "Services directory"))
    checks.append(check_directory("src/utils", "Utils directory"))
    checks.append(check_file("src/utils/logger.py", "Logger module"))
    checks.append(check_file("src/utils/errors.py", "Errors module"))
    checks.append(check_file("src/utils/config.py", "Config module"))
    
    print("\nData Models:")
    checks.append(check_file("src/models/common.py", "Common models"))
    checks.append(check_file("src/models/user.py", "User models"))
    checks.append(check_file("src/models/price.py", "Price models"))
    checks.append(check_file("src/models/query.py", "Query models"))
    checks.append(check_file("src/models/advisory.py", "Advisory models"))
    
    print("\nInfrastructure:")
    checks.append(check_directory("infrastructure", "Infrastructure directory"))
    checks.append(check_file("infrastructure/app.py", "CDK app"))
    checks.append(check_file("infrastructure/cdk.json", "CDK config"))
    checks.append(check_file("infrastructure/stacks/agribridge_stack.py", "CDK stack"))
    
    print("\nTests:")
    checks.append(check_directory("tests", "Tests directory"))
    checks.append(check_file("tests/conftest.py", "Pytest fixtures"))
    checks.append(check_directory("tests/test_utils", "Utils tests"))
    checks.append(check_directory("tests/test_models", "Models tests"))
    
    print("\nScripts:")
    checks.append(check_directory("scripts", "Scripts directory"))
    checks.append(check_file("scripts/setup_local.sh", "Setup script"))
    checks.append(check_file("scripts/create_dynamodb_tables.py", "DynamoDB setup"))
    checks.append(check_file("scripts/init_postgres.py", "PostgreSQL setup"))
    
    print("\nDocumentation:")
    checks.append(check_directory("docs", "Docs directory"))
    checks.append(check_file("docs/DEVELOPMENT.md", "Development guide"))
    
    # Summary
    print("\n" + "="*60)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    
    print(f"Total checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All checks passed! Project structure is set up correctly.")
        return 0
    else:
        print(f"\n✗ {failed} checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
