"""Tool manager for Deep Research system."""

from typing import Dict, List, Any, Optional
from src.tools.base import BaseTool
from src.tools.search import WebSearchTool, WebFetchTool
from src.tools.memory import MemoryStoreTool, ResearchPlanMemory
from src.utils.logger import logger


class ToolManager:
    """Manager for all tools in the system."""
    
    def __init__(self):
        """Initialize tool manager."""
        self.tools: Dict[str, BaseTool] = {}
        self._initialize_tools()
        
    def _initialize_tools(self):
        """Initialize all available tools."""
        # Search tools
        self.register_tool(WebSearchTool())
        self.register_tool(WebFetchTool())
        
        # Memory tools
        self.register_tool(MemoryStoreTool())
        self.register_tool(ResearchPlanMemory())
        
        logger.info(f"Initialized {len(self.tools)} tools")
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool.
        
        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self.tools.get(name)
    
    def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        """Get tools available for a specific agent type.
        
        Args:
            agent_type: Type of agent (lead, subagent, citation)
            
        Returns:
            List of available tools
        """
        if agent_type == "lead":
            # Lead agent gets all tools
            return list(self.tools.values())
        elif agent_type == "subagent":
            # Subagents get search and basic memory tools
            return [
                self.tools.get("web_search"),
                self.tools.get("web_fetch"),
                self.tools.get("memory_store")
            ]
        elif agent_type == "citation":
            # Citation agent only needs memory access
            return [
                self.tools.get("memory_store")
            ]
        else:
            return []
    
    def get_tool_descriptions(self, tools: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """Get descriptions of tools for LLM consumption.
        
        Args:
            tools: List of tool names to include, or None for all
            
        Returns:
            List of tool descriptions
        """
        if tools:
            return [
                self.tools[name].to_dict() 
                for name in tools 
                if name in self.tools
            ]
        else:
            return [tool.to_dict() for tool in self.tools.values()]
    
    async def execute_tool(
        self, 
        tool_name: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        return await tool(**kwargs)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all tools.
        
        Returns:
            Usage statistics
        """
        stats = {}
        for name, tool in self.tools.items():
            stats[name] = tool.get_usage_stats()
        
        total_usage = sum(s["usage_count"] for s in stats.values())
        
        return {
            "tools": stats,
            "total_usage": total_usage
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics for all tools."""
        for tool in self.tools.values():
            tool.usage_count = 0
            tool.last_used = None
        
        logger.info("Reset tool usage statistics")