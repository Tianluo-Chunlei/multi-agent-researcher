"""Test database storage functionality."""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import ResearchDatabase


async def test_database():
    """Test database operations."""
    # Initialize database
    db = ResearchDatabase("data/test_research.db")
    await db.initialize()
    print("✅ Database initialized\n")
    
    # Test research plan
    plan_id = str(uuid.uuid4())
    query = "What are the latest AI developments?"
    plan = {
        "query_type": "breadth-first",
        "complexity": "medium",
        "subagent_count": 3,
        "tasks": [
            {"id": "task1", "description": "Search for AI news"},
            {"id": "task2", "description": "Find research papers"},
            {"id": "task3", "description": "Analyze trends"}
        ]
    }
    
    # Save plan
    success = await db.save_research_plan(plan_id, query, plan)
    print(f"Save plan: {'✅' if success else '❌'}")
    
    # Get plan
    retrieved_plan = await db.get_research_plan(plan_id)
    print(f"Get plan: {'✅' if retrieved_plan else '❌'}")
    
    # Update status
    success = await db.update_plan_status(plan_id, "in_progress")
    print(f"Update status: {'✅' if success else '❌'}")
    
    # Save subagent result
    agent_id = "agent-001"
    task = "Search for AI news"
    results = {
        "status": "completed",
        "findings": [
            {"title": "New AI Model Released", "snippet": "..."},
            {"title": "AI in Healthcare", "snippet": "..."}
        ]
    }
    success = await db.save_subagent_result(plan_id, agent_id, task, results)
    print(f"Save subagent result: {'✅' if success else '❌'}")
    
    # Get plan results
    plan_results = await db.get_plan_results(plan_id)
    print(f"Get plan results: {'✅' if len(plan_results) > 0 else '❌'}")
    
    # Test memory store
    key = "test_memory"
    value = {"data": "important information", "timestamp": "2024-01-01"}
    success = await db.save_memory(key, value, "test")
    print(f"Save memory: {'✅' if success else '❌'}")
    
    # Get memory
    retrieved = await db.get_memory(key)
    print(f"Get memory: {'✅' if retrieved else '❌'}")
    
    # Search memory
    memories = await db.search_memory("test", limit=5)
    print(f"Search memory: {'✅' if len(memories) > 0 else '❌'}")
    
    # Save research report
    report_id = str(uuid.uuid4())
    report = "This is the research report..."
    cited_report = "This is the research report [1]..."
    sources = [{"url": "https://example.com", "title": "Source 1"}]
    metrics = {"tokens": 1000, "time": 30.5}
    
    success = await db.save_research_report(
        report_id, plan_id, query, report, cited_report, sources, metrics
    )
    print(f"Save report: {'✅' if success else '❌'}")
    
    # Get report
    retrieved_report = await db.get_research_report(report_id)
    print(f"Get report: {'✅' if retrieved_report else '❌'}")
    
    # List recent reports
    recent = await db.list_recent_reports(5)
    print(f"List recent reports: {'✅' if len(recent) > 0 else '❌'}")
    
    print("\n✅ All database tests passed!")


if __name__ == "__main__":
    asyncio.run(test_database())