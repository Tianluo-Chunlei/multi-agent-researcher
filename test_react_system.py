#!/usr/bin/env python3
"""
测试ReAct多智能体系统
"""

import asyncio
import sys
import os

# 添加src目录到path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.react_research_system import ReactMultiAgentResearchSystem


async def test_react_system():
    """测试ReAct多智能体系统"""
    
    print("🚀 Initializing ReAct Multi-Agent Research System...")
    system = ReactMultiAgentResearchSystem()
    
    # 简单测试查询
    test_query = "What are the main benefits of renewable energy?"
    
    print(f"\n📋 Testing Query: {test_query}")
    print("=" * 60)
    
    try:
        result = await system.research(test_query)
        
        print(f"\n✅ Research completed successfully!")
        print(f"📊 Results:")
        print(f"  - Method: {result.get('method', 'unknown')}")
        print(f"  - Iterations: {result.get('iterations', 0)}")
        print(f"  - Sources: {len(result.get('sources', []))}")
        print(f"  - Subagents: {len(result.get('subagent_results', []))}")
        
        print(f"\n📝 Final Report:")
        report = result.get('final_report', 'No report generated')
        print("-" * 40)
        print(report)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_react_system())
    exit(0 if success else 1)