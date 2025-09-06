"""Base tools for React agents."""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> List[Dict[str, str]]:
    """Search the web for information.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with title, snippet, and url
    """
    max_results = 5  # Fixed value
    try:
        search = DuckDuckGoSearchRun()
        raw_results = search.run(query)
        
        # Parse results
        results = []
        if raw_results:
            # DuckDuckGo returns string format, need to parse
            lines = raw_results.split('\n')
            for i in range(0, min(len(lines), max_results * 2), 2):
                if i + 1 < len(lines):
                    title_snippet = lines[i]
                    url = lines[i + 1] if i + 1 < len(lines) else ""
                    
                    # Extract title and snippet
                    parts = title_snippet.split(' - ', 1)
                    title = parts[0] if parts else title_snippet
                    snippet = parts[1] if len(parts) > 1 else ""
                    
                    results.append({
                        "title": title.strip(),
                        "snippet": snippet.strip(),
                        "url": url.strip()
                    })
                    
                if len(results) >= max_results:
                    break
        
        return results
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


@tool
def web_fetch(url: str) -> Dict[str, str]:
    """Fetch the complete content of a webpage.
    
    Args:
        url: URL of the webpage to fetch
        
    Returns:
        Dictionary with title and content of the webpage
    """
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        if docs:
            content = "\n".join([doc.page_content for doc in docs])
            # Limit content length
            if len(content) > 10000:
                content = content[:10000] + "...[truncated]"
                
            return {
                "url": url,
                "title": docs[0].metadata.get("title", "Untitled"),
                "content": content
            }
        else:
            return {
                "url": url,
                "title": "Error",
                "content": "Failed to fetch content"
            }
            
    except Exception as e:
        logger.error(f"Web fetch failed for {url}: {e}")
        return {
            "url": url,
            "title": "Error",
            "content": f"Failed to fetch: {str(e)}"
        }


@tool
async def parallel_web_search(queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
    """Execute multiple web searches in parallel.
    
    Args:
        queries: List of search queries
        max_results_per_query: Maximum results per query
        
    Returns:
        Combined results from all searches
    """
    async def search_async(query):
        return web_search(query, max_results_per_query)
    
    # Execute searches in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, web_search, query, max_results_per_query)
            for query in queries
        ]
        results = await asyncio.gather(*tasks)
    
    # Combine results
    combined = []
    for query, query_results in zip(queries, results):
        for result in query_results:
            result["query"] = query
            combined.append(result)
    
    return combined


@tool
def complete_task(report: str) -> Dict[str, str]:
    """Submit the final research report.
    
    Args:
        report: The complete research report in markdown format
        
    Returns:
        Confirmation of task completion
    """
    return {
        "status": "completed",
        "report": report,
        "message": "Research report submitted successfully"
    }