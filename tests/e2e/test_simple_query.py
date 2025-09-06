"""Simple end-to-end test for the research system."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.lead_agent import LeadResearchAgent
from src.agents.subagent import ResearchSubagent
from src.agents.citation_agent import CitationAgent


async def test_simple_query():
    """Test a simple query end-to-end."""
    
    query = "What is artificial intelligence?"
    print(f"Query: {query}\n")
    
    # 1. Lead agent analyzes and plans
    print("1. Lead Agent Analysis...")
    lead = LeadResearchAgent()
    analysis = await lead.analyze_query(query)
    print(f"   Type: {analysis['query_type']}, Complexity: {analysis['complexity']}")
    
    # 2. Create plan
    print("\n2. Creating Research Plan...")
    plan = await lead.create_research_plan(
        query, 
        analysis['query_type'],
        analysis['complexity']
    )
    print(f"   Tasks: {len(plan['tasks'])}")
    
    # 3. Execute one subagent
    if plan['tasks']:
        print("\n3. Executing Subagent...")
        task = plan['tasks'][0]
        subagent = ResearchSubagent(
            agent_id="test-001",
            task_description=task['description'],
            tools=["web_search"]
        )
        
        results = await subagent.execute_research()
        print(f"   Findings: {len(results.get('findings', []))}")
        
        if results.get('findings'):
            # 4. Synthesize
            print("\n4. Synthesizing Results...")
            synthesis = await lead.synthesize_results(
                query,
                results['findings'],
                plan
            )
            print(f"   Report length: {len(synthesis['report'])} chars")
            
            # 5. Add citations
            print("\n5. Adding Citations...")
            citation_agent = CitationAgent()
            cited = await citation_agent.add_citations(
                synthesis['report'],
                synthesis['sources']
            )
            
            print("\n" + "="*60)
            print("FINAL REPORT:")
            print("="*60)
            print(cited[:1000] + "..." if len(cited) > 1000 else cited)
            print("="*60)
            
            return True
    
    return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_query())
    print(f"\n{'✅ Success' if success else '❌ Failed'}")