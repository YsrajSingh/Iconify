"""Logo.dev source implementation."""

from typing import Optional
import httpx

from .base import BaseSource
from ..models import LogoSource


class LogoDevSource(BaseSource):
    """Fetch logos from logo.dev API with Google favicon fallback."""

    source_type = LogoSource.LOGODEV
    SEARCH_URL = "https://www.logo.dev/api/search"
    GOOGLE_FAVICON_URL = "https://www.google.com/s2/favicons"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        """Initialize LogoDev source.

        Args:
            api_key: Optional API key for logo.dev
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.api_key = api_key

    async def fetch(self, domain: str) -> Optional[str]:
        """Fetch logo URL from logo.dev or Google favicon.

        Args:
            domain: Domain to fetch logo for

        Returns:
            Logo URL if available, None otherwise
        """
        domain = self._normalize_domain(domain)

        # Try logo.dev search API first
        url = await self._try_logodev(domain)
        if url:
            return url

        # Fall back to Google favicon service
        return await self._try_google_favicon(domain)

    async def _try_logodev(self, domain: str) -> Optional[str]:
        """Try fetching from logo.dev search API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = await client.get(
                    self.SEARCH_URL,
                    params={"q": domain},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    logo_url = self._extract_logo(data, domain)
                    if logo_url:
                        self.logger.debug(f"Found logo for {domain} via logo.dev")
                        return logo_url

        except httpx.TimeoutException:
            self.logger.warning(f"Timeout fetching logo for {domain} from logo.dev")
        except httpx.HTTPError as e:
            self.logger.warning(f"HTTP error fetching logo for {domain}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching logo for {domain}: {e}")

        return None

    async def _try_google_favicon(self, domain: str) -> Optional[str]:
        """Fetch high-quality favicon from Google's service."""
        url = f"{self.GOOGLE_FAVICON_URL}?domain={domain}&sz=128"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code == 200:
                    self.logger.debug(f"Found logo for {domain} via Google favicon")
                    return url
        except Exception as e:
            self.logger.warning(f"Google favicon error for {domain}: {e}")

        return None

    def _extract_logo(self, data: list, domain: str) -> Optional[str]:
        """Extract the best matching logo URL from search results.

        Args:
            data: logo.dev search API response
            domain: Original domain searched for

        Returns:
            Logo URL if found, None otherwise
        """
        if not data:
            return None

        # First try to find exact domain match
        for item in data:
            if item.get("domain", "").lower() == domain.lower():
                return item.get("logo_url")

        # If no exact match, return first result
        if data and data[0].get("logo_url"):
            return data[0].get("logo_url")

        return None
