"""Unit tests for common data models."""

import pytest
from pydantic import ValidationError
from src.models.common import GeoLocation, Intent, Channel, UserType


@pytest.mark.unit
def test_geolocation_valid():
    """Test valid geolocation creation."""
    location = GeoLocation(latitude=28.6139, longitude=77.2090)
    
    assert location.latitude == 28.6139
    assert location.longitude == 77.2090


@pytest.mark.unit
def test_geolocation_invalid_latitude():
    """Test that invalid latitude raises error."""
    with pytest.raises(ValidationError):
        GeoLocation(latitude=91.0, longitude=77.2090)
    
    with pytest.raises(ValidationError):
        GeoLocation(latitude=-91.0, longitude=77.2090)


@pytest.mark.unit
def test_geolocation_invalid_longitude():
    """Test that invalid longitude raises error."""
    with pytest.raises(ValidationError):
        GeoLocation(latitude=28.6139, longitude=181.0)
    
    with pytest.raises(ValidationError):
        GeoLocation(latitude=28.6139, longitude=-181.0)


@pytest.mark.unit
def test_intent_enum():
    """Test Intent enum values."""
    assert Intent.PRICE_QUERY == "PRICE_QUERY"
    assert Intent.BUYER_MATCHING == "BUYER_MATCHING"
    assert Intent.CROP_ADVISORY == "CROP_ADVISORY"


@pytest.mark.unit
def test_channel_enum():
    """Test Channel enum values."""
    assert Channel.IVR == "IVR"
    assert Channel.SMS == "SMS"
    assert Channel.MOBILE == "MOBILE"


@pytest.mark.unit
def test_user_type_enum():
    """Test UserType enum values."""
    assert UserType.FARMER == "FARMER"
    assert UserType.BUYER == "BUYER"
    assert UserType.ADMIN == "ADMIN"
