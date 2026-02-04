"""CLI tool for Logo Fetcher using Typer."""

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src import LogoFetcher, LogoSource, __version__


app = typer.Typer(
    name="logo-fetcher",
    help="Fetch company logos from multiple sources",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"logo-fetcher version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Logo Fetcher - Fetch company logos from multiple sources."""
    pass


@app.command()
def get(
    domain: str = typer.Argument(..., help="Domain to fetch logo for (e.g., google.com)"),
    source: Optional[str] = typer.Option(
        None,
        "--source",
        "-s",
        help="Specific source to use (logodev, brandfetch, scraper)",
    ),
    all_sources: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Fetch from all sources",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON",
    ),
):
    """Fetch logo for a domain."""

    async def _fetch():
        fetcher = LogoFetcher()

        if all_sources:
            result = await fetcher.fetch_all(domain)

            if output_json:
                console.print(result.model_dump_json(indent=2))
            else:
                if result.results:
                    table = Table(title=f"Logos for {domain}")
                    table.add_column("Source", style="cyan")
                    table.add_column("URL", style="green")

                    for logo in result.results:
                        table.add_row(logo.source.value, logo.url)

                    console.print(table)

                    if result.errors:
                        console.print("\n[yellow]Errors:[/yellow]")
                        for src, err in result.errors.items():
                            console.print(f"  {src}: {err}")
                else:
                    console.print(f"[red]No logos found for {domain}[/red]")
                    if result.errors:
                        console.print("\n[yellow]Errors:[/yellow]")
                        for src, err in result.errors.items():
                            console.print(f"  {src}: {err}")
                    raise typer.Exit(1)
        else:
            sources = None
            if source:
                try:
                    sources = [LogoSource(source.lower())]
                except ValueError:
                    console.print(
                        f"[red]Invalid source: {source}. "
                        f"Valid options: logodev, brandfetch, scraper[/red]"
                    )
                    raise typer.Exit(1)

            result = await fetcher.fetch(domain, sources=sources)

            if result:
                if output_json:
                    console.print(result.model_dump_json(indent=2))
                else:
                    console.print(f"[green]Found logo for {domain}[/green]")
                    console.print(f"  Source: [cyan]{result.source.value}[/cyan]")
                    console.print(f"  URL: {result.url}")
            else:
                if output_json:
                    console.print(json.dumps({"error": f"No logo found for {domain}"}))
                else:
                    console.print(f"[red]No logo found for {domain}[/red]")
                raise typer.Exit(1)

    asyncio.run(_fetch())


@app.command()
def sources():
    """List available logo sources."""
    fetcher = LogoFetcher()
    available = fetcher.get_available_sources()

    table = Table(title="Available Sources")
    table.add_column("Source", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Priority")

    for i, src in enumerate(fetcher.source_priority):
        enabled = "[green]Yes[/green]" if src in available else "[red]No[/red]"
        table.add_row(src.value, enabled, str(i + 1))

    console.print(table)


if __name__ == "__main__":
    app()
