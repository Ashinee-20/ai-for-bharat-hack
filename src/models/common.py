"""Common data models used across the platform."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GeoLocation(BaseModel):
    """Geographic location with latitude and longitude."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates(cls, v: float) -> float:
        """Validate coordinate values."""
        if not isinstance(v, (int, float)):
            raise ValueError("Coordinates must be numeric")
        return v


class Intent(str, Enum):
    """Query intent classification."""

    PRICE_QUERY = "PRICE_QUERY"
    BUYER_MATCHING = "BUYER_MATCHING"
    CROP_ADVISORY = "CROP_ADVISORY"
    FERTILIZER_ADVICE = "FERTILIZER_ADVICE"
    WEATHER_INFO = "WEATHER_INFO"
    GENERAL_QUERY = "GENERAL_QUERY"


class Channel(str, Enum):
    """Communication channel."""

    IVR = "IVR"
    SMS = "SMS"
    MOBILE = "MOBILE"
    WEB = "WEB"


class UserType(str, Enum):
    """User type classification."""

    FARMER = "FARMER"
    BUYER = "BUYER"
    ADMIN = "ADMIN"


class Language(str, Enum):
    """Supported languages."""

    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MARATHI = "mr"
    ENGLISH = "en"


class QualityGrade(str, Enum):
    """Crop quality grade."""

    A = "A"
    B = "B"
    C = "C"


class Unit(str, Enum):
    """Quantity units."""

    QUINTAL = "QUINTAL"
    TON = "TON"
    KG = "KG"


class Currency(str, Enum):
    """Currency types."""

    INR = "INR"
