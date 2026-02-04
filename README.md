# Logo Fetcher

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A professional library for fetching company logos from multiple sources. Includes a FastAPI REST API, CLI tool, and Cloudflare Worker deployment.

## Features

- **Multiple Sources**: Fetches logos from logo.dev, Brandfetch, and website scraping
- **Fallback Chain**: Automatically tries multiple sources until a logo is found
- **Async Support**: Built with async/await for optimal performance
- **REST API**: FastAPI-powered API with OpenAPI documentation
- **CLI Tool**: Easy-to-use command-line interface
- **Edge Deployment**: Cloudflare Worker for global, low-latency access
- **Docker Ready**: Multi-stage Dockerfile for production deployments

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/ysrajsingh/iconify.git
cd iconify

# Start the API with Docker (works without API keys)
docker-compose up -d

# Test it
curl http://localhost:8000/api/v1/logo/google.com
```

## Installation (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file (optional):

```bash
cp .env.example .env
```

API keys are **optional** - the APIs work without them:

```env
# API Keys (Optional - for better results)
LOGODEV_API_KEY=your_logodev_api_key_here
BRANDFETCH_API_KEY=your_brandfetch_api_key_here

# Timeouts
REQUEST_TIMEOUT=10.0
SCRAPER_TIMEOUT=15.0

# Rate limiting
API_RATE_LIMIT=100
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LOGODEV_API_KEY` | API key for logo.dev | No (optional) |
| `BRANDFETCH_API_KEY` | API key for Brandfetch | No (optional) |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | No (default: 10.0) |
| `SCRAPER_TIMEOUT` | Website scraper timeout (seconds) | No (default: 15.0) |
| `ENABLE_LOGODEV` | Enable logo.dev source | No (default: true) |
| `ENABLE_BRANDFETCH` | Enable Brandfetch source | No (default: true) |
| `ENABLE_SCRAPER` | Enable website scraper | No (default: true) |
| `API_RATE_LIMIT` | API requests per minute per IP | No (default: 100) |
| `REDIS_URL` | Redis URL for caching | No |

## Usage

### As a Library

```python
import asyncio
from src import LogoFetcher

async def main():
    fetcher = LogoFetcher()

    # Fetch logo (tries all sources)
    result = await fetcher.fetch("google.com")
    if result:
        print(f"Found logo: {result.url}")
        print(f"Source: {result.source}")

    # Fetch from all sources
    all_results = await fetcher.fetch_all("github.com")
    for logo in all_results.results:
        print(f"{logo.source}: {logo.url}")

asyncio.run(main())
```

### CLI

```bash
# Basic usage
python -m cli.main get google.com

# Get from specific source
python -m cli.main get google.com --source logodev

# Get from all sources
python -m cli.main get google.com --all

# Output as JSON
python -m cli.main get google.com --json

# List available sources
python -m cli.main sources
```

### REST API

```bash
# Start the API server
uvicorn api.main:app --reload

# Or use Docker
docker-compose up -d
```

API Endpoints:
- `GET /api/v1/logo/{domain}` - Get logo for domain
- `GET /api/v1/logo/{domain}/all` - Get logos from all sources
- `GET /api/v1/sources` - List available sources
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

Example requests:
```bash
# Get logo
curl http://localhost:8000/api/v1/logo/google.com

# Get from specific source
curl "http://localhost:8000/api/v1/logo/google.com?source=logodev"

# Get from all sources
curl http://localhost:8000/api/v1/logo/google.com/all
```

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Cloudflare Worker

```bash
cd worker

# Install dependencies
npm install

# Development
npm run dev

# Deploy
npm run deploy

# Optional: Set API keys as secrets
npx wrangler secret put LOGODEV_API_KEY
npx wrangler secret put BRANDFETCH_API_KEY
```

Worker endpoints:
- `GET /logo/{domain}` - Get logo
- `GET /logo/{domain}?all=true` - Get from all sources
- `GET /logo/{domain}?source=logodev` - Get from specific source
- `GET /health` - Health check

## Logo Sources

### 1. logo.dev

- API key optional
- High-quality company logos
- Falls back to Google Favicon Service if unavailable
- Get your key at [logo.dev](https://logo.dev)

### 2. Brandfetch

- API key optional
- Official brand assets
- Multiple formats (SVG, PNG)
- Falls back to DuckDuckGo Icons if unavailable
- Get your key at [brandfetch.com/developers](https://brandfetch.com/developers)

### 3. Website Scraper

- No API key required
- Extracts from og:image, apple-touch-icon, favicon
- Direct website scraping as fallback

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov=api --cov=cli

# Run specific tests
pytest tests/test_sources.py
```

### Code Quality

```bash
# Format and lint
ruff check .
ruff format .

# Type checking
mypy src api cli
```

## Project Structure

```
iconify/
├── src/                  # Core library
│   ├── config.py         # Configuration
│   ├── models.py         # Pydantic models
│   ├── fetcher.py        # Main orchestrator
│   └── sources/          # Logo sources
├── api/                  # FastAPI application
├── cli/                  # CLI tool
├── worker/               # Cloudflare Worker
├── tests/                # Test suite
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose
├── .env.example          # Example environment file
└── .env                  # Your configuration (optional)
```

## API Response Format

```json
{
  "domain": "google.com",
  "url": "https://img.logo.dev/google.com?token=...",
  "source": "logodev",
  "metadata": null,
  "cached": false
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [logo.dev](https://logo.dev) - Logo API
- [Brandfetch](https://brandfetch.com) - Brand assets API
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Typer](https://typer.tiangolo.com) - CLI framework
