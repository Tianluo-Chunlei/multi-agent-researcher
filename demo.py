#!/usr/bin/env python3
"""
Comprehensive demo script for Deep Research Multi-Agent System.

This script demonstrates both implementation approaches:
1. React-Agent based system (autonomous decision making)
2. Workflow-based system (LangGraph state management)
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

class DemoRunner:
    """Demo runner for showcasing the research system."""
    
    def __init__(self):
        self.console = console
    
    def print_header(self, title: str, subtitle: str = ""):
        """Print a formatted header."""
        content = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            content += f"\n\n{subtitle}"
        
        self.console.print(Panel.fit(
            content,
            border_style="cyan",
            padding=(1, 2)
        ))
    
    def print_section(self, title: str):
        """Print a section header."""
        self.console.print(f"\n[bold yellow]{'='*60}[/bold yellow]")
        self.console.print(f"[bold yellow]{title}[/bold yellow]")
        self.console.print(f"[bold yellow]{'='*60}[/bold yellow]\n")
    
    async def demo_react_agent_system(self, query: str):
        """Demo the React-Agent based system."""
        self.print_section("REACT-AGENT SYSTEM DEMO")
        
        try:
            from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
            
            self.console.print("🤖 [cyan]Initializing React-Agent based system...[/cyan]")
            researcher = MultiAgentLeadResearcher()
            
            self.console.print(f"🔍 [green]Researching:[/green] {query}")
            self.console.print("⏱️  [yellow]Note: This may take 1-3 minutes for comprehensive research[/yellow]\n")
            
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Research in progress...", total=None)
                result = await researcher.research(query)
            
            elapsed = time.time() - start_time
            
            if result.get("success"):
                self.console.print(f"✅ [green]Research completed in {elapsed:.2f} seconds![/green]\n")
                
                # Create results table
                table = Table(title="Research Results - React-Agent System")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Status", "✅ Success")
                table.add_row("Execution Time", f"{elapsed:.2f} seconds")
                table.add_row("Report Length", f"{len(result['report'])} characters")
                
                self.console.print(table)
                
                self.console.print("\n[bold]Research Report:[/bold]")
                self.console.print(Panel(
                    result["report"][:1000] + "..." if len(result["report"]) > 1000 else result["report"],
                    title="Report Preview",
                    border_style="green"
                ))
                
                return result
            else:
                self.console.print(f"❌ [red]Research failed:[/red] {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.console.print(f"❌ [red]Demo failed:[/red] {e}")
            return None
    
    async def demo_workflow_system(self, query: str):
        """Demo the Workflow-based system."""
        self.print_section("WORKFLOW SYSTEM DEMO")
        
        try:
            from src.cli import ResearchCLI
            
            self.console.print("🔄 [cyan]Initializing Workflow-based system...[/cyan]")
            cli = ResearchCLI()
            await cli.initialize()
            
            self.console.print(f"🔍 [green]Researching:[/green] {query}")
            self.console.print("⏱️  [yellow]Note: This may take 1-3 minutes for comprehensive research[/yellow]\n")
            
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Workflow execution in progress...", total=None)
                report_id = await cli.run_research(query, verbose=False)
            
            elapsed = time.time() - start_time
            
            if report_id:
                self.console.print(f"✅ [green]Research completed in {elapsed:.2f} seconds![/green]")
                self.console.print(f"📄 [blue]Report ID:[/blue] {report_id}")
                
                # Create results table
                table = Table(title="Research Results - Workflow System")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Status", "✅ Success")
                table.add_row("Execution Time", f"{elapsed:.2f} seconds")
                table.add_row("Report ID", report_id[:8] + "...")
                
                self.console.print(table)
                return {"success": True, "report_id": report_id, "execution_time": elapsed}
            else:
                self.console.print("❌ [red]Research failed[/red]")
                return None
                
        except Exception as e:
            self.console.print(f"❌ [red]Demo failed:[/red] {e}")
            return None
    
    def compare_results(self, react_result, workflow_result):
        """Compare results from both systems."""
        self.print_section("SYSTEM COMPARISON")
        
        if not react_result or not workflow_result:
            self.console.print("⚠️ [yellow]Cannot compare - one or both systems failed[/yellow]")
            return
        
        comparison_table = Table(title="Performance Comparison")
        comparison_table.add_column("System", style="bold")
        comparison_table.add_column("Execution Time", style="cyan")
        comparison_table.add_column("Output Type", style="green")
        comparison_table.add_column("Strengths", style="blue")
        
        react_time = react_result.get("execution_time", 0)
        workflow_time = workflow_result.get("execution_time", 0)
        
        comparison_table.add_row(
            "React-Agent",
            f"{react_time:.2f}s",
            "Direct Report",
            "Autonomous, Real-time streaming, Flexible"
        )
        comparison_table.add_row(
            "Workflow",
            f"{workflow_time:.2f}s", 
            "Persistent Report",
            "State management, Checkpoints, Structured"
        )
        
        self.console.print(comparison_table)
        
        # Performance analysis
        if react_time < workflow_time:
            faster = "React-Agent"
            diff = workflow_time - react_time
        else:
            faster = "Workflow"
            diff = react_time - workflow_time
        
        self.console.print(f"\n🏃 [green]{faster} system was {diff:.2f}s faster[/green]")


async def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Deep Research System Demo")
    parser.add_argument(
        "query", 
        nargs="?", 
        default="Latest developments in artificial intelligence for healthcare",
        help="Research query to demonstrate"
    )
    parser.add_argument(
        "--system",
        choices=["react", "workflow", "both"],
        default="both",
        help="Which system to demo"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use a simple query for faster demo"
    )
    
    args = parser.parse_args()
    
    # Use simple query if requested
    if args.simple:
        query = "What is the capital of France?"
    else:
        query = args.query
    
    demo = DemoRunner()
    
    # Welcome message
    demo.print_header(
        "Deep Research Multi-Agent System - Live Demo",
        "Showcasing two powerful approaches to AI-driven research:\n"
        "• React-Agent: Autonomous decision-making agents\n"
        "• Workflow: Structured LangGraph state management"
    )
    
    console.print(f"\n🎯 [bold]Demo Query:[/bold] {query}\n")
    
    react_result = None
    workflow_result = None
    
    # Run React-Agent system
    if args.system in ["react", "both"]:
        react_result = await demo.demo_react_agent_system(query)
    
    # Run Workflow system  
    if args.system in ["workflow", "both"]:
        workflow_result = await demo.demo_workflow_system(query)
    
    # Compare results
    if args.system == "both":
        demo.compare_results(react_result, workflow_result)
    
    # Final summary
    demo.print_section("DEMO COMPLETE")
    
    console.print("🎉 [bold green]Demo completed successfully![/bold green]\n")
    
    console.print("📚 [cyan]Next Steps:[/cyan]")
    console.print("  • Explore the codebase in src/")
    console.print("  • Run your own queries with different systems")
    console.print("  • Check out the examples/ directory")
    console.print("  • Read the documentation in docs/")
    
    console.print("\n💡 [yellow]Usage Examples:[/yellow]")
    console.print("  [dim]# Interactive React-Agent mode[/dim]")
    console.print("  python multi_reactagent.py -i")
    console.print("  [dim]# Single query with Workflow system[/dim]")
    console.print("  python workflow_agent.py")
    console.print("  [dim]# Compare systems[/dim]")
    console.print("  python demo.py \"your research question\"")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n⚠️ [yellow]Demo interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ [red]Demo failed:[/red] {e}")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)