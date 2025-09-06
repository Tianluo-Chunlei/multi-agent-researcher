"""
Research Subagent Tool - 作为Lead Agent的工具
复用现有的SubAgent架构
"""

import json
from typing import Dict, Any
from langsmith import traceable

from src.tools.base import BaseTool
# 延迟导入避免循环依赖
# from src.agents.subagent import ResearchSubagent
from src.prompts.prompt_manager import PromptManager
from src.utils.logger import logger


class SubAgentTool(BaseTool):
    """研究子智能体工具"""
    
    def __init__(self):
        super().__init__(
            name="run_blocking_subagent",
            description="Create and run a specialized research subagent for independent research on a specific task. The subagent will conduct thorough research using web search and content fetching, following OODA loop methodology until sufficient information is gathered."
        )
    
    @traceable(name="run_subagent_tool")
    async def execute(self, task_prompt: str, **kwargs) -> Dict[str, Any]:
        """执行子智能体研究任务
        
        Args:
            task_prompt: 研究任务描述
            
        Returns:
            子智能体研究结果
        """
        try:
            logger.info(f"Starting subagent with task: {task_prompt[:100]}...")
            
            import uuid
            
            # 延迟导入避免循环依赖
            from src.agents.subagent import ResearchSubagent
            
            # 创建子智能体 (使用正确的构造函数)
            agent_id = f"subagent_{uuid.uuid4().hex[:8]}"
            subagent = ResearchSubagent(
                agent_id=agent_id,
                task_description=task_prompt,
                tools=["web_search", "web_fetch", "memory_store"]
            )
            
            # 执行研究任务
            result = await subagent.execute_task(task_prompt)
            
            # 格式化结果
            formatted_result = {
                'subagent_id': agent_id,
                'task': task_prompt,
                'findings': result.get('findings', []),
                'sources': result.get('sources', []),
                'tool_calls_used': getattr(subagent, 'tool_calls_made', 0),
                'status': 'completed' if result.get('findings') else 'failed'
            }
            
            logger.info(f"Subagent completed with {len(formatted_result.get('sources', []))} sources")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Subagent execution failed: {e}")
            return {
                'subagent_id': 'failed',
                'task': task_prompt,
                'findings': f"Subagent failed: {str(e)}",
                'sources': [],
                'tool_calls_used': 0,
                'status': 'error',
                'error': str(e)
            }