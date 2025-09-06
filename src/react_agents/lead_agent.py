"""Lead React Agent implementation."""

from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
import asyncio
import logging
from datetime import datetime

from .prompts import get_lead_agent_prompt
from .subagent_tool import run_subagent, run_parallel_subagents
from .citation_tool import add_citations
from .base_tools import web_search, complete_task
from src.utils.config import config

logger = logging.getLogger(__name__)


class LeadReactAgent:
    """Lead Research Agent that coordinates the research process."""
    
    def __init__(self):
        """Initialize the Lead React Agent."""
        # Use Opus model for lead agent
        self.model = ChatAnthropic(
            model=config.lead_agent_model,
            temperature=0.5,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            anthropic_api_url=config.anthropic_base_url
        )
        
        # Lead agent tools
        self.tools = [
            run_subagent,
            run_parallel_subagents,
            add_citations,
            web_search,  # For quick lookups only
            complete_task
        ]
        
        # Create the React agent with system prompt
        self.agent = create_react_agent(
            self.model,
            self.tools,
            prompt=get_lead_agent_prompt()
        )
        
        self.research_history = []
    
    async def research(self, query: str) -> Dict[str, Any]:
        """Execute a research query.
        
        Args:
            query: The research query from the user
            
        Returns:
            Research results including the final report
        """
        try:
            logger.info(f"Starting research for: {query[:100]}...")
            start_time = datetime.now()
            
            # Create initial message
            messages = [HumanMessage(content=f"""Please research the following query and provide a comprehensive report:

{query}

Remember to:
1. Analyze the query type (depth-first, breadth-first, or straightforward)
2. Create a research plan with appropriate number of subagents
3. Deploy subagents with clear, specific instructions
4. Synthesize findings into a comprehensive report
5. Add citations to support claims
6. Use the complete_task tool to submit the final report""")]
            
            # Run the agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config={
                    "configurable": {
                        "thread_id": f"lead-{hash(query)}",
                        "recursion_limit": 50
                    }
                }
            )
            
            # Extract the final report
            final_report = None
            sources = []
            
            # Look for complete_task call in messages
            for message in reversed(result["messages"]):
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call["name"] == "complete_task":
                            final_report = tool_call["args"].get("report", "")
                            break
                if final_report:
                    break
            
            # Extract sources from subagent results
            for message in result["messages"]:
                if hasattr(message, "content") and "url" in str(message.content):
                    # Try to extract URLs from content
                    import re
                    urls = re.findall(r'https?://[^\s]+', str(message.content))
                    for url in urls[:10]:  # Limit to 10 sources
                        sources.append({"url": url, "title": "Research Source"})
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Store in history
            self.research_history.append({
                "query": query,
                "report": final_report,
                "sources": sources,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Research completed in {execution_time:.2f} seconds")
            
            return {
                "success": True,
                "query": query,
                "report": final_report or "No report generated",
                "sources": sources,
                "execution_time": execution_time,
                "message_count": len(result["messages"])
            }
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "report": f"Research failed: {str(e)}"
            }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get research history.
        
        Returns:
            List of previous research sessions
        """
        return self.research_history
    
    def clear_history(self):
        """Clear research history."""
        self.research_history = []
        logger.info("Research history cleared")