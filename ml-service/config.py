"""
ML Service Configuration
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional

class MLServiceSettings(BaseSettings):
    """
    ML Service configuration settings
    """
    
    # Service settings
    service_name: str = Field(default="ml-service", env="ML_SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="ML_SERVICE_VERSION")
    host: str = Field(default="0.0.0.0", env="ML_SERVICE_HOST")
    port: int = Field(default=8001, env="ML_SERVICE_PORT")
    
    # Model settings
    model_path: str = Field(default="./models", env="ML_MODEL_PATH")
    model_version: str = Field(default="1.0.0-mvp-stub", env="ML_MODEL_VERSION")
    
    # Backend integration
    backend_url: str = Field(default="http://localhost:8000", env="BACKEND_URL")
    backend_api_key: Optional[str] = Field(default=None, env="BACKEND_API_KEY")
    
    # Database settings (for direct DB access if needed)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis settings (for caching predictions)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Performance settings
    max_batch_size: int = Field(default=100, env="ML_MAX_BATCH_SIZE")
    prediction_timeout: int = Field(default=30, env="ML_PREDICTION_TIMEOUT")
    
    # Supported assets
    supported_assets: List[str] = Field(
        default=["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "MATIC", "AVAX"],
        env="ML_SUPPORTED_ASSETS"
    )
    
    # Feature flags
    enable_model_caching: bool = Field(default=True, env="ML_ENABLE_CACHING")
    enable_feature_logging: bool = Field(default=False, env="ML_ENABLE_FEATURE_LOGGING")
    enable_prediction_logging: bool = Field(default=True, env="ML_ENABLE_PREDICTION_LOGGING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = MLServiceSettings()

# Validation
def validate_settings():
    """
    Validate configuration settings
    """
    errors = []
    
    if settings.port < 1 or settings.port > 65535:
        errors.append("Port must be between 1 and 65535")
    
    if settings.max_batch_size < 1 or settings.max_batch_size > 1000:
        errors.append("Max batch size must be between 1 and 1000")
    
    if settings.prediction_timeout < 1 or settings.prediction_timeout > 300:
        errors.append("Prediction timeout must be between 1 and 300 seconds")
    
    if not settings.supported_assets:
        errors.append("At least one supported asset must be specified")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    return True 