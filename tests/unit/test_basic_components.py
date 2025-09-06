"""Basic tests for core components."""

import asyncio
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import config
from src.tools.memory import MemoryStoreTool
from src.tools.search import WebSearchTool, WebFetchTool
from src.managers.tool_manager import ToolManager


async def test_memory_tool():
    """Test memory storage tool."""
    print("\n=== Testing Memory Tool ===")
    
    tool = MemoryStoreTool()
    
    # Test save
    result = await tool.execute(
        action="save",
        key="test_key",
        value={"data": "test_value"},
        type="test"
    )
    print(f"Save result: {result}")
    assert result["saved"] == True
    
    # Test retrieve
    result = await tool.execute(
        action="retrieve",
        key="test_key"
    )
    print(f"Retrieve result: {result}")
    assert result["found"] == True
    assert result["value"]["data"] == "test_value"
    
    # Test list
    result = await tool.execute(
        action="list",
        type="test"
    )
    print(f"List result: {result}")
    assert result["count"] > 0
    
    # Test delete
    result = await tool.execute(
        action="delete",
        key="test_key"
    )
    print(f"Delete result: {result}")
    assert result["deleted"] == True
    
    print("✓ Memory tool tests passed")


async def test_search_tool():
    """Test web search tool."""
    print("\n=== Testing Search Tool ===")
    
    tool = WebSearchTool()
    
    # Test search using the tool's __call__ method (which includes formatting)
    result = await tool(
        query="artificial intelligence",
        max_results=3
    )
    print(f"Search result: {result}")
    assert result["success"] == True
    assert result["data"]["count"] == 3
    assert len(result["data"]["results"]) == 3
    
    print("✓ Search tool tests passed")


async def test_tool_manager():
    """Test tool manager."""
    print("\n=== Testing Tool Manager ===")
    
    manager = ToolManager()
    
    # Test tool registration
    tools = manager.get_tool_descriptions()
    print(f"Registered tools: {[t['name'] for t in tools]}")
    assert len(tools) >= 4
    
    # Test get tools for agent
    lead_tools = manager.get_tools_for_agent("lead")
    print(f"Lead agent tools: {len(lead_tools)}")
    assert len(lead_tools) >= 4
    
    subagent_tools = manager.get_tools_for_agent("subagent")
    print(f"Subagent tools: {len(subagent_tools)}")
    assert len(subagent_tools) == 3
    
    # Test tool execution
    result = await manager.execute_tool(
        "web_search",
        query="test query",
        max_results=2
    )
    print(f"Tool execution result: {result}")
    assert result["success"] == True
    
    print("✓ Tool manager tests passed")


async def test_config():
    """Test configuration."""
    print("\n=== Testing Configuration ===")
    
    print(f"Lead agent model: {config.lead_agent_model}")
    print(f"Subagent model: {config.subagent_model}")
    print(f"Max concurrent subagents: {config.max_concurrent_subagents}")
    print(f"Database path: {config.database_path}")
    
    # Check required environment variables
    assert config.anthropic_api_key is not None
    assert len(config.anthropic_api_key) > 0
    
    print("✓ Configuration tests passed")


async def test_all():
    """Run all basic tests."""
    await test_config()
    await test_memory_tool()
    await test_search_tool()
    await test_tool_manager()
    return True


async def main():
    """Run all basic tests."""
    print("=" * 50)
    print("RUNNING BASIC COMPONENT TESTS")
    print("=" * 50)
    
    try:
        await test_config()
        await test_memory_tool()
        await test_search_tool()
        await test_tool_manager()
        
        print("\n" + "=" * 50)
        print("ALL BASIC TESTS PASSED ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)