#!/usr/bin/env python3
"""Main entry point for Multi-Agent Research System."""

import asyncio
import argparse
import sys
from pathlib import Path
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.react_agents.multi_agent_system import MultiAgentLeadResearcher
from src.utils.logger import logger


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Deep Research System"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Research query to execute"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file for the research report",
        default=None
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Set environment variable
    os.environ["USER_AGENT"] = "MultiAgentResearchSystem/1.0"
    
    if args.interactive:
        # Interactive mode
        print("=" * 60)
        print("MULTI-AGENT RESEARCH SYSTEM")
        print("=" * 60)
        print("Type 'exit' to quit")
        print("-" * 60)
        
        researcher = MultiAgentLeadResearcher()
        
        while True:
            try:
                query = input("\nEnter research query: ").strip()
                
                if query.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                print(f"\n🔍 Researching: {query}")
                print("-" * 40)
                
                result = await researcher.research(query)
                
                if result.get("success"):
                    print("\n" + "=" * 60)
                    print("RESEARCH REPORT")
                    print("=" * 60)
                    print(result["report"])
                    print("=" * 60)
                    print(f"\n⏱️  Time: {result['execution_time']:.2f} seconds")
                    
                    if args.output:
                        with open(args.output, 'w', encoding='utf-8') as f:
                            f.write(f"# Research Report\n\n")
                            f.write(f"Query: {query}\n")
                            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write("---\n\n")
                            f.write(result["report"])
                        print(f"📄 Report saved to: {args.output}")
                else:
                    print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"Error: {e}")
    
    else:
        # Single query mode
        if not args.query:
            print("Error: Please provide a query or use -i for interactive mode")
            parser.print_help()
            sys.exit(1)
        
        print("=" * 60)
        print("MULTI-AGENT RESEARCH SYSTEM")
        print("=" * 60)
        print(f"Query: {args.query}")
        print("-" * 60)
        
        researcher = MultiAgentLeadResearcher()
        result = await researcher.research(args.query)
        
        if result.get("success"):
            print("\n" + "=" * 60)
            print("RESEARCH REPORT")
            print("=" * 60)
            print(result["report"])
            print("=" * 60)
            print(f"\n⏱️  Execution time: {result['execution_time']:.2f} seconds")
            
            if result.get("sources"):
                print(f"📚 Sources used: {len(result['sources'])}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"# Multi-Agent Research Report\n\n")
                    f.write(f"Query: {args.query}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Execution Time: {result['execution_time']:.2f} seconds\n\n")
                    f.write("---\n\n")
                    f.write(result["report"])
                print(f"\n📄 Report saved to: {args.output}")
        else:
            print(f"\n❌ Research failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)