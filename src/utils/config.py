"""Configuration management using pydantic-settings."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = Field(default="ap-south-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    
    # DynamoDB Configuration
    dynamodb_table_prefix: str = Field(
        default="agribridge", description="Prefix for DynamoDB tables"
    )
    dynamodb_endpoint_url: Optional[str] = Field(
        default=None, description="DynamoDB endpoint (for LocalStack)"
    )
    
    # RDS PostgreSQL Configuration
    rds_host: str = Field(default="localhost", description="RDS host")
    rds_port: int = Field(default=5432, description="RDS port")
    rds_database: str = Field(default="agribridge", description="Database name")
    rds_user: str = Field(default="postgres", description="Database user")
    rds_password: str = Field(default="password", description="Database password")
    
    # OpenSearch Configuration
    opensearch_endpoint: str = Field(
        default="localhost:9200", description="OpenSearch endpoint"
    )
    opensearch_use_ssl: bool = Field(default=False, description="Use SSL for OpenSearch")
    opensearch_verify_certs: bool = Field(
        default=False, description="Verify SSL certificates"
    )
    
    # AWS Bedrock Configuration
    bedrock_model_id: str = Field(
        default="anthropic.claude-v2", description="Bedrock model ID"
    )
    bedrock_embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v1", description="Bedrock embedding model ID"
    )
    
    # S3 Configuration
    s3_bucket_name: str = Field(
        default="agribridge-storage", description="S3 bucket for storage"
    )
    s3_endpoint_url: Optional[str] = Field(
        default=None, description="S3 endpoint (for LocalStack)"
    )
    
    # SNS Configuration (for SMS)
    sns_endpoint_url: Optional[str] = Field(
        default=None, description="SNS endpoint (for LocalStack)"
    )
    
    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")
    
    # Security Configuration
    jwt_secret_key: str = Field(
        default="change-me-in-production", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")
    
    # Encryption Configuration
    encryption_key_id: Optional[str] = Field(
        default=None, description="KMS key ID for encryption"
    )
    
    # Rate Limiting
    sms_rate_limit_per_day: int = Field(
        default=10, description="SMS queries per farmer per day"
    )
    
    # Performance Configuration
    max_concurrent_queries: int = Field(
        default=10000, description="Maximum concurrent queries"
    )
    query_timeout_seconds: int = Field(
        default=30, description="Query timeout in seconds"
    )
    
    # RAG Configuration
    rag_top_k: int = Field(default=5, description="Number of documents to retrieve")
    rag_confidence_threshold: float = Field(
        default=0.7, description="Confidence threshold for RAG"
    )
    
    # Geospatial Configuration
    default_search_radius_km: int = Field(
        default=100, description="Default search radius in kilometers"
    )
    buyer_matching_radius_km: int = Field(
        default=50, description="Buyer matching radius in kilometers"
    )

    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{self.rds_user}:{self.rds_password}"
            f"@{self.rds_host}:{self.rds_port}/{self.rds_database}"
        )

    @property
    def is_local(self) -> bool:
        """Check if running in local development mode."""
        return self.environment == "development"


@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance.
    
    Returns:
        Configuration instance
    """
    return Config()
