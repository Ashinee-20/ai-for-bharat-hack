"""Authentication-related data models."""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    """Request to send OTP to a phone number."""
    
    phone_number: str = Field(..., description="Phone number to send OTP to")


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP."""
    
    phone_number: str = Field(..., description="Phone number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class OTPRecord(BaseModel):
    """OTP record stored in DynamoDB."""
    
    phone_hash: str = Field(..., description="Hashed phone number")
    otp_hash: str = Field(..., description="Hashed OTP code")
    attempts: int = Field(default=0, ge=0, le=3, description="Number of verification attempts")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="OTP creation time")
    expires_at: datetime = Field(..., description="OTP expiration time")
    
    @classmethod
    def create(cls, phone_hash: str, otp_hash: str, expiry_minutes: int = 10) -> "OTPRecord":
        """Create a new OTP record.
        
        Args:
            phone_hash: Hashed phone number
            otp_hash: Hashed OTP code
            expiry_minutes: Minutes until OTP expires
            
        Returns:
            New OTPRecord instance
        """
        now = datetime.utcnow()
        return cls(
            phone_hash=phone_hash,
            otp_hash=otp_hash,
            attempts=0,
            created_at=now,
            expires_at=now + timedelta(minutes=expiry_minutes)
        )
    
    def is_expired(self) -> bool:
        """Check if OTP has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at
    
    def is_locked(self) -> bool:
        """Check if OTP is locked due to too many attempts.
        
        Returns:
            True if locked (3 or more attempts), False otherwise
        """
        return self.attempts >= 3
    
    def increment_attempts(self) -> None:
        """Increment the number of verification attempts."""
        self.attempts += 1


class OTPResponse(BaseModel):
    """Response after sending OTP."""
    
    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Response message")
    expires_in_minutes: Optional[int] = Field(None, description="Minutes until OTP expires")


class AuthResponse(BaseModel):
    """Response after successful authentication."""
    
    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Response message")
    token: Optional[str] = Field(None, description="JWT authentication token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    user_id: Optional[str] = Field(None, description="User identifier")
