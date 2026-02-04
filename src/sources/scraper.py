"""Website scraper source implementation."""

from typing import Optional
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

from .base import BaseSource
from ..models import LogoSource


class ScraperSource(BaseSource):
    """Scrape logos directly from websites."""

    source_type = LogoSource.SCRAPER

    LOGO_PATTERNS = ["logo", "brand", "icon"]

    def __init__(self, timeout: float = 15.0, min_size: int = 32):
        """Initialize scraper source.

        Args:
            timeout: Request timeout in seconds
            min_size: Minimum logo dimension in pixels
        """
        super().__init__(timeout)
        self.min_size = min_size

    async def fetch(self, domain: str) -> Optional[str]:
        """Scrape logo from website.

        Args:
            domain: Domain to scrape logo from

        Returns:
            Logo URL if found, None otherwise
        """
        domain = self._normalize_domain(domain)
        base_url = f"https://{domain}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
            ) as client:
                response = await client.get(base_url)

                if response.status_code != 200:
                    self.logger.debug(
                        f"Failed to fetch {base_url}: status {response.status_code}"
                    )
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # Try different strategies to find logo
                strategies = [
                    self._find_apple_touch_icon,
                    self._find_og_image,
                    self._find_favicon,
                    self._find_logo_in_html,
                ]

                for strategy in strategies:
                    logo_url = strategy(soup, base_url)
                    if logo_url:
                        # Verify the URL is accessible
                        if await self._verify_image(client, logo_url):
                            self.logger.debug(
                                f"Found logo for {domain} via scraper: {logo_url}"
                            )
                            return logo_url

        except httpx.TimeoutException:
            self.logger.warning(f"Timeout scraping {domain}")
        except httpx.HTTPError as e:
            self.logger.warning(f"HTTP error scraping {domain}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {domain}: {e}")

        return None

    def _find_og_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find Open Graph image meta tag."""
        # Try different og:image selectors
        for selector in [
            {"property": "og:image"},
            {"name": "og:image"},
            {"property": "twitter:image"},
        ]:
            og_image = soup.find("meta", selector)
            if og_image:
                content = og_image.get("content")
                if content:
                    return urljoin(base_url, content)
        return None

    def _find_apple_touch_icon(
        self, soup: BeautifulSoup, base_url: str
    ) -> Optional[str]:
        """Find Apple touch icon link."""
        best_icon = None
        best_size = 0

        # Find all link tags
        for link in soup.find_all("link"):
            rel = link.get("rel", [])
            # rel can be a list or string
            if isinstance(rel, str):
                rel = [rel]
            rel_str = " ".join(rel).lower()

            if "apple-touch-icon" in rel_str:
                href = link.get("href")
                if not href:
                    continue

                sizes = link.get("sizes", "")
                if sizes:
                    try:
                        size = int(sizes.split("x")[0])
                        if size > best_size:
                            best_size = size
                            best_icon = href
                    except (ValueError, IndexError):
                        if not best_icon:
                            best_icon = href
                elif not best_icon:
                    best_icon = href

        if best_icon:
            return urljoin(base_url, best_icon)
        return None

    def _find_favicon(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find favicon link."""
        best_favicon = None
        best_size = 0

        # Find all link tags with icon rel
        for link in soup.find_all("link"):
            rel = link.get("rel", [])
            if isinstance(rel, str):
                rel = [rel]
            rel_str = " ".join(rel).lower()

            if "icon" in rel_str and "apple" not in rel_str:
                href = link.get("href")
                if not href:
                    continue

                sizes = link.get("sizes", "")
                if sizes:
                    try:
                        size = int(sizes.split("x")[0])
                        if size >= self.min_size and size > best_size:
                            best_size = size
                            best_favicon = href
                    except (ValueError, IndexError):
                        if not best_favicon:
                            best_favicon = href
                elif not best_favicon:
                    best_favicon = href

        if best_favicon:
            return urljoin(base_url, best_favicon)

        # Default favicon location
        return urljoin(base_url, "/favicon.ico")

    def _find_logo_in_html(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find logo in HTML by analyzing img tags and common patterns."""
        # Look for images with logo-related attributes
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue

            alt = img.get("alt", "").lower()
            class_list = " ".join(img.get("class", [])).lower()
            img_id = img.get("id", "").lower()

            # Check if this looks like a logo
            is_logo = any(
                pattern in text
                for pattern in self.LOGO_PATTERNS
                for text in [src.lower(), alt, class_list, img_id]
            )

            if is_logo:
                return urljoin(base_url, src)

        return None

    async def _verify_image(self, client: httpx.AsyncClient, url: str) -> bool:
        """Verify that a URL points to a valid image.

        Args:
            client: HTTP client to use
            url: URL to verify

        Returns:
            True if URL is a valid image
        """
        try:
            response = await client.head(url, follow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                return (
                    "image" in content_type
                    or "icon" in content_type
                    or url.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".gif")
                    )
                )
        except Exception:
            pass
        return False
