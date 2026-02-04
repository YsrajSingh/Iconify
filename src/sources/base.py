"""Abstract base class for logo sources."""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from ..models import LogoSource, LogoMetadata


logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Abstract base class for all logo sources."""

    source_type: LogoSource

    def __init__(self, timeout: float = 10.0):
        """Initialize the source.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def fetch(self, domain: str) -> Optional[str]:
        """Fetch logo URL for a domain.

        Args:
            domain: The domain to fetch logo for (e.g., 'google.com')

        Returns:
            Logo URL if found, None otherwise
        """
        pass

    async def fetch_with_metadata(
        self, domain: str
    ) -> Optional[tuple[str, Optional[LogoMetadata]]]:
        """Fetch logo URL with optional metadata.

        Args:
            domain: The domain to fetch logo for

        Returns:
            Tuple of (url, metadata) if found, None otherwise
        """
        url = await self.fetch(domain)
        if url:
            return (url, None)
        return None

    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain by removing protocol and www prefix.

        Args:
            domain: Raw domain input

        Returns:
            Normalized domain
        """
        domain = domain.lower().strip()
        for prefix in ["https://", "http://", "www."]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain.rstrip("/")

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL appears to be a valid image URL.

        Args:
            url: URL to validate

        Returns:
            True if URL looks like an image
        """
        if not url:
            return False
        lower_url = url.lower()
        return any(
            ext in lower_url
            for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".gif"]
        ) or "image" in lower_url
