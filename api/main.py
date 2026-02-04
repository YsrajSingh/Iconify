"""FastAPI application for Logo Fetcher API."""

from contextlib import asynccontextmanager
from typing import Optional
import time

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src import LogoFetcher, LogoResult, LogoSource, __version__
from src.config import settings
from src.models import AllLogosResult, HealthResponse


# Rate limiting state (simple in-memory implementation)
rate_limit_store: dict[str, list[float]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    app.state.fetcher = LogoFetcher()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Logo Fetcher API",
    description="A professional API for fetching company logos from multiple sources",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # 1 minute window

        # Clean old entries and add new request
        if client_ip not in rate_limit_store:
            rate_limit_store[client_ip] = []

        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if now - t < window
        ]

        if len(rate_limit_store[client_ip]) >= settings.api_rate_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        rate_limit_store[client_ip].append(now)

    return await call_next(request)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and available sources."""
    fetcher: LogoFetcher = app.state.fetcher
    available_sources = fetcher.get_available_sources()

    return HealthResponse(
        status="healthy",
        version=__version__,
        sources={
            "logodev": LogoSource.LOGODEV in available_sources,
            "brandfetch": LogoSource.BRANDFETCH in available_sources,
            "scraper": LogoSource.SCRAPER in available_sources,
        },
    )


@app.get(
    "/api/v1/logo/{domain}",
    response_model=LogoResult,
    tags=["Logo"],
    summary="Get logo for domain",
    responses={
        200: {"description": "Logo found successfully"},
        404: {"description": "No logo found for domain"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_logo(
    domain: str,
    source: Optional[LogoSource] = Query(
        None, description="Specific source to use (optional)"
    ),
):
    """Fetch logo for a domain.

    Tries sources in priority order until a logo is found:
    1. logo.dev
    2. Brandfetch
    3. Website scraper

    Optionally specify a single source to use.
    """
    fetcher: LogoFetcher = app.state.fetcher

    if source:
        result = await fetcher.fetch_from_source(domain, source)
    else:
        result = await fetcher.fetch(domain)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No logo found for domain: {domain}",
        )

    return result


@app.get(
    "/api/v1/logo/{domain}/all",
    response_model=AllLogosResult,
    tags=["Logo"],
    summary="Get logos from all sources",
    responses={
        200: {"description": "Results from all sources (may be empty)"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_all_logos(domain: str):
    """Fetch logos from all available sources concurrently.

    Returns results from all sources, including any errors encountered.
    """
    fetcher: LogoFetcher = app.state.fetcher
    return await fetcher.fetch_all(domain)


@app.get("/api/v1/sources", tags=["Info"])
async def list_sources():
    """List all available logo sources."""
    fetcher: LogoFetcher = app.state.fetcher
    return {
        "sources": [s.value for s in fetcher.get_available_sources()],
        "priority": [s.value for s in fetcher.source_priority],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
