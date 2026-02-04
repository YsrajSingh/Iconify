"""Brandfetch source implementation."""

from typing import Optional
import httpx

from .base import BaseSource
from ..models import LogoSource, LogoMetadata


class BrandfetchSource(BaseSource):
    """Fetch logos from Brandfetch API with DuckDuckGo fallback."""

    source_type = LogoSource.BRANDFETCH
    SEARCH_URL = "https://api.brandfetch.io/v2/search"
    BRANDS_URL = "https://api.brandfetch.io/v2/brands"
    DUCKDUCKGO_URL = "https://icons.duckduckgo.com/ip3"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        """Initialize Brandfetch source.

        Args:
            api_key: Optional API key for Brandfetch
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.api_key = api_key

    async def fetch(self, domain: str) -> Optional[str]:
        """Fetch logo URL from Brandfetch or DuckDuckGo.

        Args:
            domain: Domain to fetch logo for

        Returns:
            Logo URL if available, None otherwise
        """
        domain = self._normalize_domain(domain)

        # Try Brandfetch search API first
        url = await self._try_search(domain)
        if url:
            return url

        # Try Brandfetch brands API
        url = await self._try_brands(domain)
        if url:
            return url

        # Fall back to DuckDuckGo icon service
        return await self._try_duckduckgo(domain)

    async def _try_search(self, domain: str) -> Optional[str]:
        """Try fetching from Brandfetch search API."""
        url = f"{self.SEARCH_URL}/{domain}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    logo_url = self._extract_from_search(data, domain)
                    if logo_url:
                        self.logger.debug(f"Found logo for {domain} via Brandfetch search")
                        return logo_url
        except Exception as e:
            self.logger.warning(f"Brandfetch search error for {domain}: {e}")

        return None

    async def _try_brands(self, domain: str) -> Optional[str]:
        """Try fetching from Brandfetch brands API."""
        url = f"{self.BRANDS_URL}/{domain}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    logo_url = self._extract_best_logo(data)
                    if logo_url:
                        self.logger.debug(f"Found logo for {domain} via Brandfetch brands")
                        return logo_url
        except Exception as e:
            self.logger.warning(f"Brandfetch brands error for {domain}: {e}")

        return None

    async def _try_duckduckgo(self, domain: str) -> Optional[str]:
        """Fetch icon from DuckDuckGo service."""
        url = f"{self.DUCKDUCKGO_URL}/{domain}.ico"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type or "icon" in content_type:
                        self.logger.debug(f"Found logo for {domain} via DuckDuckGo")
                        return url
        except Exception as e:
            self.logger.warning(f"DuckDuckGo error for {domain}: {e}")

        return None

    def _extract_from_search(self, data: list, domain: str) -> Optional[str]:
        """Extract logo URL from search results.

        Args:
            data: Brandfetch search API response
            domain: Original domain searched for

        Returns:
            Logo URL if found, None otherwise
        """
        if not data:
            return None

        # First try to find exact domain match
        for item in data:
            if item.get("domain", "").lower() == domain.lower():
                return item.get("icon")

        # If no exact match, return first result
        if data and data[0].get("icon"):
            return data[0].get("icon")

        return None

    async def fetch_with_metadata(
        self, domain: str
    ) -> Optional[tuple[str, Optional[LogoMetadata]]]:
        """Fetch logo URL with optional metadata.

        Args:
            domain: Domain to fetch logo for

        Returns:
            Tuple of (url, metadata) if found, None otherwise
        """
        url = await self.fetch(domain)
        if url:
            return (url, None)
        return None

    def _extract_best_logo(self, data: dict) -> Optional[str]:
        """Extract the best logo URL from Brandfetch brands response.

        Args:
            data: Brandfetch brands API response

        Returns:
            Best logo URL found, or None
        """
        logos = data.get("logos", [])

        # Prefer logo type over icon, prefer svg over png
        for logo_type in ["logo", "icon", "symbol"]:
            for logo in logos:
                if logo.get("type") == logo_type:
                    formats = logo.get("formats", [])

                    # Try SVG first
                    for fmt in formats:
                        if fmt.get("format") == "svg":
                            return fmt.get("src")

                    # Then PNG
                    for fmt in formats:
                        if fmt.get("format") == "png":
                            return fmt.get("src")

                    # Any format
                    if formats:
                        return formats[0].get("src")

        return None
