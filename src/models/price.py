"""Price-related data models."""

from datetime import datetime
from datetime import date as DateType
from typing import List, Optional
from pydantic import BaseModel, Field
from .common import GeoLocation, Currency


class PriceData(BaseModel):
    """Mandi price data."""

    mandi_name: str = Field(..., description="Mandi name")
    mandi_location: GeoLocation = Field(..., description="Mandi location")
    crop_name: str = Field(..., description="Crop name")
    variety: Optional[str] = Field(None, description="Crop variety")
    price_per_quintal: float = Field(..., gt=0, description="Price per quintal")
    currency: Currency = Field(default=Currency.INR, description="Currency")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Price timestamp"
    )
    source: str = Field(..., description="Data source")
    distance_km: Optional[float] = Field(
        None, ge=0, description="Distance from query location"
    )


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    date: DateType = Field(..., description="Date")
    value: float = Field(..., description="Value")


class TrendData(BaseModel):
    """Price trend analysis data."""

    crop: str = Field(..., description="Crop name")
    historical_prices: List[TimeSeriesPoint] = Field(
        ..., description="Historical price data"
    )
    forecast: List[TimeSeriesPoint] = Field(..., description="Forecasted prices")
    seasonal_pattern: str = Field(..., description="Seasonal pattern description")
    volatility: float = Field(..., ge=0, le=1, description="Price volatility (0-1)")


class Recommendation(BaseModel):
    """Selling recommendation."""

    action: str = Field(
        ...,
        description="Recommended action",
        pattern="^(SELL_NOW|WAIT|SELL_WITHIN_WEEK)$",
    )
    confidence: float = Field(
        ..., ge=0, le=100, description="Confidence score (0-100)"
    )
    reasoning: str = Field(..., description="Reasoning for recommendation")
    expected_price_range: dict = Field(
        ..., description="Expected price range with min and max"
    )
    optimal_timing: datetime = Field(..., description="Optimal selling time")
    disclaimer: str = Field(
        default="This is a prediction and not a guarantee. Market conditions may change.",
        description="Forecast disclaimer",
    )
