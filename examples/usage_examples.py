#!/usr/bin/env python3
"""
Usage examples for the Deep Research Multi-Agent System.

This file provides comprehensive examples of how to use both
the React-Agent and Workflow-based implementations.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel

console = Console()

class UsageExamples:
    """Collection of usage examples for the research system."""
    
    def __init__(self):
        self.console = console
    
    def print_example_header(self, title: str, description: str):
        """Print example header."""
        content = f"[bold cyan]{title}[/bold cyan]\n\n{description}"
        self.console.print(Panel(content, border_style="cyan"))

    async def example_1_basic_react_agent(self):
        """Example 1: Basic React-Agent usage."""
        self.print_example_header(
            "Example 1: Basic React-Agent Usage",
            "Simple research query using the autonomous React-Agent system"
        )
        
        try:
            from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
            
            # Initialize the researcher
            researcher = MultiAgentLeadResearcher()
            
            # Perform research
            query = "What are the main benefits of renewable energy?"
            console.print(f"🔍 Researching: {query}")
            
            result = await researcher.research(query)
            
            if result["success"]:
                console.print("✅ Research completed!")
                console.print(f"⏱️ Time: {result['execution_time']:.2f} seconds")
                console.print(f"📝 Report preview: {result['report'][:300]}...")
            else:
                console.print(f"❌ Research failed: {result.get('error')}")
                
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    async def example_2_workflow_with_persistence(self):
        """Example 2: Workflow system with persistence."""
        self.print_example_header(
            "Example 2: Workflow System with Persistence",
            "Using the workflow-based system with database persistence"
        )
        
        try:
            from src.cli import ResearchCLI
            
            # Initialize CLI
            cli = ResearchCLI()
            await cli.initialize()
            
            # Run research with persistence
            query = "How does blockchain technology work?"
            console.print(f"🔍 Researching: {query}")
            
            report_id = await cli.run_research(query, verbose=True)
            
            if report_id:
                console.print(f"✅ Research completed!")
                console.print(f"📄 Report saved with ID: {report_id}")
            else:
                console.print("❌ Research failed")
                
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    async def example_3_comparative_research(self):
        """Example 3: Comparative research across multiple topics."""
        self.print_example_header(
            "Example 3: Comparative Research",
            "Researching multiple related topics for comparison"
        )
        
        try:
            from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
            
            researcher = MultiAgentLeadResearcher()
            
            # Multiple related queries
            queries = [
                "Advantages of solar energy",
                "Advantages of wind energy", 
                "Advantages of hydroelectric power"
            ]
            
            results = []
            for query in queries:
                console.print(f"🔍 Researching: {query}")
                result = await researcher.research(query)
                results.append(result)
            
            # Simple comparison
            console.print("\n📊 Comparison Results:")
            for i, (query, result) in enumerate(zip(queries, results)):
                status = "✅" if result.get("success") else "❌"
                time_taken = result.get("execution_time", 0)
                console.print(f"{status} Query {i+1}: {time_taken:.1f}s - {query}")
                
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    async def example_4_custom_configuration(self):
        """Example 4: Custom configuration and profiles."""
        self.print_example_header(
            "Example 4: Custom Configuration",
            "Using custom research profiles and configuration"
        )
        
        try:
            # Load custom profile
            from examples.configs.research_profiles import get_profile
            
            profile = get_profile("academic")
            console.print("📋 Using Academic Research Profile:")
            console.print(f"   Max Agents: {profile['max_concurrent_subagents']}")
            console.print(f"   Iterations: {profile['max_iterations']}")
            console.print(f"   Quality: {profile['quality_threshold']}")
            
            # Note: In a real implementation, you'd apply these settings
            # to your research system configuration
            console.print("\n💡 Profile loaded successfully!")
            console.print("   (In real usage, these settings would configure the system)")
            
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    async def example_5_batch_processing(self):
        """Example 5: Batch processing multiple queries."""
        self.print_example_header(
            "Example 5: Batch Processing",
            "Processing multiple research queries efficiently"
        )
        
        try:
            from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
            
            researcher = MultiAgentLeadResearcher()
            
            # Batch of research queries
            batch_queries = [
                "Current trends in artificial intelligence",
                "Impact of climate change on agriculture", 
                "Latest developments in quantum computing"
            ]
            
            console.print(f"🔄 Processing {len(batch_queries)} queries in batch...")
            
            batch_results = []
            total_time = 0
            
            for i, query in enumerate(batch_queries, 1):
                console.print(f"📋 [{i}/{len(batch_queries)}] Processing: {query[:50]}...")
                
                result = await researcher.research(query)
                batch_results.append(result)
                
                if result.get("success"):
                    time_taken = result.get("execution_time", 0)
                    total_time += time_taken
                    console.print(f"   ✅ Completed in {time_taken:.1f}s")
                else:
                    console.print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Summary
            successful = sum(1 for r in batch_results if r.get("success"))
            console.print(f"\n📊 Batch Summary:")
            console.print(f"   ✅ Successful: {successful}/{len(batch_queries)}")
            console.print(f"   ⏱️ Total time: {total_time:.1f} seconds")
            console.print(f"   📈 Average per query: {total_time/len(batch_queries):.1f} seconds")
            
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    async def example_6_error_handling(self):
        """Example 6: Proper error handling and recovery."""
        self.print_example_header(
            "Example 6: Error Handling",
            "Demonstrating robust error handling and recovery strategies"
        )
        
        try:
            from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
            
            # Example with potential error conditions
            researcher = MultiAgentLeadResearcher()
            
            # Test with various query types
            test_queries = [
                "Valid query: What is machine learning?",
                "",  # Empty query
                "Very specific query that might be challenging to research",
            ]
            
            for query in test_queries:
                try:
                    if not query.strip():
                        console.print("⚠️ Skipping empty query")
                        continue
                    
                    console.print(f"🔍 Testing: {query}")
                    result = await researcher.research(query)
                    
                    if result.get("success"):
                        console.print("   ✅ Query handled successfully")
                    else:
                        error = result.get("error", "Unknown error")
                        console.print(f"   ⚠️ Query failed gracefully: {error}")
                        
                except Exception as e:
                    console.print(f"   ❌ Exception caught and handled: {e}")
            
            console.print("\n💡 Error handling demonstration complete!")
            
        except Exception as e:
            console.print(f"❌ Example failed: {e}")
    
    def example_7_integration_patterns(self):
        """Example 7: Common integration patterns."""
        self.print_example_header(
            "Example 7: Integration Patterns",
            "Common patterns for integrating the research system into applications"
        )
        
        # Show code patterns
        integration_code = '''
# Pattern 1: Web API Integration
from fastapi import FastAPI
from src.react_agents.multi_agent_system import MultiAgentLeadResearcher

app = FastAPI()
researcher = MultiAgentLeadResearcher()

@app.post("/research")
async def research_endpoint(query: str):
    result = await researcher.research(query)
    return {
        "success": result.get("success", False),
        "report": result.get("report", ""),
        "execution_time": result.get("execution_time", 0)
    }

# Pattern 2: Scheduled Research Jobs
import asyncio
from datetime import datetime

async def scheduled_research_job():
    queries = get_daily_research_queries()  # Your implementation
    researcher = MultiAgentLeadResearcher()
    
    for query in queries:
        result = await researcher.research(query)
        if result["success"]:
            save_report(query, result["report"])  # Your implementation

# Pattern 3: Interactive CLI Application
import click

@click.command()
@click.option('--query', prompt='Research query', help='What to research')
@click.option('--output', help='Output file for report')
async def cli_research(query: str, output: str):
    researcher = MultiAgentLeadResearcher()
    result = await researcher.research(query)
    
    if output and result["success"]:
        with open(output, 'w') as f:
            f.write(result["report"])

# Pattern 4: Batch Processing Pipeline
class ResearchPipeline:
    def __init__(self):
        self.researcher = MultiAgentLeadResearcher()
        self.results = []
    
    async def process_batch(self, queries: List[str]):
        for query in queries:
            result = await self.researcher.research(query)
            self.results.append(result)
        return self.results
        '''
        
        console.print(Panel(
            integration_code,
            title="Integration Code Examples",
            border_style="blue"
        ))
        
        console.print("💡 These patterns show how to integrate the research system into:")
        console.print("   • Web APIs and microservices")
        console.print("   • Scheduled background jobs")
        console.print("   • Interactive command-line tools") 
        console.print("   • Batch processing pipelines")


async def main():
    """Run all usage examples."""
    examples = UsageExamples()
    
    console.print(Panel.fit(
        "[bold cyan]Deep Research System - Usage Examples[/bold cyan]\n\n"
        "This interactive demo showcases various ways to use the system.",
        border_style="cyan"
    ))
    
    # Check if environment is configured
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("⚠️ [yellow]Warning: ANTHROPIC_API_KEY not found in environment[/yellow]")
        console.print("   Some examples may not work without proper API configuration")
        console.print("   Copy .env.example to .env and configure your API keys\n")
    
    # Menu of examples
    example_menu = [
        ("Basic React-Agent", examples.example_1_basic_react_agent),
        ("Workflow with Persistence", examples.example_2_workflow_with_persistence),
        ("Comparative Research", examples.example_3_comparative_research),
        ("Custom Configuration", examples.example_4_custom_configuration),
        ("Batch Processing", examples.example_5_batch_processing),
        ("Error Handling", examples.example_6_error_handling),
        ("Integration Patterns", lambda: examples.example_7_integration_patterns()),
    ]
    
    console.print("📋 [bold]Available Examples:[/bold]")
    for i, (name, _) in enumerate(example_menu, 1):
        console.print(f"   {i}. {name}")
    
    console.print("\n🚀 [cyan]Running all examples...[/cyan]\n")
    
    for i, (name, func) in enumerate(example_menu, 1):
        console.print(f"\n{'='*60}")
        console.print(f"Running Example {i}")
        console.print('='*60)
        
        try:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
        except Exception as e:
            console.print(f"❌ Example {i} failed: {e}")
        
        console.print("\n✅ Example completed\n")
    
    console.print(Panel.fit(
        "[bold green]All examples completed![/bold green]\n\n"
        "Check the source code of each example for implementation details.",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n⚠️ [yellow]Examples interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n❌ [red]Examples failed:[/red] {e}")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")