"""Pydantic models for Logo Fetcher."""

from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel, Field


class LogoSource(str, Enum):
    """Available logo sources."""

    LOGODEV = "logodev"
    BRANDFETCH = "brandfetch"
    SCRAPER = "scraper"


class LogoMetadata(BaseModel):
    """Metadata about a fetched logo."""

    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    size_bytes: Optional[int] = None


class LogoResult(BaseModel):
    """Result from a logo fetch operation."""

    domain: str = Field(..., description="The domain the logo was fetched for")
    url: str = Field(..., description="URL to the logo image")
    source: LogoSource = Field(..., description="Source that provided the logo")
    metadata: Optional[LogoMetadata] = Field(
        default=None, description="Optional metadata about the logo"
    )
    cached: bool = Field(default=False, description="Whether result was from cache")

    model_config = {"json_schema_extra": {"example": {
        "domain": "google.com",
        "url": "https://img.logo.dev/google.com?token=xxx",
        "source": "logodev",
        "metadata": {"width": 200, "height": 200, "format": "png"},
        "cached": False,
    }}}


class LogoRequest(BaseModel):
    """Request model for logo fetching."""

    domain: str = Field(..., description="Domain to fetch logo for")
    sources: Optional[list[LogoSource]] = Field(
        default=None, description="Specific sources to try (default: all)"
    )


class AllLogosResult(BaseModel):
    """Result containing logos from all sources."""

    domain: str
    results: list[LogoResult]
    errors: Dict[str, str] = Field(
        default_factory=dict, description="Errors from failed sources"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    sources: Dict[str, bool]
