"""Unit tests for configuration management."""

import pytest
from src.utils.config import Config, get_config


@pytest.mark.unit
def test_config_defaults():
    """Test that configuration has sensible defaults."""
    config = Config()
    
    assert config.aws_region == "ap-south-1"
    assert config.dynamodb_table_prefix == "agribridge"
    assert config.log_level == "INFO"
    assert config.environment == "development"


@pytest.mark.unit
def test_config_database_url():
    """Test database URL generation."""
    config = Config(
        rds_host="localhost",
        rds_port=5432,
        rds_database="testdb",
        rds_user="testuser",
        rds_password="testpass",
    )
    
    expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
    assert config.database_url == expected_url


@pytest.mark.unit
def test_config_is_local():
    """Test local environment detection."""
    dev_config = Config(environment="development")
    assert dev_config.is_local is True
    
    prod_config = Config(environment="production")
    assert prod_config.is_local is False


@pytest.mark.unit
def test_get_config_cached():
    """Test that get_config returns cached instance."""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2
