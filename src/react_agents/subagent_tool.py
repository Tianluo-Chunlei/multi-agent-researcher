"""Research SubAgent as a tool for Lead Agent."""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
import asyncio
import logging

from .prompts import get_subagent_prompt
from .base_tools import web_search, web_fetch, complete_task
from src.utils.config import config

logger = logging.getLogger(__name__)


class ResearchSubAgentTool:
    """Research SubAgent that can be called as a tool by Lead Agent."""
    
    def __init__(self):
        """Initialize the Research SubAgent."""
        self.model = ChatAnthropic(
            model=config.subagent_model,
            temperature=0.3,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            anthropic_api_url=config.anthropic_base_url
        )
        
        # SubAgent has its own tools
        self.tools = [web_search, web_fetch, complete_task]
        
        # Create the React agent
        self.agent = create_react_agent(
            self.model,
            self.tools,
            prompt=get_subagent_prompt()
        )
    
    async def run(self, task_description: str) -> Dict[str, Any]:
        """Execute a research task.
        
        Args:
            task_description: Detailed description of the research task
            
        Returns:
            Research results including findings and summary
        """
        try:
            logger.info(f"SubAgent starting task: {task_description[:100]}...")
            
            # Create message for the agent
            messages = [HumanMessage(content=task_description)]
            
            # Run the agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config={"configurable": {"thread_id": f"subagent-{hash(task_description)}"}}
            )
            
            # Extract the final report from messages
            final_report = None
            for message in reversed(result["messages"]):
                if hasattr(message, "content") and message.content:
                    # Look for the complete_task tool call result
                    if "Research report submitted successfully" in str(message.content):
                        # Get the previous message which should contain the report
                        idx = result["messages"].index(message)
                        if idx > 0:
                            prev_msg = result["messages"][idx - 1]
                            if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                                for tool_call in prev_msg.tool_calls:
                                    if tool_call["name"] == "complete_task":
                                        final_report = tool_call["args"].get("report", "")
                                        break
                    
                    if final_report:
                        break
            
            # If no complete_task was called, get the last assistant message
            if not final_report:
                for message in reversed(result["messages"]):
                    if hasattr(message, "content") and message.content and message.type == "ai":
                        final_report = message.content
                        break
            
            return {
                "success": True,
                "task": task_description,
                "report": final_report or "No findings reported",
                "message_count": len(result["messages"])
            }
            
        except Exception as e:
            logger.error(f"SubAgent failed: {e}")
            return {
                "success": False,
                "task": task_description,
                "error": str(e),
                "report": f"Research failed: {str(e)}"
            }


# Create tool wrapper for LangChain
@tool
async def run_subagent(task_description: str) -> Dict[str, Any]:
    """Deploy a research subagent to investigate a specific task.
    
    This tool creates and runs a specialized research agent that will:
    1. Plan a research approach for the given task
    2. Execute web searches and fetch relevant content
    3. Synthesize findings into a comprehensive report
    4. Return the research results
    
    Args:
        task_description: Detailed description of what to research, including:
            - Specific objectives and questions to answer
            - Suggested sources or search queries
            - Expected output format
            - Any constraints or focus areas
            
    Returns:
        Research results with findings and summary report
    """
    subagent = ResearchSubAgentTool()
    return await subagent.run(task_description)


# Batch execution tool for parallel subagents
@tool
async def run_parallel_subagents(task_descriptions: list[str]) -> list[Dict[str, Any]]:
    """Deploy multiple research subagents in parallel.
    
    This tool creates and runs multiple specialized research agents simultaneously.
    Each agent works independently on its assigned task.
    
    Args:
        task_descriptions: List of detailed task descriptions for each subagent
            
    Returns:
        List of research results from all subagents
    """
    tasks = []
    for description in task_descriptions:
        subagent = ResearchSubAgentTool()
        tasks.append(subagent.run(description))
    
    results = await asyncio.gather(*tasks)
    return results