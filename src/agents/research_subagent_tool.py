"""
Research Subagent Tool
基于research_subagent.md prompt实现的独立研究工具
作为Lead Agent的工具使用
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from langsmith import trace

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import Tool

from ..config import config
from ..tools.web_search import DuckDuckGoSearchTool
from ..tools.web_fetch import WebContentFetcher
from ..database.db_manager import DatabaseManager
from ..utils.rate_limiter import RateLimiter


class ResearchSubagentTool:
    """
    独立研究子智能体工具
    实现OODA循环、自主研究、智能停止条件
    """
    
    def __init__(self, subagent_id: str = None):
        self.subagent_id = subagent_id or f"research_subagent_{uuid.uuid4().hex[:8]}"
        self.config = config.get_research_subagent_config()
        self.db_manager = DatabaseManager()
        self.rate_limiter = RateLimiter()
        
        # 初始化Anthropic模型
        self.llm = ChatAnthropic(
            model=self.config['model'],
            api_key=self.config['api_key'],
            base_url=self.config['base_url'],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens'],
            timeout=self.config['timeout']
        )
        
        # 初始化研究工具
        self.research_tools = self._setup_research_tools()
        self.tool_map = {tool.name: tool for tool in self.research_tools}
        
        # 研究状态跟踪
        self.tool_call_count = 0
        self.max_tool_calls = self.config.get('max_tool_calls', 15)
        self.research_budget = 10  # 默认预算
        self.sources_found = []
        self.key_findings = []
        
    def _setup_research_tools(self) -> List[Tool]:
        """设置子智能体可用的研究工具"""
        tools = []
        
        # Web搜索工具
        search_tool = Tool(
            name="web_search",
            description="Search the web for current information using search queries. Returns snippets and URLs.",
            func=self._web_search_wrapper
        )
        tools.append(search_tool)
        
        # Web内容获取工具
        fetch_tool = Tool(
            name="web_fetch", 
            description="Fetch complete content from a specific URL. Use this after web_search to get detailed information.",
            func=self._web_fetch_wrapper
        )
        tools.append(fetch_tool)
        
        # 完成任务工具
        complete_tool = Tool(
            name="complete_task",
            description="Complete the research task and submit findings. Use when sufficient information is gathered.",
            func=self._complete_task_wrapper
        )
        tools.append(complete_tool)
        
        return tools
    
    async def _web_search_wrapper(self, query: str) -> str:
        """Web搜索工具包装器"""
        await self.rate_limiter.acquire('search')
        self.tool_call_count += 1
        
        search_tool = DuckDuckGoSearchTool()
        results = await search_tool.search(query, max_results=5)
        
        # 记录源
        for result in results:
            self.sources_found.append({
                'url': result['url'],
                'title': result['title'],
                'type': 'web_search',
                'query': query
            })
        
        # 格式化返回结果
        formatted_results = []
        for result in results:
            formatted_results.append(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Snippet: {result['snippet']}\n"
            )
        
        return "\n".join(formatted_results)
    
    async def _web_fetch_wrapper(self, url: str) -> str:
        """Web内容获取工具包装器"""
        await self.rate_limiter.acquire('fetch')
        self.tool_call_count += 1
        
        fetcher = WebContentFetcher()
        content = await fetcher.fetch_content(url)
        
        # 更新源记录
        for source in self.sources_found:
            if source['url'] == url:
                source['content_length'] = len(content)
                source['fetched'] = True
                break
        
        return content
    
    async def _complete_task_wrapper(self, findings_summary: str) -> str:
        """完成任务工具包装器"""
        return f"TASK_COMPLETED: {findings_summary}"
    
    def _load_research_prompt(self) -> str:
        """加载research_subagent.md prompt"""
        try:
            with open('/Users/chunleicai/Documents/workspace/ai/agent/deep_research/patterns/agents/prompts/research_subagent.md', 'r', encoding='utf-8') as f:
                base_prompt = f.read()
            
            # 添加工具描述
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.research_tools
            ])
            
            # 当前日期
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 替换模板变量
            prompt = base_prompt.replace("{{.CurrentDate}}", current_date)
            
            # 添加工具调用格式说明
            prompt += f"""

Available Tools:
{tool_descriptions}

Tool Usage Format:
When you need to use a tool, format your response as:
Action: [tool_name]
Action Input: [input_for_tool]

You will receive:
Observation: [result_from_tool]

Research Budget: {self.research_budget} tool calls maximum
Current Progress: {self.tool_call_count}/{self.research_budget} tool calls used
"""
            
            return prompt
            
        except FileNotFoundError:
            return """You are a research subagent. Conduct thorough research on the given task using available tools. 
Follow OODA loop: Observe, Orient, Decide, Act. Stop when sufficient information is gathered."""
    
    @trace(name="research_subagent_execute")
    async def execute_research(self, task_prompt: str) -> Dict[str, Any]:
        """
        执行研究任务 - 主要方法
        """
        try:
            # 构建系统prompt
            system_prompt = self._load_research_prompt()
            
            # 初始消息
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"<task>\n{task_prompt}\n</task>")
            ]
            
            # OODA循环执行
            while self.tool_call_count < self.max_tool_calls:
                # 让Subagent决定下一步行动
                response = await self.llm.ainvoke(messages)
                messages.append(response)
                
                # 检查是否完成任务
                if "TASK_COMPLETED:" in response.content:
                    final_findings = response.content.split("TASK_COMPLETED:")[1].strip()
                    break
                
                # 解析并执行工具调用
                if "Action:" in response.content:
                    action_result = await self._parse_and_execute_action(response.content)
                    
                    # 检查是否完成
                    if action_result.startswith("TASK_COMPLETED:"):
                        final_findings = action_result.replace("TASK_COMPLETED:", "").strip()
                        break
                    
                    # 添加观察结果
                    messages.append(HumanMessage(content=f"Observation: {action_result}"))
                
                # 检查是否应该停止（智能停止条件）
                if self._should_stop_research():
                    # 让Agent总结当前发现
                    summary_prompt = HumanMessage(content="Based on your research so far, please provide a comprehensive summary of your findings and complete the task.")
                    messages.append(summary_prompt)
                    
                    final_response = await self.llm.ainvoke(messages)
                    final_findings = final_response.content
                    break
            
            else:
                # 达到最大调用次数，强制完成
                final_findings = "Research completed due to tool call limit. Summary of findings from available sources."
            
            # 编译最终结果
            result = {
                'subagent_id': self.subagent_id,
                'task': task_prompt,
                'findings': final_findings,
                'sources': self.sources_found,
                'tool_calls_used': self.tool_call_count,
                'key_findings': self.key_findings,
                'completed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_result = {
                'subagent_id': self.subagent_id,
                'task': task_prompt,
                'error': str(e),
                'findings': f"Research failed due to error: {str(e)}",
                'sources': self.sources_found,
                'tool_calls_used': self.tool_call_count,
                'completed_at': datetime.now().isoformat()
            }
            return error_result
    
    async def _parse_and_execute_action(self, response_content: str) -> str:
        """解析并执行Action"""
        lines = response_content.strip().split('\n')
        action_line = None
        input_line = None
        
        for line in lines:
            if line.startswith("Action:"):
                action_line = line.replace("Action:", "").strip()
            elif line.startswith("Action Input:"):
                input_line = line.replace("Action Input:", "").strip()
        
        if not action_line:
            return "No valid action found in response."
        
        if action_line not in self.tool_map:
            return f"Unknown action: {action_line}. Available: {list(self.tool_map.keys())}"
        
        try:
            tool = self.tool_map[action_line]
            result = await tool.afunc(input_line) if input_line else await tool.afunc("")
            return str(result)
        except Exception as e:
            return f"Tool execution failed: {str(e)}"
    
    def _should_stop_research(self) -> bool:
        """智能停止条件判断"""
        # 1. 工具调用预算检查
        if self.tool_call_count >= self.research_budget:
            return True
        
        # 2. 信息充分性检查
        if len(self.sources_found) >= 3 and len([s for s in self.sources_found if s.get('fetched')]) >= 2:
            return True
        
        # 3. 递减收益检查（简化版本）
        if self.tool_call_count > 5 and len(self.sources_found) == 0:
            return True  # 没有找到有用信息，应该停止
        
        return False


def create_research_subagent_tool() -> Tool:
    """创建Research Subagent工具供Lead Agent使用"""
    
    async def run_research_subagent(task_prompt: str) -> str:
        """运行研究子智能体"""
        subagent = ResearchSubagentTool()
        result = await subagent.execute_research(task_prompt)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    return Tool(
        name="run_blocking_subagent",
        description="Create and run a specialized research subagent for independent research on a specific task. The subagent will conduct thorough research using web search and content fetching, following OODA loop methodology until sufficient information is gathered.",
        func=run_research_subagent
    )