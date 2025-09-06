"""
True Multi-Agent Research System - Lead Agent v2
基于research_lead_agent.md实现的ReAct模式Lead Agent
使用LangGraph框架支持，但Agent是自主决策的ReAct智能体
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Annotated
from langsmith import trace

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from ..config import config
from ..tools.web_search import DuckDuckGoSearchTool
from ..tools.web_fetch import WebContentFetcher
from ..database.db_manager import DatabaseManager
from ..utils.rate_limiter import RateLimiter
from .research_subagent_tool import create_research_subagent_tool
from .citations_agent_tool import create_citations_agent_tool


class LeadAgentState(TypedDict):
    """Lead Agent状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    session_id: str
    iteration_count: int
    final_report: str
    completed_subagents: List[Dict]
    sources: List[Dict]


class TrueLeadAgent:
    """
    真正的多智能体Lead Agent - LangGraph + ReAct模式
    基于research_lead_agent.md prompt实现
    """
    
    def __init__(self):
        self.config = config.get_lead_agent_config()
        self.system_config = config.get_system_config()
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
        
        # 设置工具
        self.tools = self._setup_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 创建LangGraph
        self.graph = self._create_graph()
        
        # 存储子智能体结果
        self.subagent_results = []
        self.all_sources = []
    
    def _setup_tools(self) -> List[Tool]:
        """设置Lead Agent可用的工具"""
        tools = []
        
        # Web搜索工具
        search_tool = Tool(
            name="web_search",
            description="Search the web for current information using search queries. Returns snippets and URLs of relevant results.",
            func=self._web_search_wrapper
        )
        tools.append(search_tool)
        
        # Web内容获取工具
        fetch_tool = Tool(
            name="web_fetch", 
            description="Fetch complete content from a specific URL. Use this after web_search to get detailed information from promising sources.",
            func=self._web_fetch_wrapper
        )
        tools.append(fetch_tool)
        
        # 研究子智能体工具 (核心工具)
        subagent_tool = create_research_subagent_tool()
        tools.append(subagent_tool)
        
        # 引用添加工具
        citations_tool = create_citations_agent_tool()
        tools.append(citations_tool)
        
        # 完成任务工具
        complete_tool = Tool(
            name="complete_task",
            description="Submit the final comprehensive research report when all necessary research is completed and synthesized. This ends the research process.",
            func=self._complete_task_wrapper
        )
        tools.append(complete_tool)
        
        return tools
    
    async def _web_search_wrapper(self, query: str) -> str:
        """Web搜索工具包装器"""
        await self.rate_limiter.acquire('search')
        search_tool = DuckDuckGoSearchTool()
        results = await search_tool.search(query, max_results=5)
        
        # 记录源
        for result in results:
            source = {
                'url': result['url'],
                'title': result['title'],
                'snippet': result['snippet'],
                'type': 'web_search',
                'query': query,
                'found_at': datetime.now().isoformat()
            }
            self.all_sources.append(source)
        
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
        fetcher = WebContentFetcher()
        content = await fetcher.fetch_content(url)
        
        # 更新源记录
        for source in self.all_sources:
            if source['url'] == url:
                source['content'] = content[:5000]  # 限制长度
                source['content_length'] = len(content)
                source['fetched'] = True
                break
        else:
            # 如果没找到现有记录，创建新的
            self.all_sources.append({
                'url': url,
                'content': content[:5000],
                'content_length': len(content),
                'type': 'web_content',
                'fetched': True,
                'found_at': datetime.now().isoformat()
            })
        
        return content
    
    async def _complete_task_wrapper(self, final_report: str) -> str:
        """完成任务工具包装器"""
        return f"RESEARCH_COMPLETED: {final_report}"
    
    def _load_lead_agent_prompt(self) -> str:
        """加载research_lead_agent.md prompt"""
        try:
            with open('/Users/chunleicai/Documents/workspace/ai/agent/deep_research/patterns/agents/prompts/research_lead_agent.md', 'r', encoding='utf-8') as f:
                base_prompt = f.read()
            
            # 当前日期
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 替换模板变量
            prompt = base_prompt.replace("{{.CurrentDate}}", current_date)
            
            # 添加工具描述
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tools
            ])
            
            prompt += f"""

Available Tools:
{tool_descriptions}

IMPORTANT INSTRUCTIONS:
- You are a lead research agent with full autonomy to decide your research strategy
- Use run_blocking_subagent for parallel research on different aspects of the query  
- Use web_search and web_fetch for quick initial research or verification
- Use add_citations to properly cite your final report
- Use complete_task only when you have a comprehensive, well-researched final report
- Follow the research process guidelines in your instructions above
- Adapt your strategy dynamically based on findings from subagents
"""
            
            return prompt
            
        except FileNotFoundError:
            return """You are an expert research lead agent. Research the user's query comprehensively by using available tools including creating subagents for parallel research. Provide a thorough, well-cited final report."""
    
    def _create_graph(self) -> StateGraph:
        """创建LangGraph图"""
        
        # 定义agent节点
        async def agent_node(state: LeadAgentState) -> LeadAgentState:
            """主agent节点 - ReAct决策"""
            
            # 检查迭代次数
            if state.get("iteration_count", 0) >= self.config.get('max_iterations', 20):
                # 强制完成
                final_msg = AIMessage(content="Research completed due to iteration limit. Providing summary based on available information.")
                return {
                    **state,
                    "messages": [final_msg],
                    "final_report": "Research summary based on available findings."
                }
            
            # 调用LLM
            response = await self.llm_with_tools.ainvoke(state["messages"])
            
            # 检查是否完成研究
            if "RESEARCH_COMPLETED:" in response.content:
                final_report = response.content.split("RESEARCH_COMPLETED:")[1].strip()
                return {
                    **state,
                    "messages": [response],
                    "final_report": final_report
                }
            
            return {
                **state,
                "messages": [response],
                "iteration_count": state.get("iteration_count", 0) + 1
            }
        
        # 创建图
        workflow = StateGraph(LeadAgentState)
        
        # 添加节点
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # 添加边
        workflow.add_edge(START, "agent")
        
        # 条件边：决定是使用工具还是结束
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                END: END
            }
        )
        
        workflow.add_edge("tools", "agent")
        
        # 编译图
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    @trace(name="true_lead_agent_research")
    async def research(self, query: str) -> Dict[str, Any]:
        """
        主研究方法
        """
        # 创建研究会话
        session_id = await self.db_manager.create_session(
            query=query,
            agent_type="true_lead_agent_v2"
        )
        
        try:
            # 构建系统prompt
            system_prompt = self._load_lead_agent_prompt()
            
            # 初始状态
            initial_state = LeadAgentState(
                messages=[
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Research Query: {query}")
                ],
                query=query,
                session_id=session_id,
                iteration_count=0,
                final_report="",
                completed_subagents=[],
                sources=[]
            )
            
            # 运行图
            config_dict = {"configurable": {"thread_id": session_id}}
            final_state = await self.graph.ainvoke(initial_state, config=config_dict)
            
            # 提取最终报告
            final_report = final_state.get("final_report", "")
            if not final_report:
                # 从最后的消息中提取
                last_message = final_state["messages"][-1] if final_state["messages"] else None
                if last_message and hasattr(last_message, 'content'):
                    final_report = last_message.content
            
            # 保存结果到数据库
            await self.db_manager.save_final_result(
                session_id,
                final_report,
                metadata={
                    'iterations': final_state.get("iteration_count", 0),
                    'sources_found': len(self.all_sources),
                    'subagents_used': len(self.subagent_results)
                }
            )
            
            # 返回结果
            result = {
                'query': query,
                'session_id': session_id,
                'final_report': final_report,
                'sources': self.all_sources,
                'subagent_results': self.subagent_results,
                'iterations': final_state.get("iteration_count", 0),
                'completed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            await self.db_manager.save_final_result(
                session_id,
                error_msg,
                metadata={'error': True, 'exception': str(e)}
            )
            raise