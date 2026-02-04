"""Main orchestrator for logo fetching."""

import asyncio
from typing import Optional, List, Dict
import logging

from .config import Settings, settings
from .models import LogoResult, LogoSource, AllLogosResult
from .sources import LogoDevSource, BrandfetchSource, ScraperSource, BaseSource


logger = logging.getLogger(__name__)


class LogoFetcher:
    """Main orchestrator for fetching logos from multiple sources."""

    def __init__(
        self,
        config: Optional[Settings] = None,
        source_priority: Optional[List[LogoSource]] = None,
    ):
        """Initialize the logo fetcher.

        Args:
            config: Configuration settings (uses default if not provided)
            source_priority: Order of sources to try (default: logodev, brandfetch, scraper)
        """
        self.config = config or settings
        self.source_priority = source_priority or [
            LogoSource.LOGODEV,
            LogoSource.BRANDFETCH,
            LogoSource.SCRAPER,
        ]
        self._sources: Dict[LogoSource, BaseSource] = {}
        self._init_sources()

    def _init_sources(self) -> None:
        """Initialize all enabled sources."""
        if self.config.enable_logodev:
            self._sources[LogoSource.LOGODEV] = LogoDevSource(
                api_key=self.config.logodev_api_key,
                timeout=self.config.request_timeout,
            )

        if self.config.enable_brandfetch:
            self._sources[LogoSource.BRANDFETCH] = BrandfetchSource(
                api_key=self.config.brandfetch_api_key,
                timeout=self.config.request_timeout,
            )

        if self.config.enable_scraper:
            self._sources[LogoSource.SCRAPER] = ScraperSource(
                timeout=self.config.scraper_timeout,
                min_size=self.config.min_logo_width,
            )

    async def fetch(
        self,
        domain: str,
        sources: Optional[List[LogoSource]] = None,
    ) -> Optional[LogoResult]:
        """Fetch logo for a domain using fallback chain.

        Args:
            domain: Domain to fetch logo for
            sources: Specific sources to try (uses priority order if not provided)

        Returns:
            LogoResult if found, None otherwise
        """
        sources_to_try = sources or self.source_priority

        for source_type in sources_to_try:
            source = self._sources.get(source_type)
            if not source:
                continue

            try:
                url = await source.fetch(domain)
                if url:
                    return LogoResult(
                        domain=domain,
                        url=url,
                        source=source_type,
                    )
            except Exception as e:
                logger.warning(f"Error fetching from {source_type}: {e}")
                continue

        return None

    async def fetch_all(self, domain: str) -> AllLogosResult:
        """Fetch logos from all sources concurrently.

        Args:
            domain: Domain to fetch logos for

        Returns:
            AllLogosResult with results from all sources
        """
        results: List[LogoResult] = []
        errors: Dict[str, str] = {}

        async def fetch_from_source(
            source_type: LogoSource, source: BaseSource
        ) -> None:
            try:
                url = await source.fetch(domain)
                if url:
                    results.append(
                        LogoResult(
                            domain=domain,
                            url=url,
                            source=source_type,
                        )
                    )
            except Exception as e:
                errors[source_type.value] = str(e)

        tasks = [
            fetch_from_source(source_type, source)
            for source_type, source in self._sources.items()
        ]

        await asyncio.gather(*tasks)

        return AllLogosResult(
            domain=domain,
            results=results,
            errors=errors,
        )

    async def fetch_from_source(
        self, domain: str, source: LogoSource
    ) -> Optional[LogoResult]:
        """Fetch logo from a specific source.

        Args:
            domain: Domain to fetch logo for
            source: Specific source to use

        Returns:
            LogoResult if found, None otherwise
        """
        return await self.fetch(domain, sources=[source])

    def get_available_sources(self) -> List[LogoSource]:
        """Get list of available (enabled) sources.

        Returns:
            List of enabled LogoSource values
        """
        return list(self._sources.keys())
