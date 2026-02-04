"""Tests for FastAPI application."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from api.main import app
from src import LogoFetcher, __version__
from src.models import LogoResult, LogoSource, AllLogosResult


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_fetcher():
    """Create mock LogoFetcher."""
    return AsyncMock(spec=LogoFetcher)


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client):
        """Test health check returns correct response."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == __version__
        assert "sources" in data


class TestLogoEndpoint:
    """Tests for logo endpoints."""

    def test_get_logo_success(self, client):
        """Test successful logo fetch."""
        mock_result = LogoResult(
            domain="google.com",
            url="https://img.logo.dev/google.com",
            source=LogoSource.LOGODEV,
        )

        with patch.object(
            app.state, "fetcher", create=True
        ) as mock_fetcher:
            mock_fetcher.fetch = AsyncMock(return_value=mock_result)

            response = client.get("/api/v1/logo/google.com")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "google.com"
            assert data["source"] == "logodev"

    def test_get_logo_not_found(self, client):
        """Test logo not found returns 404."""
        with patch.object(
            app.state, "fetcher", create=True
        ) as mock_fetcher:
            mock_fetcher.fetch = AsyncMock(return_value=None)

            response = client.get("/api/v1/logo/nonexistent-xyz.com")

            assert response.status_code == 404
            assert "No logo found" in response.json()["detail"]

    def test_get_logo_with_source(self, client):
        """Test fetching logo from specific source."""
        mock_result = LogoResult(
            domain="google.com",
            url="https://img.logo.dev/google.com",
            source=LogoSource.LOGODEV,
        )

        with patch.object(
            app.state, "fetcher", create=True
        ) as mock_fetcher:
            mock_fetcher.fetch_from_source = AsyncMock(return_value=mock_result)

            response = client.get("/api/v1/logo/google.com?source=logodev")

            assert response.status_code == 200

    def test_get_all_logos(self, client):
        """Test fetching from all sources."""
        mock_result = AllLogosResult(
            domain="google.com",
            results=[
                LogoResult(
                    domain="google.com",
                    url="https://img.logo.dev/google.com",
                    source=LogoSource.LOGODEV,
                ),
            ],
            errors={},
        )

        with patch.object(
            app.state, "fetcher", create=True
        ) as mock_fetcher:
            mock_fetcher.fetch_all = AsyncMock(return_value=mock_result)

            response = client.get("/api/v1/logo/google.com/all")

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "google.com"
            assert len(data["results"]) == 1


class TestSourcesEndpoint:
    """Tests for sources endpoint."""

    def test_list_sources(self, client):
        """Test listing available sources."""
        with patch.object(
            app.state, "fetcher", create=True
        ) as mock_fetcher:
            mock_fetcher.get_available_sources = lambda: [
                LogoSource.LOGODEV,
                LogoSource.SCRAPER,
            ]
            mock_fetcher.source_priority = [
                LogoSource.LOGODEV,
                LogoSource.BRANDFETCH,
                LogoSource.SCRAPER,
            ]

            response = client.get("/api/v1/sources")

            assert response.status_code == 200
            data = response.json()
            assert "sources" in data
            assert "priority" in data
