"""
简单清晰的ReAct多智能体系统
使用LangGraph内置的ReAct Agent
"""

import os
from typing import List, Dict, Any
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage

# 设置环境变量
from dotenv import load_dotenv
load_dotenv()


# 1. 定义工具 - 简单直接

@tool
def web_search(query: str) -> str:
    """Search the web for information."""
    search = DuckDuckGoSearchRun()
    return search.run(query)


@tool
async def run_research_subagent(task: str) -> str:
    """
    Run a research subagent for a specific task.
    The subagent will conduct independent research and return findings.
    """
    # 创建子智能体 (使用更便宜的模型)
    subagent_llm = ChatAnthropic(
        model=os.getenv('SUBAGENT_MODEL', 'claude-3-5-sonnet-20241022'),
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        base_url=os.getenv('ANTHROPIC_BASE_URL')
    )
    
    # 简单的子智能体prompt
    prompt = f"""You are a research subagent. Research this specific task thoroughly:

Task: {task}

Provide a comprehensive summary of your findings. Be factual and cite sources where possible.
"""
    
    response = await subagent_llm.ainvoke([HumanMessage(content=prompt)])
    return f"Subagent findings for '{task}':\n{response.content}"


@tool
def add_citations(text: str, sources: List[str]) -> str:
    """
    Add citations to a text based on sources.
    This is a simplified version - in production would be more sophisticated.
    """
    # 简单的引用添加逻辑
    cited_text = text
    for i, source in enumerate(sources, 1):
        # 在相关句子后添加引用标记
        cited_text = cited_text.replace(". ", f" [{i}]. ", 1)
    
    # 添加引用列表
    citations_section = "\n\n## References\n"
    for i, source in enumerate(sources, 1):
        citations_section += f"[{i}] {source}\n"
    
    return cited_text + citations_section


# 2. 创建主Agent - 使用LangGraph的ReAct

def create_lead_agent():
    """创建Lead Agent - 简单直接使用LangGraph ReAct"""
    
    # 初始化LLM
    llm = ChatAnthropic(
        model=os.getenv('LEAD_AGENT_MODEL', 'claude-3-opus-20240229'),
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        base_url=os.getenv('ANTHROPIC_BASE_URL'),
        temperature=0.1
    )
    
    # 工具列表
    tools = [
        web_search,
        run_research_subagent,
        add_citations
    ]
    
    # 系统prompt - 基于patterns但简化
    system_prompt = f"""You are an expert research lead agent. Today is {datetime.now().strftime('%Y-%m-%d')}.

Your goal is to research the user's query comprehensively and provide an excellent report.

## Process:
1. Analyze the query to understand what information is needed
2. Use web_search for quick facts and current information
3. Use run_research_subagent for in-depth research on specific aspects (can run multiple in parallel)
4. Synthesize findings into a comprehensive report
5. Use add_citations to properly cite your sources

## Guidelines:
- Be thorough but efficient
- Use subagents for complex subtopics
- Always cite your sources
- Provide balanced, factual information

You have full autonomy to decide how to research the query."""
    
    # 创建ReAct agent
    agent = create_react_agent(
        llm,
        tools,
        messages_modifier=system_prompt
    )
    
    return agent


# 3. 主系统类 - 简洁明了

class SimpleReactSystem:
    """简单的ReAct多智能体研究系统"""
    
    def __init__(self):
        self.agent = create_lead_agent()
        print("✅ Initialized Simple ReAct Multi-Agent System")
    
    async def research(self, query: str) -> Dict[str, Any]:
        """执行研究"""
        print(f"\n🔍 Researching: {query}")
        
        # 调用agent
        result = await self.agent.ainvoke({
            "messages": [HumanMessage(content=query)]
        })
        
        # 提取最终消息
        final_message = result["messages"][-1].content if result["messages"] else "No result"
        
        return {
            "query": query,
            "report": final_message,
            "message_count": len(result["messages"]),
            "timestamp": datetime.now().isoformat()
        }


# 4. 测试

async def test():
    """测试系统"""
    system = SimpleReactSystem()
    
    # 测试查询
    query = "What are the main benefits and challenges of quantum computing in 2024?"
    
    result = await system.research(query)
    
    print("\n" + "="*60)
    print("📝 Research Report:")
    print("="*60)
    print(result["report"])
    print("\n" + "="*60)
    print(f"✅ Completed with {result['message_count']} messages")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test())