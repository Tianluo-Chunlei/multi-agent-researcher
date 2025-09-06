"""Search tools for Deep Research system."""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from ddgs import DDGS
from src.tools.base import BaseTool
from src.utils.logger import logger
from src.utils.rate_limiter import search_rate_limited, fetch_rate_limited


class WebSearchTool(BaseTool):
    """Tool for searching the web."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information. Returns snippets from search results."
        )
        
    @search_rate_limited(tokens=1)
    async def execute(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Execute web search using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Search results
        """
        logger.info(f"Searching web for: {query}")
        
        try:
            # Run DuckDuckGo search in executor to avoid blocking
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results))
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", "")
                })
            
            logger.info(f"Found {len(results)} search results")
            
            # Return raw data - the base class will format it
            return {
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Fallback to mock results if search fails
            results = []
            for i in range(min(3, max_results)):
                results.append({
                    "title": f"Fallback Result {i+1}",
                    "snippet": f"Search service temporarily unavailable. This is fallback data.",
                    "url": f"https://example.com/result{i+1}"
                })
            
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "error": str(e)
            }
    
    def validate_params(self, **kwargs) -> bool:
        """Validate search parameters."""
        return "query" in kwargs and kwargs["query"]


class WebFetchTool(BaseTool):
    """Tool for fetching complete web page content."""
    
    def __init__(self):
        super().__init__(
            name="web_fetch",
            description="Fetch the complete content of a web page given its URL."
        )
        
    @fetch_rate_limited(tokens=1)
    async def execute(self, url: str) -> Dict[str, Any]:
        """Fetch web page content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Web page content
        """
        logger.info(f"Fetching URL: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse HTML
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract text content
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return {
                            "url": url,
                            "title": soup.title.string if soup.title else "No title",
                            "content": text[:10000],  # Limit content length
                            "status": response.status
                        }
                    else:
                        return {
                            "url": url,
                            "error": f"HTTP {response.status}",
                            "status": response.status
                        }
                        
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return {
                "url": url,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return {
                "url": url,
                "error": str(e)
            }
    
    def validate_params(self, **kwargs) -> bool:
        """Validate fetch parameters."""
        if "url" not in kwargs:
            return False
        
        url = kwargs["url"]
        return url and (url.startswith("http://") or url.startswith("https://"))