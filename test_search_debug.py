#!/usr/bin/env python3
"""Debug script to test search functionality."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.search import WebSearchTool
from src.utils.logger import logger

async def test_search():
    """Test search functionality."""
    print("🔍 Testing WebSearchTool...")
    
    # Initialize search tool
    search_tool = WebSearchTool()
    
    # Test search
    try:
        result = await search_tool.execute(query="Python programming", max_results=3)
        print(f"✅ Search successful!")
        print(f"Result keys: {result.keys()}")
        print(f"Success: {result.get('success', 'Not set')}")
        print(f"Data: {result.get('data', 'Not set')}")
        print(f"Error: {result.get('error', 'Not set')}")
        
        if result.get('data'):
            results = result['data'].get('results', [])
            print(f"Number of results: {len(results)}")
            if results:
                print(f"First result: {results[0]}")
        
    except Exception as e:
        print(f"❌ Search failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
