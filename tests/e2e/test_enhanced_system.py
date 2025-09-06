"""End-to-end test for the enhanced research system."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph.workflow import ResearchWorkflow
from src.storage.database import ResearchDatabase
from src.utils.tracing import enable_tracing, disable_tracing, is_tracing_enabled


async def test_enhanced_system():
    """Test the enhanced system with all new features."""
    
    print("="*60)
    print("ENHANCED SYSTEM END-TO-END TEST")
    print("="*60)
    
    # 1. Initialize components
    print("\n1. Initializing components...")
    workflow = ResearchWorkflow()
    db = ResearchDatabase("data/test_e2e.db")
    await db.initialize()
    print("   ✅ Database initialized")
    
    # 2. Check tracing
    print("\n2. Checking LangSmith tracing...")
    if is_tracing_enabled():
        print("   ✅ Tracing enabled")
    else:
        print("   ℹ️  Tracing disabled (set LANGSMITH_API_KEY to enable)")
    
    # 3. Test query with real search
    query = "What are the latest breakthroughs in quantum computing in 2024?"
    print(f"\n3. Running research query...")
    print(f"   Query: {query}")
    
    start_time = datetime.now()
    
    try:
        # Run research
        result = await workflow.run_research(query)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Check results
        print("\n4. Validating results...")
        
        checks = {
            "Query ID exists": bool(result.get("query_id")),
            "Query type identified": bool(result.get("query_type")),
            "Complexity assessed": bool(result.get("query_complexity")),
            "Research plan created": bool(result.get("research_plan")),
            "Subagents executed": len(result.get("completed_subagents", [])) > 0,
            "Raw results collected": len(result.get("raw_results", [])) > 0,
            "Report synthesized": bool(result.get("synthesized_text")),
            "Citations added": bool(result.get("cited_text")),
            "Sources included": len(result.get("sources", [])) > 0,
            "Token tracking": result.get("total_tokens_used", 0) > 0
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        # 5. Test database persistence
        print("\n5. Testing database persistence...")
        
        # Save report
        report_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = await db.save_research_report(
            report_id=report_id,
            plan_id=result.get("query_id", ""),
            query=query,
            report=result.get("synthesized_text", ""),
            cited_report=result.get("cited_text", ""),
            sources=result.get("sources", []),
            metrics={
                "tokens": result.get("total_tokens_used", 0),
                "time": execution_time,
                "subagents": len(result.get("completed_subagents", []))
            }
        )
        print(f"   {'✅' if success else '❌'} Report saved to database")
        
        # Retrieve report
        retrieved = await db.get_research_report(report_id)
        print(f"   {'✅' if retrieved else '❌'} Report retrieved from database")
        
        # Test memory store
        await db.save_memory("test_key", {"test": "data"}, "test")
        memory = await db.get_memory("test_key")
        print(f"   {'✅' if memory else '❌'} Memory store working")
        
        # 6. Display results summary
        print("\n6. Results Summary:")
        print(f"   • Query Type: {result.get('query_type', 'Unknown')}")
        print(f"   • Complexity: {result.get('query_complexity', 'Unknown')}")
        print(f"   • Subagents Used: {len(result.get('completed_subagents', []))}")
        print(f"   • Sources Found: {len(result.get('sources', []))}")
        print(f"   • Tokens Used: {result.get('total_tokens_used', 0)}")
        print(f"   • Execution Time: {execution_time:.2f}s")
        
        # 7. Show report preview
        print("\n7. Report Preview (first 500 chars):")
        print("-"*60)
        cited_text = result.get("cited_text", "")
        if cited_text:
            preview = cited_text[:500] + "..." if len(cited_text) > 500 else cited_text
            print(preview)
        else:
            print("No report generated")
        print("-"*60)
        
        # 8. Show sources
        if result.get("sources"):
            print("\n8. Sources Used:")
            for i, source in enumerate(result.get("sources", [])[:5], 1):
                print(f"   {i}. {source.get('title', 'Unknown')}")
                print(f"      {source.get('url', '')}")
        
        # Overall test result
        all_passed = all(checks.values()) and success and retrieved and memory
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check results above")
        print("="*60)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_system())
    sys.exit(0 if success else 1)