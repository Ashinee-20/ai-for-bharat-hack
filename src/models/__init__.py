"""Pydantic data models for the AgriBridge AI platform."""

from .common import GeoLocation, Intent, Channel, UserType
from .user import UserProfile, FarmerProfile, BuyerProfile, AuthToken
from .price import PriceData, TrendData, Recommendation, TimeSeriesPoint
from .query import QueryRequest, QueryResponse, ResponseMetadata
from .advisory import Advisory, FertilizerAdvice, FertilizerRecommendation, WeatherAdvice
from .dynamodb_schemas import (
    FarmerRecord,
    BuyerRecord,
    PriceCacheRecord,
    QueryLogRecord,
    ConversationRecord,
    DYNAMODB_TABLES,
)

__all__ = [
    # Common
    "GeoLocation",
    "Intent",
    "Channel",
    "UserType",
    # User
    "UserProfile",
    "FarmerProfile",
    "BuyerProfile",
    "AuthToken",
    # Price
    "PriceData",
    "TrendData",
    "Recommendation",
    "TimeSeriesPoint",
    # Query
    "QueryRequest",
    "QueryResponse",
    "ResponseMetadata",
    # Advisory
    "Advisory",
    "FertilizerAdvice",
    "FertilizerRecommendation",
    "WeatherAdvice",
    # DynamoDB Schemas
    "FarmerRecord",
    "BuyerRecord",
    "PriceCacheRecord",
    "QueryLogRecord",
    "ConversationRecord",
    "DYNAMODB_TABLES",
]
