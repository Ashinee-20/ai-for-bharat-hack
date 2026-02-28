"""Query-related data models."""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from .common import Intent, Channel, Language, GeoLocation


class QueryRequest(BaseModel):
    """Incoming query request."""

    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., min_length=1, description="Query text")
    channel: Channel = Field(..., description="Communication channel")
    language: Language = Field(default=Language.HINDI, description="Query language")
    session_id: Optional[str] = Field(None, description="Session identifier")
    location: Optional[GeoLocation] = Field(None, description="User location")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Query timestamp"
    )


class ResponseMetadata(BaseModel):
    """Response metadata."""

    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    source: str = Field(..., description="Response source (cloud/offline)")
    model_used: Optional[str] = Field(None, description="Model used for generation")
    rag_documents_retrieved: Optional[int] = Field(
        None, description="Number of RAG documents retrieved"
    )


class QueryResponse(BaseModel):
    """Query response."""

    response: str = Field(..., description="Response text")
    intent: Intent = Field(..., description="Classified intent")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
    fallback_data: Optional[Dict[str, Any]] = Field(
        None, description="Fallback data if available"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
