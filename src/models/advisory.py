"""Advisory-related data models."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .common import Language


class FertilizerRecommendation(BaseModel):
    """Fertilizer recommendation."""

    name: str = Field(..., description="Fertilizer name")
    type: str = Field(
        ..., description="Fertilizer type", pattern="^(ORGANIC|CHEMICAL|BIO)$"
    )
    npk_ratio: str = Field(..., description="NPK ratio")
    application_method: str = Field(..., description="Application method")
    estimated_cost: float = Field(..., ge=0, description="Estimated cost in INR")


class FertilizerAdvice(BaseModel):
    """Fertilizer advisory."""

    recommendations: List[FertilizerRecommendation] = Field(
        ..., description="Fertilizer recommendations"
    )
    timing: str = Field(..., description="Application timing")
    dosage: str = Field(..., description="Recommended dosage")
    precautions: List[str] = Field(..., description="Safety precautions")
    alternatives: List[str] = Field(default_factory=list, description="Alternative options")


class Advisory(BaseModel):
    """Crop advisory content."""

    content: str = Field(..., description="Advisory content")
    language: Language = Field(..., description="Content language")
    sources: List[str] = Field(default_factory=list, description="Information sources")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    applicable_regions: List[str] = Field(
        default_factory=list, description="Applicable regions"
    )
    uncertainty_disclaimer: Optional[str] = Field(
        None, description="Disclaimer for low confidence responses"
    )


class WeatherAdvice(BaseModel):
    """Weather-based advisory."""

    weather_summary: str = Field(..., description="Weather summary")
    recommendations: List[str] = Field(..., description="Weather-based recommendations")
    alerts: List[str] = Field(default_factory=list, description="Weather alerts")
    forecast_days: int = Field(..., ge=1, le=7, description="Forecast period in days")
