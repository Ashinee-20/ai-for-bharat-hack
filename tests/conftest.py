"""Pytest configuration and shared fixtures."""

import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)

# Load the appropriate profile
settings.load_profile("default")


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from src.utils.config import Config
    
    return Config(
        aws_region="ap-south-1",
        dynamodb_table_prefix="test-agribridge",
        rds_host="localhost",
        rds_database="test_agribridge",
        opensearch_endpoint="localhost:9200",
        environment="test",
    )


@pytest.fixture
def sample_geolocation():
    """Sample geolocation for testing."""
    from src.models.common import GeoLocation
    
    return GeoLocation(latitude=28.6139, longitude=77.2090)  # Delhi


@pytest.fixture
def sample_farmer_profile():
    """Sample farmer profile for testing."""
    from src.models.user import FarmerProfile
    
    return FarmerProfile(
        land_size=5.0,
        crop_types=["wheat", "rice"],
        soil_type="loamy",
        district="Delhi",
    )
