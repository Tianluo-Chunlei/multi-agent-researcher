"""Main Deep Research System using React Agents."""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from .lead_agent import LeadReactAgent
from src.utils.logger import setup_logger
from src.utils.config import config

logger = logging.getLogger(__name__)


class DeepResearchSystem:
    """Main system for deep research using multiple React agents."""
    
    def __init__(self):
        """Initialize the Deep Research System."""
        # Setup logging
        setup_logger()
        
        # Initialize lead agent
        self.lead_agent = LeadReactAgent()
        
        logger.info("Deep Research System initialized")
        logger.info(f"Lead Agent Model: {config.lead_agent_model}")
        logger.info(f"SubAgent Model: {config.subagent_model}")
    
    async def research(
        self,
        query: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a research query.
        
        Args:
            query: The research query
            output_file: Optional file path to save the report
            
        Returns:
            Research results
        """
        logger.info("=" * 50)
        logger.info(f"Starting Deep Research")
        logger.info(f"Query: {query}")
        logger.info("=" * 50)
        
        try:
            # Run research through lead agent
            result = await self.lead_agent.research(query)
            
            # Save report if output file specified
            if output_file and result.get("success"):
                self._save_report(result["report"], output_file)
            
            # Log summary
            if result.get("success"):
                logger.info("=" * 50)
                logger.info("Research Completed Successfully")
                logger.info(f"Execution Time: {result.get('execution_time', 0):.2f} seconds")
                logger.info(f"Sources Found: {len(result.get('sources', []))}")
                logger.info(f"Report Length: {len(result.get('report', ''))} characters")
                logger.info("=" * 50)
            else:
                logger.error(f"Research failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"System error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _save_report(self, report: str, output_file: str):
        """Save report to file.
        
        Args:
            report: The research report
            output_file: File path to save to
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Research Report\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write("---\n\n")
                f.write(report)
            logger.info(f"Report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def get_history(self) -> list:
        """Get research history.
        
        Returns:
            List of previous research sessions
        """
        return self.lead_agent.get_history()
    
    def clear_history(self):
        """Clear research history."""
        self.lead_agent.clear_history()
        logger.info("System history cleared")


async def main():
    """Main entry point for the research system."""
    import sys
    
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What are the latest developments in quantum computing in 2024?"
    
    # Create system
    system = DeepResearchSystem()
    
    # Run research
    result = await system.research(
        query=query,
        output_file="research_output.md"
    )
    
    # Print summary
    if result.get("success"):
        print("\n" + "=" * 50)
        print("RESEARCH REPORT")
        print("=" * 50)
        print(result["report"][:1000] + "..." if len(result["report"]) > 1000 else result["report"])
        print("\n" + "=" * 50)
        print(f"Full report saved to: research_output.md")
    else:
        print(f"Research failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())