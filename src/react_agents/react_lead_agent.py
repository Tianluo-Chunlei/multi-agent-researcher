"""Lead Agent using LangGraph's create_react_agent."""

from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent, ToolNode
from langchain_core.messages import SystemMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool
import asyncio
import os
from datetime import datetime

from src.utils.config import config
from src.utils.logger import logger


class ReactLeadAgent:
    """Lead Agent using LangGraph's React Agent."""
    
    def __init__(self):
        """Initialize the React Lead Agent."""
        # Initialize the LLM with proper configuration
        self.llm = ChatAnthropic(
            model=config.lead_agent_model,
            temperature=0.5,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url if config.anthropic_base_url else None
        )
        
        # Get system prompt
        self.system_message = self._get_system_prompt()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Create the React agent using LangGraph
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_message
        )
        
        logger.info(f"React Lead Agent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the lead agent."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""You are an expert research lead agent. The current date is {current_date}.

Your goal is to research the user's query thoroughly and provide a comprehensive report.

## Process:
1. Analyze the query to determine if it's simple, standard, or complex
2. For simple queries: Use search tools directly to find answers
3. For complex queries: Break down into sub-tasks and research each
4. Synthesize findings into a well-structured report
5. Add citations where appropriate

## Available Tools:
- Search: Find information on the web
- Fetch: Get complete webpage content
- SubAgent: Delegate specific research tasks (for complex queries)

## Guidelines:
- Be thorough but efficient
- Verify information from multiple sources when possible
- Structure your report with clear sections
- Include sources and citations
- Focus on accuracy and relevance

Start by analyzing the query, then proceed with research."""
    
    def _initialize_tools(self) -> List:
        """Initialize and return the tools for the agent."""
        tools = []
        
        # Add search tool - prefer Tavily if API key available
        if os.getenv("TAVILY_API_KEY"):
            search_tool = TavilySearchResults(
                max_results=5,
                description="Search the web for information"
            )
        else:
            # Use DuckDuckGo as fallback
            search_tool = DuckDuckGoSearchRun(
                description="Search the web for information"
            )
        tools.append(search_tool)
        
        # Add webpage fetching tool
        @tool
        def fetch_webpage(url: str) -> str:
            """Fetch the complete content of a webpage.
            
            Args:
                url: URL of the webpage to fetch
                
            Returns:
                The webpage content
            """
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                if docs:
                    content = "\n".join([doc.page_content for doc in docs])
                    if len(content) > 10000:
                        content = content[:10000] + "...[truncated]"
                    return content
                return "Failed to fetch content"
            except Exception as e:
                return f"Error: {str(e)}"
        
        tools.append(fetch_webpage)
        
        # Add subagent tool for complex queries
        @tool
        async def research_subtask(task_description: str) -> str:
            """Research a specific subtask using a specialized subagent.
            
            Args:
                task_description: Detailed description of what to research
                
            Returns:
                Research findings for this subtask
            """
            # Create a simple subagent for the task
            subagent_llm = ChatAnthropic(
                model=config.subagent_model,
                temperature=0.3,
                anthropic_api_key=config.anthropic_api_key,
                base_url=config.anthropic_base_url if config.anthropic_base_url else None
            )
            
            subagent_prompt = f"""You are a research subagent. 
Research the following task and provide detailed findings:

{task_description}

Be thorough and accurate. Focus on facts and cite sources when possible."""
            
            # Create subagent with search tools
            subagent = create_react_agent(
                model=subagent_llm,
                tools=[search_tool, fetch_webpage],
                prompt=subagent_prompt
            )
            
            # Run subagent
            try:
                result = await subagent.ainvoke({
                    "messages": [{"role": "user", "content": task_description}]
                })
                
                # Extract the final message
                if result.get("messages"):
                    return result["messages"][-1].content
                return "No findings from subagent"
                
            except Exception as e:
                logger.error(f"Subagent failed: {e}")
                return f"Subagent error: {str(e)}"
        
        tools.append(research_subtask)
        
        return tools
    
    async def research(self, query: str) -> Dict[str, Any]:
        """Execute a research query.
        
        Args:
            query: The research query
            
        Returns:
            Research results including report and sources
        """
        logger.info(f"Starting research: {query[:100]}...")
        start_time = datetime.now()
        
        try:
            # Run the agent with streaming
            final_report = ""
            messages = []
            
            # Stream the agent execution
            async for chunk in self.agent.astream({
                "messages": [{"role": "user", "content": query}]
            }):
                # Process each chunk
                if "messages" in chunk:
                    messages = chunk["messages"]
                    
                    # Print progress for tool calls
                    for msg in messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                logger.info(f"🔧 Calling tool: {tool_call.get('name', 'unknown')}")
                        
                        # Check if this is an AI message with content
                        if msg.type == "ai" and msg.content:
                            # Update the final report with the latest AI message
                            final_report = msg.content
                            # Print partial content for long responses
                            if len(msg.content) > 100:
                                logger.info(f"📝 Generating response... ({len(msg.content)} chars)")
                
                # Handle agent actions
                if "agent" in chunk:
                    agent_messages = chunk["agent"].get("messages", [])
                    for msg in agent_messages:
                        if msg.type == "ai" and msg.content:
                            logger.info(f"💭 Agent thinking: {msg.content[:100]}...")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Research completed in {execution_time:.2f}s")
            
            return {
                "success": True,
                "query": query,
                "report": final_report,
                "execution_time": execution_time,
                "message_count": len(messages)
            }
            
        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "report": ""
            }