"""User-related data models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from .common import GeoLocation, UserType, Language


class FarmerProfile(BaseModel):
    """Farmer-specific profile information."""

    land_size: float = Field(..., gt=0, description="Land size in acres")
    crop_types: List[str] = Field(..., min_length=1, description="Types of crops grown")
    soil_type: str = Field(..., description="Soil type")
    district: str = Field(..., description="District name")


class BuyerProfile(BaseModel):
    """Buyer-specific profile information."""

    business_name: str = Field(..., min_length=1, description="Business name")
    contact_person: Optional[str] = Field(None, description="Contact person name")
    crop_interests: List[str] = Field(
        ..., min_length=1, description="Crops interested in purchasing"
    )
    typical_volume_quintal: int = Field(
        ..., gt=0, description="Typical purchase volume in quintals"
    )
    max_purchase_distance_km: int = Field(
        ..., gt=0, description="Maximum distance for purchases"
    )
    quality_preferences: List[str] = Field(
        default_factory=list, description="Quality grade preferences"
    )
    verified: bool = Field(default=False, description="Verification status")


class UserProfile(BaseModel):
    """User profile information."""

    user_id: str = Field(..., description="Unique user identifier")
    phone_number: str = Field(..., description="Phone number (encrypted)")
    name: str = Field(..., min_length=1, description="User name")
    language: Language = Field(default=Language.HINDI, description="Preferred language")
    location: GeoLocation = Field(..., description="User location")
    user_type: UserType = Field(..., description="User type")
    farmer_profile: Optional[FarmerProfile] = Field(
        None, description="Farmer-specific profile"
    )
    buyer_profile: Optional[BuyerProfile] = Field(
        None, description="Buyer-specific profile"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Profile creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    rating: Optional[float] = Field(
        None, ge=0, le=5, description="User rating (0-5)"
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Basic validation - should be enhanced for production
        if not v or len(v) < 10:
            raise ValueError("Invalid phone number")
        return v


class AuthToken(BaseModel):
    """Authentication token."""

    token: str = Field(..., description="JWT token")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    user_id: str = Field(..., description="User identifier")
    user_type: UserType = Field(..., description="User type")
