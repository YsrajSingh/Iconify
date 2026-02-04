"""Configuration management using pydantic-settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    logodev_api_key: Optional[str] = None
    brandfetch_api_key: Optional[str] = None

    # Timeouts (in seconds)
    request_timeout: float = 10.0
    scraper_timeout: float = 15.0

    # Source configuration
    enable_logodev: bool = True
    enable_brandfetch: bool = True
    enable_scraper: bool = True

    # Caching
    cache_ttl: int = 3600  # 1 hour
    redis_url: Optional[str] = None

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_rate_limit: int = 100  # requests per minute

    # Minimum logo dimensions
    min_logo_width: int = 32
    min_logo_height: int = 32


settings = Settings()
