"""
ReAct Research System - 新的三智能体协作系统入口
基于patterns/agents/prompts重新设计的真正多智能体系统
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from src.agents.lead_agent import LeadResearchAgent
from src.storage.database import DatabaseManager
from src.utils.logger import logger
from src.utils.config import config


class ReactMultiAgentResearchSystem:
    """
    ReAct模式的多智能体研究系统
    Lead Agent作为自主决策的ReAct智能体，子智能体和Citations Agent作为工具
    """
    
    def __init__(self):
        self.lead_agent = LeadResearchAgent()
        self.db_manager = DatabaseManager()
        logger.info("Initialized ReAct Multi-Agent Research System")
    
    async def research(self, query: str) -> Dict[str, Any]:
        """
        执行研究任务
        
        Args:
            query: 研究查询
            
        Returns:
            研究结果
        """
        session_id = None
        
        try:
            logger.info(f"Starting ReAct research: {query}")
            
            # 创建数据库会话
            session_id = await self.db_manager.create_session(
                query=query,
                agent_type="react_multi_agent"
            )
            
            # 使用Lead Agent的ReAct模式进行研究
            result = await self.lead_agent.research_with_tools(query)
            
            # 保存结果到数据库
            await self.db_manager.save_final_result(
                session_id,
                result.get('final_report', ''),
                metadata={
                    'method': 'react_multi_agent',
                    'iterations': result.get('iterations', 0),
                    'sources_count': len(result.get('sources', [])),
                    'subagents_used': len(result.get('subagent_results', []))
                }
            )
            
            # 添加会话信息
            result['session_id'] = session_id
            result['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"ReAct research completed successfully in {result.get('iterations', 0)} iterations")
            return result
            
        except Exception as e:
            logger.error(f"ReAct research failed: {e}")
            
            if session_id:
                await self.db_manager.save_final_result(
                    session_id,
                    f"Research failed: {str(e)}",
                    metadata={'error': True, 'exception': str(e)}
                )
            
            raise


async def main():
    """测试ReAct多智能体系统"""
    
    # 测试查询
    test_queries = [
        "What are the latest developments in quantum computing in 2024?",
        "Compare the economic impacts of renewable energy vs fossil fuels",
        "What is the current status of AI safety research?"
    ]
    
    system = ReactMultiAgentResearchSystem()
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing Query: {query}")
        print(f"{'='*60}")
        
        try:
            result = await system.research(query)
            
            print(f"\n✅ Research completed successfully!")
            print(f"📊 Statistics:")
            print(f"  - Iterations: {result.get('iterations', 0)}")
            print(f"  - Sources found: {len(result.get('sources', []))}")
            print(f"  - Subagents used: {len(result.get('subagent_results', []))}")
            print(f"  - Session ID: {result.get('session_id')}")
            
            print(f"\n📝 Final Report Preview:")
            report = result.get('final_report', '')
            preview = report[:500] + "..." if len(report) > 500 else report
            print(preview)
            
            # 等待一下再处理下一个查询
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"\n❌ Research failed: {e}")
        
        # 只测试第一个查询，避免运行太久
        break


if __name__ == "__main__":
    asyncio.run(main())