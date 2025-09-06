"""Tools using LangGraph and LangChain built-in implementations."""

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool
from typing import List, Dict, Any
import os


def get_search_tool():
    """Get search tool - prefer Tavily if API key available, else DuckDuckGo."""
    if os.getenv("TAVILY_API_KEY"):
        # Use Tavily if API key is available
        return TavilySearchResults(max_results=5)
    else:
        # Fallback to DuckDuckGo (no API key needed)
        return DuckDuckGoSearchRun()


@tool
def fetch_webpage(url: str) -> str:
    """Fetch content from a webpage.
    
    Args:
        url: The URL to fetch
        
    Returns:
        The webpage content as text
    """
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        if docs:
            content = "\n".join([doc.page_content for doc in docs])
            # Limit content length
            if len(content) > 10000:
                content = content[:10000] + "...[truncated]"
            return content
        return "Failed to fetch content"
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@tool  
def run_subagent(task: str) -> str:
    """Run a research subagent for a specific task.
    
    Args:
        task: The research task description
        
    Returns:
        The research findings
    """
    # This will be replaced with actual subagent call
    # For now, it's a placeholder that will be overridden
    return f"Subagent researching: {task}"


@tool
def add_citations_to_report(report: str, sources: List[str]) -> str:
    """Add citations to a research report.
    
    Args:
        report: The report text
        sources: List of source URLs
        
    Returns:
        Report with citations added
    """
    # Simple citation adding
    cited_report = report
    sources_section = "\n\n## Sources\n"
    for i, source in enumerate(sources, 1):
        sources_section += f"[{i}] {source}\n"
    
    return cited_report + sources_section