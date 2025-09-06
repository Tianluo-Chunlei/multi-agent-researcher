"""Citation Agent as a tool for Lead Agent."""

from typing import Dict, List, Any
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
import re
import logging

from .prompts import get_citation_prompt
from src.utils.config import config

logger = logging.getLogger(__name__)


class CitationAgentTool:
    """Citation Agent that adds citations to research reports."""
    
    def __init__(self):
        """Initialize the Citation Agent."""
        self.model = ChatAnthropic(
            model=config.citation_model,
            temperature=0.1,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            anthropic_api_url=config.anthropic_base_url
        )
    
    async def add_citations(
        self,
        report: str,
        sources: List[Dict[str, str]]
    ) -> str:
        """Add citations to a research report.
        
        Args:
            report: The research report text without citations
            sources: List of sources with title and url
            
        Returns:
            Report with citations added
        """
        try:
            logger.info("Adding citations to report...")
            
            # Format sources for the prompt
            sources_text = "\n".join([
                f"[{i+1}] {source.get('title', 'Untitled')} - {source.get('url', '')}"
                for i, source in enumerate(sources)
            ])
            
            # Create prompt for citation agent
            prompt = f"""{get_citation_prompt()}

<synthesized_text>
{report}
</synthesized_text>

<sources>
{sources_text}
</sources>

Please add appropriate citations to the report text. Use the format [1], [2], etc. to reference the sources.
Output the complete text with citations added."""
            
            # Get response from model
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            # Extract the cited text
            cited_text = response.content
            
            # Try to extract text between tags if present
            match = re.search(
                r'<exact_text_with_citation>(.*?)</exact_text_with_citation>',
                cited_text,
                re.DOTALL
            )
            if match:
                cited_text = match.group(1).strip()
            
            # Add source list at the end if not already present
            if not re.search(r'\n\s*##?\s*(?:References|Sources)', cited_text, re.IGNORECASE):
                cited_text += "\n\n## Sources\n"
                for i, source in enumerate(sources):
                    cited_text += f"[{i+1}] {source.get('title', 'Untitled')} - {source.get('url', '')}\n"
            
            logger.info("Citations added successfully")
            return cited_text
            
        except Exception as e:
            logger.error(f"Citation failed: {e}")
            # Return original report if citation fails
            return report


# Create tool wrapper for LangChain
@tool
async def add_citations(report: str, sources: List[Dict[str, str]]) -> str:
    """Add citations to a research report.
    
    This tool takes a research report and a list of sources, then adds
    appropriate citations throughout the text where claims are supported
    by the sources.
    
    Args:
        report: The research report text without citations
        sources: List of dictionaries containing 'title' and 'url' for each source
        
    Returns:
        The report with citations added in [1], [2] format, plus a sources list
    """
    citation_agent = CitationAgentTool()
    return await citation_agent.add_citations(report, sources)