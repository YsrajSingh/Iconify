"""Tests for logo sources."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.sources import LogoDevSource, BrandfetchSource, ScraperSource
from src.models import LogoSource


class TestLogoDev:
    """Tests for LogoDev source."""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful logo fetch from logo.dev."""
        source = LogoDevSource(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/png"}

            mock_client_instance = AsyncMock()
            mock_client_instance.head = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.fetch("google.com")

            assert result is not None
            assert "google.com" in result
            assert "token=test_key" in result

    @pytest.mark.asyncio
    async def test_fetch_not_found(self):
        """Test logo.dev returns None for missing logo."""
        source = LogoDevSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404

            mock_client_instance = AsyncMock()
            mock_client_instance.head = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.fetch("nonexistent-domain-xyz.com")

            assert result is None

    def test_source_type(self):
        """Test source type is correct."""
        source = LogoDevSource()
        assert source.source_type == LogoSource.LOGODEV


class TestBrandfetch:
    """Tests for Brandfetch source."""

    @pytest.mark.asyncio
    async def test_fetch_without_api_key(self):
        """Test Brandfetch returns None without API key."""
        source = BrandfetchSource()
        result = await source.fetch("google.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful logo fetch from Brandfetch."""
        source = BrandfetchSource(api_key="test_key")

        mock_response_data = {
            "logos": [
                {
                    "type": "logo",
                    "formats": [
                        {"format": "svg", "src": "https://example.com/logo.svg"},
                        {"format": "png", "src": "https://example.com/logo.png"},
                    ],
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value=mock_response_data)

            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.fetch("google.com")

            assert result == "https://example.com/logo.svg"

    def test_extract_best_logo_prefers_svg(self):
        """Test that SVG format is preferred."""
        source = BrandfetchSource(api_key="test")
        data = {
            "logos": [
                {
                    "type": "logo",
                    "formats": [
                        {"format": "png", "src": "https://example.com/logo.png"},
                        {"format": "svg", "src": "https://example.com/logo.svg"},
                    ],
                }
            ]
        }
        result = source._extract_best_logo(data)
        assert result == "https://example.com/logo.svg"

    def test_source_type(self):
        """Test source type is correct."""
        source = BrandfetchSource()
        assert source.source_type == LogoSource.BRANDFETCH


class TestScraper:
    """Tests for Scraper source."""

    def test_source_type(self):
        """Test source type is correct."""
        source = ScraperSource()
        assert source.source_type == LogoSource.SCRAPER

    def test_normalize_domain(self):
        """Test domain normalization."""
        source = ScraperSource()

        assert source._normalize_domain("https://www.google.com/") == "google.com"
        assert source._normalize_domain("http://example.com") == "example.com"
        assert source._normalize_domain("WWW.TEST.COM") == "test.com"

    @pytest.mark.asyncio
    async def test_fetch_with_og_image(self):
        """Test fetching logo via og:image tag."""
        source = ScraperSource()

        html_content = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/og-image.png">
        </head>
        <body></body>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client:
            # Mock GET for page content
            mock_page_response = MagicMock()
            mock_page_response.status_code = 200
            mock_page_response.text = html_content

            # Mock HEAD for image verification
            mock_image_response = MagicMock()
            mock_image_response.status_code = 200
            mock_image_response.headers = {"content-type": "image/png"}

            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_page_response)
            mock_client_instance.head = AsyncMock(return_value=mock_image_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.fetch("example.com")

            assert result == "https://example.com/og-image.png"
