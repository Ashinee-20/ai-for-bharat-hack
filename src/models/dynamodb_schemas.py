"""DynamoDB table schemas and record models for AgriBridge AI platform."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .common import GeoLocation, UserType, Language


class DynamoDBRecord(BaseModel):
    """Base class for DynamoDB records with partition and sort keys."""
    
    PK: str = Field(..., description="Partition key")
    SK: str = Field(..., description="Sort key")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }


class FarmerRecord(DynamoDBRecord):
    """DynamoDB record for farmer profiles.
    
    Key Structure:
        PK: "FARMER#{phoneHash}"
        SK: "PROFILE"
    
    GSI1 (for district-based queries):
        GSI1PK: "DISTRICT#{district}"
        GSI1SK: "FARMER#{userId}"
    """
    
    # Primary keys
    PK: str = Field(..., description="FARMER#{phoneHash}")
    SK: str = Field(default="PROFILE", description="PROFILE")
    
    # User identification
    user_id: str = Field(..., description="Unique user identifier")
    phone_number: str = Field(..., description="Encrypted phone number")
    phone_hash: str = Field(..., description="Hashed phone number for PK")
    
    # Profile information
    name: str = Field(..., description="Farmer name")
    language: Language = Field(default=Language.HINDI, description="Preferred language")
    
    # Location
    location: GeoLocation = Field(..., description="Farmer location")
    district: str = Field(..., description="District name")
    
    # Farmer-specific fields
    land_size: float = Field(..., gt=0, description="Land size in acres")
    crop_types: List[str] = Field(..., description="Types of crops grown")
    soil_type: str = Field(..., description="Soil type")
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Profile creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    rating: Optional[float] = Field(None, ge=0, le=5, description="Farmer rating")
    
    # GSI1 keys for district-based queries
    GSI1PK: str = Field(..., description="DISTRICT#{district}")
    GSI1SK: str = Field(..., description="FARMER#{userId}")
    
    @classmethod
    def create_keys(cls, phone_hash: str, user_id: str, district: str) -> Dict[str, str]:
        """Create key structure for a farmer record.
        
        Args:
            phone_hash: Hashed phone number
            user_id: User identifier
            district: District name
            
        Returns:
            Dictionary with PK, SK, GSI1PK, GSI1SK
        """
        return {
            "PK": f"FARMER#{phone_hash}",
            "SK": "PROFILE",
            "GSI1PK": f"DISTRICT#{district}",
            "GSI1SK": f"FARMER#{user_id}",
        }


class BuyerRecord(DynamoDBRecord):
    """DynamoDB record for buyer profiles.
    
    Key Structure:
        PK: "BUYER#{phoneHash}"
        SK: "PROFILE"
    
    GSI1 (for district-based queries):
        GSI1PK: "DISTRICT#{district}"
        GSI1SK: "BUYER#{userId}"
    """
    
    # Primary keys
    PK: str = Field(..., description="BUYER#{phoneHash}")
    SK: str = Field(default="PROFILE", description="PROFILE")
    
    # User identification
    user_id: str = Field(..., description="Unique user identifier")
    phone_number: str = Field(..., description="Encrypted phone number")
    phone_hash: str = Field(..., description="Hashed phone number for PK")
    
    # Profile information
    name: str = Field(..., description="Buyer name")
    language: Language = Field(default=Language.HINDI, description="Preferred language")
    
    # Location
    location: GeoLocation = Field(..., description="Buyer location")
    district: str = Field(..., description="District name")
    
    # Buyer-specific fields
    business_name: str = Field(..., description="Business name")
    contact_person: Optional[str] = Field(None, description="Contact person name")
    crop_interests: List[str] = Field(..., description="Crops interested in purchasing")
    typical_volume_quintal: int = Field(..., gt=0, description="Typical purchase volume")
    max_purchase_distance_km: int = Field(..., gt=0, description="Max purchase distance")
    quality_preferences: List[str] = Field(
        default_factory=list, description="Quality grade preferences"
    )
    verified: bool = Field(default=False, description="Verification status")
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Profile creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    rating: Optional[float] = Field(None, ge=0, le=5, description="Buyer rating")
    
    # GSI1 keys for district-based queries
    GSI1PK: str = Field(..., description="DISTRICT#{district}")
    GSI1SK: str = Field(..., description="BUYER#{userId}")
    
    @classmethod
    def create_keys(cls, phone_hash: str, user_id: str, district: str) -> Dict[str, str]:
        """Create key structure for a buyer record.
        
        Args:
            phone_hash: Hashed phone number
            user_id: User identifier
            district: District name
            
        Returns:
            Dictionary with PK, SK, GSI1PK, GSI1SK
        """
        return {
            "PK": f"BUYER#{phone_hash}",
            "SK": "PROFILE",
            "GSI1PK": f"DISTRICT#{district}",
            "GSI1SK": f"BUYER#{user_id}",
        }


class PriceCacheRecord(DynamoDBRecord):
    """DynamoDB record for cached mandi prices.
    
    Key Structure:
        PK: "PRICE#{crop}#{district}"
        SK: "DATE#{YYYY-MM-DD}"
    
    TTL: 24 hours from timestamp
    """
    
    # Primary keys
    PK: str = Field(..., description="PRICE#{crop}#{district}")
    SK: str = Field(..., description="DATE#{YYYY-MM-DD}")
    
    # Price data
    crop: str = Field(..., description="Crop name")
    variety: str = Field(..., description="Crop variety")
    mandi_name: str = Field(..., description="Mandi name")
    location: GeoLocation = Field(..., description="Mandi location")
    district: str = Field(..., description="District name")
    price_per_quintal: float = Field(..., gt=0, description="Price per quintal in INR")
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Price timestamp"
    )
    source: str = Field(..., description="Data source (e.g., Agmarknet)")
    TTL: int = Field(..., description="Time-to-live epoch timestamp")
    
    @classmethod
    def create_keys(cls, crop: str, district: str, date: datetime) -> Dict[str, str]:
        """Create key structure for a price cache record.
        
        Args:
            crop: Crop name
            district: District name
            date: Price date
            
        Returns:
            Dictionary with PK and SK
        """
        date_str = date.strftime("%Y-%m-%d")
        return {
            "PK": f"PRICE#{crop}#{district}",
            "SK": f"DATE#{date_str}",
        }
    
    @classmethod
    def calculate_ttl(cls, timestamp: datetime, hours: int = 24) -> int:
        """Calculate TTL epoch timestamp.
        
        Args:
            timestamp: Base timestamp
            hours: Hours until expiration
            
        Returns:
            Unix epoch timestamp for TTL
        """
        from datetime import timedelta
        expiry = timestamp + timedelta(hours=hours)
        return int(expiry.timestamp())


class QueryLogRecord(DynamoDBRecord):
    """DynamoDB record for query logs.
    
    Key Structure:
        PK: "USER#{userId}"
        SK: "QUERY#{timestamp}"
    """
    
    # Primary keys
    PK: str = Field(..., description="USER#{userId}")
    SK: str = Field(..., description="QUERY#{timestamp}")
    
    # Query information
    query_id: str = Field(..., description="Unique query identifier")
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Query text")
    intent: str = Field(..., description="Classified intent")
    channel: str = Field(..., description="Channel: IVR, SMS, or MOBILE")
    language: Language = Field(..., description="Query language")
    
    # Response information
    response: str = Field(..., description="Response text")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Query timestamp"
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @classmethod
    def create_keys(cls, user_id: str, timestamp: datetime) -> Dict[str, str]:
        """Create key structure for a query log record.
        
        Args:
            user_id: User identifier
            timestamp: Query timestamp
            
        Returns:
            Dictionary with PK and SK
        """
        timestamp_str = timestamp.isoformat()
        return {
            "PK": f"USER#{user_id}",
            "SK": f"QUERY#{timestamp_str}",
        }


class ConversationRecord(DynamoDBRecord):
    """DynamoDB record for conversation context.
    
    Key Structure:
        PK: "SESSION#{sessionId}"
        SK: "TURN#{turnNumber}"
    
    TTL: 1 hour from timestamp
    """
    
    # Primary keys
    PK: str = Field(..., description="SESSION#{sessionId}")
    SK: str = Field(..., description="TURN#{turnNumber}")
    
    # Conversation data
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    turn_number: int = Field(..., ge=0, description="Turn number in conversation")
    
    # Messages
    user_message: str = Field(..., description="User message")
    assistant_message: str = Field(..., description="Assistant response")
    intent: str = Field(..., description="Classified intent")
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Turn timestamp"
    )
    TTL: int = Field(..., description="Time-to-live epoch timestamp")
    
    @classmethod
    def create_keys(cls, session_id: str, turn_number: int) -> Dict[str, str]:
        """Create key structure for a conversation record.
        
        Args:
            session_id: Session identifier
            turn_number: Turn number
            
        Returns:
            Dictionary with PK and SK
        """
        return {
            "PK": f"SESSION#{session_id}",
            "SK": f"TURN#{turn_number:04d}",  # Zero-padded for proper sorting
        }
    
    @classmethod
    def calculate_ttl(cls, timestamp: datetime, hours: int = 1) -> int:
        """Calculate TTL epoch timestamp.
        
        Args:
            timestamp: Base timestamp
            hours: Hours until expiration
            
        Returns:
            Unix epoch timestamp for TTL
        """
        from datetime import timedelta
        expiry = timestamp + timedelta(hours=hours)
        return int(expiry.timestamp())


# DynamoDB Table Definitions
DYNAMODB_TABLES = {
    "farmers": {
        "table_name": "agribridge-farmers",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [
            {
                "name": "GSI1",
                "partition_key": {"name": "GSI1PK", "type": "S"},
                "sort_key": {"name": "GSI1SK", "type": "S"},
                "projection": "ALL",
            }
        ],
        "ttl_attribute": None,
    },
    "buyers": {
        "table_name": "agribridge-buyers",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [
            {
                "name": "GSI1",
                "partition_key": {"name": "GSI1PK", "type": "S"},
                "sort_key": {"name": "GSI1SK", "type": "S"},
                "projection": "ALL",
            }
        ],
        "ttl_attribute": None,
    },
    "price_cache": {
        "table_name": "agribridge-price-cache",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [],
        "ttl_attribute": "TTL",
    },
    "query_logs": {
        "table_name": "agribridge-query-logs",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [],
        "ttl_attribute": None,
    },
    "conversations": {
        "table_name": "agribridge-conversations",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [],
        "ttl_attribute": "TTL",
    },
    "otp": {
        "table_name": "agribridge-otp",
        "partition_key": {"name": "PK", "type": "S"},
        "sort_key": {"name": "SK", "type": "S"},
        "gsi": [],
        "ttl_attribute": "TTL",
    },
}
