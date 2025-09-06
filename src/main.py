"""Main entry point for Deep Research system."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.workflow import ResearchWorkflow
from src.utils.logger import logger
from src.utils.config import config


async def run_research(query: str) -> str:
    """Run a research query.
    
    Args:
        query: The research query
        
    Returns:
        Final research report with citations
    """
    try:
        # Create workflow
        workflow = ResearchWorkflow()
        
        logger.info(f"Starting research for: {query}")
        
        # Run research
        result = await workflow.run_research(query)
        
        if result and result.get("cited_text"):
            return result["cited_text"]
        else:
            return "Research failed to produce results."
            
    except Exception as e:
        logger.error(f"Research failed: {e}")
        return f"Error: {str(e)}"


async def main():
    """Main function."""
    print("=" * 60)
    print("Deep Research Multi-Agent System")
    print("=" * 60)
    
    # Check configuration
    if not config.anthropic_api_key or config.anthropic_api_key == "your_key_here_change_this":
        print("\n❌ Please set your Anthropic API key in .env file")
        return
    
    print(f"\nConfiguration:")
    print(f"- Lead Agent Model: {config.lead_agent_model}")
    print(f"- Subagent Model: {config.subagent_model}")
    print(f"- Max Concurrent Subagents: {config.max_concurrent_subagents}")
    
    # Get query from command line or interactive
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("\nEnter your research query (or 'quit' to exit):")
        query = input("> ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            return
    
    if not query:
        query = "What are the latest developments in AI agents?"
        print(f"\nUsing example query: {query}")
    
    print(f"\n🔍 Researching: {query}")
    print("-" * 60)
    
    # Run research
    result = await run_research(query)
    
    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()