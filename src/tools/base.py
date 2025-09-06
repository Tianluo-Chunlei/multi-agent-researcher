"""Base tool class for Deep Research system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from langsmith import traceable
from src.utils.logger import logger


class BaseTool(ABC):
    """Base class for all tools in the system."""
    
    def __init__(self, name: str, description: str):
        """Initialize base tool.
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
        """
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used = None
        
    @abstractmethod
    @traceable(name="tool_execute")
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Result of tool execution
        """
        pass
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make tool callable.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Result of tool execution
        """
        # Track usage
        self.usage_count += 1
        self.last_used = datetime.now()
        
        # Validate parameters
        if not self.validate_params(**kwargs):
            return self.format_error("Invalid parameters")
        
        try:
            # Execute tool
            result = await self.execute(**kwargs)
            return self.format_output(result)
            
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return self.format_error(str(e))
    
    def validate_params(self, **kwargs) -> bool:
        """Validate tool parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        # Default implementation - override in subclasses
        return True
    
    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format tool output.
        
        Args:
            result: Raw tool result
            
        Returns:
            Formatted output
        """
        return {
            "success": True,
            "data": result,
            "tool": self.name,
            "timestamp": datetime.now().isoformat()
        }
    
    def format_error(self, error: str) -> Dict[str, Any]:
        """Format error output.
        
        Args:
            error: Error message
            
        Returns:
            Formatted error
        """
        return {
            "success": False,
            "error": error,
            "tool": self.name,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this tool.
        
        Returns:
            Usage statistics
        """
        return {
            "name": self.name,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    def to_dict(self) -> Dict[str, str]:
        """Convert tool to dictionary for LLM consumption.
        
        Returns:
            Tool dictionary
        """
        return {
            "name": self.name,
            "description": self.description
        }