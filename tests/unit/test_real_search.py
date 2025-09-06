"""Test real web search functionality."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.search import WebSearchTool


async def test_real_search():
    """Test DuckDuckGo search."""
    search_tool = WebSearchTool()
    
    # Test search
    query = "artificial intelligence latest developments 2024"
    print(f"Searching for: {query}\n")
    
    result = await search_tool.execute(query, max_results=5)
    
    if result.get("error"):
        print(f"Search had an error: {result['error']}\n")
    
    print(f"Found {result['count']} results:\n")
    
    for i, res in enumerate(result["results"], 1):
        print(f"{i}. {res['title']}")
        print(f"   URL: {res['url']}")
        print(f"   Snippet: {res['snippet'][:200]}...")
        print()
    
    return result["count"] > 0


if __name__ == "__main__":
    success = asyncio.run(test_real_search())
    print(f"\n{'✅ Real search working!' if success else '❌ Search failed'}")