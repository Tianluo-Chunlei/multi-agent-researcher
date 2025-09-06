#!/usr/bin/env python3
"""Demo script for Deep Research system."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli import ResearchCLI
from rich.console import Console
from rich.panel import Panel

console = Console()


async def main():
    """Run demo of the research system."""
    
    # Display welcome
    console.print(Panel.fit(
        "[bold cyan]Deep Research System Demo[/bold cyan]\n\n"
        "This demo shows the enhanced multi-agent research system\n"
        "with real web search, database persistence, and more!",
        border_style="cyan"
    ))
    
    # Initialize system
    console.print("\n[cyan]Initializing system...[/cyan]")
    cli = ResearchCLI()
    await cli.initialize()
    
    # Demo queries
    queries = [
        "What is artificial intelligence?",
        # "Latest breakthroughs in quantum computing 2024",
        # "How does blockchain technology work?"
    ]
    
    console.print("\n[bold]Running demo queries:[/bold]")
    for i, query in enumerate(queries, 1):
        console.print(f"\n[cyan]Query {i}:[/cyan] {query}")
        
        try:
            report_id = await cli.run_research(query, verbose=False)
            console.print(f"[green]✓ Complete![/green] Report ID: {report_id[:8]}...")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
    
    console.print("\n" + "="*60)
    console.print("[bold green]Demo complete![/bold green]")
    console.print("="*60)
    console.print("\nTo run the system interactively, use:")
    console.print("  [cyan]python src/cli.py[/cyan]")
    console.print("\nOr research a specific topic:")
    console.print("  [cyan]python src/cli.py \"your research question\"[/cyan]")


if __name__ == "__main__":
    asyncio.run(main())