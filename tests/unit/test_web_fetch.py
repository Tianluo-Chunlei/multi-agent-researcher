"""Test web fetch functionality."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.search import WebFetchTool


async def test_web_fetch():
    """Test web page fetching."""
    fetch_tool = WebFetchTool()
    
    # Test fetching a simple page
    url = "https://example.com"
    print(f"Fetching: {url}\n")
    
    result = await fetch_tool.execute(url)
    
    if result.get("error"):
        print(f"Fetch error: {result['error']}\n")
        return False
    
    print(f"Title: {result.get('title', 'No title')}")
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Content preview: {result.get('content', '')[:500]}...")
    
    return result.get("status") == 200


if __name__ == "__main__":
    success = asyncio.run(test_web_fetch())
    print(f"\n{'✅ Web fetch working!' if success else '❌ Fetch failed'}")