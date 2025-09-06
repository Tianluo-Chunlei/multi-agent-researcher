#!/usr/bin/env python3
"""Command-line interface for Deep Research system."""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph.workflow import ResearchWorkflow
from src.storage.database import ResearchDatabase
from src.utils.logger import logger

console = Console()


class ResearchCLI:
    """CLI interface for research system."""
    
    def __init__(self):
        """Initialize CLI."""
        self.workflow = ResearchWorkflow()
        self.db = ResearchDatabase()
        
    async def initialize(self):
        """Initialize database and workflow."""
        await self.db.initialize()
        console.print("[green]✓[/green] System initialized")
    
    async def run_research(self, query: str, verbose: bool = False) -> str:
        """Run research on a query."""
        report_id = str(uuid.uuid4())
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=not verbose
        ) as progress:
            task = progress.add_task("[cyan]Starting research...", total=None)
            
            try:
                # Run workflow
                progress.update(task, description="[cyan]Running research workflow...")
                result = await self.workflow.run_research(query)
                
                # Save results
                progress.update(task, description="[cyan]Saving results...")
                await self.db.save_research_report(
                    report_id=report_id,
                    plan_id=result.get("query_id", ""),
                    query=query,
                    report=result.get("synthesized_text", ""),
                    cited_report=result.get("cited_text", ""),
                    sources=result.get("sources", []),
                    metrics={
                        "tokens": result.get("total_tokens_used", 0),
                        "time": result.get("execution_time", 0),
                        "subagents": len(result.get("completed_subagents", []))
                    }
                )
                
                progress.update(task, description="[green]✓ Research complete!")
                
                # Show results immediately
                console.print("\n" + "="*60)
                console.print("[bold cyan]RESEARCH RESULTS[/bold cyan]")
                console.print("="*60 + "\n")
                
                if result.get("cited_text"):
                    console.print(Markdown(result["cited_text"]))
                else:
                    console.print(result.get("synthesized_text", "No results"))
                
                # Show metrics
                console.print("\n[bold]Metrics:[/bold]")
                console.print(f"• Tokens: {result.get('total_tokens_used', 0)}")
                console.print(f"• Time: {result.get('execution_time', 0):.2f}s")
                console.print(f"• Subagents: {len(result.get('completed_subagents', []))}")
                
                return report_id
                
            except Exception as e:
                progress.update(task, description=f"[red]✗ Error: {e}")
                raise


@click.command()
@click.argument('query', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
def main(query: Optional[str], verbose: bool):
    """Deep Research - Multi-agent research system.
    
    Run with a QUERY to research that topic, or without arguments for interactive mode.
    """
    async def run():
        cli = ResearchCLI()
        await cli.initialize()
        
        if query:
            # Single query mode
            console.print(f"\n[cyan]🔍 Researching:[/cyan] {query}\n")
            try:
                report_id = await cli.run_research(query, verbose)
                console.print(f"\n[green]✓ Report saved:[/green] {report_id[:8]}...")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
        else:
            # Interactive mode
            console.print(Panel.fit(
                "[bold cyan]Deep Research System[/bold cyan]\n"
                "Multi-agent research powered by AI",
                border_style="cyan"
            ))
            
            while True:
                try:
                    query = console.input("\n[bold cyan]Enter query (or 'exit'):[/bold cyan] ").strip()
                    
                    if query.lower() in ['exit', 'quit', 'q']:
                        console.print("[yellow]Goodbye![/yellow]")
                        break
                    
                    if query:
                        console.print(f"\n[cyan]🔍 Researching:[/cyan] {query}\n")
                        report_id = await cli.run_research(query, verbose=True)
                        console.print(f"\n[green]✓ Report saved:[/green] {report_id[:8]}...")
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    logger.error(f"CLI error: {e}", exc_info=True)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()