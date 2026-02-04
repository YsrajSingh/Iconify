"""Logo Fetcher - A professional library for fetching company logos."""

from .fetcher import LogoFetcher
from .models import LogoResult, LogoSource
from .config import Settings

__version__ = "1.0.0"
__all__ = ["LogoFetcher", "LogoResult", "LogoSource", "Settings"]
